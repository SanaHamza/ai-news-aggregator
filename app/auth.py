import hashlib
import hmac
import os
import re
import secrets
from datetime import datetime, timedelta
from typing import Annotated, Optional

from fastapi import Cookie, Depends, HTTPException, Response, status
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.database.connection import get_session
from app.database.models import User, UserSession


SESSION_COOKIE_NAME = "ai_news_session"
SESSION_DAYS = 7
PBKDF2_ITERATIONS = 260_000
USERNAME_RE = re.compile(r"^[a-zA-Z0-9_]{3,30}$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def get_db():
    db = get_session()
    try:
        yield db
    finally:
        db.close()


def serialize_user(user: User) -> dict:
    return {
        "id": user.id,
        "email": user.email,
        "username": user.username,
    }


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    derived = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PBKDF2_ITERATIONS,
    )
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt.hex()}${derived.hex()}"


def verify_password(password: str, password_hash: str) -> bool:
    try:
        algorithm, iterations, salt_hex, stored_hex = password_hash.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        derived = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            bytes.fromhex(salt_hex),
            int(iterations),
        )
        return hmac.compare_digest(derived.hex(), stored_hex)
    except (ValueError, TypeError):
        return False


def hash_session_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def validate_signup(email: str, username: str, password: str) -> tuple[str, str]:
    normalized_email = email.strip().lower()
    normalized_username = username.strip()

    if not EMAIL_RE.match(normalized_email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Enter a valid email address.",
        )

    if not USERNAME_RE.match(normalized_username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username must be 3-30 characters and use only letters, numbers, and underscores.",
        )

    if len(password) < 8 or not re.search(r"[A-Za-z]", password) or not re.search(r"\d", password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters and include a letter and a number.",
        )

    return normalized_email, normalized_username


def find_user_by_identifier(db: Session, identifier: str) -> Optional[User]:
    normalized = identifier.strip().lower()
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


def register_user(db: Session, email: str, username: str, password: str) -> User:
    normalized_email, normalized_username = validate_signup(email, username, password)
    normalized_username_lookup = normalized_username.lower()

    email_exists = db.query(User).filter(func.lower(User.email) == normalized_email).first()
    if email_exists:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already registered.",
        )

    username_exists = (
        db.query(User)
        .filter(func.lower(User.username) == normalized_username_lookup)
        .first()
    )
    if username_exists:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username is already taken.",
        )

    user = User(
        email=normalized_email,
        username=normalized_username,
        password_hash=hash_password(password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, identifier: str, password: str) -> Optional[User]:
    user = find_user_by_identifier(db, identifier)
    if not user or not verify_password(password, user.password_hash):
        return None
    return user


def create_session(db: Session, user: User) -> str:
    token = secrets.token_urlsafe(48)
    session = UserSession(
        user_id=user.id,
        token_hash=hash_session_token(token),
        expires_at=datetime.utcnow() + timedelta(days=SESSION_DAYS),
    )
    db.add(session)
    db.commit()
    return token


def set_session_cookie(response: Response, token: str) -> None:
    secure_cookie = os.getenv("AUTH_COOKIE_SECURE", "false").lower() == "true"
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        max_age=SESSION_DAYS * 24 * 60 * 60,
        httponly=True,
        secure=secure_cookie,
        samesite="lax",
        path="/",
    )


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(
        key=SESSION_COOKIE_NAME,
        path="/",
        httponly=True,
        samesite="lax",
    )


def revoke_session(db: Session, token: str) -> None:
    session = (
        db.query(UserSession)
        .filter(UserSession.token_hash == hash_session_token(token))
        .filter(UserSession.revoked_at.is_(None))
        .first()
    )
    if session:
        session.revoked_at = datetime.utcnow()
        db.commit()


def get_current_user(
    session_token: Annotated[Optional[str], Cookie(alias=SESSION_COOKIE_NAME)] = None,
    db: Session = Depends(get_db),
) -> User:
    if not session_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
        )

    session = (
        db.query(UserSession)
        .filter(UserSession.token_hash == hash_session_token(session_token))
        .filter(UserSession.revoked_at.is_(None))
        .first()
    )

    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session is invalid.",
        )

    if session.expires_at <= datetime.utcnow():
        session.revoked_at = datetime.utcnow()
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session has expired.",
        )

    if not session.user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User no longer exists.",
        )

    return session.user
