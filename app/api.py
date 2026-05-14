from typing import Annotated, Optional

from fastapi import BackgroundTasks, Cookie, Depends, FastAPI, HTTPException, Response, status
from fastapi.responses import HTMLResponse, JSONResponse
from pathlib import Path
import logging
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.auth import (
    SESSION_COOKIE_NAME,
    authenticate_user,
    clear_session_cookie,
    create_session,
    get_current_user,
    get_db,
    register_user,
    revoke_session,
    serialize_user,
    set_session_cookie,
)
from app.database.connection import engine
from app.database.models import Base, User
from app.database.repository import Repository
from app.daily_runner import run_daily_pipeline
import traceback

# Setup basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI News Aggregator API")

# Global status variable for the pipeline
# Simple in-memory tracker to know if the pipeline is currently running
pipeline_status = {
    "status": "idle",
    "last_run": None,
    "error": None
}

# Mount the frontend directory if needed, but we will explicitly serve the HTML file on root
frontend_dir = Path(__file__).parent.parent / "frontend"


class SignupRequest(BaseModel):
    email: str
    username: str
    password: str


class LoginRequest(BaseModel):
    identifier: str
    password: str


@app.on_event("startup")
def ensure_database_tables():
    """
    Create any missing tables, including auth tables, during local startup.
    """
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables are ready")
    except Exception:
        logger.error(f"Error creating database tables: {traceback.format_exc()}")

def format_date(dt):
    """Format a datetime object to match the frontend 'DD/MM/YYYY' style"""
    if not dt:
        return ""
    return dt.strftime("%d/%m/%Y")

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """
    Serve the frontend/static-desing.html page as the main UI.
    """
    html_path = frontend_dir / "static-desing.html"
    try:
        with open(html_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        logger.error(f"Error reading HTML file: {e}")
        return f"<html><body><h1>Error loading UI: {e}</h1></body></html>"


@app.post("/api/auth/signup", status_code=status.HTTP_201_CREATED)
async def signup(payload: SignupRequest, response: Response, db: Session = Depends(get_db)):
    """
    Create a user account, start a session, and set the session cookie.
    """
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
    """
    Login with either email or username.
    """
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
    """
    Return the user attached to the current session cookie.
    """
    return {"user": serialize_user(current_user)}


@app.post("/api/auth/logout")
async def logout(
    response: Response,
    session_token: Annotated[Optional[str], Cookie(alias=SESSION_COOKIE_NAME)] = None,
    db: Session = Depends(get_db),
):
    """
    Revoke the current session token and clear the browser cookie.
    """
    if session_token:
        revoke_session(db, session_token)
    clear_session_cookie(response)
    return {"message": "Logged out"}


@app.get("/api/articles")
async def get_articles(current_user: User = Depends(get_current_user)):
    """
    Fetch all articles and videos from the database and format them for the UI.
    """
    from app.database.models import Digest
    
    ui_articles = []
    
    try:
        repo = Repository()
        
        # We fetch the processed Digests to match exactly what is sent in the emails
        digests = repo.session.query(Digest).order_by(Digest.created_at.desc()).all()
        
        for digest in digests:
            # Generate thumbnail for YouTube videos
            image_url = None
            if digest.article_type == "youtube":
                image_url = f"https://img.youtube.com/vi/{digest.article_id}/hqdefault.jpg"
                
            # Map article_type to the source name
            source_map = {
                "youtube": "YouTube",
                "openai": "OpenAI",
                "anthropic": "Anthropic"
            }
            
            ui_articles.append({
                "id": digest.id,
                "category": digest.article_type,
                "title": digest.title,
                "description": digest.summary,  # Using the AI generated summary
                "date": format_date(digest.created_at),
                "source": source_map.get(digest.article_type, digest.article_type.capitalize()),
                "url": digest.url,
                "image_url": image_url
            })
            
        return JSONResponse(
            content={"articles": ui_articles},
            headers={"Cache-Control": "no-store, max-age=0"}
        )
        
    except Exception as e:
        logger.error(f"Error fetching articles: {traceback.format_exc()}")
        return JSONResponse(status_code=500, content={"error": str(e)})
    finally:
        if 'repo' in locals() and hasattr(repo, 'session'):
            repo.session.close()

def run_pipeline_task():
    """
    Background task to run the daily pipeline.
    Updates the global status dictionary.
    """
    global pipeline_status
    try:
        logger.info("Background task started: run_daily_pipeline")
        
        # Run the pipeline (increased to 168 hours/7 days so it catches recent videos from less active channels)
        result = run_daily_pipeline(hours=168, top_n=10)
        
        pipeline_status["status"] = "idle"
        pipeline_status["last_run"] = result
        pipeline_status["error"] = None
        logger.info(f"Background task finished successfully: {result}")
        
    except Exception as e:
        logger.error(f"Background task failed: {traceback.format_exc()}")
        pipeline_status["status"] = "idle"
        pipeline_status["error"] = str(e)

@app.post("/api/pipeline/run")
async def run_pipeline(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
):
    """
    Trigger the aggregator pipeline to run in the background.
    """
    global pipeline_status
    
    if pipeline_status["status"] == "running":
        return {"message": "Pipeline is already running", "status": "running"}
        
    pipeline_status["status"] = "running"
    pipeline_status["error"] = None
    
    # Add the task to FastAPI's background tasks
    background_tasks.add_task(run_pipeline_task)
    
    return {"message": "Pipeline execution started", "status": "running"}

@app.get("/api/pipeline/status")
async def get_pipeline_status(current_user: User = Depends(get_current_user)):
    """
    Check if the pipeline is currently running.
    """
    return pipeline_status
