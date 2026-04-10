import os
import uvicorn
import shutil
import uuid
import json
import concurrent.futures
import subprocess
import tempfile
import sqlite3
from datetime import datetime, timedelta
from threading import Lock
from typing import Optional, List

from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, EmailStr
from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError, TimeoutError
from dotenv import load_dotenv
import jwt as pyjwt
from werkzeug.security import generate_password_hash, check_password_hash
from googleapiclient.discovery import build

load_dotenv()

# Modular imports
from orm.session import get_session, SessionLocal
from orm.models import User, SearchHistory
from video_utils import create_video_from_summary
from ai_service import query_ollama, generate_mcqs, evaluate_explanation, generate_performance_analysis

# ─────────────────────────────────────────────
# App Setup
# ─────────────────────────────────────────────
app = FastAPI(title="Learnify API", version="2.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

try:
    SECRET_KEY = os.environ["SECRET_KEY"]
    JWT_SECRET_KEY = os.environ["JWT_SECRET_KEY"]
except KeyError as e:
    print(f"❌ CRITICAL ERROR: {e.args[0]} missing from .env. See README for setup.")
    raise

JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = 24

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

VIDEO_STORAGE_DIR = os.path.join(os.getcwd(), "video_storage")
if not os.path.exists(VIDEO_STORAGE_DIR):
    os.makedirs(VIDEO_STORAGE_DIR)

_video_tasks_lock = Lock()
video_tasks: dict = {}
video_executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)

youtube_client = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=YOUTUBE_API_KEY) if YOUTUBE_API_KEY else None

# ─────────────────────────────────────────────
# JWT Auth Dependency
# ─────────────────────────────────────────────
security = HTTPBearer(auto_error=False)

def verify_jwt(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Decode and validate the Bearer JWT token."""
    if not credentials:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    try:
        payload = pyjwt.decode(
            credentials.credentials, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM]
        )
        return payload
    except pyjwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except pyjwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

def create_access_token(identity: str, extra_claims: dict = None) -> str:
    """Create a signed JWT token."""
    extra_claims = extra_claims or {}
    payload = {
        "sub": identity,
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRE_HOURS),
        **extra_claims,
    }
    return pyjwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

# ─────────────────────────────────────────────
# Pydantic Request Models
# ─────────────────────────────────────────────
class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=2, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=128)

class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1, max_length=128)

class AddSearchRequest(BaseModel):
    username: str = Field(..., max_length=50)
    email: EmailStr
    searches: str = Field(..., max_length=500)
    thumbnail_url: Optional[str] = Field(None, max_length=512)

class UpdateHistoryRequest(BaseModel):
    historyId: int
    thumbnail_url: Optional[str] = None
    query: Optional[str] = None

class ToggleFavoriteRequest(BaseModel):
    historyId: int

class SummaryRequest(BaseModel):
    keyword: str = Field(..., min_length=1, max_length=200)
    historyId: Optional[int] = None

class SaveQuizRequest(BaseModel):
    historyId: int
    quiz: list

class SaveScoreRequest(BaseModel):
    historyId: int
    score: int = Field(..., ge=0)
    total: int = Field(..., ge=1)

class VideoRequest(BaseModel):
    text: str = Field(..., min_length=10, max_length=20000)
    keyword: Optional[str] = Field(default="technology", max_length=200)
    historyId: Optional[int] = None

class MCQRequest(BaseModel):
    text: str = Field(..., min_length=10, max_length=50000)

class AnswerItem(BaseModel):
    question: str
    selected: str
    correct: str

class EvaluateRequest(BaseModel):
    topic: str
    answers: List[AnswerItem]
    historyId: Optional[int] = None

class ExecuteCodeRequest(BaseModel):
    language: str = Field(..., max_length=20)
    code: str = Field(..., min_length=1, max_length=100000)

# ─────────────────────────────────────────────
# Authentication Routes
# ─────────────────────────────────────────────

@app.post("/register")
def register(data: RegisterRequest, db: Session = Depends(get_session)):
    user = db.query(User).filter(User.email == data.email).first()
    if user:
        return JSONResponse(status_code=400, content={"error": "Email already registered"})
    hashed_pw = generate_password_hash(data.password)
    new_user = User(username=data.username, email=data.email, password=hashed_pw)
    db.add(new_user)
    db.commit()
    return {"message": "Registration successful"}

@app.post("/login")
def login(data: LoginRequest, db: Session = Depends(get_session)):
    user = db.query(User).filter(User.email == data.email).first()
    if user and check_password_hash(user.password, data.password):
        token = create_access_token(
            identity=str(user.email),
            extra_claims={"id": user.id, "username": user.username, "email": user.email},
        )
        return {
            "message": "Login successful",
            "username": user.username,
            "email": user.email,
            "token": token,
        }
    return JSONResponse(status_code=401, content={"error": "Invalid credentials"})


@app.post("/update_history")
def update_history(data: UpdateHistoryRequest, _user=Depends(verify_jwt), db: Session = Depends(get_session)):
    history = db.query(SearchHistory).filter(SearchHistory.id == data.historyId).first()
    if history:
        if data.thumbnail_url:
            history.thumbnail_url = data.thumbnail_url
        if data.query:
            history.query = data.query
        db.commit()
    return {"message": "History updated"}

# ─────────────────────────────────────────────
# Search & History Routes
# ─────────────────────────────────────────────

@app.post("/add_search")
def add_search(data: AddSearchRequest, _user=Depends(verify_jwt), db: Session = Depends(get_session)):
    new_search = SearchHistory(
        username=data.username,
        email=data.email,
        query=data.searches,
        thumbnail_url=data.thumbnail_url
    )
    db.add(new_search)
    db.commit()
    db.refresh(new_search)
    return {"message": "Search added", "historyId": new_search.id}

@app.get("/get_history")
def get_history(
    username: str = Query(...),
    email: str = Query(...),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=50, ge=1, le=100),
    _user=Depends(verify_jwt),
    db: Session = Depends(get_session)
):
    offset = (page - 1) * limit
    histories = db.query(SearchHistory).filter(
        SearchHistory.username == username,
        SearchHistory.email == email
    ).order_by(SearchHistory.timestamp.desc()).offset(offset).limit(limit).all()
    
    return [
        {
            "id": h.id,
            "query": h.query,
            "time": h.timestamp.strftime("%Y-%m-%d %H:%M:%S") if h.timestamp else "",
            "video_filename": h.video_filename,
            "quiz_json": h.quiz_json,
            "quiz_score": h.quiz_score,
            "quiz_total": h.quiz_total,
            "is_favorite": bool(h.is_favorite),
            "thumbnail_url": h.thumbnail_url,
        }
        for h in histories
    ]

@app.post("/toggle_favorite")
def toggle_favorite(data: ToggleFavoriteRequest, _user=Depends(verify_jwt), db: Session = Depends(get_session)):
    history = db.query(SearchHistory).filter(SearchHistory.id == data.historyId).first()
    if not history:
        raise HTTPException(status_code=404, detail="Not found")
    history.is_favorite = 0 if history.is_favorite else 1
    db.commit()
    return {"message": "Toggled favorite", "is_favorite": bool(history.is_favorite)}

@app.get("/search")
def search_videos(q: str = Query(..., min_length=1, description="Search query")):
    if not youtube_client:
        raise HTTPException(status_code=503, detail="YouTube API not configured")
    try:
        res = youtube_client.search().list(q=q, part="snippet", type="video", maxResults=15).execute()
        results = []
        for item in res.get("items", []):
            video_id = item.get("id", {}).get("videoId")
            if not video_id:
                continue
                
            results.append({
                "videoId": video_id,
                "title": item.get("snippet", {}).get("title", "No Title"),
                "thumbnail": item.get("snippet", {}).get("thumbnails", {}).get("high", {}).get("url", ""),
            })
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ─────────────────────────────────────────────
# Core Logic Routes
# ─────────────────────────────────────────────

@app.post("/summary")
def summary(data: SummaryRequest, user=Depends(verify_jwt), db: Session = Depends(get_session)):
    keyword = data.keyword
    history_id = data.historyId
    user_email = user["email"]

    summary_text = None
    cached_quiz = None
    is_favorite = False
    previous_performance = None

    # Get cached summary from ANY record
    cached = db.query(SearchHistory).filter(
        SearchHistory.query == keyword,
        SearchHistory.summary.isnot(None)
    ).order_by(SearchHistory.timestamp.desc()).first()
    
    if cached:
        summary_text = cached.summary

    # Check for user's previous attempt on SAME topic
    prev = db.query(SearchHistory).filter(
        SearchHistory.email == user_email,
        SearchHistory.query == keyword,
        SearchHistory.performance_analysis.isnot(None),
        SearchHistory.id != (history_id or 0)
    ).order_by(SearchHistory.timestamp.desc()).first()
    
    if prev:
        previous_performance = prev.performance_analysis

    if history_id:
        current_history = db.query(SearchHistory).filter(SearchHistory.id == history_id).first()
        if current_history:
            cached_quiz = json.loads(current_history.quiz_json) if current_history.quiz_json else None
            is_favorite = bool(current_history.is_favorite)
    
    if not summary_text:
        summary_text = query_ollama(keyword)

    if summary_text and not cached_quiz and previous_performance:
        print(f"Generating adaptive quiz for {user_email} on {keyword}...")
        cached_quiz = generate_mcqs(summary_text, previous_analysis=previous_performance)
        
        if history_id and cached_quiz:
            current_history = db.query(SearchHistory).filter(SearchHistory.id == history_id).first()
            if current_history:
                current_history.quiz_json = json.dumps(cached_quiz)
                db.commit()

    if history_id and summary_text:
        current_history = db.query(SearchHistory).filter(SearchHistory.id == history_id).first()
        if current_history:
            current_history.summary = summary_text
            db.commit()

    return {
        "summary": summary_text,
        "quiz": cached_quiz,
        "is_favorite": is_favorite,
    }

@app.post("/save_quiz")
def save_quiz(data: SaveQuizRequest, _user=Depends(verify_jwt), db: Session = Depends(get_session)):
    history = db.query(SearchHistory).filter(SearchHistory.id == data.historyId).first()
    if history:
        history.quiz_json = json.dumps(data.quiz)
        db.commit()
        return {"message": "Quiz saved"}
    raise HTTPException(status_code=404, detail="Not found")
    
@app.post("/save_score")
def save_score(data: SaveScoreRequest, _user=Depends(verify_jwt), db: Session = Depends(get_session)):
    history = db.query(SearchHistory).filter(SearchHistory.id == data.historyId).first()
    if history:
        history.quiz_score = data.score
        history.quiz_total = data.total
        db.commit()
        return {"message": "Score saved"}
    raise HTTPException(status_code=404, detail="Not found")

# ─────────────────────────────────────────────
# Video Routes
# ─────────────────────────────────────────────

@app.post("/video")
def generate_video_route(data: VideoRequest, _user=Depends(verify_jwt), db: Session = Depends(get_session)):
    try:
        text = data.text
        keyword = data.keyword or "technology"
        history_id = data.historyId

        print(f"Request for background video: {keyword}, History ID: {history_id}")

        cached = db.query(SearchHistory).filter(
            SearchHistory.query == keyword,
            SearchHistory.video_filename.isnot(None)
        ).order_by(SearchHistory.timestamp.desc()).first()

        if cached and cached.video_filename:
            temp_path = os.path.join(VIDEO_STORAGE_DIR, cached.video_filename)
            if os.path.exists(temp_path):
                return {"status": "completed", "video_url": f"/get_video/{cached.video_filename}"}

        task_id = str(uuid.uuid4())
        with _video_tasks_lock:
            video_tasks[task_id] = {"status": "processing", "video_url": None, "error": None}
        video_executor.submit(_video_worker, task_id, text, keyword, history_id)

        return JSONResponse(
            content={"status": "processing", "task_id": task_id},
            status_code=202,
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"CRITICAL ERROR in /video: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def _video_worker(task_id: str, text: str, keyword: str, history_id):
    """Background worker — runs in thread pool."""
    try:
        temp_video_path = create_video_from_summary(text, keyword)
        if not temp_video_path or not os.path.exists(temp_video_path):
            with _video_tasks_lock:
                video_tasks[task_id] = {"status": "error", "error": "Video generation failed"}
            return

        permanent_filename = f"{uuid.uuid4()}.mp4"
        permanent_path = os.path.join(VIDEO_STORAGE_DIR, permanent_filename)
        shutil.move(temp_video_path, permanent_path)

        if history_id:
            db_session = SessionLocal()
            try:
                history = db_session.query(SearchHistory).filter(SearchHistory.id == history_id).first()
                if history:
                    history.video_filename = permanent_filename
                    db_session.commit()
            except Exception as e:
                print(f"Background DB update failed: {e}")
            finally:
                db_session.close()

        with _video_tasks_lock:
            video_tasks[task_id] = {
                "status": "completed",
                "video_url": f"/get_video/{permanent_filename}",
            }
    except Exception as e:
        print(f"Unhandled general exception in _video_worker: {e}")
        with _video_tasks_lock:
            video_tasks[task_id] = {"status": "error", "error": str(e)}

@app.get("/video/status/{task_id}")
def get_video_status(task_id: str):
    with _video_tasks_lock:
        task = video_tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@app.get("/get_video/{filename}")
def serve_video(filename: str):
    safe_name = os.path.basename(filename)
    file_path = os.path.join(VIDEO_STORAGE_DIR, safe_name)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Video not found")
    return FileResponse(file_path, media_type="video/mp4")

# ─────────────────────────────────────────────
# MCQ / Evaluate Routes
# ─────────────────────────────────────────────

@app.post("/mcqs")
def get_mcqs(data: MCQRequest):
    return generate_mcqs(data.text)

@app.post("/evaluate")
def evaluate(data: EvaluateRequest, _user=Depends(verify_jwt), db: Session = Depends(get_session)):
    results = []
    answers_for_analysis = []
    for item in data.answers:
        is_correct = item.selected.strip() == item.correct.strip()
        if is_correct:
            explanation = f"✅ Correct! '{item.correct}' is the right answer."
        else:
            explanation = evaluate_explanation(item.question, item.selected, item.correct)
        
        results.append({
            "correct": is_correct,
            "explanation": explanation,
        })
        answers_for_analysis.append({
            "question": item.question,
            "selected": item.selected,
            "correct": item.correct,
            "is_correct": is_correct
        })
    
    analysis = generate_performance_analysis(data.topic, answers_for_analysis)
    
    if data.historyId:
        try:
            history = db.query(SearchHistory).filter(SearchHistory.id == data.historyId).first()
            if history:
                history.performance_analysis = analysis
                history.quiz_results = json.dumps(results)
                db.commit()
        except Exception as e:
            print(f"Error saving evaluation results: {e}")

    return {
        "results": results,
        "analysis": analysis
    }


# ─────────────────────────────────────────────
# Local Sandboxed Execution Routes
# ─────────────────────────────────────────────
@app.post("/execute_code")
def execute_code(data: ExecuteCodeRequest, _user=Depends(verify_jwt)):
    # Local sandboxed execution implementation
    lang = data.language.lower()
    code = data.code
    
    stdout_val = ""
    stderr_val = ""
    exit_code = 1
    
    try:
        if lang == "python":
            res = subprocess.run(["python", "-c", code], capture_output=True, text=True, timeout=5)
            stdout_val, stderr_val, exit_code = res.stdout, res.stderr, res.returncode
            
        elif lang == "javascript":
            res = subprocess.run(["node", "-e", code], capture_output=True, text=True, timeout=5)
            stdout_val, stderr_val, exit_code = res.stdout, res.stderr, res.returncode
            
        elif lang == "sqlite3":
            # Native SQLite3 execution
            with sqlite3.connect(":memory:") as conn:
                try:
                    cursor = conn.cursor()
                    all_results = []
                    # Split by semicolon and execute each statement
                    for statement in code.split(';'):
                        stmt = statement.strip()
                        if not stmt:
                            continue
                        cursor.execute(stmt)
                        if cursor.description: # This indicates a query like SELECT
                            rows = cursor.fetchall()
                            all_results.extend(rows)
                    
                    if all_results:
                        stdout_val = "\n".join([str(row) for row in all_results])
                    exit_code = 0
                except Exception as e:
                    stderr_val = str(e)
                    exit_code = 1
                    
        elif lang == "java":
            with tempfile.TemporaryDirectory() as temp_dir:
                # Java requires class name to match file name. We will just enforce Main.java
                java_file = os.path.join(temp_dir, "Main.java")
                with open(java_file, "w") as f:
                    f.write(code)
                
                # Compile
                compile_res = subprocess.run(["javac", "Main.java"], cwd=temp_dir, capture_output=True, text=True, timeout=5)
                if compile_res.returncode != 0:
                    exit_code = compile_res.returncode
                    stderr_val = compile_res.stderr
                else:
                    # Execute
                    run_res = subprocess.run(["java", "Main"], cwd=temp_dir, capture_output=True, text=True, timeout=5)
                    stdout_val, stderr_val, exit_code = run_res.stdout, run_res.stderr, run_res.returncode
                    
        elif lang == "cpp":
            with tempfile.TemporaryDirectory() as temp_dir:
                cpp_file = os.path.join(temp_dir, "temp.cpp")
                out_file = os.path.join(temp_dir, "a.exe" if os.name == "nt" else "a.out")
                with open(cpp_file, "w") as f:
                    f.write(code)
                
                # Compile
                compile_res = subprocess.run(["g++", "temp.cpp", "-o", out_file], cwd=temp_dir, capture_output=True, text=True, timeout=5)
                if compile_res.returncode != 0:
                    exit_code = compile_res.returncode
                    stderr_val = compile_res.stderr
                else:
                    # Execute
                    run_res = subprocess.run([out_file], cwd=temp_dir, capture_output=True, text=True, timeout=5)
                    stdout_val, stderr_val, exit_code = run_res.stdout, run_res.stderr, run_res.returncode
        else:
            return JSONResponse(status_code=400, content={"error": f"Unsupported language: {lang}"})
            
    except subprocess.TimeoutExpired:
        stderr_val = "Execution timed out (5 seconds max limit exceeded)."
        exit_code = 124
    except Exception as e:
        stderr_val = f"Execution engine error: {str(e)}"
        exit_code = 1
        
    return {
        "run": {
            "stdout": stdout_val.strip(),
            "stderr": stderr_val.strip(),
            "code": exit_code
        }
    }


# ─────────────────────────────────────────────
# Run
# ─────────────────────────────────────────────
@app.exception_handler(OperationalError)
@app.exception_handler(TimeoutError)
async def pool_error_handler(request, exc):
    return JSONResponse(
        status_code=503,
        content={"error": "Database error. Server busy or unreachable."},
    )

if __name__ == "__main__":
    print("\n🚀 Starting Learnify FastAPI backend...")
    print("📡 API running at:  http://localhost:5000")
    print("📖 Swagger UI at:   http://localhost:5000/docs\n")
    uvicorn.run("app:app", host="0.0.0.0", port=5000, reload=True)