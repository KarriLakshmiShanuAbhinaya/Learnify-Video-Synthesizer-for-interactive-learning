# Learnify Security Overview

This document outlines the security measures implemented in the Learnify project to ensure safe development and deployment, specifically focusing on the newly added **Code Practice** feature and general repository hygiene for GitHub.

## 🔐 Sensitive Data Management

### 1. Environment Variables
All sensitive credentials (API keys, database passwords, JWT secrets) are stored in a `.env` file. This file is explicitly listed in `.gitignore` to prevent accidental commits to GitHub.

### 2. User Data
- **Passwords**: User passwords are encrypted using `werkzeug.security` (PBKDF2 with SHA-256) before storage. They are never stored or transmitted in plain text.
- **Authentication**: JWT tokens are used for session management, ensuring only authenticated users can access history or execute code.

## 💻 Code Practice Feature Security

The Code Practice execution engine routes code directly through the backend server. To ensure this is safe during local development:

### 1. Sandboxed Local Subprocesses
Code execution utilizes `subprocess.run` with the following safety flags:
- **`capture_output=True`**: Prevents code from outputting directly to the server's console.
- **`text=True`**: Ensures output is strictly handled as string data.
- **`timeout=5`**: Enforces a strict 5-second execution limit. This prevents "infinite loop" scripts from hanging the backend or consuming host resources.

### 2. Ephemeral Workspaces
For compiled languages (Java, C++), the engine uses `tempfile.TemporaryDirectory()`. This creates a strictly isolated, random-named folder on your OS that is **automatically deleted** immediately after execution finishes, ensuring no binary debris remains in your local directory.

### 3. Native JWT Authorization
The `/execute_code` endpoint is protected by the `verify_jwt` dependency. This ensures that only logged-in users of your application can trigger the execution engine.

> [!IMPORTANT]
> **Production Note:** The current execution engine is designed for **LOCAL** use in a trusted workspace environment. If you intend to host this project publicly on a cloud server, it is highly recommended to wrap the backend execution calls in an additional layer of isolation, such as a separate Docker container for each execution request.

## 🚦 Pre-Push Checklist
Before pushing to GitHub, ensure the following:
- [ ] Your `.env` file is NOT being tracked (`git status` should not show it).
- [ ] You have updated your `SECRET_KEY` and `JWT_SECRET_KEY` to unique values.
- [ ] No temporary `.mp4` or `.mp3` files are staged for commit.
