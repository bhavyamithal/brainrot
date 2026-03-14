
## Wave 1 Task 1: Project Scaffolding (2026-03-15)

### Decisions Made
- Used PEP 621 compliant `pyproject.toml` with hatchling as build backend
- Set minimum Python version to 3.10 (supports modern type hints and features)
- All API dependencies are free-tier (YouTube Data API, Reddit API, Ollama local)
- No paid API dependencies included

### Package Structure
```
brainrot/
├── __init__.py      # Package init with __version__ = "0.1.0"
├── pyproject.toml   # PEP 621 build config
├── .python-version  # pyenv compatibility (3.11)
├── .env.example     # Environment template
├── .gitignore       # Includes .env, media files
└── tests/
    └── __init__.py
```

### Dependencies
- Core: ffmpeg-python, requests, pydantic, python-dotenv, ollama, pytube, praw, google-api-python-client, google-auth-oauthlib
- Dev: pytest, pytest-asyncio, mypy, ruff

### Environment Variables Required
- YOUTUBE_API_KEY, YOUTUBE_CLIENT_SECRETS_FILE, YOUTUBE_CREDENTIALS_FILE
- REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT
- GROQ_API_KEY (optional), OLLAMA_HOST (optional)

### Notes
- Entry point defined: `brainrot = "brainrot.cli:main"` (cli module to be created)
- pyenv not configured on this system; package requires Python 3.10+
