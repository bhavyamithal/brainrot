
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

## Wave 1 Task 4: Logging + Error Handling Framework (2026-03-15)

### Files Created
- `brainrot/logging_config.py` - Structured logging with JSON formatter
- `brainrot/exceptions.py` - Exception hierarchy and retry decorator

### Exception Hierarchy
```
BrainrotError (base)
├── ConfigurationError
├── AuthenticationError
├── QuotaExceededError
├── TrendFetchError
├── VideoGenerationError
└── UploadFailedError
```

### Key Features
- `setup_logging(level, json_output)` - Configures root logger
- `set_correlation_id()` / `get_correlation_id()` - Context-aware request tracing
- `JSONFormatter` - Structured JSON output for logs
- `@retry(max_attempts, backoff_factor, exceptions)` - Exponential backoff decorator

### Compatibility Note
- Used `from __future__ import annotations` for Python 3.9 compatibility
- System has Python 3.9.6, but package targets 3.10+

## Wave 1 Task 3: Type Definitions + Interfaces (2026-03-15)

### Files Created
- `brainrot/types.py` - Core data models and Protocol interfaces

### Data Models Defined
- `Trend` - Trending content from external sources (id, title, source, url, score, fetched_at, keywords)
- `Script` - Generated script content (id, trend_id, text, hook, word_count, template, created_at)
- `Video` - Assembled video metadata (id, script_id, path, duration, thumbnail_path, created_at)
- `Channel` - Platform channel config (id, name, platform, credentials_path, is_active)
- `Analytics` - Video performance metrics (video_id, views, likes, comments, avg_view_duration, fetched_at)
- `UploadResult` - Upload operation result (video_id, platform, external_id, status, uploaded_at, error)
- `ContentTemplate` - Video styling configuration (name, style_config, caption_style, font_family, colors)

### Protocol Interfaces
- `TrendSource` - fetch(limit) -> List[Trend]
- `ScriptGenerator` - generate(trend, template) -> Script
- `VideoAssembler` - assemble(script, template) -> Video
- `Publisher` - publish(video, channel) -> UploadResult

### Type Aliases
- `JSONDict`, `StringList`, `OptionalStr`, `OptionalPath`

### Notes
- All models use Pydantic BaseModel with Field for validation
- Protocols use @runtime_checkable decorator for isinstance checks
- Follows existing codebase style (from __future__ import annotations)


## Wave 1 Task 6: LLM Client Setup (2026-03-15)

### File Created
- `brainrot/llm_client.py` - Unified LLM client with Ollama/Groq support

### Key Features
- `LLMClient` class with auto-provider detection
- Primary: Ollama (local, http://localhost:11434)
- Fallback: Groq free tier (llama-3.1-8b-instant)
- `@retry` decorator for transient failures
- `generate(prompt, model, system, **kwargs)` method

### Default Models
- Ollama: `llama3.2`
- Groq: `llama-3.1-8b-instant` (free tier)

### API Patterns
- Ollama: Uses `ollama.chat()` from ollama package
- Groq: Uses `requests.post()` to OpenAI-compatible endpoint

### Notes
- Lazy import of `ollama` package inside `_generate_ollama()` to avoid import errors when only using Groq
- Provider detection caches result in `_ollama_available` to avoid repeated health checks

## Wave 1 Task 5: YouTube API Client + Quota Tracker (2026-03-15)

### Files Created
- `brainrot/youtube_client.py` - YouTube Data API v3 client with OAuth and quota management

### Classes Implemented
- `QuotaManager` - Daily quota tracking with JSON persistence
  - `record_upload(units)` - Deduct quota units (default 1600)
  - `remaining_quota()` - Get remaining units
  - `can_upload(units)` - Check if upload possible
  - `_reset_if_new_day()` - Auto-reset at midnight UTC
- `YouTubeClient` - OAuth 2.0 and video operations
  - `authenticate()` - OAuth flow with credential persistence
  - `upload_video(video, title, description, tags, category_id, privacy_status)` -> UploadResult
  - `get_video_analytics(video_id)` -> dict
  - `get_channel_info()` -> dict

### Quota Constants
- `DEFAULT_DAILY_QUOTA = 10000` units
- `UPLOAD_QUOTA_COST = 1600` units
- `SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]`

### Key Design Decisions
- Quota persisted to `cache_dir/youtube_quota.json` with date and used_quota
- Automatic quota reset when date changes (UTC timezone)
- Credentials saved as JSON with token, refresh_token, client_id, client_secret
- Resumable uploads with 1MB chunk size
- QuotaExceededError raised before upload attempt if quota insufficient

### Bug Fix Applied
- Added `from __future__ import annotations` to `config.py` for Python 3.9 compatibility
- Added missing `from google.auth.transport.requests import Request` import for credential refresh

### Notes
- Category ID "22" = People & Blogs (default for uploads)
- Privacy status defaults to "private" for safety
- Upload uses resumable MediaFileUpload for large files

## Wave 1 Task 10: Stock Footage/Asset Manager (2026-03-15)

### Files Created
- `brainrot/assets/__init__.py` - Package exports
- `brainrot/assets/sources/__init__.py` - Sources package exports
- `brainrot/assets/sources/pexels.py` - Pexels API integration
- `brainrot/assets/sources/pixabay.py` - Pixabay API integration
- `brainrot/assets/manager.py` - Unified asset management

### Classes Implemented
- `PexelsSource` - Free stock video source from Pexels
  - `search(query, limit, orientation, size)` - Video search
  - `get_popular(limit)` - Get trending videos
  - `get_by_id(video_id)` - Get specific video
- `PixabaySource` - Free stock video/image source from Pixabay
  - `search(query, limit, video_type, orientation, category)` - Video search
  - `search_images(query, limit, image_type, orientation)` - Image search
  - `get_categories()` - Available category filters
- `AssetManager` - Unified asset management
  - `search(query, source, limit)` - Search single source
  - `search_all_sources(query, limit_per_source)` - Search all sources
  - `download(asset_url, filename)` - Download to cache
  - `get_cached(asset_id)` - Check cache
  - `track_usage(asset_id, context)` - Record usage
  - `get_usage_stats(asset_id)` - Get usage count
  - `get_unused_assets(assets)` - Filter unused
  - `get_least_used_assets(assets, max_usage)` - Filter by usage threshold
- `LocalAssetLibrary` - Custom footage management
  - `add_asset(file_path, category, tags, mood)` - Add local file
  - `search(query, category, tags, mood)` - Search local assets
  - `get_categories()` - List used categories
  - `get_by_mood(mood)` - Filter by mood
- `BackgroundMusicLibrary` - Royalty-free music management
  - `add_track(file_path, title, mood, tempo, duration, source, license_info)` - Add track
  - `search(mood, tempo, max_duration)` - Search tracks
  - `get_random_track(mood)` - Get random track
  - `get_available_moods()` - List moods

### API Keys
- Pexels: Users need their own key from https://www.pexels.com/api/new/
- Pixabay: Users need their own key from https://pixabay.com/api/docs/
- Both use placeholder defaults that need to be replaced for actual API calls

### Data Persistence
- Usage tracking: `cache_dir/asset_usage.json`
- Local library metadata: `library_dir/library_metadata.json`
- Music library: `music_dir/music_library.json`

### License Compatibility
- Pexels License: Free for commercial use, no attribution required
- Pixabay License: Free for commercial use, no attribution required

### Notes
- Both APIs return videos with royalty-free licenses suitable for commercial content
- Asset IDs prefixed with source name (e.g., 'pexels_123', 'pixabay_456')
- Video files selected by highest resolution available

## Wave 1 Task 7: Trend Detection Engine (2026-03-15)

### Files Created
- `brainrot/trends/__init__.py` - Package exports
- `brainrot/trends/reddit.py` - Reddit API integration via PRAW
- `brainrot/trends/google_trends.py` - Google Trends integration via pytrends
- `brainrot/trends/aggregator.py` - Trend aggregation and caching

### Classes Implemented
- `RedditTrendSource` - Fetches trending posts from Reddit
  - `__init__(subreddits)` - Configurable subreddit list
  - `fetch(limit)` - Returns list of Trend objects
  - Filters: stickied posts, NSFW content, low score (<100)
  - Default subreddits: technology, programming, artificial, MachineLearning
- `GoogleTrendsSource` - Fetches trending searches from Google Trends
  - `__init__(geo)` - Geographic region (default: US)
  - `fetch(limit)` - Returns daily trending searches
  - `fetch_related_topics(query, limit)` - Get related topics for a query
- `TrendAggregator` - Combines trends from multiple sources
  - `__init__(sources, cache)` - Accepts list of TrendSource implementations
  - `add_source(source)` - Add source dynamically
  - `get_trends(limit, fetch_limit, exclude_processed)` - Fetch and aggregate
  - Deduplicates by title similarity (Jaccard index, threshold 0.7)
  - Ranks by: score + recency bonus (up to 20% for recent)
- `TrendCache` - Tracks processed trends to avoid reprocessing
  - `is_processed(trend_id)` - Check if trend was processed
  - `mark_processed(trend_id)` - Mark single trend
  - `mark_many_processed(trend_ids)` - Mark multiple trends
  - `clear()` - Reset cache
  - Persists to `cache_dir/trend_cache.json`

### Dependencies Added
- `pytrends>=4.9.0` - Google Trends API client

### Design Patterns
- Lazy initialization for API clients (Reddit client created on first fetch)
- Protocol class for source interface compatibility
- Graceful degradation: continues to other sources on individual failures
- Error aggregation: collects errors from all sources before raising

### Filtering Logic
- Reddit: Skip stickied, NSFW, score < 100
- Deduplication: Jaccard similarity on word sets (threshold 0.7)
- Cache: Exclude previously processed trend IDs

### Notes
- PRAW Reddit client is read-only (no user authentication needed)
- pytrends uses unofficial Google Trends API (may have rate limits)
- Trend IDs prefixed by source: 'reddit-', 'gt-'
- Recency bonus formula: `max(0, 1 - age_hours/24) * 0.2`

## Wave 1 Task 8: Script Generator with Templates (2026-03-15)

### Files Created
- `brainrot/content/__init__.py` - Package exports
- `brainrot/content/script_generator.py` - Script generation with templates
- `brainrot/content/templates/` - Directory for future template files

### Classes Implemented
- `ScriptTemplate` (dataclass) - Template definition
  - `name`, `system_prompt`, `user_prompt_template`, `min_words`, `max_words`
  - `format_prompt(**kwargs)` - Fills placeholders with values
- `ScriptGenerator` - Main generator class
  - `__init__(llm_client)` - Optional LLM client injection
  - `generate(trend, template)` - Generate script from trend
  - `_validate_script(text, min_words, max_words)` - Check length
  - `_extract_hook(text)` - Get first engaging sentence
  - `_count_words(text)` - Word counter
  - `register_template(template)` - Add custom templates
  - `get_template(name)` - Retrieve template by name
  - `is_duplicate(trend_id)` - Check history for existing script
  - `get_history(limit)` - Retrieve recent scripts
  - `clear_history()` - Reset history

### Default Templates
- `news_synthesis` - Tech news summary with analysis
  - System: Engaging tech content creator persona
  - Placeholders: {title}, {source}, {url}, {keywords}
  - Constraints: 150-300 words, compelling hook required
- `explainer` - Concept explanation with examples
  - System: Simplifier of complex concepts
  - Placeholders: {title}, {keywords}
  - Constraints: 150-300 words, analogy-based explanation

### Script History
- Persisted to `cache_dir/script_history.json`
- Tracks all generated scripts with full metadata
- Prevents duplicate content generation
- `is_duplicate()` checks before generating

### Key Design Decisions
- Lazy LLM client initialization (creates on first use if not provided)
- Template validation with word count bounds (150-300 for 30-second videos)
- Hook extraction using regex sentence splitting (first sentence, max 150 chars)
- Auto-adjustment attempt via LLM regeneration if validation fails
- Trend can be passed as Trend object or dict for flexibility

### Notes
- Templates use Python format strings with named placeholders
- Word count validation is strict - raises ValueError on failure
- History stores full Script model data for reconstruction

## Wave 1 Task 9: TTS Integration (2026-03-15)

### Files Created
- `brainrot/audio/__init__.py` - Package exports
- `brainrot/audio/tts.py` - TTS client with edge-tts integration

### Classes Implemented
- `TTSClient` - Text-to-speech client using edge-tts
  - `synthesize(text, voice, output_path)` - Generate speech from text
  - `_synthesize_edge(text, voice)` - edge-tts API call
  - `_normalize_audio(input_path, output_path)` - FFmpeg loudnorm filter
  - `_get_cache_key(text, voice)` - MD5 hash for caching
  - `_get_voice_config(voice)` - Resolve profile name to config
  - `get_available_voices()` - List supported voice IDs
  - `get_voice_profiles()` - List predefined profiles
  - `register_voice_profile(name, config)` - Add custom profile
  - `clear_cache()` - Remove cached audio files

### Voice Profiles
- `default` - en-US-AriaNeural, neutral rate/pitch
- `energetic` - en-US-JennyNeural, +10% rate, +5Hz pitch
- `calm` - en-US-GuyNeural, -5% rate, -5Hz pitch
- `professional` - en-GB-SoniaNeural, neutral
- `casual` - en-AU-NatashaNeural, +5% rate

### Audio Normalization
- FFmpeg loudnorm filter: `loudnorm=I=-14:TP=-1.5:LRA=11`
- Target: -14 LUFS (streaming standard)
- Output: 44.1kHz stereo MP3

### Dependencies Added
- `edge-tts>=6.1.0` - Microsoft Edge TTS (free, no API key)

### Key Design Decisions
- Lazy import of `brainrot.config.settings` to avoid triggering Settings validation at module import time
- Cache stored in `cache_dir/audio/` with MD5 hash filenames
- Voice profiles support both rate and pitch adjustments
- asyncio.run() wrapper for edge-tts async API

### Gotcha
- Importing `from brainrot.config import settings` at module level causes Settings() instantiation which requires env vars
- Solution: Use lazy import in `_get_default_cache_dir()` helper function

## Wave 1 Task 11: Video Assembly Pipeline (2026-03-15)

### Files Created
- `brainrot/video/__init__.py` - Package exports
- `brainrot/video/captions.py` - ASS format subtitle generation
- `brainrot/video/assembly.py` - FFmpeg-based video builder

### Classes Implemented
- `CaptionStyle` (dataclass) - Caption appearance configuration
  - font_family, font_size, color, outline_color, outline_width
  - position (top/center/bottom), margin_v, alignment
  - `to_ass_style()` - Convert to ASS style definition string
- `CaptionLine` (dataclass) - Single caption line with timing
- `CaptionGenerator` - Generates ASS format subtitles
  - `generate_ass(text, duration, words_per_line, words_per_second)` - Full ASS content
  - `generate_ass_to_file(text, duration, output_path)` - Save to disk
  - `_split_into_lines()`, `_time_lines()`, `_build_ass_file()` - Internal helpers
- `BackgroundConfig` (dataclass) - Video background settings
- `AudioConfig` (dataclass) - Audio track configuration
- `ConcatDemuxer` - FFmpeg concat demuxer file generator
  - `add_entry(source, duration)` - Add video file entry
  - `add_color(color, duration)` - Add solid color entry
  - `build()` - Generate concat file (CRITICAL: repeats last entry)
  - `cleanup()` - Remove generated file
- `VideoBuilder` - Main video assembly class
  - `add_background(source, duration)` - Add footage or color
  - `add_captions(text, style)` - Add subtitle overlay
  - `add_audio(audio_path, music_path, music_volume)` - Add audio tracks
  - `render(output_path, progress_callback)` - Render final video
  - `_build_ffmpeg_command()` - Construct FFmpeg command
  - `_execute_ffmpeg()` - Run with progress tracking
- `check_ffmpeg_available()` - Utility to check FFmpeg installation

### ASS Format Details
- Color format: `&HAABBGGRR` (alpha, blue, green, red) - NOT typical hex
- Alignment: Numpad layout (1-9), bottom=2, center=5, top=8
- Bold: -1 for true, 0 for false
- Style format: 21 fields in specific order

### FFmpeg Commands Used
- Scale/crop for vertical: `scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920`
- Subtitle overlay: `ass='path/to/captions.ass'`
- Pixel format: `-pix_fmt yuv420p` (compatibility)
- Audio mix: `amix=inputs=2:duration=first:dropout_transition=2`
- Web optimization: `-movflags +faststart`

### CRITICAL: FFmpeg Concat Demuxer Bug
- FFmpeg concat demuxer does NOT honor duration of last entry
- Workaround: Repeat the last entry in the concat file
- Example:
  ```
  file 'video.mp4'
  duration 10.0
  file 'video.mp4'  # Repeated to honor duration
  ```

### Key Design Decisions
- Resolution default: 1080x1920 (vertical/TikTok format)
- H.264 codec with medium preset, CRF 23
- AAC audio at 192kbps
- Progress tracking via stderr parsing (Duration/time regex)
- Temp files cleaned up after render (success or failure)
- Supports both video files and solid color backgrounds
- Audio duration auto-detection via ffprobe

### Video Filter Chain
1. Scale with aspect ratio preservation (increase mode)
2. Crop to exact resolution
3. ASS subtitle overlay (if captions provided)

### Notes
- FFmpeg/ffprobe must be installed on system (not bundled)
- `check_ffmpeg_available()` utility for runtime verification
- Subprocess-based execution with stderr parsing for progress
- Error handling via VideoGenerationError from exceptions module

## Wave 1 Task 12: Content Templates Library (2026-03-15)

### Files Created
- `brainrot/templates/__init__.py` - Package exports
- `brainrot/templates/renderer.py` - TemplateConfig and TemplateRenderer classes
- `brainrot/templates/tech_news.json` - Dark tech news style template
- `brainrot/templates/data_story.json` - Light data visualization template
- `brainrot/templates/explainer.json` - Clean educational template
- `brainrot/templates/listicle.json` - Bold countdown style template

### Classes Implemented
- `BackgroundStyle` (dataclass) - Background configuration
  - type, color, secondary_color, gradient_direction, opacity
- `TransitionConfig` (dataclass) - Transition effect settings
  - type, duration, easing
- `TypographyConfig` (dataclass) - Font configuration
  - primary_font, secondary_font, sizes, line_height, letter_spacing
- `ColorPalette` (dataclass) - Color scheme
  - primary, secondary, background, text, text_secondary, accent, outline
- `TemplateConfig` (dataclass) - Complete template definition
  - name, display_name, description, background, caption, transition, typography, colors
  - `from_json(path)` - Load from JSON file
  - `from_dict(data)` - Create from dictionary
  - `to_content_template()` - Convert to ContentTemplate for type compatibility
- `TemplateRenderer` - Applies template to VideoBuilder
  - `load_template(name)` - Load template by name
  - `get_caption_style()` - Get CaptionStyle for template
  - `apply_to_builder(builder, script, audio_path, duration)` - Apply styling
  - `generate_thumbnail(video_path, output_path, timestamp)` - Extract frame via FFmpeg
  - `get_style_summary()` - Get summary dict of template styling

### Functions
- `list_templates()` - Returns sorted list of available template names
- `get_template_path(name)` - Returns Path to template JSON file

### Template Visual Distinctions
- **tech_news**: Dark (#1a1a2e), cyan accents (#00d9ff), Montserrat Bold, bottom captions, fade
- **data_story**: Light (#f8f9fa), blue accents (#3498db), Open Sans Bold, center captions, zoom
- **explainer**: White (#FFFFFF), green accents (#00b894), Roboto Medium, bottom captions, fade
- **listicle**: Black (#0d0d0d), red accents (#ff6b6b), Bebas Neue, top captions, slide

### Color Format Conversion
- ASS format uses `&HAABBGGRR` (alpha, blue, green, red)
- `hex_to_ass()` converts `#RRGGBB` to ASS format
- Example: `#FFFFFF` → `&H00FFFFFF`

### Key Design Decisions
- Templates stored as JSON files alongside Python module
- TemplateConfig dataclass provides structured access to template data
- TemplateRenderer bridges template config to VideoBuilder method calls
- Each template must have distinctly different visual branding (per MUST NOT DO)
- CaptionStyle derived from template caption config + typography + colors
- Thumbnail generation uses FFmpeg with configurable timestamp

### Integration Points
- Uses `CaptionStyle` from `brainrot.video.captions`
- Uses `VideoBuilder` from `brainrot.video.assembly`
- Uses `Script` and `ContentTemplate` from `brainrot.types`
- TemplateConfig can convert to ContentTemplate for type compatibility

### Notes
- Gradient backgrounds currently fall back to solid color (gradient FFmpeg filter work needed)
- Template directory resolved via `Path(__file__).parent`
- All 4 templates verified loading with distinct styling

## Wave 1 Task 14: Scheduling System (2026-03-15)

### Files Created
- `brainrot/scheduler/__init__.py` - Package exports
- `brainrot/scheduler/scheduler.py` - Scheduler implementation with APScheduler

### Dependencies Added
- `apscheduler>=3.10.0` - Background scheduling with multiple trigger types

### Classes Implemented
- `ScheduledJob` (dataclass) - Job state tracking
  - name, func, trigger_type, trigger_config, last_run, next_run, is_running
- `DefaultJobConfig` (dataclass) - Default job configuration
  - trend_fetch_hours (default: 4), video_generation_hours (default: 1), upload_times (default: 9am, 12pm, 6pm)
- `Scheduler` - Main scheduler class
  - `__init__(timezone)` - Timezone-aware scheduling (default: UTC)
  - `add_job(name, func, trigger, **kwargs)` - Add interval/cron/date jobs
  - `remove_job(name)` - Remove job by name
  - `start()` - Start scheduler
  - `stop(wait=True)` - Graceful shutdown (wait for running jobs)
  - `trigger_now(name)` - Manual trigger for testing
  - `get_jobs()` - List all jobs with state
  - `get_next_run(name)` - Get next run time
  - `setup_default_jobs(...)` - Configure trend_fetch, video_generation, upload jobs
  - Context manager support (`with Scheduler() as s:`)

### Trigger Types
- `interval`: Run at fixed intervals (hours, minutes, seconds)
- `cron`: Run at specific times (hour, minute, day_of_week, etc.)
- `date`: Run once at specific datetime

### Default Job Schedule
- `trend_fetch`: Every 4 hours
- `video_generation`: Every hour
- `upload`: At 09:00, 12:00, 18:00 (configurable)

### Key Design Decisions
- Used `zoneinfo.ZoneInfo` for timezone support (Python 3.9+)
- `DefaultJobConfig` allows customizing posting times without code changes
- Jobs wrapped with logging and state tracking
- Context manager ensures graceful shutdown on exit
- APScheduler's BackgroundScheduler runs in a separate thread

### Gotcha Fixed
- APScheduler job objects don't have `next_run_time` attribute until scheduler is started
- Solution: Use `getattr(job_state, "next_run_time", None)` instead of direct access

## Wave 1 Task 13: Upload Orchestrator with Quota Management (2026-03-15)

### Files Created
- `brainrot/pipeline/__init__.py` - Package exports
- `brainrot/pipeline/uploader.py` - Upload orchestration with queue management

### Classes Implemented
- `UploadStatus` (Enum) - Video upload states: PENDING, UPLOADING, UPLOADED, FAILED
- `QueuedVideo` (dataclass) - Queued video metadata
  - video_path, script, status, scheduled_at, uploaded_at, external_id, error, retry_count
  - `to_dict()` / `from_dict()` for JSON serialization
- `UploadQueue` - Queue persistence layer
  - `_load()` / `_save()` for JSON file persistence
  - `add()`, `get_pending()`, `get_failed(max_retries)`, `get_by_id()`, `update()`
  - Properties: `length`, `pending_count`, `uploaded_today`
- `UploadOrchestrator` - Main upload orchestration class
  - `__init__(youtube_client, quota_manager, queue_file, max_uploads_per_day)`
  - `queue_video(video_path, script, scheduled_at)` -> QueuedVideo
  - `process_queue(human_review, max_uploads)` -> list[UploadResult]
  - `_generate_metadata(script)` -> dict (title, description, tags)
  - `_should_upload()` -> bool (checks daily limit + quota)
  - `get_queue_status()` -> dict (full status report)
  - Properties: `uploads_today`, `queue_length`, `pending_count`

### Key Design Decisions
- Max 5 uploads per day as safety buffer (configurable via `max_uploads_per_day`)
- Queue persisted to `cache_dir/upload_queue.json` with full video metadata
- Retry logic uses `@retry` decorator with 3 attempts, 2.0 backoff factor
- Human review checkpoint: logs metadata and returns None if `human_review=True`
- Failed videos with `retry_count < 3` are retried on next `process_queue()` call
- Metadata generation: title from hook (max 60 chars), tags from word frequency + defaults

### Lazy Import Pattern (Critical)
- Used `_get_default_queue_file()` helper function to lazily import settings
- This prevents `Settings()` instantiation at module import time
- Same pattern as Task 9 (TTS) to avoid requiring environment variables for imports

### Upload Flow
1. `queue_video()` adds video to queue with PENDING status
2. `process_queue(human_review=False)` processes pending + failed (with retries < 3)
3. For each video: check `_should_upload()` (daily limit + quota)
4. `_process_single()`: generate metadata, upload with retry, update status
5. Queue persisted after each state change

### Notes
- Created `.env` file with placeholder values for testing imports
- `youtube_client.py` still has module-level settings import (would need lazy pattern for full independence)
- Upload metadata tags include: word frequency analysis + "shorts", "viral", "trending"

## Wave 1 Task 15: Analytics Fetcher (2026-03-15)

### Files Created
- `brainrot/analytics/__init__.py` - Package exports
- `brainrot/analytics/fetcher.py` - YouTube Analytics integration with SQLite

### Dependencies Added
- `aiosqlite>=0.19.0` - Async SQLite for analytics persistence

### Classes Implemented
- `VideoAnalytics` (dataclass) - Per-video performance metrics
  - video_id, views, likes, comments, avg_view_duration, fetched_at
- `ChannelAnalytics` (dataclass) - Channel-level statistics
  - channel_id, subscriber_count, total_views, video_count, fetched_at
- `VideoGrowth` (dataclass) - Trend detection metrics
  - video_id, views_growth, likes_growth, growth_score, latest_analytics
- `AnalyticsFetcher` - Main analytics class
  - `fetch_video(video_id)` - Fetch single video analytics (sync)
  - `fetch_channel()` - Fetch channel analytics (sync)
  - `fetch_all_videos(video_ids)` - Fetch multiple videos (sync)
  - `store_video_analytics(analytics)` - Store video snapshot (async)
  - `store_channel_analytics(analytics)` - Store channel snapshot (async)
  - `get_video_analytics(video_id, days)` - Retrieve stored analytics (async)
  - `get_trending_videos(limit)` - Get highest growth videos (async)
  - `export_to_csv(output_path)` - Export to CSV (async)
  - `export_to_json(output_path)` - Export to JSON (async)
  - `compare_periods(video_id, ...)` - Compare time periods (async)

### SQLite Schema
- `video_analytics`: id, video_id, views, likes, comments, avg_view_duration, fetched_at
- `channel_analytics`: id, channel_id, subscriber_count, total_views, video_count, fetched_at
- Indexes on video_id, channel_id, fetched_at for query performance

### Trend Detection Algorithm
- Analyzes snapshots from past 7 days
- Requires at least 2 snapshots per video for growth calculation
- Growth formula: `views_growth * 0.7 + likes_growth * 0.3`
- Returns sorted list by growth_score (descending)

### Key Design Decisions
- Sync methods for fetching (YouTubeClient is sync)
- Async methods for storage (aiosqlite)
- Lazy initialization of YouTube client and database
- Growth score prioritizes views (70%) over likes (30%)
- Database path defaults to `cache_dir/analytics.db`

### Integration Points
- Uses `YouTubeClient.get_video_analytics()` for video metrics
- Uses `YouTubeClient.get_channel_info()` for channel metrics
- Lazy import of `brainrot.config.settings` to avoid triggering Settings validation
- Lazy import of `brainrot.youtube_client.YouTubeClient` for optional dependency

### Notes
- Average view duration not available from basic YouTube API (returns 0.0)
- Period comparison calculates percentage change between periods
- Export includes both video and channel analytics in JSON format


## Wave 1 Task 16: Analytics Dashboard (2026-03-15)

### Files Created
- `brainrot/dashboard/__init__.py` - Package exports with run_dashboard() helper
- `brainrot/dashboard/app.py` - Streamlit dashboard application

### Dependencies Added
- `streamlit>=1.28.0` - Web framework for data apps
- `pandas>=2.0.0` - Data manipulation for charts and tables

### Dashboard Features
- Dark theme with GitHub-inspired color scheme (#0d1117 background)
- Sidebar filters: date range (st.date_input), content type (st.selectbox)
- Key metrics cards: Total Views, Total Videos, Avg Engagement, Total Likes
- Three tabs: Performance Trends, Top Videos, Trending
- Charts: st.line_chart for time series, st.bar_chart for distributions
- Tables: st.dataframe with column formatting

### Key Design Decisions
- Lazy import pattern for settings and AnalyticsFetcher (avoids Settings validation)
- Async-to-sync bridge using ThreadPoolExecutor for Streamlit compatibility
- DashboardStats dataclass for structured data aggregation
- Custom CSS injection for dark theme (_apply_dark_theme function)
- Read-only MVP (no controls, just display)

### Streamlit Integration Notes
- Streamlit doesn't natively support async - requires bridge pattern
- st.set_page_config must be first Streamlit command
- Custom theming via st.markdown with CSS
- Charts accept pandas DataFrames with index for x-axis

### Growth Score Integration
- Uses AnalyticsFetcher.get_trending_videos() for growth data
- Growth formula: views_growth * 0.7 + likes_growth * 0.3
- Requires at least 2 snapshots per video for growth calculation

### Notes
- Content type filter is placeholder (not yet implemented in fetcher)
- Dashboard accessible via: streamlit run brainrot/dashboard/app.py
- Uses port 8501 by default (configurable via --server.port)


## Wave 1 Task 17: Performance Tracking Agent (2026-03-15)

### Files Created
- `brainrot/agents/__init__.py` - Package exports
- `brainrot/agents/performance_agent.py` - Performance tracking agent implementation

### Classes Implemented
- `RecommendationType` (Enum) - Types: INCREASE_TOPIC, DECREASE_TOPIC, TEMPLATE_CHANGE, POSTING_TIME, CONTENT_LENGTH, VIRAL_OPPORTUNITY, GENERAL
- `ContentScore` (dataclass) - Scoring result with formula: views * 0.5 + engagement * 0.3 + growth * 0.2
- `ViralAlert` (dataclass) - Alert for viral detection (>2x average views)
- `ContentPattern` (dataclass) - Identified performance patterns
- `Recommendation` (dataclass) - Actionable recommendation with confidence and priority
- `PerformanceReport` (dataclass) - Comprehensive analysis report
- `WeeklySummary` (dataclass) - Weekly performance summary
- `PerformanceAgent` - Main agent class with analyze(), generate_report(), detect_viral()

### Scoring System
- Views score: Normalized against max views in dataset
- Engagement score: Normalized (likes + comments) against max engagement
- Growth score: Direct from AnalyticsFetcher VideoGrowth.growth_score
- Formula: views_weight * 0.5 + engagement_weight * 0.3 + growth_weight * 0.2
- Ranks: excellent (>=0.8), good (>=0.6), average (>=0.4), below_average (<0.4)

### Viral Detection
- Threshold: 2.0x average views (VIRAL_THRESHOLD constant)
- Creates ViralAlert with video_id, current_views, average_views, view_ratio
- acknowledge_viral_alert() method to mark alerts as handled

### Weekly Summary Features
- Stores to cache_dir/reports/weekly_summary_YYYYMMDD.json
- Tracks: videos_published, total_views, total_likes, top_video, best_template
- Generates key_insights and next_week_focus recommendations

### Integration Points
- Uses AnalyticsFetcher.get_trending_videos() for performance data
- Reads script history from cache_dir/script_history.json for pattern analysis
- Lazy import pattern for settings (avoids Settings validation at module import)
- Uses asyncio.run() wrapper for async AnalyticsFetcher methods

### Key Design Decisions
- No auto-adjust without human review (MVP limitation per task spec)
- Recommendations prioritized (1=highest) and sorted
- Pattern detection focuses on template performance and channel growth
- Reports include supporting_data dict for transparency
- Weekly summary auto-saved to JSON file

### Notes
- When no analytics data available, generates "Insufficient Data" recommendation
- ContentPattern identification requires at least 2 videos per template
- Growth score capped at [0.0, 1.0] range for scoring

## Wave 1 Task 18: Main Orchestration Pipeline (2026-03-15)

### Files Created
- `brainrot/pipeline/orchestrator.py` - Main orchestration pipeline with state management

### Classes Implemented
- `PipelineStatus` (Enum) - Pipeline execution states: PENDING, RUNNING, COMPLETED, PARTIAL, FAILED
- `StepStatus` (Enum) - Step-level states: PENDING, RUNNING, COMPLETED, SKIPPED, FAILED
- `StepResult` (dataclass) - Individual step execution tracking with timing
- `PipelineState` (dataclass) - Full pipeline state with persistence to JSON
- `PipelineResult` (dataclass) - Execution result with status, completed steps, error info
- `PipelineConfig` (dataclass) - Configuration for pipeline behavior
- `Pipeline` - Main orchestration class coordinating all components

### Methods Implemented
- `run_daily()` - Full pipeline execution with checkpoint persistence
- `run_trend_fetch()` - Fetch trends from configured sources
- `run_video_gen()` - Generate videos from trends (script → audio → video)
- `run_upload()` - Upload queued videos with quota management
- `run_analytics()` - Fetch and analyze performance data
- `resume()` - Resume from failure point (skip completed steps)
- `get_status()` - Get current pipeline status
- `reset_state()` - Clear all pipeline state

### Component Integration Order
1. TrendAggregator → fetch trends
2. ScriptGenerator → generate scripts from trends
3. TTSClient → synthesize audio
4. AssetManager → get background footage
5. VideoBuilder → assemble video with TemplateRenderer
6. UploadOrchestrator → upload to YouTube
7. AnalyticsFetcher → fetch performance data
8. PerformanceAgent → analyze and recommend

### State Persistence
- State persisted to `cache_dir/pipeline_state.json`
- Tracks: last_run, run_id, status, steps, processed_trends, generated_videos, pending_videos, uploaded_videos, errors
- Each step saves state after completion for resume capability

### Error Handling & Recovery
- On step failure: save state, log error, return PARTIAL result
- On resume: load state, skip completed steps, continue from failure
- Analytics failure is non-critical (logged but doesn't stop pipeline)

### Key Design Decisions
- Lazy import pattern for all components (avoids Settings() at module import)
- State saved after each step for granular recovery
- Sequential uploads (no parallel) to avoid quota tracking issues
- Configurable limits: max_trends_per_run, max_videos_per_run, max_uploads_per_run
- Template and voice configurable via PipelineConfig

### Notes
- External APIs (Reddit, Google Trends) require valid credentials
- Pipeline returns "partial" status when external APIs fail (graceful degradation)
- Video generation includes fallback to solid color background if asset search fails


## Wave 1 Task 19: End-to-End Integration Test (2026-03-15)

### Files Created
- `tests/conftest.py` - Shared pytest fixtures for mocking all external dependencies
- `tests/integration/__init__.py` - Integration test package
- `tests/integration/test_e2e.py` - Comprehensive E2E pipeline tests

### Test Coverage
- `TestE2EPipeline`: Full pipeline tests with mocked components
  - State persistence, trend fetch, video gen, upload, analytics
  - Full pipeline mock test, state recovery, error handling
  - Skip completed steps, quota protection
- `TestPipelineStatus`: Status tracking tests
- `TestPipelineConfig`: Configuration tests
- `TestPipelineResult`: Result dataclass tests
- `TestBenchmark`: Performance benchmark (completes under 60s)
- `TestErrorScenarios`: Error handling tests

### Mock Fixtures Provided
- `sample_trends`, `sample_script`, `sample_video_analytics`
- `mock_reddit`, `mock_google_trends` - Trend source mocks
- `mock_youtube_client`, `mock_quota_manager` - YouTube API mocks
- `mock_pexels_api`, `mock_pixabay_api` - Asset source mocks
- `mock_llm_client` - Script generation mock
- `mock_tts` - Text-to-speech mock
- `mock_video_builder` - Video assembly mock
- `mock_analytics_fetcher`, `mock_performance_agent` - Analytics mocks
- `mock_settings` - Settings without env vars
- `pipeline`, `pipeline_config` - Pipeline instances

### Key Design Decisions
- All external API calls are mocked via `unittest.mock.patch`
- Tests use temporary directories via pytest's `tmp_path` fixture
- Pipeline catches per-trend errors in video_gen, logs them, and continues
- Tests verify error logging rather than exception raising for resilience
- Fixtures defined in conftest.py for cross-test-class availability
- Benchmark test with `@pytest.mark.timeout(60)` ensures performance

### Test Execution
```bash
pytest tests/integration/test_e2e.py -v
```
Result: 21 passed in 16.50s

### Notes
- Video generation pipeline is resilient - catches individual trend errors and continues
- Fixtures can be imported by other test modules via `from tests.conftest import *`
- The `mock_settings` fixture prevents environment variable requirements during testing


## Wave 1 Task 20: CLI Interface (2026-03-15)

### Files Created
- `brainrot/cli.py` - Click-based CLI with all commands
- `brainrot/__main__.py` - Entry point for `python -m brainrot`

### Commands Implemented
- `brainrot run` - Full pipeline execution with --dry-run, --max-trends, --max-videos, --max-uploads
- `brainrot trends` - Fetch and display trends with --limit, --json-output
- `brainrot generate` - Single video generation with --trend-id, --template, --voice, --output
- `brainrot upload` - Process upload queue with --max, --human-review, --dry-run
- `brainrot status` - Show pipeline state with --json-output
- `brainrot dashboard` - Launch Streamlit dashboard with --port, --no-browser

### Global Options
- `--verbose` / `-v` - Enable verbose logging (DEBUG level)
- `--help` - Show command help

### Key Design Decisions
- Used Click's `@click.group()` for command hierarchy
- Colored output via `click.secho()` with fg="red/green/cyan/yellow"
- Docstrings used for --help text (Click convention with `\b` for formatting)
- Lazy import pattern for all components (prevents Settings() at module import)
- JSON output option for programmatic consumption

### Entry Points
- `brainrot` command (via pyproject.toml entry point)
- `python -m brainrot` (via __main__.py)
- `python -m brainrot.cli` (direct module execution)

### Notes
- Dry-run mode in `run` command skips upload step entirely
- Dry-run mode in `upload` command shows queue status without uploading
- Status command reads from cache/pipeline_state.json
- Dashboard command spawns streamlit subprocess


## Wave 1 Task 21: Documentation (2026-03-15)

### Files Created
- `README.md` - Comprehensive project documentation with overview, installation, CLI, architecture
- `docs/setup.md` - API credentials setup guide (YouTube, Reddit, Pexels, Pixabay, Ollama)
- `docs/content-templates.md` - Template creation guide with JSON structure explanation

### Documentation Structure
- README.md covers: features, prerequisites, installation, configuration, quick start, CLI commands, architecture, templates
- docs/setup.md covers: YouTube API setup (GCP project, OAuth), Reddit API setup, stock footage APIs, Ollama/Groq setup, first video walkthrough, troubleshooting
- docs/content-templates.md covers: built-in templates, JSON structure, configuration options, color/font guidelines, programmatic usage, best practices

### Key Documentation Decisions
- Python 3.10+ requirement documented in prerequisites
- FFmpeg installation instructions provided for all platforms
- All 4 built-in templates documented with style descriptions
- Troubleshooting section covers common setup issues
- CLI examples use actual command syntax from implementation

### Module Docstrings Status
All key public modules already have comprehensive docstrings:
- config.py, cli.py, types.py - Complete
- audio/tts.py, content/script_generator.py - Complete
- trends/aggregator.py, video/assembly.py - Complete
- analytics/fetcher.py, llm_client.py - Complete
- templates/renderer.py, pipeline/orchestrator.py - Complete

Added docstring to `check_ffmpeg_available()` in video/assembly.py

### Notes
- System has Python 3.9.6, but package requires 3.10+ (documented in README)
- Installation correctly enforces Python version requirement
