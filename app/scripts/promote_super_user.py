import argparse
import getpass
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from sqlalchemy import func, or_

from app.auth import verify_password
from app.database.connection import engine, get_session
from app.database.migrations import run_admin_rbac_migrations
from app.database.models import Base, ROLE_SUPER_USER, User


def find_user(identifier: str) -> User | None:
    normalized = identifier.strip().lower()
    db = get_session()
    try:
        return (
            db.query(User)
            .filter(
                or_(
                    func.lower(User.email) == normalized,
                    func.lower(User.username) == normalized,
                )
            )
            .first()
        )
    finally:
        db.close()


def promote_user(identifier: str, password: str) -> None:
    Base.metadata.create_all(bind=engine)
    run_admin_rbac_migrations(engine)

    normalized = identifier.strip().lower()
    db = get_session()
    try:
        user = (
            db.query(User)
            .filter(
                or_(
                    func.lower(User.email) == normalized,
                    func.lower(User.username) == normalized,
                )
            )
            .first()
        )

        if not user:
            raise ValueError("No user was found with that email or username.")

        if not verify_password(password, user.password_hash):
            raise ValueError("Password did not match that account.")

        user.role = ROLE_SUPER_USER
        user.is_active = True
        db.commit()

        print(f"Promoted {user.username} <{user.email}> to Super User.")
    finally:
        db.close()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Promote an existing account to Super User after verifying its password."
    )
    parser.add_argument(
        "identifier",
        help="The user's email address or username.",
    )
    parser.add_argument(
        "--password",
        help="The user's password. If omitted, the script asks securely.",
    )
    args = parser.parse_args()

    password = args.password or getpass.getpass("Account password: ")
    if not password:
        print("Password is required.", file=sys.stderr)
        return 1

    try:
        promote_user(args.identifier, password)
        return 0
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"Could not promote user: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
