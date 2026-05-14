# Terminology

This page explains common terms in simple English.

## API

An API is a way for one program to talk to another program.

In this project, the browser talks to FastAPI endpoints such as:

```text
GET /api/articles
```

## Endpoint

An endpoint is one URL handled by the backend.

Example:

```text
POST /api/auth/login
```

## FastAPI

FastAPI is the Python web framework used by this project.

It receives browser requests and returns responses.

## PostgreSQL

PostgreSQL is the database used to store users, articles, digests, sessions, and logs.

## ORM

ORM means Object Relational Mapper.

It lets developers write Python classes that represent database tables.

Example:

```python
class User(Base):
    __tablename__ = "users"
```

## SQLAlchemy

SQLAlchemy is the ORM library used in this project.

It helps the app query and update PostgreSQL.

## Model

In this project, "model" can mean two things:

1. Database model: a Python class that maps to a table.
2. LLM model: an OpenAI model like `gpt-4.1`.

Read the context to know which meaning is intended.

## Migration

A migration is a database change.

Example:

- Add a new column.
- Create a new table.

This project uses a small helper in `app/database/migrations.py` instead of Alembic.

## Session

A session means a logged-in browser state.

The app stores a session token in an HTTP-only cookie and stores a hash of that token in PostgreSQL.

## Cookie

A cookie is a small value saved by the browser for a website.

This app uses a cookie named:

```text
ai_news_session
```

## HTTP-only Cookie

An HTTP-only cookie cannot be read by JavaScript in the browser.

This makes the session safer from some browser attacks.

## Authentication

Authentication means proving who the user is.

Example:

- Logging in with username/email and password.

## Authorization

Authorization means checking what the user is allowed to do.

Example:

- A normal user can read articles.
- A Super User can run the pipeline.

## RBAC

RBAC means Role-Based Access Control.

The app uses two roles:

- `normal_user`
- `super_user`

## Super User

A Super User is an admin account.

Super Users can:

- Open Admin Panel.
- Manage users.
- Run the pipeline.

## Pipeline

The pipeline is the full workflow that collects, processes, summarizes, ranks, and emails news.

## Scraper

A scraper is code that collects content from another website or feed.

Example:

- `OpenAIScraper` reads OpenAI News RSS.

## RSS

RSS is a simple feed format websites use to publish updates.

The app uses RSS to discover new articles and videos.

## Digest

A digest is a short summary of a source article or video.

In this project, digests are created by OpenAI and saved in the `digests` table.

## LLM

LLM means Large Language Model.

OpenAI models are LLMs. The app uses them to summarize, rank, and write email text.

## Prompt

A prompt is the instruction sent to an LLM.

Example:

- "Create a digest for this article."

## Temperature

Temperature controls how creative or consistent an LLM response is.

Lower values are more consistent.
Higher values are more creative.

## Structured Output

Structured output means asking the LLM to return data in a specific shape.

The app uses Pydantic schemas so the LLM output can become Python objects.

## Pydantic

Pydantic validates data in Python.

The app uses it for:

- API request bodies.
- Scraper result objects.
- OpenAI structured response objects.

## Background Task

A background task runs after the API has accepted a request.

The app uses FastAPI background tasks to run the pipeline after a Super User starts it.

## SMTP

SMTP is a protocol for sending email.

The app uses Gmail SMTP to send the digest email.

## Docker

Docker runs software in containers.

This project uses Docker Compose to run PostgreSQL locally.

## Docker Compose

Docker Compose starts one or more containers using a YAML file.

This project has:

```text
docker/docker-compose.yml
```

## Environment Variable

An environment variable is a setting read by the app at runtime.

Example:

```env
OPENAI_API_KEY=...
```

## `.env`

`.env` is a local file for environment variables.

It should not be committed because it can contain secrets.

## Audit Log

An audit log records important admin actions.

Example:

- User role changed.
- Pipeline started.

## Health Check

A health check is a simple check that tells whether a service is running.

The Docker PostgreSQL service has a health check using `pg_isready`.
