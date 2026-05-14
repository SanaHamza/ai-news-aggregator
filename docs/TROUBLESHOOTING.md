# Troubleshooting

## PostgreSQL Is Not Running

Symptoms:

- App starts but database requests fail.
- Login or signup fails.
- Terminal shows database connection errors.

Fix:

```bash
cd docker
docker-compose up -d
cd ..
```

Check status:

```bash
cd docker
docker-compose ps
```

## Tables Do Not Exist

Symptoms:

- Errors mention missing tables such as `users` or `digests`.

Fix:

```bash
python app/database/create_tables.py
```

The FastAPI app also tries to create missing tables on startup.

## Cannot Log In

Possible causes:

- Wrong email or username.
- Wrong password.
- Account is deactivated.
- Database is not running.

Fix:

1. Confirm PostgreSQL is running.
2. Try logging in with email instead of username.
3. If account is deactivated, ask a Super User to reactivate it.

## Admin Button Does Not Show

Cause:

- Your account is not a Super User.

Fix:

```bash
python -m app.scripts.promote_super_user your-email@example.com
```

Then log out and log back in.

## Normal User Gets `403 Forbidden`

This is expected when a normal user tries to access admin routes or run the pipeline.

Only Super Users can use:

- `/api/pipeline/run`
- `/api/pipeline/status`
- `/api/admin/*`

## OpenAI Calls Fail

Symptoms:

- Digest generation fails.
- Ranking fails.
- Email generation fails.
- Logs mention OpenAI errors.

Common causes:

- `OPENAI_API_KEY` is missing.
- API key is invalid.
- The configured model is not available to the key.
- Network connection issue.

Fix:

1. Check `.env`.
2. Confirm `OPENAI_API_KEY` is set.
3. Confirm the key works in your OpenAI account.
4. Try a smaller run with fewer articles.

## Gmail Email Fails

Symptoms:

- Pipeline completes scraping and digest steps but email fails.
- Logs mention SMTP login failure.

Common causes:

- `MY_EMAIL` is missing.
- `APP_PASSWORD` is missing.
- App password is invalid.
- Gmail account does not allow app passwords.

Fix:

1. Set `MY_EMAIL`.
2. Create a Gmail App Password.
3. Set `APP_PASSWORD`.
4. Run the pipeline again.

## YouTube Transcripts Are Missing

This can be normal.

Some videos do not have transcripts, or transcripts can be disabled.

The app stores:

```text
__UNAVAILABLE__
```

when transcripts cannot be fetched.

Optional fix:

- Set `PROXY_USERNAME` and `PROXY_PASSWORD` if transcript requests are blocked.

## Anthropic Markdown Conversion Fails

Possible causes:

- Article page cannot be fetched.
- Docling cannot parse the page.
- Network issue.

Current behavior:

- The article remains without Markdown.
- Digest generation skips Anthropic articles without Markdown.

## Pipeline Says It Is Already Running

Cause:

- `pipeline_status.status` is `running`.

Fix:

- Wait for the current run to finish.
- If the server crashed during a run, restart the server. The in-memory status resets.

## Pipeline History Is Empty

Cause:

- Only Admin Panel/API-triggered pipeline runs create `pipeline_runs` rows.
- Older command-line runs may not appear there.

Fix:

- Run the pipeline from the Admin Panel.

## Browser Shows Old UI

Possible causes:

- Browser cache.
- Server not restarted.

Fix:

1. Hard refresh the browser.
2. Restart Uvicorn.
3. Make sure you are opening `http://localhost:8000`.

## Port Already In Use

Symptoms:

- Uvicorn cannot bind to port `8000`.

Fix:

Use another port:

```bash
python -m uvicorn app.api:app --reload --port 8001
```

Open:

```text
http://localhost:8001
```

## Docker Volume Has Old Data

Sometimes you want a completely fresh database.

Warning: this deletes local PostgreSQL data.

```bash
cd docker
docker-compose down -v
docker-compose up -d
cd ..
python app/database/create_tables.py
```

## Python Command Not Found

On Windows, try:

```bash
py -m uvicorn app.api:app --reload
```

or activate your virtual environment first:

```bash
.venv\Scripts\activate
```

## Dependency Install Issues

Try:

```bash
python -m uv sync
```

or:

```bash
pip install -e .
```

If the virtual environment is broken, recreate it:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e .
```
