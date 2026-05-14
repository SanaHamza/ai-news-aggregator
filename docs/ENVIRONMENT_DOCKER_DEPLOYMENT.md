# Environment, Docker, and Deployment

## Environment Variables

The app reads environment variables from `.env` using `python-dotenv`.

Example file:

- `app/example.env`

Your real `.env` should stay private and should not be committed.

## Required Variables

### `OPENAI_API_KEY`

Used by:

- `DigestAgent`
- `CuratorAgent`
- `EmailAgent`

Purpose:

- Allows the app to call OpenAI models.

Example:

```env
OPENAI_API_KEY=your-openai-api-key
```

### `MY_EMAIL`

Used by:

- `app/services/email.py`

Purpose:

- Sender email address.
- Default recipient for the digest email.

Example:

```env
MY_EMAIL=your-email@gmail.com
```

### `APP_PASSWORD`

Used by:

- `app/services/email.py`

Purpose:

- Gmail app password for SMTP login.

This is not your normal Gmail password. For Gmail, create an App Password from your Google account security settings.

Example:

```env
APP_PASSWORD=your-gmail-app-password
```

### PostgreSQL Variables

Used by:

- `app/database/connection.py`
- `docker/docker-compose.yml`

Variables:

```env
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=ai_news_aggregator
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
```

### `AUTH_COOKIE_SECURE`

Used by:

- `app/auth.py`

Purpose:

- Controls whether auth cookies require HTTPS.

Local development:

```env
AUTH_COOKIE_SECURE=false
```

Production with HTTPS:

```env
AUTH_COOKIE_SECURE=true
```

## Optional Variables

### `PROXY_USERNAME` and `PROXY_PASSWORD`

Used by:

- `app/scrapers/youtube.py`

Purpose:

- Optional Webshare proxy credentials for YouTube transcript requests.

Example:

```env
PROXY_USERNAME=
PROXY_PASSWORD=
```

## Docker Setup

Docker is used for PostgreSQL.

File:

- `docker/docker-compose.yml`

Service:

- `postgres`

Image:

```text
postgres:17
```

Container name:

```text
ai-news-aggregator-db
```

## Start PostgreSQL

From the project root:

```bash
cd docker
docker-compose up -d
cd ..
```

## Stop PostgreSQL

```bash
cd docker
docker-compose down
cd ..
```

## Persistent Data

Docker Compose uses a named volume:

```text
postgres_data
```

This means database data remains even if the container stops.

To remove the database data completely:

```bash
cd docker
docker-compose down -v
cd ..
```

Be careful: `-v` deletes the database volume.

## Create Tables

Run:

```bash
python app/database/create_tables.py
```

The FastAPI app also creates missing tables on startup.

## Deployment Flow

This project currently has local Docker only for PostgreSQL. A simple deployment flow would be:

1. Create a production PostgreSQL database.
2. Set production environment variables.
3. Run the FastAPI app with Uvicorn or a process manager.
4. Serve behind HTTPS.
5. Set `AUTH_COOKIE_SECURE=true`.
6. Configure a scheduler if you want automatic pipeline runs.

## Production Notes

For production, consider:

- A real migration tool such as Alembic.
- A job queue for pipeline runs.
- Centralized logs.
- Secrets manager instead of `.env`.
- HTTPS termination.
- Backups for PostgreSQL.
- Rate limiting for auth endpoints.
