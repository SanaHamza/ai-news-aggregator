# Developer Workflows

## Running Locally

### 1. Start PostgreSQL

```bash
cd docker
docker-compose up -d
cd ..
```

### 2. Install Dependencies

Using `uv`:

```bash
python -m uv sync
```

Or using pip:

```bash
pip install -e .
```

### 3. Create Tables

```bash
python app/database/create_tables.py
```

### 4. Start The Web App

```bash
python -m uvicorn app.api:app --reload
```

Open:

```text
http://localhost:8000
```

### 5. Create First Super User

First sign up in the browser. Then run:

```bash
python -m app.scripts.promote_super_user your-email@example.com
```

Log out and log back in.

## Running The Pipeline

From the command line:

```bash
python main.py
```

With custom values:

```bash
python main.py 24 10
```

From the UI:

1. Log in as a Super User.
2. Open Admin Panel.
3. Click Run Pipeline.

## Testing

There is no automated test suite yet.

Recommended manual checks:

1. Signup works.
2. Login works.
3. Logout works.
4. Normal user can see articles.
5. Normal user cannot see Admin or Run Pipeline.
6. Normal user direct `POST /api/pipeline/run` returns `403`.
7. Super User can open Admin Panel.
8. Super User can update another user.
9. Pipeline run creates a `pipeline_runs` row.
10. Admin action creates an `audit_logs` row.

## Syntax Checks

Compile Python files:

```bash
python -m compileall app
```

If your machine uses `py` on Windows:

```bash
py -m compileall app
```

## Debugging API Issues

Start with:

```bash
python -m uvicorn app.api:app --reload
```

Then watch the terminal logs.

Common checks:

- Is PostgreSQL running?
- Does `.env` have the right database settings?
- Is the user logged in?
- Is the user a Super User?
- Is `OPENAI_API_KEY` set?
- Is `APP_PASSWORD` set before sending email?

## Debugging Database Issues

Check Docker:

```bash
cd docker
docker-compose ps
```

Recreate tables:

```bash
python app/database/create_tables.py
```

If the schema is old, startup should run the RBAC migration helper automatically.

## Debugging LLM Issues

Check:

- `OPENAI_API_KEY` exists.
- The key has access to the configured model.
- The source content is not empty.
- The terminal logs for errors from the agent classes.

## Debugging Email Issues

Check:

- `MY_EMAIL` is set.
- `APP_PASSWORD` is set.
- Gmail App Password is valid.
- The account allows SMTP with app passwords.

## Deployment Checklist

- Set production `.env` values.
- Use a production PostgreSQL database.
- Run table creation/migrations.
- Serve the app over HTTPS.
- Set `AUTH_COOKIE_SECURE=true`.
- Create the first Super User.
- Confirm normal users cannot access admin endpoints.
- Configure backups for PostgreSQL.
- Configure logs and alerting.

## Common Commands

| Task | Command |
| --- | --- |
| Start DB | `cd docker && docker-compose up -d` |
| Stop DB | `cd docker && docker-compose down` |
| Create tables | `python app/database/create_tables.py` |
| Start web app | `python -m uvicorn app.api:app --reload` |
| Run pipeline | `python main.py` |
| Promote admin | `python -m app.scripts.promote_super_user email@example.com` |
| Compile check | `python -m compileall app` |
