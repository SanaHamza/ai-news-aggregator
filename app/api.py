from datetime import datetime
from pathlib import Path
from typing import Annotated, Optional

import json
import logging
import traceback

from fastapi import BackgroundTasks, Cookie, Depends, FastAPI, HTTPException, Response, status
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.auth import (
    SESSION_COOKIE_NAME,
    authenticate_user,
    clear_session_cookie,
    create_session,
    get_current_user,
    get_db,
    register_user,
    require_super_user,
    revoke_session,
    serialize_user,
    set_session_cookie,
)
from app.daily_runner import run_daily_pipeline
from app.database.connection import engine, get_session
from app.database.migrations import run_admin_rbac_migrations
from app.database.models import (
    AuditLog,
    Base,
    Digest,
    PipelineRun,
    ROLE_SUPER_USER,
    USER_ROLES,
    User,
)
from app.database.repository import Repository


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI News Aggregator API")

pipeline_status = {
    "status": "idle",
    "last_run": None,
    "error": None,
    "current_run_id": None,
}

frontend_dir = Path(__file__).parent.parent / "frontend"


class SignupRequest(BaseModel):
    email: str
    username: str
    password: str


class LoginRequest(BaseModel):
    identifier: str
    password: str


class AdminUserUpdateRequest(BaseModel):
    role: Optional[str] = None
    is_active: Optional[bool] = None


@app.on_event("startup")
def ensure_database_tables():
    """
    Create missing tables and apply the small RBAC upgrade for existing databases.
    """
    try:
        Base.metadata.create_all(bind=engine)
        run_admin_rbac_migrations(engine)
        logger.info("Database tables are ready")
    except Exception:
        logger.error(f"Error creating database tables: {traceback.format_exc()}")


def format_date(dt):
    if not dt:
        return ""
    return dt.strftime("%d/%m/%Y")


def format_datetime(dt):
    if not dt:
        return None
    return dt.isoformat()


def make_json_safe(value):
    return json.loads(json.dumps(value, default=str))


def create_audit_log(
    db: Session,
    actor: Optional[User],
    action: str,
    target_type: str,
    target_id: Optional[str] = None,
    details: Optional[dict] = None,
) -> AuditLog:
    log = AuditLog(
        actor_user_id=actor.id if actor else None,
        action=action,
        target_type=target_type,
        target_id=target_id,
        details=details or {},
    )
    db.add(log)
    return log


def serialize_admin_user(user: User) -> dict:
    return {
        "id": user.id,
        "email": user.email,
        "username": user.username,
        "role": user.role,
        "is_active": user.is_active,
        "created_at": format_datetime(user.created_at),
        "updated_at": format_datetime(user.updated_at),
    }


def serialize_pipeline_run(run: PipelineRun) -> dict:
    return {
        "id": run.id,
        "status": run.status,
        "triggered_by": run.triggered_by.username if run.triggered_by else None,
        "triggered_by_email": run.triggered_by.email if run.triggered_by else None,
        "started_at": format_datetime(run.started_at),
        "finished_at": format_datetime(run.finished_at),
        "duration_seconds": run.duration_seconds,
        "result": run.result,
        "error": run.error,
    }


def serialize_audit_log(log: AuditLog) -> dict:
    return {
        "id": log.id,
        "actor": log.actor.username if log.actor else None,
        "actor_email": log.actor.email if log.actor else None,
        "action": log.action,
        "target_type": log.target_type,
        "target_id": log.target_id,
        "details": log.details or {},
        "created_at": format_datetime(log.created_at),
    }


def count_active_super_users(db: Session, excluding_user_id: Optional[str] = None) -> int:
    query = db.query(User).filter(User.role == ROLE_SUPER_USER, User.is_active.is_(True))
    if excluding_user_id:
        query = query.filter(User.id != excluding_user_id)
    return query.count()


@app.get("/", response_class=HTMLResponse)
async def read_root():
    html_path = frontend_dir / "static-desing.html"
    try:
        with open(html_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        logger.error(f"Error reading HTML file: {e}")
        return f"<html><body><h1>Error loading UI: {e}</h1></body></html>"


@app.post("/api/auth/signup", status_code=status.HTTP_201_CREATED)
async def signup(payload: SignupRequest, response: Response, db: Session = Depends(get_db)):
    user = register_user(
        db=db,
        email=payload.email,
        username=payload.username,
        password=payload.password,
    )
    token = create_session(db, user)
    set_session_cookie(response, token)
    return {"user": serialize_user(user)}


@app.post("/api/auth/login")
async def login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)):
    user = authenticate_user(db, payload.identifier, payload.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email, username, or password.",
        )

    token = create_session(db, user)
    set_session_cookie(response, token)
    return {"user": serialize_user(user)}


@app.get("/api/auth/me")
async def get_me(current_user: User = Depends(get_current_user)):
    return {"user": serialize_user(current_user)}


@app.post("/api/auth/logout")
async def logout(
    response: Response,
    session_token: Annotated[Optional[str], Cookie(alias=SESSION_COOKIE_NAME)] = None,
    db: Session = Depends(get_db),
):
    if session_token:
        revoke_session(db, session_token)
    clear_session_cookie(response)
    return {"message": "Logged out"}


@app.get("/api/articles")
async def get_articles(current_user: User = Depends(get_current_user)):
    ui_articles = []

    try:
        repo = Repository()
        digests = repo.session.query(Digest).order_by(Digest.created_at.desc()).all()

        for digest in digests:
            image_url = None
            if digest.article_type == "youtube":
                image_url = f"https://img.youtube.com/vi/{digest.article_id}/hqdefault.jpg"

            source_map = {
                "youtube": "YouTube",
                "openai": "OpenAI",
                "anthropic": "Anthropic",
            }

            ui_articles.append(
                {
                    "id": digest.id,
                    "category": digest.article_type,
                    "title": digest.title,
                    "description": digest.summary,
                    "date": format_date(digest.created_at),
                    "source": source_map.get(digest.article_type, digest.article_type.capitalize()),
                    "url": digest.url,
                    "image_url": image_url,
                }
            )

        return JSONResponse(
            content={"articles": ui_articles},
            headers={"Cache-Control": "no-store, max-age=0"},
        )

    except Exception as e:
        logger.error(f"Error fetching articles: {traceback.format_exc()}")
        return JSONResponse(status_code=500, content={"error": str(e)})
    finally:
        if "repo" in locals() and hasattr(repo, "session"):
            repo.session.close()


def run_pipeline_task(run_id: str):
    global pipeline_status

    db = get_session()
    run = db.query(PipelineRun).filter(PipelineRun.id == run_id).first()
    started_at = datetime.utcnow()

    try:
        logger.info("Background task started: run_daily_pipeline")
        result = run_daily_pipeline(hours=168, top_n=10)
        finished_at = datetime.utcnow()

        if run:
            run.status = "success" if result.get("success") else "failed"
            run.finished_at = finished_at
            run.duration_seconds = (finished_at - started_at).total_seconds()
            run.result = make_json_safe(result)
            run.error = result.get("error")
            db.commit()

        pipeline_status["status"] = "idle"
        pipeline_status["last_run"] = result
        pipeline_status["error"] = result.get("error")
        pipeline_status["current_run_id"] = None
        logger.info(f"Background task finished: {result}")

    except Exception as e:
        finished_at = datetime.utcnow()
        error = str(e)
        logger.error(f"Background task failed: {traceback.format_exc()}")

        if run:
            run.status = "failed"
            run.finished_at = finished_at
            run.duration_seconds = (finished_at - started_at).total_seconds()
            run.error = error
            db.commit()

        pipeline_status["status"] = "idle"
        pipeline_status["error"] = error
        pipeline_status["current_run_id"] = None
    finally:
        db.close()


@app.post("/api/pipeline/run")
async def run_pipeline(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_super_user),
    db: Session = Depends(get_db),
):
    global pipeline_status

    if pipeline_status["status"] == "running":
        return {
            "message": "Pipeline is already running",
            "status": "running",
            "run_id": pipeline_status["current_run_id"],
        }

    run = PipelineRun(status="running", triggered_by_user_id=current_user.id)
    db.add(run)
    db.flush()
    create_audit_log(
        db=db,
        actor=current_user,
        action="pipeline.trigger",
        target_type="pipeline_run",
        target_id=run.id,
        details={"status": "running"},
    )
    db.commit()
    db.refresh(run)

    pipeline_status["status"] = "running"
    pipeline_status["error"] = None
    pipeline_status["current_run_id"] = run.id

    background_tasks.add_task(run_pipeline_task, run.id)

    return {"message": "Pipeline execution started", "status": "running", "run_id": run.id}


@app.get("/api/pipeline/status")
async def get_pipeline_status(current_user: User = Depends(require_super_user)):
    return pipeline_status


@app.get("/api/admin/summary")
async def get_admin_summary(
    current_user: User = Depends(require_super_user),
    db: Session = Depends(get_db),
):
    source_counts = {
        article_type: count
        for article_type, count in db.query(Digest.article_type, func.count(Digest.id))
        .group_by(Digest.article_type)
        .all()
    }

    latest_run = db.query(PipelineRun).order_by(PipelineRun.started_at.desc()).first()

    return {
        "users": {
            "total": db.query(User).count(),
            "active": db.query(User).filter(User.is_active.is_(True)).count(),
            "super_users": db.query(User).filter(User.role == ROLE_SUPER_USER).count(),
        },
        "content": {
            "digests": db.query(Digest).count(),
            "sources": source_counts,
        },
        "pipeline": {
            "status": pipeline_status,
            "latest_run": serialize_pipeline_run(latest_run) if latest_run else None,
        },
    }


@app.get("/api/admin/users")
async def list_admin_users(
    current_user: User = Depends(require_super_user),
    db: Session = Depends(get_db),
):
    users = db.query(User).order_by(User.created_at.desc()).all()
    return {"users": [serialize_admin_user(user) for user in users]}


@app.patch("/api/admin/users/{user_id}")
async def update_admin_user(
    user_id: str,
    payload: AdminUserUpdateRequest,
    current_user: User = Depends(require_super_user),
    db: Session = Depends(get_db),
):
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    if payload.role is None and payload.is_active is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No changes provided.")

    if payload.role is not None and payload.role not in USER_ROLES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid role.")

    next_role = payload.role if payload.role is not None else target.role
    next_active = payload.is_active if payload.is_active is not None else target.is_active

    removing_self_admin = (
        target.id == current_user.id
        and target.role == ROLE_SUPER_USER
        and (next_role != ROLE_SUPER_USER or not next_active)
    )
    if removing_self_admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot remove your own Super User access.",
        )

    removing_active_super = (
        target.role == ROLE_SUPER_USER
        and target.is_active
        and (next_role != ROLE_SUPER_USER or not next_active)
    )
    if removing_active_super and count_active_super_users(db, excluding_user_id=target.id) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one active Super User is required.",
        )

    changes = {}
    if payload.role is not None and payload.role != target.role:
        changes["role"] = {"from": target.role, "to": payload.role}
        target.role = payload.role

    if payload.is_active is not None and payload.is_active != target.is_active:
        changes["is_active"] = {"from": target.is_active, "to": payload.is_active}
        target.is_active = payload.is_active

    if not changes:
        return {"user": serialize_admin_user(target), "changes": {}}

    target.updated_at = datetime.utcnow()
    create_audit_log(
        db=db,
        actor=current_user,
        action="user.update",
        target_type="user",
        target_id=target.id,
        details=changes,
    )
    db.commit()
    db.refresh(target)

    return {"user": serialize_admin_user(target), "changes": changes}


@app.get("/api/admin/pipeline/runs")
async def list_pipeline_runs(
    current_user: User = Depends(require_super_user),
    db: Session = Depends(get_db),
):
    runs = db.query(PipelineRun).order_by(PipelineRun.started_at.desc()).limit(25).all()
    return {"runs": [serialize_pipeline_run(run) for run in runs]}


@app.get("/api/admin/audit-logs")
async def list_audit_logs(
    current_user: User = Depends(require_super_user),
    db: Session = Depends(get_db),
):
    logs = db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(50).all()
    return {"logs": [serialize_audit_log(log) for log in logs]}
