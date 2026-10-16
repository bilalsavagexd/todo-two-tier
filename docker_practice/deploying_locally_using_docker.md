## Step 1: Write the Dockerfile for the app

Create `Dockerfile` in the project root:

```
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["python", "app.py"]
```

Also create `.dockerignore`, which keeps junk out of the image:

```
__pycache__
.env
.git
*.zip
```

## Step 2: Manually deploying it

Create a private network so containers can communicate by name

```
docker network create todo-net
```

Create a named volume for persistent database storage

```
docker volume create todo-data
```

Tier 2: Start the PostgreSQL database

```
docker run -d \
  --name db \
  --network todo-net \
  -v todo-data:/var/lib/postgresql/data \
  -e POSTGRES_DB=todos \
  -e POSTGRES_USER=todo_user \
  -e POSTGRES_PASSWORD=todo_pass \
  postgres:16
```

Open `http://localhost:5000`

Some Handy Commands:

```
docker ps                  # running containers
docker logs -f app         # follow the app's logs
docker exec -it db psql -U todo_user -d todos   # open a SQL shell, try: SELECT * FROM tasks;
docker stop app db && docker rm app db          # clean up containers
```

## Step 3: Deploying using Docker Compose

Create `compose.yaml`:

```
services:
  db:
    image: postgres:16
    environment:
      POSTGRES_DB: todos
      POSTGRES_USER: todo_user
      POSTGRES_PASSWORD: todo_pass
    volumes:
      - db-data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U todo_user -d todos"]
      interval: 5s
      timeout: 3s
      retries: 5

  app:
    build: .
    ports:
      - "5000:5000"
    environment:
      DB_HOST: db
      DB_NAME: todos
      DB_USER: todo_user
      DB_PASSWORD: ${DB_PASSWORD}
    depends_on:
      db:
        condition: service_healthy

volumes:
  db-data:
```

Run it:

```
docker compose up --build      # start everything
docker compose down            # stop and remove containers (keeps the volume)
docker compose down -v         # also deletes the volume (your data!)
```

