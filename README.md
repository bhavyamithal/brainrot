# brainrot

AI-powered viral content generation platform. Automatically creates short-form vertical videos from trending topics using AI script generation, text-to-speech, and video assembly.

## Features

- **Trend Detection**: Fetches trending topics from Reddit and Google Trends
- **Script Generation**: AI-powered script writing with customizable templates
- **Text-to-Speech**: Free TTS via Microsoft Edge's neural voices
- **Video Assembly**: FFmpeg-powered video creation with stylized captions
- **YouTube Upload**: Automated uploads with quota management
- **Analytics Dashboard**: Streamlit-based performance tracking
- **Scheduling**: APScheduler integration for automated content pipelines

## Prerequisites

- Python 3.10 or higher
- FFmpeg (required for video processing)
- Ollama (optional, for local LLM inference)

### Installing FFmpeg

**macOS:**
```bash
brew install ffmpeg
```

**Ubuntu/Debian:**
```bash
sudo apt update && sudo apt install ffmpeg
```

**Windows:**
Download from [ffmpeg.org](https://ffmpeg.org/download.html) and add to PATH.

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/brainrot.git
cd brainrot

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install the package
pip install -e .

# Install development dependencies (optional)
pip install -e ".[dev]"
```

## Configuration

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Edit `.env` with your API credentials:
```bash
# Required: YouTube API
YOUTUBE_API_KEY=your_api_key
YOUTUBE_CLIENT_SECRETS_FILE=/path/to/client_secrets.json
YOUTUBE_CREDENTIALS_FILE=/path/to/credentials.json

# Required: Reddit API
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_client_secret
REDDIT_USER_AGENT=brainrot/0.1.0 by your_username

# Optional: LLM providers
GROQ_API_KEY=your_groq_key
OLLAMA_HOST=http://localhost:11434
```

See [docs/setup.md](docs/setup.md) for detailed API credential setup instructions.

## Quick Start

### Check Status
```bash
brainrot status
```

### Fetch Trending Topics
```bash
brainrot trends --limit 10
```

### Generate a Video
```bash
brainrot generate --template tech_news --voice energetic
```

### Run Full Pipeline
```bash
brainrot run --dry-run  # Test without uploading
brainrot run            # Full pipeline with upload
```

### Launch Analytics Dashboard
```bash
brainrot dashboard --port 8501
```

## CLI Commands

| Command | Description |
|---------|-------------|
| `brainrot run` | Execute full content pipeline |
| `brainrot trends` | Fetch and display trending topics |
| `brainrot generate` | Create a single video |
| `brainrot upload` | Process upload queue |
| `brainrot status` | Show pipeline state |
| `brainrot dashboard` | Launch analytics dashboard |

### Global Options

- `-v, --verbose`: Enable debug logging

### Command Options

**run:**
- `--dry-run`: Skip upload step
- `--max-trends N`: Limit trends to fetch
- `--max-videos N`: Limit videos to generate
- `--max-uploads N`: Limit uploads per run

**trends:**
- `-l, --limit N`: Number of trends to show
- `-j, --json-output`: Output as JSON

**generate:**
- `-t, --trend-id ID`: Specific trend to process
- `-T, --template NAME`: Video template (tech_news, data_story, explainer, listicle)
- `-V, --voice PROFILE`: Voice profile (default, energetic, calm, professional, casual)
- `-o, --output DIR`: Output directory

**upload:**
- `-m, --max N`: Maximum uploads to process
- `--human-review`: Enable review checkpoint
- `--dry-run`: Show queue status without uploading

**dashboard:**
- `-p, --port N`: Server port (default: 8501)
- `--no-browser`: Don't open browser automatically

## Architecture

```
+------------------+     +------------------+     +------------------+
|   Trend Sources  |     | Script Generator |     |   TTS Client     |
|  - Reddit        | --> |  - Templates     | --> |  - edge-tts      |
|  - Google Trends |     |  - LLM (Ollama)  |     |  - Voice profiles|
+------------------+     +------------------+     +------------------+
                                                           |
                                                           v
+------------------+     +------------------+     +------------------+
| YouTube Upload   | <-- | Video Assembly   | <-- | Asset Manager    |
|  - Quota mgmt    |     |  - FFmpeg        |     |  - Pexels        |
|  - OAuth flow    |     |  - Templates     |     |  - Pixabay       |
+------------------+     +------------------+     +------------------+
         |
         v
+------------------+     +------------------+
| Analytics Fetch  | --> | Performance Agent|
|  - SQLite store  |     |  - Recommendations|
|  - CSV/JSON exp  |     |  - Viral detection|
+------------------+     +------------------+
```

### Data Flow

1. **Trend Fetch**: Reddit and Google Trends APIs provide trending content
2. **Script Gen**: LLM generates scripts from trends using templates
3. **Audio Synthesis**: edge-tts creates narration from scripts
4. **Asset Search**: Pexels/Pixabay provide background footage
5. **Video Assembly**: FFmpeg combines audio, video, and captions
6. **Upload**: YouTube Data API uploads with quota tracking
7. **Analytics**: Performance data stored and analyzed

### Directory Structure

```
brainrot/
+-- brainrot/
|   +-- __init__.py
|   +-- cli.py              # CLI commands
|   +-- config.py           # Settings management
|   +-- types.py            # Data models
|   +-- logging_config.py   # Structured logging
|   +-- exceptions.py       # Exception hierarchy
|   +-- llm_client.py       # Ollama/Groq client
|   +-- youtube_client.py   # YouTube API client
|   +-- trends/             # Trend detection
|   +-- content/            # Script generation
|   +-- audio/              # TTS integration
|   +-- video/              # Video assembly
|   +-- assets/             # Stock footage
|   +-- templates/          # Video templates
|   +-- pipeline/           # Orchestration
|   +-- scheduler/          # Job scheduling
|   +-- analytics/          # Performance tracking
|   +-- dashboard/          # Streamlit app
|   +-- agents/             # AI agents
+-- tests/
+-- docs/
+-- pyproject.toml
+-- .env.example
```

## Templates

Built-in video templates:

| Template | Style | Use Case |
|----------|-------|----------|
| `tech_news` | Dark, cyan accents | Technology updates |
| `data_story` | Light, blue accents | Data visualization |
| `explainer` | Clean, green accents | Educational content |
| `listicle` | Bold, red accents | Countdown videos |

See [docs/content-templates.md](docs/content-templates.md) for creating custom templates.

## Quota Management

YouTube API has daily quota limits (default: 10,000 units). Video uploads cost 1,600 units each.

- Maximum 5 uploads per day (configurable)
- Automatic quota reset at midnight UTC
- Upload queue persists across restarts
- Resumable uploads for large files

## Development

### Running Tests
```bash
pytest tests/ -v
```

### Type Checking
```bash
mypy brainrot/
```

### Linting
```bash
ruff check brainrot/
```

## Deployment

### Docker Deployment

The platform can be deployed using Docker Compose for VPS or local server environments.

#### Prerequisites
- Docker and Docker Compose installed
- API credentials configured in `.env`

#### Quick Deploy
```bash
./scripts/deploy.sh deploy
```

#### Available Commands
```bash
./scripts/deploy.sh deploy    # Build and start all services
./scripts/deploy.sh start     # Start existing services
./scripts/deploy.sh stop      # Stop all services
./scripts/deploy.sh restart   # Restart all services
./scripts/deploy.sh status    # Show service status
./scripts/deploy.sh logs      # View logs (add service name to filter)
./scripts/deploy.sh build     # Build containers only
```

#### Services
| Service | Description | Port |
|---------|-------------|------|
| `scheduler` | Runs content pipeline on schedule | - |
| `dashboard` | Streamlit analytics interface | 8501 |

#### Volume Mounts
| Host Path | Container Path | Purpose |
|-----------|----------------|---------|
| `./cache` | `/app/cache` | Analytics DB, pipeline state, audio cache |
| `./credentials` | `/app/credentials` | YouTube OAuth tokens |
| `./output` | `/app/output` | Generated videos |
| `./logs` | `/app/logs` | Application logs |

#### Health Checks
Both services include health checks:
- `scheduler`: FFmpeg availability check every 60s
- `dashboard`: HTTP health endpoint check every 30s

#### Manual Docker Commands
```bash
docker-compose up -d          # Start in background
docker-compose down           # Stop all services
docker-compose logs -f        # Follow all logs
docker-compose ps             # Show status
docker-compose config         # Validate configuration
```

#### Monitoring
- Logs: `docker-compose logs -f scheduler`
- Container status: `docker-compose ps`
- Dashboard: http://localhost:8501

## License

MIT License - see [LICENSE](LICENSE) for details.
