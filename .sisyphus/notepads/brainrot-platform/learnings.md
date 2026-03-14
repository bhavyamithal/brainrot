
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
