import os
import shutil
import uuid
from flask import Flask, request, jsonify, send_file, session, send_from_directory
from dotenv import load_dotenv
load_dotenv()

from flask_cors import CORS
from googleapiclient.discovery import build
import random
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

# Modular imports
from database import init_db, get_db
from video_utils import create_video_from_summary
from ai_service import query_ollama, generate_mcqs, evaluate_explanation

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "supersecretkey")

# ✅ FIXED CORS (VERY IMPORTANT)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

# ✅ HANDLE PREFLIGHT REQUESTS
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,PUT,DELETE,OPTIONS')
    return response

# Initialize Database
init_db(app)

# Video Storage Config
VIDEO_STORAGE_DIR = os.path.join(os.getcwd(), "video_storage")
if not os.path.exists(VIDEO_STORAGE_DIR):
    os.makedirs(VIDEO_STORAGE_DIR)

# YouTube API Setup
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

# --- Authentication Routes ---

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username, email, password = data.get('username'), data.get('email'), data.get('password')
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT * FROM users WHERE email = %s", (email,))
    if cur.fetchone():
        return jsonify({'error': 'Email already registered'}), 400
    hashed_pw = generate_password_hash(password)
    cur.execute("INSERT INTO users (username, email, password) VALUES (%s, %s, %s)", (username, email, hashed_pw))
    db.commit()
    cur.close()
    return jsonify({'message': 'Registration successful'}), 200

@app.route('/login', methods=['POST', 'OPTIONS'])
def login():
    if request.method == 'OPTIONS':
        return '', 200

    data = request.get_json()
    email, password = data.get('email'), data.get('password')
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT * FROM users WHERE email = %s", (email,))
    user = cur.fetchone()
    cur.close()
    if user and check_password_hash(user[3], password):
        session['user'] = {'id': user[0], 'username': user[1], 'email': user[2]}
        return jsonify({'message': 'Login successful', 'username': user[1], 'email': user[2]}), 200
    return jsonify({'error': 'Invalid credentials'}), 401

# --- Search & History ---

@app.route('/add_search', methods=['POST'])
def add_search():
    data = request.get_json()
    username, email, query = data.get("username"), data.get("email"), data.get("searches")
    timestamp = datetime.now()

    db = get_db()
    cur = db.cursor()
    cur.execute("INSERT INTO search_history (username, email, query, timestamp) VALUES (%s, %s, %s, %s)",
                (username, email, query, timestamp))
    history_id = cur.lastrowid
    db.commit()
    cur.close()
    return jsonify({"message": "Search added", "historyId": history_id}), 200

@app.route("/get_history", methods=["GET"])
def get_history():
    username, email = request.args.get("username"), request.args.get("email")
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT id, query, timestamp, video_filename, quiz_json, quiz_score, quiz_total, is_favorite FROM search_history WHERE username=%s AND email=%s ORDER BY timestamp DESC", 
                (username, email))
    rows = cur.fetchall()
    cur.close()
    
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
            "is_favorite": bool(row[7]) if len(row) > 7 else False
        })
    return jsonify(history)

# --- Video + AI + MCQ (UNCHANGED LOGIC) ---

@app.route("/summary", methods=["POST"])
def summary():
    data = request.get_json()
    keyword = data.get("keyword")
    history_id = data.get("historyId")
    if not keyword: return "No keyword", 400

    db = get_db()
    cur = db.cursor()

    cur.execute("SELECT summary FROM search_history WHERE query = %s AND summary IS NOT NULL ORDER BY timestamp DESC LIMIT 1", (keyword,))
    cached = cur.fetchone()
    
    if cached and cached[0]:
        summary_text = cached[0]
    else:
        summary_text = query_ollama(keyword)

    if history_id:
        cur.execute("UPDATE search_history SET summary = %s WHERE id = %s", (summary_text, history_id))
        db.commit()

    cur.close()
    return jsonify({"summary": summary_text}), 200

@app.route("/video", methods=["POST"])
def generate_video_route():
    data = request.get_json()
    text = data.get("text")
    if not text: return "No text", 400

    video_path = create_video_from_summary(text, "topic")
    return send_file(video_path, mimetype="video/mp4")

@app.route("/mcqs", methods=["POST"])
def get_mcqs():
    data = request.get_json()
    return jsonify(generate_mcqs(data.get("text")))

@app.route("/evaluate", methods=["POST"])
def evaluate():
    data = request.get_json()
    return jsonify([])

# --- RUN ---
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)