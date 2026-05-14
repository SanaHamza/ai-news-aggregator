# Module Reference

This page explains every important project file in beginner-friendly language.

## Root Files

### `main.py`

Command-line entry point for the pipeline.

It calls:

```python
run_daily_pipeline(hours=hours, top_n=top_n)
```

You can run:

```bash
python main.py
```

or:

```bash
python main.py 24 10
```

### `pyproject.toml`

Defines:

- Project name.
- Python version.
- Dependencies.
- Development dependencies.

### `README.md`

Main project setup guide.

### `uv.lock`

Lock file used by `uv` to install exact dependency versions.

## `app/`

Main Python application package.

### `app/api.py`

FastAPI application.

Responsibilities:

- Serves the frontend HTML file.
- Handles signup, login, logout, and current user.
- Returns dashboard article data.
- Runs the pipeline for Super Users.
- Exposes Admin Panel APIs.
- Creates tables and runs small migrations on startup.
- Stores in-memory pipeline status.

Important endpoints:

- `GET /`
- `POST /api/auth/signup`
- `POST /api/auth/login`
- `GET /api/auth/me`
- `POST /api/auth/logout`
- `GET /api/articles`
- `POST /api/pipeline/run`
- `GET /api/pipeline/status`
- `GET /api/admin/summary`
- `GET /api/admin/users`
- `PATCH /api/admin/users/{user_id}`
- `GET /api/admin/pipeline/runs`
- `GET /api/admin/audit-logs`

### `app/auth.py`

Authentication and authorization helpers.

Responsibilities:

- Validate signup input.
- Hash passwords.
- Verify passwords.
- Create session tokens.
- Store session token hashes.
- Set and clear cookies.
- Load the current user from a cookie.
- Block deactivated users.
- Check Super User access.

Important functions:

- `register_user`
- `authenticate_user`
- `create_session`
- `get_current_user`
- `require_super_user`
- `serialize_user`

### `app/config.py`

Stores YouTube channel IDs used by the YouTube scraper.

### `app/daily_runner.py`

Main pipeline orchestrator.

Runs:

1. Scrapers.
2. Anthropic Markdown processing.
3. YouTube transcript processing.
4. Digest generation.
5. Email digest sending.

Important function:

- `run_daily_pipeline`

### `app/runner.py`

Runs all source scrapers.

Responsibilities:

- Read YouTube channel IDs from config.
- Fetch YouTube videos.
- Fetch OpenAI articles.
- Fetch Anthropic articles.
- Save new source rows to the database.

Important function:

- `run_scrapers`

### `app/example.env`

Example environment variable file.

Do not put real secrets in this example file.

## `app/agent/`

LLM agent classes.

### `app/agent/digest_agent.py`

Uses OpenAI to create a short digest title and summary.

Input:

- Article title.
- Article content.
- Article type.

Output:

- `DigestOutput`

### `app/agent/curator_agent.py`

Uses OpenAI to rank digests for the configured user profile.

Input:

- User profile.
- Recent digests.

Output:

- `RankedDigestList`

### `app/agent/email_agent.py`

Uses OpenAI to create the email greeting and introduction.

Also defines response models for email digest data.

Important classes:

- `EmailIntroduction`
- `RankedArticleDetail`
- `EmailDigestResponse`
- `EmailAgent`

## `app/database/`

Database connection, models, queries, and migration helpers.

### `app/database/connection.py`

Builds the PostgreSQL connection URL from environment variables.

Creates:

- `engine`
- `SessionLocal`
- `get_session`

### `app/database/models.py`

Defines SQLAlchemy ORM models.

Models:

- `User`
- `UserSession`
- `YouTubeVideo`
- `OpenAIArticle`
- `AnthropicArticle`
- `Digest`
- `PipelineRun`
- `AuditLog`

### `app/database/repository.py`

Reusable database query and write methods.

Used heavily by:

- Scrapers.
- Processing services.
- Pipeline.

### `app/database/migrations.py`

Small idempotent migration helper for the current RBAC upgrade.

It adds:

- `users.role`
- `users.is_active`

### `app/database/create_tables.py`

Manual script to create database tables.

Run:

```bash
python app/database/create_tables.py
```

## `app/profiles/`

User profile data used for personalized ranking.

### `app/profiles/user_profile.py`

Defines `USER_PROFILE`.

Used by:

- `CuratorAgent`
- `EmailAgent`

The profile includes:

- Name.
- Background.
- Interests.
- Preferences.
- Expertise level.

## `app/scrapers/`

Code that collects source content.

### `app/scrapers/youtube.py`

Collects YouTube videos from channel RSS feeds and fetches transcripts.

Important classes:

- `YouTubeScraper`
- `ChannelVideo`
- `Transcript`

### `app/scrapers/openai.py`

Collects OpenAI News articles from:

```text
https://openai.com/news/rss.xml
```

Important class:

- `OpenAIScraper`

### `app/scrapers/anthropic.py`

Collects Anthropic articles from RSS feed mirrors.

Also converts article URLs to Markdown using Docling.

Important class:

- `AnthropicScraper`

## `app/services/`

Business logic steps used by the pipeline.

### `app/services/process_youtube.py`

Finds YouTube videos without transcripts and fills them.

Stores `__UNAVAILABLE__` when no transcript exists.

### `app/services/process_anthropic.py`

Finds Anthropic articles without Markdown and converts them with Docling.

### `app/services/process_digest.py`

Finds source items without digests and summarizes them with `DigestAgent`.

### `app/services/process_curator.py`

Ranks recent digests with `CuratorAgent`.

This is useful as a standalone curation check.

### `app/services/process_email.py`

Generates and sends the final email digest.

Uses:

- `CuratorAgent`
- `EmailAgent`
- `send_email`
- `digest_to_html`

### `app/services/email.py`

Email utilities.

Responsibilities:

- Convert Markdown to HTML.
- Convert digest objects to HTML email.
- Send email through Gmail SMTP.

## `app/scripts/`

Local helper scripts.

### `app/scripts/promote_super_user.py`

Promotes an existing account to Super User after verifying the account password.

Run:

```bash
python -m app.scripts.promote_super_user your-email@example.com
```

## `frontend/`

Browser UI.

### `frontend/static-desing.html`

Single-page static UI.

Contains:

- Login/signup screen.
- News dashboard.
- Admin Panel.
- CSS theme.
- JavaScript API calls.

## `docker/`

Docker setup.

### `docker/docker-compose.yml`

Runs PostgreSQL 17 locally.

Creates:

- PostgreSQL container.
- Persistent `postgres_data` volume.
- Health check.

## `docs/`

Project documentation.

Important docs:

- `README.md`
- `PROJECT_OVERVIEW.md`
- `ARCHITECTURE.md`
- `DATABASE.md`
- `API.md`
- `LLM_INTEGRATION.md`
- `NEWS_PROVIDERS.md`
- `PIPELINE_AND_JOBS.md`
- `ENVIRONMENT_DOCKER_DEPLOYMENT.md`
- `DEVELOPER_WORKFLOWS.md`
- `TERMINOLOGY.md`
- `TROUBLESHOOTING.md`
