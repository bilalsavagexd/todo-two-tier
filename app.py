import os
import time

import psycopg2
import psycopg2.extras
from flask import Flask, jsonify, request, send_from_directory

app = Flask(__name__, static_folder="static")

# All configuration comes from environment variables (nothing hard-coded).
DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "localhost"),
    "port": os.environ.get("DB_PORT", "5432"),
    "dbname": os.environ.get("DB_NAME", "todos"),
    "user": os.environ.get("DB_USER", "todo_user"),
    "password": os.environ.get("DB_PASSWORD", "todo_pass"),
}


def get_conn():
    return psycopg2.connect(**DB_CONFIG)


def init_db(retries=10, delay=2):
    """Create the table. Retries because the database may start after the app."""
    for attempt in range(1, retries + 1):
        try:
            with get_conn() as conn, conn.cursor() as cur:
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS tasks (
                        id SERIAL PRIMARY KEY,
                        text TEXT NOT NULL,
                        done BOOLEAN NOT NULL DEFAULT FALSE
                    )
                    """
                )
            print("Database ready.")
            return
        except psycopg2.OperationalError as e:
            print(f"DB not ready (attempt {attempt}/{retries}): {e}")
            time.sleep(delay)
    raise RuntimeError("Could not connect to the database.")


# ---------- Tier 1: serves the web page ----------
@app.route("/")
def index():
    return send_from_directory("static", "index.html")


# ---------- Tier 1: the API ----------
@app.route("/health")
def health():
    return jsonify(status="ok")


@app.route("/api/tasks", methods=["GET"])
def list_tasks():
    with get_conn() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute("SELECT id, text, done FROM tasks ORDER BY id")
        return jsonify(cur.fetchall())


@app.route("/api/tasks", methods=["POST"])
def add_task():
    text = (request.get_json(silent=True) or {}).get("text", "").strip()
    if not text:
        return jsonify(error="text is required"), 400
    with get_conn() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute("INSERT INTO tasks (text) VALUES (%s) RETURNING id, text, done", (text,))
        return jsonify(cur.fetchone()), 201


@app.route("/api/tasks/<int:task_id>", methods=["PATCH"])
def update_task(task_id):
    done = bool((request.get_json(silent=True) or {}).get("done"))
    with get_conn() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            "UPDATE tasks SET done = %s WHERE id = %s RETURNING id, text, done",
            (done, task_id),
        )
        row = cur.fetchone()
    return (jsonify(row), 200) if row else (jsonify(error="not found"), 404)


@app.route("/api/tasks/<int:task_id>", methods=["DELETE"])
def delete_task(task_id):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("DELETE FROM tasks WHERE id = %s", (task_id,))
    return "", 204


# Initialize the database when the application module is imported.
init_db()


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "5000"))
    )
