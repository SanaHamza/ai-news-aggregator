# Logging and Monitoring

## Logging Overview

The project uses Python's built-in `logging` module.

Most logs are written to the terminal where the Python process is running.

There is no external monitoring system configured yet.

## Where Logging Is Configured

### API

File:

- `app/api.py`

Setup:

```python
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
```

Used for:

- Database startup messages.
- Frontend file loading errors.
- Article fetch errors.
- Pipeline background task logs.

### Pipeline

File:

- `app/daily_runner.py`

Setup:

```python
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
```

Used for:

- Pipeline start.
- Each pipeline step.
- Counts for scraped and processed items.
- Email success or failure.
- Final duration.

### Service Scripts

Files:

- `app/services/process_digest.py`
- `app/services/process_curator.py`
- `app/services/process_email.py`

Used for:

- Processing counts.
- LLM success or failure.
- Curation output.
- Email generation status.

## Audit Logs

Admin actions are also stored in the database table:

```text
audit_logs
```

Current audit events:

- `pipeline.trigger`
- `user.update`

The Admin Panel shows recent audit logs.

## Pipeline Monitoring

The app tracks pipeline status in two places:

### 1. In-memory status

Stored in `app/api.py`:

```python
pipeline_status = {
    "status": "idle",
    "last_run": None,
    "error": None,
    "current_run_id": None,
}
```

This powers:

```text
GET /api/pipeline/status
```

### 2. Database history

Stored in:

```text
pipeline_runs
```

This powers Admin Panel pipeline history.

## What To Watch During Development

Watch the terminal for:

- Database connection errors.
- OpenAI errors.
- Email SMTP errors.
- Scraper failures.
- Pipeline step counts.

## Current Monitoring Limitations

The app does not currently have:

- Metrics.
- Health endpoint.
- Alerting.
- Log files.
- Centralized logging.
- Error tracking like Sentry.

## Suggested Future Improvements

- Add `GET /api/health`.
- Add structured JSON logs.
- Add request logging middleware.
- Add Sentry or similar error tracking.
- Add metrics for pipeline duration and failures.
- Add alerts when email sending fails.
