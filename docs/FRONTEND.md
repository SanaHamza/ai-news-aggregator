# Frontend Documentation

## Frontend Overview

The frontend is a single static file:

```text
frontend/static-desing.html
```

It contains:

- HTML layout.
- CSS theme and responsive styles.
- JavaScript app state and API calls.

FastAPI serves this file at:

```text
GET /
```

## Main Screens

### Auth Screen

Shown when the user is not logged in.

Features:

- Login form.
- Signup form.
- Password visibility toggle.
- Password strength hints.
- Inline error messages.

### News Dashboard

Shown after login.

Features:

- Search box.
- Category tabs:
  - All.
  - YouTube.
  - OpenAI.
  - Anthropic.
- Article cards.
- User chip.
- Logout button.

### Admin Panel

Shown only to Super Users.

Features:

- System stats.
- User management.
- Pipeline trigger.
- Pipeline history.
- Audit logs.

## Frontend State

The JavaScript has a `state` object:

```js
const state = {
  user: null,
  articles: [],
  activeTab: 'all',
  activeView: 'news',
  searchQuery: '',
  pipelineRunning: false,
  pollInterval: null,
  adminLoaded: false
};
```

Meaning:

- `user`: current logged-in user.
- `articles`: digest cards from the API.
- `activeTab`: selected category.
- `activeView`: `news` or `admin`.
- `searchQuery`: dashboard search text.
- `pipelineRunning`: whether pipeline UI shows running.
- `pollInterval`: timer for pipeline status checks.
- `adminLoaded`: whether admin data has been loaded.

## API Calls

The frontend calls:

- `/api/auth/me`
- `/api/auth/login`
- `/api/auth/signup`
- `/api/auth/logout`
- `/api/articles`
- `/api/pipeline/run`
- `/api/pipeline/status`
- `/api/admin/summary`
- `/api/admin/users`
- `/api/admin/pipeline/runs`
- `/api/admin/audit-logs`

All calls use:

```js
credentials: 'same-origin'
```

This makes the browser include the session cookie.

## Access Control In The UI

The frontend checks:

```js
state.user?.role === 'super_user'
```

If the user is not a Super User:

- Run Pipeline button is hidden.
- Pipeline status pill is hidden.
- Admin button is hidden.
- Pipeline polling stops.

Important: this is only for user experience. Real security is enforced by FastAPI with `require_super_user`.

## Article Rendering

Articles are loaded from:

```text
GET /api/articles
```

The frontend filters them by:

- Active category tab.
- Search query.

Each card displays:

- Image or generated SVG background.
- Category badge.
- Title.
- Summary.
- Date.
- Source.
- Read More link.

## Admin User Updates

The Admin Panel renders each user with:

- Role dropdown.
- Active checkbox.
- Save button.

When Save is clicked, the frontend sends:

```text
PATCH /api/admin/users/{user_id}
```

With body:

```json
{
  "role": "super_user",
  "is_active": true
}
```

## Responsive Design

The CSS uses media queries for:

- Tablet width: fewer columns and stacked header.
- Mobile width: one-column cards and admin rows.

The style is based on CSS variables:

```css
--bg
--panel
--ink
--muted
--line
--accent
--teal
--rose
--amber
--green
```

## Current Frontend Limitations

- It is one large file, which is easy to serve but harder to maintain.
- There is no frontend build system.
- There are no frontend tests.
- There is no client-side router.

## Possible Future Improvements

- Split CSS and JavaScript into separate files.
- Add frontend tests.
- Add a small router if more pages are added.
- Add toast messages for admin actions.
- Add loading skeletons for admin tables.
