import os
import uvicorn
import shutil
import uuid
import json
import concurrent.futures
from datetime import datetime, timedelta
from typing import Optional

from fastapi import FastAPI, Depends, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from dotenv import load_dotenv
import jwt as pyjwt
from werkzeug.security import generate_password_hash, check_password_hash
from googleapiclient.discovery import build

load_dotenv()

# Modular imports (unchanged)
from database import get_db
from video_utils import create_video_from_summary
from ai_service import query_ollama, generate_mcqs, evaluate_explanation

# ─────────────────────────────────────────────
# App Setup
# ─────────────────────────────────────────────
app = FastAPI(title="Learnify API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "superjwtsecret")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = 24

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

VIDEO_STORAGE_DIR = os.path.join(os.getcwd(), "video_storage")
if not os.path.exists(VIDEO_STORAGE_DIR):
    os.makedirs(VIDEO_STORAGE_DIR)

# Background video task registry
video_executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)
video_tasks: dict = {}

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

def create_access_token(identity: str, extra_claims: dict = {}) -> str:
    """Create a JWT token identical in structure to Flask-JWT-Extended output."""
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
    username: str
    email: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str

class AddSearchRequest(BaseModel):
    username: str
    email: str
    searches: str

class ToggleFavoriteRequest(BaseModel):
    historyId: int

class SummaryRequest(BaseModel):
    keyword: str
    historyId: Optional[int] = None

class SaveQuizRequest(BaseModel):
    historyId: int
    quiz: list

class SaveScoreRequest(BaseModel):
    historyId: int
    score: int
    total: int

class VideoRequest(BaseModel):
    text: str
    keyword: Optional[str] = "technology"
    historyId: Optional[int] = None

class MCQRequest(BaseModel):
    text: str

class EvaluateRequest(BaseModel):
    question: Optional[str] = ""
    selected: Optional[str] = ""
    correct: Optional[str] = ""

# ─────────────────────────────────────────────
# Authentication Routes
# ─────────────────────────────────────────────

@app.post("/register")
def register(data: RegisterRequest):
    db = get_db()
    cur = db.cursor()
    try:
        cur.execute("SELECT * FROM users WHERE email = %s", (data.email,))
        if cur.fetchone():
            return JSONResponse(status_code=400, content={"error": "Email already registered"})
        hashed_pw = generate_password_hash(data.password)
        cur.execute(
            "INSERT INTO users (username, email, password) VALUES (%s, %s, %s)",
            (data.username, data.email, hashed_pw),
        )
        db.commit()
        return {"message": "Registration successful"}
    finally:
        cur.close()
        db.close()

@app.post("/login")
def login(data: LoginRequest):
    db = get_db()
    cur = db.cursor()
    try:
        cur.execute("SELECT * FROM users WHERE email = %s", (data.email,))
        user = cur.fetchone()
    finally:
        cur.close()
        db.close()

    if user and check_password_hash(user[3], data.password):
        token = create_access_token(
            identity=str(user[2]),
            extra_claims={"id": user[0], "username": user[1], "email": user[2]},
        )
        return {
            "message": "Login successful",
            "username": user[1],
            "email": user[2],
            "token": token,
        }
    return JSONResponse(status_code=401, content={"error": "Invalid credentials"})

# ─────────────────────────────────────────────
# Search & History Routes
# ─────────────────────────────────────────────

@app.post("/add_search")
def add_search(data: AddSearchRequest, _user=Depends(verify_jwt)):
    db = get_db()
    cur = db.cursor()
    try:
        timestamp = datetime.now()
        cur.execute(
            "INSERT INTO search_history (username, email, query, timestamp) VALUES (%s, %s, %s, %s)",
            (data.username, data.email, data.searches, timestamp),
        )
        history_id = cur.lastrowid
        db.commit()
        return {"message": "Search added", "historyId": history_id}
    finally:
        cur.close()
        db.close()

@app.get("/get_history")
def get_history(
    username: str = Query(...),
    email: str = Query(...),
    _user=Depends(verify_jwt),
):
    db = get_db()
    cur = db.cursor()
    try:
        cur.execute(
            """SELECT id, query, timestamp, video_filename, quiz_json, quiz_score, quiz_total, is_favorite
               FROM search_history WHERE username=%s AND email=%s ORDER BY timestamp DESC""",
            (username, email),
        )
        rows = cur.fetchall()
    finally:
        cur.close()
        db.close()

    history = []
    for row in rows:
        history.append({
            "id": row[0],
            "query": row[1],
            "time": row[2].strftime("%Y-%m-%d %H:%M:%S") if row[2] else "",
            "video_filename": row[3],
            "quiz_json": row[4],
            "quiz_score": row[5],
            "quiz_total": row[6],
            "is_favorite": bool(row[7]) if len(row) > 7 else False,
        })
    return history

@app.post("/toggle_favorite")
def toggle_favorite(data: ToggleFavoriteRequest, _user=Depends(verify_jwt)):
    db = get_db()
    cur = db.cursor()
    try:
        cur.execute("SELECT is_favorite FROM search_history WHERE id = %s", (data.historyId,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Not found")
        new_status = not bool(row[0])
        cur.execute(
            "UPDATE search_history SET is_favorite = %s WHERE id = %s",
            (new_status, data.historyId),
        )
        db.commit()
        return {"message": "Toggled favorite", "is_favorite": new_status}
    finally:
        cur.close()
        db.close()

@app.get("/search")
def search_videos(q: str = Query(..., description="Search query")):
    if not q.strip():
        raise HTTPException(status_code=400, detail="No query")
    try:
        youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=YOUTUBE_API_KEY)
        res = youtube.search().list(q=q, part="snippet", type="video", maxResults=15).execute()
        videos = []
        for item in res.get("items", []):
            videos.append({
                "videoId": item["id"]["videoId"],
                "title": item["snippet"]["title"],
                "thumbnail": item["snippet"]["thumbnails"]["high"]["url"],
            })
        return videos
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ─────────────────────────────────────────────
# Core Logic Routes
# ─────────────────────────────────────────────

@app.post("/summary")
def summary(data: SummaryRequest, _user=Depends(verify_jwt)):
    keyword = data.keyword
    history_id = data.historyId
    if not keyword:
        raise HTTPException(status_code=400, detail="No keyword")

    db = get_db()
    cur = db.cursor()
    try:
        # Check summary cache
        cur.execute(
            "SELECT summary FROM search_history WHERE query = %s AND summary IS NOT NULL ORDER BY timestamp DESC LIMIT 1",
            (keyword,),
        )
        cached = cur.fetchone()

        # Check quiz cache
        cached_quiz = None
        is_favorite = False
        if history_id:
            cur.execute(
                "SELECT quiz_json, is_favorite FROM search_history WHERE id = %s",
                (history_id,),
            )
            row = cur.fetchone()
            if row:
                cached_quiz = json.loads(row[0]) if row[0] else None
                is_favorite = bool(row[1])

        summary_text = cached[0] if (cached and cached[0]) else query_ollama(keyword)

        if history_id:
            cur.execute(
                "UPDATE search_history SET summary = %s WHERE id = %s",
                (summary_text, history_id),
            )
            db.commit()

        return {
            "summary": summary_text,
            "quiz": cached_quiz,
            "is_favorite": is_favorite,
        }
    finally:
        cur.close()
        db.close()

@app.post("/save_quiz")
def save_quiz(data: SaveQuizRequest, _user=Depends(verify_jwt)):
    quiz_json = json.dumps(data.quiz)
    db = get_db()
    cur = db.cursor()
    try:
        cur.execute(
            "UPDATE search_history SET quiz_json = %s WHERE id = %s",
            (quiz_json, data.historyId),
        )
        db.commit()
        return {"message": "Quiz saved"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        db.close()

@app.post("/save_score")
def save_score(data: SaveScoreRequest, _user=Depends(verify_jwt)):
    db = get_db()
    cur = db.cursor()
    try:
        cur.execute(
            "UPDATE search_history SET quiz_score = %s, quiz_total = %s WHERE id = %s",
            (data.score, data.total, data.historyId),
        )
        db.commit()
        return {"message": "Score saved"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        db.close()

# ─────────────────────────────────────────────
# Video Routes
# ─────────────────────────────────────────────

@app.post("/video")
def generate_video_route(data: VideoRequest, _user=Depends(verify_jwt)):
    try:
        text = data.text
        keyword = data.keyword or "technology"
        history_id = data.historyId

        if not text:
            raise HTTPException(status_code=400, detail="No text provided")

        print(f"Request for background video: {keyword}, History ID: {history_id}")

        # Check global cache first
        db = get_db()
        cur = db.cursor()
        try:
            cur.execute(
                "SELECT video_filename FROM search_history WHERE query = %s AND video_filename IS NOT NULL ORDER BY timestamp DESC LIMIT 1",
                (keyword,),
            )
            cached = cur.fetchone()
        finally:
            cur.close()
            db.close()

        if cached and cached[0]:
            temp_path = os.path.join(VIDEO_STORAGE_DIR, cached[0])
            if os.path.exists(temp_path):
                return {"status": "completed", "video_url": f"/get_video/{cached[0]}"}

        # Dispatch to background thread
        task_id = str(uuid.uuid4())
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
    """Background worker — runs in thread pool, no FastAPI context needed."""
    try:
        temp_video_path = create_video_from_summary(text, keyword)
        if not temp_video_path or not os.path.exists(temp_video_path):
            video_tasks[task_id] = {"status": "error", "error": "Video generation failed"}
            return

        permanent_filename = f"{uuid.uuid4()}.mp4"
        permanent_path = os.path.join(VIDEO_STORAGE_DIR, permanent_filename)
        shutil.move(temp_video_path, permanent_path)

        if history_id:
            db = get_db()
            cur = db.cursor()
            try:
                cur.execute(
                    "UPDATE search_history SET video_filename = %s WHERE id = %s",
                    (permanent_filename, history_id),
                )
                db.commit()
            except Exception as e:
                print(f"Background DB update failed: {e}")
            finally:
                cur.close()
                db.close()

        video_tasks[task_id] = {
            "status": "completed",
            "video_url": f"/get_video/{permanent_filename}",
        }
    except Exception as e:
        video_tasks[task_id] = {"status": "error", "error": str(e)}

@app.get("/video/status/{task_id}")
def get_video_status(task_id: str):
    task = video_tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@app.get("/get_video/{filename}")
def serve_video(filename: str):
    file_path = os.path.join(VIDEO_STORAGE_DIR, filename)
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
def evaluate(data: EvaluateRequest):
    return []

# ─────────────────────────────────────────────
# Run
# ─────────────────────────────────────────────
if __name__ == "__main__":
    print("\n🚀 Starting Learnify FastAPI backend...")
    print("📡 API running at:  http://localhost:5000")
    print("📖 Swagger UI at:   http://localhost:5000/docs\n")
    uvicorn.run("app:app", host="0.0.0.0", port=5000, reload=True)