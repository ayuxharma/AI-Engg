# 🚀 Simple Social

A minimal social media app where users can sign up, log in, and share photos/videos with captions. Built with **FastAPI** (backend), **Streamlit** (frontend), **SQLite** (database), and **ImageKit** (media storage/transformations).

## Features

- 🔐 User authentication (register, login, JWT-based sessions) via `fastapi-users`
- 📸 Upload images and videos with captions
- 🏠 Feed showing all posts, newest first
- 🗑️ Delete your own posts
- 🖼️ Media served through ImageKit with on-the-fly transformations (uniform sizing, caption overlays)

## Tech Stack

| Layer          | Technology                     |
|-----------------|---------------------------------|
| Backend API     | FastAPI                        |
| Auth            | fastapi-users (JWT)            |
| Database        | SQLite + SQLAlchemy (async)    |
| Media storage   | ImageKit.io                    |
| Frontend        | Streamlit                      |
| Package manager | uv                              |

## Project Structure

```
.
├── main.py              # Entrypoint — runs the FastAPI app via uvicorn
├── frontend.py           # Streamlit frontend (login, feed, upload pages)
├── pyproject.toml       # Project dependencies
├── uv.lock
├── test.db              # SQLite database (created automatically)
└── app/                 # Backend application package
    ├── app.py           # FastAPI app, routes (upload, feed, delete)
    ├── db.py            # SQLAlchemy models (User, Post) & DB session setup
    ├── images.py         # ImageKit client configuration
    ├── schemas.py        # Pydantic schemas for users/posts
    └── users.py          # fastapi-users auth backend & user manager
```

## Prerequisites

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) package manager
- An [ImageKit.io](https://imagekit.io/) account (for media upload/storage)

## Setup

1. **Clone the project and install dependencies**

   ```bash
   uv sync
   ```

2. **Create a `.env` file** in the project root with your ImageKit credentials:

   ```env
   IMAGEKIT_PRIVATE_KEY=your_private_key
   IMAGEKIT_URL=your_url_endpoint
   ```

3. **Run the backend API**

   ```bash
   uv run main.py
   ```

   This starts the FastAPI server at `http://localhost:8000`. The SQLite database (`test.db`) and tables are created automatically on startup.

4. **Run the frontend** (in a separate terminal)

   ```bash
   uv run streamlit run frontend.py
   ```

   This opens the Streamlit app in your browser, typically at `http://localhost:8501`.

## API Endpoints

| Method | Endpoint             | Description                          |
|--------|-----------------------|---------------------------------------|
| POST   | `/auth/register`      | Register a new user                  |
| POST   | `/auth/jwt/login`     | Log in and receive a JWT access token|
| GET    | `/users/me`           | Get current logged-in user info      |
| POST   | `/upload`             | Upload a media file with a caption   |
| GET    | `/feed`               | Get all posts, newest first           |
| DELETE | `/posts/{post_id}`    | Delete a post (owner only)           |

Interactive API docs are available at `http://localhost:8000/docs` once the backend is running.
