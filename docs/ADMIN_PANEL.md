# Admin Panel and Super Users

This app now has two kinds of users:

- `normal_user`: can log in and read the AI news dashboard.
- `super_user`: can open the Admin Panel, manage users, and run the pipeline.

## What Changed

The backend now checks permissions before protected admin actions run.

Normal users:

- Do not see the Run Pipeline button.
- Do not see the Admin button.
- Cannot call admin APIs directly.
- Get `403 Forbidden` if they try to run the pipeline API themselves.

Super Users:

- Can open the Admin Panel from the header.
- Can view all users.
- Can change user roles.
- Can activate or deactivate users.
- Can run the pipeline.
- Can see recent pipeline runs.
- Can see recent admin activity logs.

## First Super User

For safety, the app does not make anyone an admin from the signup page.

After creating your account normally, run this command from the project folder:

```bash
python -m app.scripts.promote_super_user your-email@example.com
```

You can also use your username instead of your email.

The script asks for that account's password before promoting it. If you need a one-line command, you can pass the password directly:

```bash
python -m app.scripts.promote_super_user super_user@gmail.com --password "password@123"
```

Then log out and log back in. The Admin button should appear in the header.

## Database Changes

The app adds these fields to `users`:

- `role`
- `is_active`

It also adds these tables:

- `pipeline_runs`: stores pipeline run status and history.
- `audit_logs`: stores admin actions like role changes and pipeline triggers.

The local startup code runs a small migration helper, so existing PostgreSQL databases get the new user fields automatically.

## Important Safety Rules

- A Super User cannot deactivate their own account.
- A Super User cannot remove their own admin role.
- The app prevents removing the last active Super User.
- Password hashes and session tokens are never shown in admin APIs.

## Quick Test

1. Sign up as a normal user.
2. Confirm there is no Admin button and no Run Pipeline button.
3. Promote your account with `python -m app.scripts.promote_super_user your-email@example.com`.
4. Log out and log back in.
5. Open Admin.
6. Try changing another user's role or active status.
7. Run the pipeline from the Admin Panel.
8. Check that Pipeline History and Audit Logs update.
