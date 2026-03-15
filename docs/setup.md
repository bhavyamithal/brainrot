# Setup Guide

This guide covers setting up all required API credentials and running your first video generation.

## YouTube API Setup

YouTube API is required for uploading videos and fetching analytics.

### Step 1: Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click "Select a project" at the top, then "New Project"
3. Enter a project name (e.g., "brainrot-content")
4. Click "Create"

### Step 2: Enable YouTube Data API v3

1. In your project, go to "APIs & Services" > "Library"
2. Search for "YouTube Data API v3"
3. Click on it and press "Enable"

### Step 3: Create API Key

1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "API Key"
3. Copy the API key (you'll add it to `.env`)
4. (Recommended) Click "Restrict Key" and limit to YouTube Data API v3

### Step 4: Create OAuth 2.0 Credentials

1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth client ID"
3. If prompted, configure the OAuth consent screen:
   - User Type: External
   - App name: brainrot
   - User support email: your email
   - Developer contact: your email
   - Click "Save and Continue" through the remaining screens
4. Back to OAuth client ID:
   - Application type: "Desktop app"
   - Name: "brainrot-client"
   - Click "Create"
5. Click the download button to save `client_secrets.json`
6. Save this file to a secure location (e.g., `~/.config/brainrot/client_secrets.json`)

### Step 5: Configure Environment Variables

Add to your `.env` file:

```bash
YOUTUBE_API_KEY=AIzaSy...your_api_key
YOUTUBE_CLIENT_SECRETS_FILE=/path/to/client_secrets.json
YOUTUBE_CREDENTIALS_FILE=/path/to/credentials.json
```

The `credentials.json` file will be created automatically on first authentication.

### First Authentication

When you first run an upload command, a browser window will open for OAuth consent. After authorizing, credentials are saved for future use.

## Reddit API Setup

Reddit API is required for fetching trending content.

### Step 1: Create a Reddit App

1. Log in to [Reddit](https://www.reddit.com/)
2. Go to [Reddit App Preferences](https://www.reddit.com/prefs/apps)
3. Scroll down and click "Create App" or "Create Another App"
4. Fill in the form:
   - Name: brainrot
   - App type: Select "script"
   - Description: (optional)
   - About URL: (optional)
   - Redirect URI: `http://localhost:8080`
5. Click "Create app"

### Step 2: Get Credentials

After creation, you'll see:
- **Client ID**: The string under "personal use script" (looks like `abc123xyz`)
- **Client Secret**: The string next to "secret"

### Step 3: Configure Environment Variables

Add to your `.env` file:

```bash
REDDIT_CLIENT_ID=abc123xyz
REDDIT_CLIENT_SECRET=your_secret_here
REDDIT_USER_AGENT=brainrot/0.1.0 by your_reddit_username
```

## Optional: Stock Footage APIs

Background videos come from free stock footage sources.

### Pexels API

1. Go to [Pexels API](https://www.pexels.com/api/new/)
2. Sign up or log in
3. Create a new application
4. Copy your API key

Add to `.env`:
```bash
PEXELS_API_KEY=your_pexels_key
```

### Pixabay API

1. Go to [Pixabay API Documentation](https://pixabay.com/api/docs/)
2. Sign up or log in
3. Find your API key in your account settings

Add to `.env`:
```bash
PIXABAY_API_KEY=your_pixabay_key
```

Without these keys, videos will use solid color backgrounds instead of stock footage.

## Optional: Ollama Setup (Local LLM)

Ollama provides free local LLM inference for script generation.

### Installation

**macOS:**
```bash
brew install ollama
```

**Linux:**
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

**Windows:**
Download from [ollama.com](https://ollama.com/download)

### Start Ollama

```bash
ollama serve
```

### Pull a Model

```bash
ollama pull llama3.2
```

### Configure Environment

The default configuration works without changes:

```bash
OLLAMA_HOST=http://localhost:11434
```

## Optional: Groq API (Fast Cloud LLM)

Groq provides fast cloud LLM inference as a fallback when Ollama is unavailable.

1. Go to [Groq Console](https://console.groq.com/)
2. Sign up or log in
3. Go to API Keys and create a new key
4. Copy the key

Add to `.env`:
```bash
GROQ_API_KEY=gsk_your_key_here
```

## First Video Generation

### 1. Verify Installation

```bash
brainrot status
```

You should see pipeline status output.

### 2. Fetch Trends

```bash
brainrot trends --limit 5
```

This fetches trending topics from Reddit and Google Trends.

### 3. Generate a Video (Dry Run)

```bash
brainrot generate --template tech_news --voice energetic
```

This creates a video without uploading it.

The video will be saved to `./cache/videos/` by default.

### 4. Check the Output

Videos are saved with timestamps in the filename. Open the video to verify:
- Captions are readable
- Audio is clear
- Background matches the theme

### 5. Run Full Pipeline (Optional)

To run the complete workflow with upload:

```bash
brainrot run
```

This will:
1. Fetch trends
2. Generate scripts
3. Create videos
4. Upload to YouTube
5. Fetch analytics

## Troubleshooting

### "FFmpeg not found"

Install FFmpeg:
```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt install ffmpeg
```

### "YouTube quota exceeded"

YouTube API has daily limits. Check your quota:
- Go to [Google Cloud Console](https://console.cloud.google.com/)
- Navigate to "APIs & Services" > "Dashboard"
- Click on YouTube Data API v3
- View quota usage

### "Reddit API error"

Verify your credentials:
- Client ID is the short string under "personal use script"
- Client Secret is the longer string
- User Agent should be in format: `appname/version by username`

### "Ollama connection refused"

Make sure Ollama is running:
```bash
ollama serve
```

Or check the OLLAMA_HOST in your `.env` file.

### "No trends found"

This can happen if:
- Reddit API credentials are invalid
- Google Trends rate limiting (wait and retry)
- Network connectivity issues

Try fetching with verbose output:
```bash
brainrot trends -v --limit 5
```

## Next Steps

- [Content Templates Guide](content-templates.md) - Create custom video styles
- Run `brainrot --help` for all CLI commands
- Check `./cache/` directory for generated content
