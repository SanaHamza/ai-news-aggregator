from sqlalchemy import text
from sqlalchemy.engine import Engine

from app.database.models import ROLE_NORMAL_USER


def run_admin_rbac_migrations(engine: Engine) -> None:
    """
    Keep the local PostgreSQL schema compatible without introducing Alembic.
    SQLAlchemy create_all creates missing tables, while these ALTER statements
    upgrade existing user tables that were created before RBAC existed.
    """
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                ALTER TABLE users
                ADD COLUMN IF NOT EXISTS role VARCHAR(32)
                """
            )
        )
        connection.execute(
            text(
                """
                UPDATE users
                SET role = :role
                WHERE role IS NULL
                """
            ),
            {"role": ROLE_NORMAL_USER},
        )
        connection.execute(
            text(
                f"""
                ALTER TABLE users
                ALTER COLUMN role SET DEFAULT '{ROLE_NORMAL_USER}'
                """
            )
        )
        connection.execute(
            text(
                """
                ALTER TABLE users
                ALTER COLUMN role SET NOT NULL
                """
            )
        )

        connection.execute(
            text(
                """
                ALTER TABLE users
                ADD COLUMN IF NOT EXISTS is_active BOOLEAN
                """
            )
        )
        connection.execute(
            text(
                """
                UPDATE users
                SET is_active = TRUE
                WHERE is_active IS NULL
                """
            )
        )
        connection.execute(
            text(
                """
                ALTER TABLE users
                ALTER COLUMN is_active SET DEFAULT TRUE
                """
            )
        )
        connection.execute(
            text(
                """
                ALTER TABLE users
                ALTER COLUMN is_active SET NOT NULL
                """
            )
        )
