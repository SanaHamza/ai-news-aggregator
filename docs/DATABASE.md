# Database Documentation

## Database Overview

The app uses PostgreSQL. Python code talks to PostgreSQL through SQLAlchemy.

SQLAlchemy is used as an ORM. ORM means "Object Relational Mapper." It lets the project define database tables as Python classes.

Connection code lives in:

- `app/database/connection.py`

Table definitions live in:

- `app/database/models.py`

Reusable queries live in:

- `app/database/repository.py`

## Connection Setup

`app/database/connection.py` reads these environment variables:

- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `POSTGRES_HOST`
- `POSTGRES_PORT`
- `POSTGRES_DB`

It builds a database URL like this:

```text
postgresql://USER:PASSWORD@HOST:PORT/DB_NAME
```

Then it creates:

- `engine`: the SQLAlchemy database engine.
- `SessionLocal`: a factory for database sessions.
- `get_session()`: creates a session object.

## Tables

### `users`

Stores app accounts.

| Column | Meaning |
| --- | --- |
| `id` | Unique user ID |
| `email` | User email, unique |
| `username` | Username, unique |
| `password_hash` | Hashed password, not the real password |
| `role` | `normal_user` or `super_user` |
| `is_active` | Whether the account can be used |
| `created_at` | Account creation time |
| `updated_at` | Last update time |

### `user_sessions`

Stores browser login sessions.

| Column | Meaning |
| --- | --- |
| `id` | Unique session ID |
| `user_id` | Links session to `users.id` |
| `token_hash` | SHA-256 hash of the browser session token |
| `created_at` | Session creation time |
| `expires_at` | When the session expires |
| `revoked_at` | Set when user logs out or session is revoked |

Relationship:

- Many sessions can belong to one user.

### `youtube_videos`

Stores YouTube videos found from channel RSS feeds.

| Column | Meaning |
| --- | --- |
| `video_id` | YouTube video ID, primary key |
| `title` | Video title |
| `url` | YouTube URL |
| `channel_id` | YouTube channel ID |
| `published_at` | Video publish date |
| `description` | RSS description |
| `transcript` | Transcript text, or unavailable marker |
| `created_at` | Row creation time |

### `openai_articles`

Stores OpenAI News RSS articles.

| Column | Meaning |
| --- | --- |
| `guid` | Unique article ID |
| `title` | Article title |
| `url` | Article URL |
| `description` | RSS description |
| `published_at` | Article publish date |
| `category` | RSS category if present |
| `created_at` | Row creation time |

### `anthropic_articles`

Stores Anthropic articles from RSS feed mirrors.

| Column | Meaning |
| --- | --- |
| `guid` | Unique article ID |
| `title` | Article title |
| `url` | Article URL |
| `description` | RSS description |
| `published_at` | Article publish date |
| `category` | RSS category if present |
| `markdown` | Full page content converted to Markdown |
| `created_at` | Row creation time |

### `digests`

Stores the final summarized items shown in the dashboard.

| Column | Meaning |
| --- | --- |
| `id` | Digest ID, usually `article_type:article_id` |
| `article_type` | `youtube`, `openai`, or `anthropic` |
| `article_id` | Original source ID |
| `url` | Original source URL |
| `title` | LLM-created digest title |
| `summary` | LLM-created summary |
| `created_at` | Publish time or creation time |

### `pipeline_runs`

Stores history for pipeline runs started from the Admin Panel.

| Column | Meaning |
| --- | --- |
| `id` | Unique run ID |
| `status` | `running`, `success`, or `failed` |
| `triggered_by_user_id` | Super User who started the run |
| `started_at` | Run start time |
| `finished_at` | Run finish time |
| `duration_seconds` | How long the run took |
| `result` | JSON summary of the run |
| `error` | Error text if it failed |

### `audit_logs`

Stores admin actions.

| Column | Meaning |
| --- | --- |
| `id` | Unique log ID |
| `actor_user_id` | User who performed the action |
| `action` | Action name, for example `user.update` |
| `target_type` | What kind of thing changed |
| `target_id` | ID of the thing changed |
| `details` | JSON details about the change |
| `created_at` | When the action happened |

## Relationship Diagram

```mermaid
erDiagram
    users ||--o{ user_sessions : has
    users ||--o{ pipeline_runs : triggers
    users ||--o{ audit_logs : performs

    youtube_videos ||--o| digests : summarized_as
    openai_articles ||--o| digests : summarized_as
    anthropic_articles ||--o| digests : summarized_as

    users {
        string id
        string email
        string username
        string role
        boolean is_active
    }

    user_sessions {
        string id
        string user_id
        string token_hash
        datetime expires_at
    }

    digests {
        string id
        string article_type
        string article_id
        string title
    }
```

Note: `digests.article_id` is not a formal database foreign key because it can point to different source tables depending on `article_type`.

## ORM Models

Models are Python classes in `app/database/models.py`.

Examples:

- `User` maps to `users`.
- `UserSession` maps to `user_sessions`.
- `YouTubeVideo` maps to `youtube_videos`.
- `OpenAIArticle` maps to `openai_articles`.
- `AnthropicArticle` maps to `anthropic_articles`.
- `Digest` maps to `digests`.
- `PipelineRun` maps to `pipeline_runs`.
- `AuditLog` maps to `audit_logs`.

Each class defines columns with SQLAlchemy, for example:

```python
email = Column(String(255), nullable=False, unique=True, index=True)
```

This means:

- Store the value as a string.
- It cannot be empty.
- It must be unique.
- Add an index so lookups are faster.

## Repository Queries and Data Flow

`app/database/repository.py` groups common database operations.

Important methods:

- `bulk_create_youtube_videos`: inserts new YouTube videos, skips duplicates.
- `bulk_create_openai_articles`: inserts OpenAI articles, skips duplicates.
- `bulk_create_anthropic_articles`: inserts Anthropic articles, skips duplicates.
- `get_youtube_videos_without_transcript`: finds videos needing transcripts.
- `update_youtube_video_transcript`: saves transcript text.
- `get_anthropic_articles_without_markdown`: finds Anthropic articles needing Markdown.
- `update_anthropic_article_markdown`: saves converted Markdown.
- `get_articles_without_digest`: finds source items that do not yet have a digest.
- `create_digest`: saves an LLM summary.
- `get_recent_digests`: gets recent digest rows for ranking and email.

## Data Flow Example

```mermaid
flowchart TD
    A["Scraper finds OpenAI RSS item"] --> B["Repository checks if guid exists"]
    B --> C{"Already stored?"}
    C -->|Yes| D["Skip duplicate"]
    C -->|No| E["Insert openai_articles row"]
    E --> F["Digest service reads articles without digest"]
    F --> G["OpenAI generates title and summary"]
    G --> H["Repository inserts digests row"]
    H --> I["Dashboard displays digest"]
```

## Migration Details

The project does not currently use Alembic.

Instead, it uses:

- `Base.metadata.create_all(bind=engine)` to create missing tables.
- `app/database/migrations.py` for small safe upgrades to existing tables.

Current migration helper:

- Adds `users.role` if missing.
- Fills old rows with `normal_user`.
- Adds `users.is_active` if missing.
- Fills old rows with `TRUE`.

It runs in:

- `app/api.py` during app startup.
- `app/database/create_tables.py` when manually creating tables.

## Common Database Commands

Start PostgreSQL:

```bash
cd docker
docker-compose up -d
```

Create tables:

```bash
python app/database/create_tables.py
```

Promote a user to Super User:

```bash
python -m app.scripts.promote_super_user your-email@example.com
```
