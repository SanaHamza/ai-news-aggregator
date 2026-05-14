# Signup, Login, Logout, and Session Logic

This app now has a simple first-party authentication flow built into the existing FastAPI and static HTML setup.

## What Was Added

- `users` table for account records.
- `user_sessions` table for active browser sessions.
- Signup with `email`, `username`, and `password`.
- Login with either email or username.
- Logout button in the dashboard header.
- Protected API routes for articles.
- Super User-only routes for admin actions and pipeline actions.
- Browser session persistence through an HTTP-only cookie.
- Frontend auth screen with inline validation, password visibility toggle, and password strength hints.

## Backend Files

- `app/database/models.py`
  - Adds `User` and `UserSession` SQLAlchemy models.
  - Adds `role` and `is_active` fields to users.
  - Adds `PipelineRun` and `AuditLog` models for admin history.
  - Existing news models are unchanged.

- `app/auth.py`
  - Hashes passwords with Python's built-in `hashlib.pbkdf2_hmac`.
  - Verifies passwords with `hmac.compare_digest`.
  - Creates random opaque session tokens with `secrets.token_urlsafe`.
  - Stores only a SHA-256 hash of the session token in the database.
  - Sets and clears the `ai_news_session` cookie.
  - Provides the `get_current_user` FastAPI dependency for protected routes.
  - Provides the `require_super_user` FastAPI dependency for admin-only routes.

- `app/api.py`
  - Adds:
    - `POST /api/auth/signup`
    - `POST /api/auth/login`
    - `GET /api/auth/me`
    - `POST /api/auth/logout`
  - Protects:
    - `GET /api/articles`
  - Restricts to Super Users:
    - `POST /api/pipeline/run`
    - `GET /api/pipeline/status`
    - `/api/admin/*`
  - Runs `Base.metadata.create_all(bind=engine)` on startup so missing auth tables are created automatically.
  - Runs the small RBAC migration helper so old databases get the new user fields.

## Roles

New accounts start as `normal_user`.

To make the first admin, create the account from the signup form, then run:

```bash
python -m app.scripts.promote_super_user your-email@example.com
```

The script asks for that account's password, promotes the account, and activates it.
Log out and log back in after the update. The Admin button should appear.

For a simple admin guide, see `docs/ADMIN_PANEL.md`.

## Frontend File

- `frontend/static-desing.html`
  - Shows login/signup when there is no valid session.
  - Calls `/api/auth/me` on load to restore an existing session.
  - Switches to the news dashboard after signup or login.
  - Calls `/api/auth/logout` and clears the UI state when the logout button is clicked.
  - Keeps article filtering and search for all users.
  - Shows pipeline controls and the Admin Panel only to Super Users.

## Session Flow

1. User signs up or logs in.
2. FastAPI verifies the credentials.
3. FastAPI creates a random session token.
4. The raw token is sent to the browser as the `ai_news_session` HTTP-only cookie.
5. The database stores only the SHA-256 hash of that token.
6. Protected endpoints hash the incoming cookie token and look up a valid, unexpired, non-revoked session.
7. Logout marks the matching session as revoked and deletes the browser cookie.

## Password Rules

The backend requires:

- At least 8 characters.
- At least one letter.
- At least one number.

The frontend mirrors those rules with a small password strength meter, but the backend remains the source of truth.

## Cookie Security

The cookie is:

- `HttpOnly`, so JavaScript cannot read it.
- `SameSite=Lax`, which helps reduce cross-site request risk.
- Valid for 7 days.
- `Secure` only when `AUTH_COOKIE_SECURE=true`.

For local development, keep:

```env
AUTH_COOKIE_SECURE=false
```

For HTTPS production deployments, use:

```env
AUTH_COOKIE_SECURE=true
```

## Running It

Start PostgreSQL, then run:

```bash
python -m uvicorn app.api:app --reload
```

Open:

```text
http://localhost:8000
```

Create a user from the signup form. After that, the dashboard APIs require a valid session.
