# Two-Tier To-Do App

**Tier 1 – Application:** Flask (Python). Serves the web page and a JSON API.
**Tier 2 – Database:** PostgreSQL. Stores the tasks.

```
Browser  ->  Flask app (port 5000)  ->  PostgreSQL (port 5432)
```

## API

| Method | Path              | What it does              |
|--------|-------------------|---------------------------|
| GET    | /health           | Is the app alive?         |
| GET    | /api/tasks        | List all tasks            |
| POST   | /api/tasks        | Add a task `{"text": ""}` |
| PATCH  | /api/tasks/<id>   | Set done `{"done": true}` |
| DELETE | /api/tasks/<id>   | Delete a task             |

## Configuration (environment variables)

See `.env.example`: DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD, PORT.

## Run it without containers first (to confirm it works)

1. Have a PostgreSQL server running with a database `todos`, user `todo_user`, password `todo_pass`.
2. `pip install -r requirements.txt`
3. `python app.py`
4. Open http://localhost:5000

## Things to think about when you containerize it

- One container per tier. How will the app find the database by name, not `localhost`?
- The app retries the DB connection on startup. Why does that matter when containers start together?
- Where does the database data live? What happens to tasks if the DB container is removed?
- Keep passwords out of the image. How do you pass in the env vars?
- Flask's built-in server is for development. What would you run in a real image?
- Which ports should be published to your machine, and which should stay private?
- Add a health check using `/health`.
- Stretch: put the two containers on a user-defined network, then try adding a third tier (e.g. nginx in front).
# todo-two-tier
