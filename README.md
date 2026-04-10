# 🚀 Learnify: AI-Powered Interactive Learning Platform

Learnify is a state-of-the-art educational application that leverages Artificial Intelligence to transform YouTube videos into comprehensive learning experiences. It automatically generates technical summaries, adaptive quizzes, and provides a real-time coding environment to master any topic.

![Learnify Preview](https://via.placeholder.com/1200x600?text=Learnify+AI+Learning+Platform)

## ✨ Features

-   **🤖 AI Video Summarization**: Instantly convert complex technical videos into structured, easy-to-read summaries.
-   **📝 Adaptive Quizzes**: Test your knowledge with AI-generated MCQs that adapt based on your previous performance and topic mastery.
-   **💻 Code Practice**: A built-in multi-language code editor (Monaco) supporting Python, JavaScript, Java, C++, and SQL (SQLite3) with real-time execution.
-   **🎨 Premium UI**: A modern, glassmorphic interface with dark/light mode support and smooth animations.
-   **🎥 Interactive Learning Paths**: Select multiple videos to build a cohesive learning curriculum.

## 🛠️ Technology Stack

-   **Frontend**: React.js, Framer Motion, Lucide Icons, Monaco Editor.
-   **Backend**: FastAPI (Python), SQLAlchemy ORM, Alembic Migrations.
-   **Database**: MySQL (Primary), SQLite3 (Local Sandbox).
-   **AI Engine**: Ollama (Mistral/Llama), Pollinations/Unsplash (Visuals).

## 🚀 Getting Started

### Prerequisites

-   Python 3.10+
-   Node.js 18+
-   MySQL Server
-   [Ollama](https://ollama.ai/) (for local AI inference)

### Backend Setup

1.  Navigate to the `backend` directory:
    ```bash
    cd backend
    ```
2.  Create and activate a virtual environment:
    ```bash
    python -m venv venv
    source venv/bin/activate  # Windows: venv\Scripts\activate
    ```
3.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
4.  Configure your environment:
    -   Create a `.env` file based on `.env.example` (or existing `.env`).
    -   Set your `DATABASE_URL`, `YOUTUBE_API_KEY`, and `JWT_SECRET_KEY`.
5.  Run migrations:
    ```bash
    alembic upgrade head
    ```
6.  Start the server:
    ```bash
    python app.py
    ```

### Frontend Setup

1.  Navigate to the `frontend` directory:
    ```bash
    cd frontend
    ```
2.  Install dependencies:
    ```bash
    npm install
    ```
3.  Start the development server:
    ```bash
    npm start
    ```

## 🐳 Docker Setup

You can run the entire stack using Docker Compose:

```bash
docker-compose up --build
```

## 🛡️ Security

This project implements industry-standard JWT authentication and password hashing. Sensitive configurations are managed via environment variables and are excluded from version control.

## 📄 License

This project is licensed under the MIT License - see the [SECURITY.md](SECURITY.md) for data handling details.

---
Built with ❤️ by the Learnify Team.
