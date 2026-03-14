# Brainrot Platform - Autonomous AI Content Farm

## TL;DR

> **Quick Summary**: Build a Python-based autonomous content generation platform that monitors trends, generates scripts via LLM, creates videos (TTS + stock footage + captions), and auto-posts to social media with analytics tracking. MVP targets YouTube-first with quota-aware design (max 5 videos/day).
>
> **Deliverables**:
> - Working content pipeline (trend → script → video → post)
> - 1-2 YouTube channels with automated posting
> - Analytics dashboard for performance tracking
> - Extensible architecture for multi-channel/multi-platform expansion
>
> **Estimated Effort**: Medium-Large (80-120 hours over 4 weeks)
> **Parallel Execution**: YES - 4 waves with 5-7 tasks each
> **Critical Path**: Project Setup → Trend Engine → Content Generator → Video Factory → Distribution → Analytics

---

## Context

### Original Request
User wants to build a free-to-use platform that generates "brainrot content" - AI-generated short videos with gaming footage backgrounds, AI voice narration, automated posting to social media platforms for passive ad revenue income.

### Interview Summary

**Evolution of the Idea**:
1. Initial: Brainrot content (gaming footage + AI voice)
2. Pivot: After YouTube policy analysis, shifted to "transformative" content models
3. Final: Fully autonomous AI-powered content farm with AI agents at every step

**Key Decisions**:
- **Content models**: Multiple (data storytelling, tech news, explainers) - experiment to find what works
- **Automation level**: Minimal human intervention (AI agents for ideation, content, video, distribution, analytics)
- **Budget**: $0-50/month (open-source tools, free APIs)
- **Timeline**: MVP in 1 month
- **Scale**: As many channels as possible for experimentation
- **Tech approach**: Hybrid (local + free APIs)
- **Validation**: Real channel testing

**Research Findings**:
- YouTube July 2025 policy bans "inauthentic content" - transformation required
- Open-source TTS: Kokoro, Fish Audio (good quality, Apache 2.0 license)
- YouTube Data API quota: 10,000 units/day = ~6 video uploads (hard constraint)
- FFmpeg concat demuxer requires special handling for slide durations
- Revenue: $0.02-0.05 RPM for entertainment content

### Metis Review

**Identified Gaps** (addressed):
- **YouTube API quota limitation**: 6 videos/day max → Plan includes quota-aware design with queueing
- **FFmpeg concat timing bug**: Last slide duration ignored → Plan includes proven pattern with duration fix
- **Audio normalization**: Variable TTS loudness → Plan includes loudnorm filter pipeline
- **Scope breadth**: Multiple niches at once → Plan starts with YouTube-first, single channel, expands later

**Guardrails Applied**:
- MUST implement daily upload counter (max 5 videos to stay under quota)
- MUST NOT create multiple GCP projects for quota sharding (ToS violation)
- MUST use human review checkpoint before publish (initially)
- MUST handle quota exceeded errors gracefully

---

## Work Objectives

### Core Objective
Build a Python-based autonomous content generation platform that can produce and publish short-form videos to YouTube with minimal human intervention, while remaining compliant with platform policies and staying within budget constraints.

### Concrete Deliverables
- `brainrot/` Python package with modular architecture
- Trend monitoring engine (Reddit, Google Trends, News APIs)
- LLM-powered script generator with multiple templates
- Video assembly pipeline (TTS + stock footage + captions)
- YouTube Data API integration with quota management
- Analytics dashboard for performance tracking
- 1-2 live YouTube channels with automated content

### Definition of Done
- [ ] Pipeline generates video from trend to upload end-to-end
- [ ] YouTube video appears on channel after automated upload
- [ ] Analytics dashboard shows view counts per video
- [ ] System respects daily upload quota (max 5 videos)
- [ ] All code passes type checking and tests

### Must Have
- YouTube Data API integration with quota tracking
- Open-source TTS (Kokoro or Fish Audio)
- Template-based video assembly with FFmpeg
- Trend detection from at least 2 sources
- LLM-based script generation (local Ollama or free API)
- Basic analytics tracking

### Must NOT Have (Guardrails)
- NO multiple GCP projects for quota sharding (ToS violation)
- NO paid APIs for MVP (stay within $0-50/month budget)
- NO fully autonomous posting without human review initially
- NO AI-generated video backgrounds (too expensive computationally)
- NO multi-platform in MVP (YouTube-first, expand later)
- NO generic "brainrot" content that violates YouTube's authenticity policy

---

## Verification Strategy (MANDATORY)

### Test Decision
- **Infrastructure exists**: NO (will create)
- **Automated tests**: YES (pytest for all modules)
- **Framework**: pytest + pytest-asyncio
- **TDD**: Tests written alongside implementation

### QA Policy
Every task includes agent-executed QA scenarios with evidence capture.

- **CLI/Scripts**: Use Bash (python script execution, verify output)
- **APIs**: Use Bash (curl requests, assert status + response)
- **Video Generation**: Use Bash (ffprobe to verify video properties)

---

## Execution Strategy

### Parallel Execution Waves

```
Wave 1 (Start Immediately — Foundation):
├── Task 1: Project scaffolding + dependencies [quick]
├── Task 2: Configuration system + secrets management [quick]
├── Task 3: Type definitions + interfaces [quick]
├── Task 4: Logging + error handling framework [quick]
├── Task 5: YouTube API client + quota tracker [quick]
└── Task 6: LLM client setup (Ollama) [quick]

Wave 2 (After Wave 1 — Core Engines):
├── Task 7: Trend detection engine [deep]
├── Task 8: Script generator with templates [unspecified-high]
├── Task 9: TTS integration (Kokoro/Fish Audio) [unspecified-high]
├── Task 10: Stock footage/asset manager [quick]
├── Task 11: Video assembly pipeline (FFmpeg) [deep]
└── Task 12: Content templates library [unspecified-high]

Wave 3 (After Wave 2 — Distribution + Intelligence):
├── Task 13: Upload orchestrator with quota management [unspecified-high]
├── Task 14: Scheduling system [quick]
├── Task 15: Analytics fetcher [quick]
├── Task 16: Analytics dashboard [visual-engineering]
├── Task 17: Performance tracking agent [unspecified-high]
└── Task 18: Main orchestration pipeline [deep]

Wave 4 (After Wave 3 — Polish + Launch):
├── Task 19: End-to-end integration test [deep]
├── Task 20: CLI interface [quick]
├── Task 21: Documentation [writing]
├── Task 22: First channel setup + validation [unspecified-high]
└── Task 23: Production deployment [quick]

Wave FINAL (After ALL tasks — verification):
├── Task F1: Plan compliance audit (oracle)
├── Task F2: Code quality review (unspecified-high)
├── Task F3: Real channel QA (unspecified-high)
└── Task F4: Scope fidelity check (deep)

Critical Path: Task 1 → Task 5 → Task 7 → Task 8 → Task 11 → Task 13 → Task 18 → Task 22
Parallel Speedup: ~65% faster than sequential
Max Concurrent: 6 (Wave 1)
```

### Dependency Matrix

- **1-6**: — — 7-18, all
- **5**: — 13, 18
- **7**: — 8, 18
- **8**: — 9, 11, 12
- **9**: — 11
- **10**: — 11
- **11**: — 13
- **12**: — 11, 13
- **13**: — 14, 18
- **14**: — 18
- **15**: — 16, 17
- **16**: — 17
- **17**: — 18
- **18**: — 19, 20, 22
- **19**: — 22
- **20**: — 22
- **22**: — F3

### Agent Dispatch Summary

- **Wave 1**: **6** — T1-T4 → `quick`, T5 → `quick`, T6 → `quick`
- **Wave 2**: **6** — T7 → `deep`, T8 → `unspecified-high`, T9 → `unspecified-high`, T10 → `quick`, T11 → `deep`, T12 → `unspecified-high`
- **Wave 3**: **6** — T13 → `unspecified-high`, T14 → `quick`, T15 → `quick`, T16 → `visual-engineering`, T17 → `unspecified-high`, T18 → `deep`
- **Wave 4**: **5** — T19 → `deep`, T20 → `quick`, T21 → `writing`, T22 → `unspecified-high`, T23 → `quick`
- **FINAL**: **4** — F1 → `oracle`, F2 → `unspecified-high`, F3 → `unspecified-high`, F4 → `deep`

---

## TODOs

- [x] 1. Project Scaffolding + Dependencies

  **What to do**:
  - Create `brainrot/` Python package structure with proper `__init__.py` files
  - Set up `pyproject.toml` with dependencies: `ffmpeg-python`, `requests`, `pydantic`, `python-dotenv`, `ollama`, `pytube`, `praw` (Reddit API), `google-api-python-client`, `google-auth-oauthlib`
  - Create development dependencies: `pytest`, `pytest-asyncio`, `mypy`, `ruff`
  - Set up `.python-version` for pyenv compatibility
  - Create `.env.example` with all required environment variables documented

  **Must NOT do**:
  - Do NOT include paid API dependencies
  - Do NOT create multiple GCP project configurations

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Standard Python project setup, well-defined structure
  - **Skills**: []
    - No special skills needed for scaffolding

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 2, 3, 4, 5, 6)
  - **Blocks**: All subsequent tasks (foundation)
  - **Blocked By**: None (can start immediately)

  **References**:
  - Standard Python package structure: `src/brainrot/` layout
  - Pyproject.toml format: PEP 621 compliant

  **Acceptance Criteria**:
  - [ ] `brainrot/__init__.py` exists and imports without error
  - [ ] `pyproject.toml` includes all required dependencies
  - [ ] `python -c "import brainrot"` succeeds
  - [ ] `pytest --collect-only` discovers test structure

  **QA Scenarios**:
  ```
  Scenario: Package imports correctly
    Tool: Bash
    Steps:
      1. cd /Users/bhavya.mithal/workspace/brainrot
      2. python -c "import brainrot; print(brainrot.__version__)"
    Expected Result: Version string printed without error
    Evidence: .sisyphus/evidence/task-01-import-check.txt

  Scenario: Dependencies install correctly
    Tool: Bash
    Steps:
      1. pip install -e . --dry-run
    Expected Result: All dependencies resolved, no conflicts
    Evidence: .sisyphus/evidence/task-01-deps-check.txt
  ```

  **Commit**: YES
  - Message: `chore: initial project scaffolding`
  - Files: `pyproject.toml`, `brainrot/__init__.py`, `.env.example`

---

- [x] 2. Configuration System + Secrets Management

  **What to do**:
  - Create `brainrot/config.py` with Pydantic settings model
  - Define settings for: API keys (YouTube, Reddit, optionally OpenAI), paths, quotas, schedules
  - Implement `.env` file loading with `python-dotenv`
  - Add validation for required vs optional settings
  - Create `Settings` class with environment-based overrides
  - Add YouTube API credentials path configuration

  **Must NOT do**:
  - Do NOT hardcode any API keys or secrets
  - Do NOT commit `.env` files

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Standard configuration pattern with Pydantic
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 1, 3, 4, 5, 6)
  - **Blocks**: Tasks that need config (5, 6, 7, 8)
  - **Blocked By**: Task 1 (project structure)

  **References**:
  - Pydantic Settings: `https://docs.pydantic.dev/latest/concepts/pydantic_settings/`

  **Acceptance Criteria**:
  - [ ] `brainrot/config.py` exports `Settings` class
  - [ ] Settings load from `.env` file
  - [ ] Missing required settings raise clear errors
  - [ ] Optional settings have sensible defaults

  **QA Scenarios**:
  ```
  Scenario: Config loads from environment
    Tool: Bash
    Preconditions: .env file exists with YOUTUBE_API_KEY=test_key
    Steps:
      1. python -c "from brainrot.config import settings; print(settings.youtube_api_key)"
    Expected Result: "test_key" printed
    Evidence: .sisyphus/evidence/task-02-config-load.txt

  Scenario: Missing required key raises error
    Tool: Bash
    Preconditions: No YOUTUBE_API_KEY in environment
    Steps:
      1. python -c "from brainrot.config import settings" 2>&1
    Expected Result: ValidationError with message about missing YOUTUBE_API_KEY
    Evidence: .sisyphus/evidence/task-02-config-error.txt
  ```

  **Commit**: YES
  - Message: `feat: add configuration system with Pydantic settings`
  - Files: `brainrot/config.py`

---

- [x] 3. Type Definitions + Interfaces

  **What to do**:
  - Create `brainrot/types.py` with all core data models
  - Define: `Trend`, `Script`, `Video`, `Channel`, `Analytics`, `UploadResult`
  - Use Pydantic models for validation
  - Create Protocol classes for: `TrendSource`, `ScriptGenerator`, `VideoAssembler`, `Publisher`
  - Add type aliases for commonly used types
  - Define `ContentTemplate` model for different video styles

  **Must NOT do**:
  - Do NOT add implementation logic, only types

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Type definitions are straightforward
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 1, 2, 4, 5, 6)
  - **Blocks**: All core engine tasks
  - **Blocked By**: Task 1

  **References**:
  - Pydantic models: `https://docs.pydantic.dev/latest/`

  **Acceptance Criteria**:
  - [ ] All core types defined in `brainrot/types.py`
  - [ ] `mypy brainrot/types.py` passes with no errors
  - [ ] Types are importable and usable

  **QA Scenarios**:
  ```
  Scenario: Types validate correctly
    Tool: Bash
    Steps:
      1. python -c "from brainrot.types import Trend, Script; t = Trend(title='test', source='reddit', score=100); print(t.title)"
    Expected Result: "test" printed
    Evidence: .sisyphus/evidence/task-03-types-validate.txt
  ```

  **Commit**: YES
  - Message: `feat: add core type definitions and interfaces`
  - Files: `brainrot/types.py`

---

- [x] 4. Logging + Error Handling Framework

  **What to do**:
  - Create `brainrot/logging_config.py` with structured logging setup
  - Use Python `logging` module with JSON formatter option
  - Create custom exceptions: `QuotaExceededError`, `UploadFailedError`, `VideoGenerationError`, `TrendFetchError`
  - Add correlation ID support for tracing requests through pipeline
  - Create `brainrot/exceptions.py` with exception hierarchy
  - Add retry decorator with exponential backoff

  **Must NOT do**:
  - Do NOT use print statements for logging

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Standard logging setup
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 1, 2, 3, 5, 6)
  - **Blocks**: All tasks that need logging/error handling
  - **Blocked By**: Task 1

  **References**:
  - Python logging: `https://docs.python.org/3/library/logging.html`

  **Acceptance Criteria**:
  - [ ] `brainrot/logging_config.py` exports `setup_logging()`
  - [ ] Custom exceptions defined in `brainrot/exceptions.py`
  - [ ] Retry decorator works with configurable attempts

  **QA Scenarios**:
  ```
  Scenario: Logging outputs structured format
    Tool: Bash
    Steps:
      1. python -c "from brainrot.logging_config import setup_logging; import logging; setup_logging(); logging.info('test')"
    Expected Result: JSON-formatted log line with timestamp and level
    Evidence: .sisyphus/evidence/task-04-logging.txt
  ```

  **Commit**: YES
  - Message: `feat: add logging and error handling framework`
  - Files: `brainrot/logging_config.py`, `brainrot/exceptions.py`

---

- [x] 5. YouTube API Client + Quota Tracker

  **What to do**:
  - Create `brainrot/youtube_client.py` with YouTube Data API v3 wrapper
  - Implement OAuth 2.0 flow for channel authentication (save credentials securely)
  - Create quota tracking system: 10,000 units/day, video upload = 1,600 units
  - Implement `upload_video()` method with title, description, tags, category
  - Add `get_video_analytics()` method for view counts, likes, comments
  - Implement daily quota counter with persistence (JSON file)
  - Add quota reset scheduling (midnight UTC)
  - Create `QuotaManager` class that queues uploads when quota exceeded

  **Must NOT do**:
  - Do NOT create multiple GCP projects to bypass quota (ToS violation)
  - Do NOT exceed 5 video uploads per day in automated mode (safety buffer)

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Well-documented API, clear requirements
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 1, 2, 3, 4, 6)
  - **Blocks**: Task 13 (Upload orchestrator)
  - **Blocked By**: Task 1, Task 2

  **References**:
  - YouTube Data API: `https://developers.google.com/youtube/v3`
  - Quota calculator: `https://developers.google.com/youtube/v3/determine_quota_cost`
  - OAuth flow: `https://developers.google.com/youtube/v3/guides/auth/server-side-web-apps`

  **Acceptance Criteria**:
  - [ ] `YouTubeClient` class authenticates with OAuth
  - [ ] `QuotaManager` tracks daily usage
  - [ ] Upload fails gracefully when quota exceeded
  - [ ] Quota counter persists across restarts

  **QA Scenarios**:
  ```
  Scenario: Quota manager tracks uploads
    Tool: Bash
    Steps:
      1. python -c "from brainrot.youtube_client import QuotaManager; q = QuotaManager(); q.record_upload(); print(q.remaining_quota())"
    Expected Result: 8400 (10000 - 1600)
    Evidence: .sisyphus/evidence/task-05-quota-track.txt

  Scenario: Quota exceeded queues video
    Tool: Bash
    Steps:
      1. python -c "from brainrot.youtube_client import QuotaManager; q = QuotaManager(); q.used_quota = 9000; result = q.can_upload(); print(result)"
    Expected Result: False
    Evidence: .sisyphus/evidence/task-05-quota-exceeded.txt
  ```

  **Commit**: YES
  - Message: `feat: add YouTube API client with quota tracking`
  - Files: `brainrot/youtube_client.py`, `brainrot/quota.json` (gitignored template)

---

- [x] 6. LLM Client Setup (Ollama)

  **What to do**:
  - Create `brainrot/llm_client.py` with Ollama API wrapper
  - Support local Ollama instance (default: http://localhost:11434)
  - Implement `generate()` method with model selection (default: llama3.2)
  - Add fallback to free API tier (Groq free tier) if Ollama unavailable
  - Create prompt templates for script generation
  - Add response parsing and validation
  - Implement retry logic for API failures

  **Must NOT do**:
  - Do NOT require paid API keys for MVP
  - Do NOT use models that require authentication if Ollama is preferred

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Standard API wrapper with fallback
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 1, 2, 3, 4, 5)
  - **Blocks**: Task 8 (Script generator)
  - **Blocked By**: Task 1, Task 2

  **References**:
  - Ollama API: `https://github.com/ollama/ollama/blob/main/docs/api.md`
  - Groq free tier: `https://console.groq.com/`

  **Acceptance Criteria**:
  - [ ] `LLMClient` connects to Ollama or falls back to Groq
  - [ ] `generate()` returns parsed response
  - [ ] Retry logic handles transient failures

  **QA Scenarios**:
  ```
  Scenario: LLM client generates text
    Tool: Bash
    Preconditions: Ollama running locally OR GROQ_API_KEY set
    Steps:
      1. python -c "from brainrot.llm_client import LLMClient; c = LLMClient(); r = c.generate('Say hello'); print(len(r) > 0)"
    Expected Result: True
    Evidence: .sisyphus/evidence/task-06-llm-generate.txt

  Scenario: Fallback to Groq works
    Tool: Bash
    Preconditions: Ollama NOT running, GROQ_API_KEY set
    Steps:
      1. python -c "from brainrot.llm_client import LLMClient; c = LLMClient(); print(c.provider)"
    Expected Result: "groq"
    Evidence: .sisyphus/evidence/task-06-llm-fallback.txt
  ```

  **Commit**: YES
  - Message: `feat: add LLM client with Ollama and Groq fallback`
  - Files: `brainrot/llm_client.py`

---

- [x] 7. Trend Detection Engine

  **What to do**:
  - Create `brainrot/trends/` package with multiple source implementations
  - Implement `RedditTrendSource`: Use PRAW to fetch trending posts from configured subreddits
  - Implement `GoogleTrendsSource`: Use `pytrends` library for trending searches
  - Implement `NewsAPISource`: Use free NewsAPI tier for headlines (optional, requires key)
  - Create `TrendAggregator` that combines and deduplicates sources
  - Add scoring/ranking based on: recency, upvotes, relevance score
  - Implement filtering: exclude already-processed topics, NSFW content
  - Create `TrendCache` to avoid reprocessing same topics

  **Must NOT do**:
  - Do NOT rely solely on one source (need diversity)
  - Do NOT fetch more than API rate limits allow

  **Recommended Agent Profile**:
  - **Category**: `deep`
    - Reason: Multiple API integrations with complex aggregation logic
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO (depends on Wave 1)
  - **Parallel Group**: Wave 2 (depends on Tasks 1-6)
  - **Blocks**: Task 8 (Script generator)
  - **Blocked By**: Task 1, Task 2, Task 3

  **References**:
  - PRAW: `https://praw.readthedocs.io/`
  - Pytrends: `https://github.com/GeneralMills/pytrends`

  **Acceptance Criteria**:
  - [ ] At least 2 trend sources implemented
  - [ ] `TrendAggregator` returns deduplicated, ranked trends
  - [ ] TrendCache prevents reprocessing

  **QA Scenarios**:
  ```
  Scenario: Reddit source fetches trends
    Tool: Bash
    Preconditions: Reddit API credentials configured
    Steps:
      1. python -c "from brainrot.trends.reddit import RedditTrendSource; s = RedditTrendSource(); trends = s.fetch(limit=5); print(len(trends))"
    Expected Result: 5
    Evidence: .sisyphus/evidence/task-07-reddit-trends.txt

  Scenario: Aggregator combines sources
    Tool: Bash
    Steps:
      1. python -c "from brainrot.trends import TrendAggregator; a = TrendAggregator(); trends = a.get_trends(limit=10); print(len(trends) > 0)"
    Expected Result: True
    Evidence: .sisyphus/evidence/task-07-aggregator.txt
  ```

  **Commit**: YES
  - Message: `feat: add trend detection engine with Reddit and Google Trends`
  - Files: `brainrot/trends/__init__.py`, `brainrot/trends/reddit.py`, `brainrot/trends/google_trends.py`, `brainrot/trends/aggregator.py`

---

- [ ] 8. Script Generator with Templates

  **What to do**:
  - Create `brainrot/content/script_generator.py`
  - Define template system for different content types:
    - `news_synthesis`: Tech news summary with analysis
    - `data_story`: Data-driven narrative
    - `explainer`: Concept explanation with examples
    - `listicle`: Top N list format
  - Use LLM client to generate scripts from trends + template
  - Add script validation: length (150-300 words for Shorts), clarity, engagement hooks
  - Implement `ScriptTemplate` class with placeholder system
  - Add hook generation (first 3 seconds critical)
  - Create script history to avoid duplicate content

  **Must NOT do**:
  - Do NOT generate scripts longer than 300 words (30-second video limit)
  - Do NOT use generic AI voice without transformation

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: Complex prompt engineering and template design
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO (depends on LLM and trends)
  - **Parallel Group**: Wave 2
  - **Blocks**: Task 9, Task 11, Task 12
  - **Blocked By**: Task 3, Task 6, Task 7

  **References**:
  - Prompt engineering for content: Use system prompts with examples

  **Acceptance Criteria**:
  - [ ] At least 2 script templates implemented
  - [ ] Generated scripts are 150-300 words
  - [ ] Scripts include hook in first sentence

  **QA Scenarios**:
  ```
  Scenario: Generate news synthesis script
    Tool: Bash
    Steps:
      1. python -c "from brainrot.content.script_generator import ScriptGenerator; g = ScriptGenerator(); script = g.generate({'title': 'AI breakthrough', 'source': 'reddit'}, template='news_synthesis'); print(len(script.text.split()))"
    Expected Result: Between 150 and 300
    Evidence: .sisyphus/evidence/task-08-script-gen.txt

  Scenario: Script has engaging hook
    Tool: Bash
    Steps:
      1. python -c "from brainrot.content.script_generator import ScriptGenerator; g = ScriptGenerator(); script = g.generate({'title': 'Test topic'}, template='news_synthesis'); print(script.hook)"
    Expected Result: Non-empty hook string
    Evidence: .sisyphus/evidence/task-08-script-hook.txt
  ```

  **Commit**: YES
  - Message: `feat: add script generator with templates`
  - Files: `brainrot/content/script_generator.py`, `brainrot/content/templates/`

---

- [ ] 9. TTS Integration (Kokoro/Fish Audio)

  **What to do**:
  - Create `brainrot/audio/tts.py` with TTS abstraction
  - Implement Kokoro TTS integration (Apache 2.0, runs locally)
  - Add Fish Audio API as alternative (higher quality, free tier available)
  - Implement `synthesize()` method that takes script and returns audio file path
  - Add audio normalization using FFmpeg loudnorm filter (target: -14 LUFS)
  - Support multiple voice profiles per channel
  - Add SSML support for emphasis and pauses
  - Cache generated audio to avoid re-synthesizing same text

  **Must NOT do**:
  - Do NOT use paid TTS services for MVP

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: Audio processing and multiple TTS integrations
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 2
  - **Blocks**: Task 11 (Video assembly)
  - **Blocked By**: Task 8

  **References**:
  - Kokoro: `https://github.com/hexgrad/kokoro`
  - Fish Audio: `https://fish.audio/`
  - Loudnorm: `https://ffmpeg.org/ffmpeg-filters.html#loudnorm`

  **Acceptance Criteria**:
  - [ ] TTS generates audio from text
  - [ ] Audio normalized to -14 LUFS (±1)
  - [ ] Multiple voice profiles available

  **QA Scenarios**:
  ```
  Scenario: TTS generates audio file
    Tool: Bash
    Steps:
      1. python -c "from brainrot.audio.tts import TTSClient; t = TTSClient(); path = t.synthesize('Hello world'); print(path)"
    Expected Result: Path to .mp3 or .wav file
    Evidence: .sisyphus/evidence/task-09-tts-gen.txt

  Scenario: Audio is normalized
    Tool: Bash
    Steps:
      1. Generate audio file
      2. ffprobe -i output.mp3 -af loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json -f null - 2>&1 | grep input_i
    Expected Result: Value close to -14
    Evidence: .sisyphus/evidence/task-09-audio-norm.txt
  ```

  **Commit**: YES
  - Message: `feat: add TTS integration with Kokoro and Fish Audio`
  - Files: `brainrot/audio/__init__.py`, `brainrot/audio/tts.py`

---

- [x] 10. Stock Footage/Asset Manager

  **What to do**:
  - Create `brainrot/assets/` package for media management
  - Implement `PexelsSource`: Free stock footage API (no auth needed for basic)
  - Implement `PixabaySource`: Another free stock source
  - Create `AssetManager` that:
    - Searches for footage matching keywords
    - Downloads and caches locally
    - Tracks asset usage to avoid repetition
  - Add background music library (royalty-free sources)
  - Implement local asset library for custom footage
  - Add asset categorization by mood/topic

  **Must NOT do**:
  - Do NOT use copyrighted footage
  - Do NOT use assets without checking license compatibility

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: API integration with caching logic
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 2
  - **Blocks**: Task 11 (Video assembly)
  - **Blocked By**: Task 1, Task 2

  **References**:
  - Pexels API: `https://www.pexels.com/api/`
  - Pixabay API: `https://pixabay.com/api/docs/`

  **Acceptance Criteria**:
  - [ ] At least 1 stock footage source working
  - [ ] Assets cached locally
  - [ ] Asset usage tracked

  **QA Scenarios**:
  ```
  Scenario: Fetch stock footage
    Tool: Bash
    Steps:
      1. python -c "from brainrot.assets import AssetManager; a = AssetManager(); assets = a.search('technology', limit=5); print(len(assets))"
    Expected Result: 5
    Evidence: .sisyphus/evidence/task-10-assets.txt
  ```

  **Commit**: YES
  - Message: `feat: add stock footage asset manager`
  - Files: `brainrot/assets/__init__.py`, `brainrot/assets/manager.py`, `brainrot/assets/sources/`

---

- [ ] 11. Video Assembly Pipeline (FFmpeg)

  **What to do**:
  - Create `brainrot/video/assembly.py` with FFmpeg-based video builder
  - Implement template-based video assembly:
    - Background footage (stock or solid color)
    - Text overlays with kinetic typography
    - Captions (ASS format for styling)
    - Audio track (TTS + optional music)
  - Create `ConcatDemuxer` wrapper that handles duration correctly (CRITICAL: repeat last slide entry)
  - Implement `VideoBuilder` class with methods:
    - `add_background(footage_path, duration)`
    - `add_captions(script_text, style)`
    - `add_audio(tts_path, music_path=None)`
    - `render(output_path)`
  - Add video filters: scale to 1080x1920, crop to vertical format
  - Ensure yuv420p pixel format for compatibility
  - Implement progress tracking for long renders

  **Must NOT do**:
  - Do NOT ignore FFmpeg concat demuxer duration bug (last slide)
  - Do NOT output non-standard video formats

  **Recommended Agent Profile**:
  - **Category**: `deep`
    - Reason: Complex FFmpeg pipeline with edge cases
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 2
  - **Blocks**: Task 13 (Upload orchestrator)
  - **Blocked By**: Task 8, Task 9, Task 10

  **References**:
  - FFmpeg concat demuxer: `https://ffmpeg.org/ffmpeg-formats.html#concat-1`
  - ASS subtitles: `https://aegi.vmoe.info/docs/3.0/ASS_Tags/`

  **Acceptance Criteria**:
  - [ ] Video output is valid MP4
  - [ ] Duration matches audio duration (±0.5s)
  - [ ] Captions are readable and styled
  - [ ] Output is 1080x1920 (vertical)

  **QA Scenarios**:
  ```
  Scenario: Assemble video from components
    Tool: Bash
    Steps:
      1. python -c "from brainrot.video.assembly import VideoBuilder; b = VideoBuilder(); b.add_background('assets/bg.mp4', 30); b.add_audio('assets/audio.mp3'); path = b.render('output.mp4'); print(path)"
    Expected Result: output.mp4 exists and is valid
    Evidence: .sisyphus/evidence/task-11-video-build.txt

  Scenario: Video duration matches audio
    Tool: Bash
    Steps:
      1. Get audio duration: ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 audio.mp3
      2. Get video duration: ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 output.mp4
      3. Compare (should be within 0.5s)
    Expected Result: Durations match
    Evidence: .sisyphus/evidence/task-11-duration.txt
  ```

  **Commit**: YES
  - Message: `feat: add FFmpeg video assembly pipeline`
  - Files: `brainrot/video/__init__.py`, `brainrot/video/assembly.py`, `brainrot/video/captions.py`

---

- [ ] 12. Content Templates Library

  **What to do**:
  - Create `brainrot/templates/` with predefined video templates
  - Implement templates for each content model:
    - `tech_news`: Dark background, techy font, news ticker style
    - `data_story`: Chart animations, data visualization focus
    - `explainer`: Clean minimal, educational feel
    - `listicle`: Numbered countdown style
  - Define template config format (JSON/YAML)
  - Each template specifies: colors, fonts, animation style, caption position, transition effects
  - Create `TemplateRenderer` that applies template to video builder
  - Add thumbnail generation per template

  **Must NOT do**:
  - Do NOT make templates too similar (need distinct channel branding)

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: Design work and template system complexity
  - **Skills**: [`frontend-ui-ux`]
    - `frontend-ui-ux`: Visual design decisions for templates

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 2
  - **Blocks**: Task 11, Task 13
  - **Blocked By**: Task 3, Task 11

  **References**:
  - Video template design: Study viral Shorts for visual patterns

  **Acceptance Criteria**:
  - [ ] At least 2 templates implemented
  - [ ] Templates produce visually distinct videos
  - [ ] Template config is editable without code changes

  **QA Scenarios**:
  ```
  Scenario: Render video with template
    Tool: Bash
    Steps:
      1. python -c "from brainrot.templates import TemplateRenderer; r = TemplateRenderer('tech_news'); video = r.render(script_text='Test'); print(video)"
    Expected Result: Video rendered with tech_news styling
    Evidence: .sisyphus/evidence/task-12-template.txt
  ```

  **Commit**: YES
  - Message: `feat: add content templates library`
  - Files: `brainrot/templates/__init__.py`, `brainrot/templates/tech_news.json`, `brainrot/templates/data_story.json`

---

- [ ] 13. Upload Orchestrator with Quota Management

  **What to do**:
  - Create `brainrot/pipeline/uploader.py`
  - Implement `UploadOrchestrator` that:
    - Takes generated videos and queues them for upload
    - Checks quota before each upload
    - Respects daily limit (max 5 uploads for safety buffer)
    - Queues excess videos for next day
    - Tracks upload status (pending, uploaded, failed)
  - Add retry logic for failed uploads
  - Implement upload metadata generation (title, description, tags from script)
  - Add human review checkpoint (optional, can be disabled later)
  - Create upload queue persistence (survive restarts)

  **Must NOT do**:
  - Do NOT exceed 5 uploads per day in automated mode
  - Do NOT lose videos if queue is interrupted

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: Critical pipeline component with quota handling
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 3
  - **Blocks**: Task 18 (Main pipeline)
  - **Blocked By**: Task 5, Task 11

  **References**:
  - YouTube upload: `https://developers.google.com/youtube/v3/guides/uploading_a_video`

  **Acceptance Criteria**:
  - [ ] Videos queued when quota exceeded
  - [ ] Queue persists across restarts
  - [ ] Upload metadata generated correctly

  **QA Scenarios**:
  ```
  Scenario: Quota exceeded queues video
    Tool: Bash
    Steps:
      1. python -c "from brainrot.pipeline.uploader import UploadOrchestrator; o = UploadOrchestrator(); o.uploads_today = 5; result = o.queue_video('test.mp4'); print(result.status)"
    Expected Result: "queued_for_tomorrow"
    Evidence: .sisyphus/evidence/task-13-quota-queue.txt

  Scenario: Upload queue persists
    Tool: Bash
    Steps:
      1. Add video to queue
      2. Restart orchestrator (create new instance)
      3. Check queue
    Expected Result: Queue contains video from before restart
    Evidence: .sisyphus/evidence/task-13-queue-persist.txt
  ```

  **Commit**: YES
  - Message: `feat: add upload orchestrator with quota management`
  - Files: `brainrot/pipeline/__init__.py`, `brainrot/pipeline/uploader.py`

---

- [ ] 14. Scheduling System

  **What to do**:
  - Create `brainrot/scheduler/` package
  - Implement cron-based scheduling for:
    - Trend fetching (every 4 hours)
    - Video generation (based on queue)
    - Upload posting (optimal times per platform)
  - Add timezone-aware scheduling
  - Implement optimal posting time detection (based on analytics or defaults)
  - Create `Scheduler` class that orchestrates all timed tasks
  - Add manual trigger capability for testing
  - Implement graceful shutdown (finish current task, then stop)

  **Must NOT do**:
  - Do NOT hardcode posting times (make configurable)

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Standard scheduling implementation
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 3
  - **Blocks**: Task 18
  - **Blocked By**: Task 4

  **References**:
  - APScheduler: `https://apscheduler.readthedocs.io/`

  **Acceptance Criteria**:
  - [ ] Scheduling works with timezone awareness
  - [ ] Manual trigger works
  - [ ] Graceful shutdown implemented

  **QA Scenarios**:
  ```
  Scenario: Scheduler runs at configured time
    Tool: Bash
    Steps:
      1. python -c "from brainrot.scheduler import Scheduler; s = Scheduler(); s.add_job('test', lambda: print('ran'), trigger='interval', seconds=5); import time; time.sleep(6)"
    Expected Result: "ran" printed
    Evidence: .sisyphus/evidence/task-14-schedule.txt
  ```

  **Commit**: YES
  - Message: `feat: add scheduling system`
  - Files: `brainrot/scheduler/__init__.py`, `brainrot/scheduler/scheduler.py`

---

- [ ] 15. Analytics Fetcher

  **What to do**:
  - Create `brainrot/analytics/fetcher.py`
  - Implement YouTube Analytics API integration
  - Fetch metrics per video: views, likes, comments, average view duration
  - Fetch channel-level metrics: subscriber count, total views
  - Store analytics data in local database (SQLite)
  - Add trend detection in analytics (which videos are growing)
  - Implement analytics export (CSV/JSON)
  - Add comparison across time periods

  **Must NOT do**:
  - Do NOT fetch more frequently than API allows

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: API integration with data storage
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 3
  - **Blocks**: Task 16, Task 17
  - **Blocked By**: Task 5

  **References**:
  - YouTube Analytics API: `https://developers.google.com/youtube/reporting/v1/reports`

  **Acceptance Criteria**:
  - [ ] Analytics fetched and stored
  - [ ] Per-video metrics available
  - [ ] Data exportable

  **QA Scenarios**:
  ```
  Scenario: Fetch video analytics
    Tool: Bash
    Steps:
      1. python -c "from brainrot.analytics.fetcher import AnalyticsFetcher; f = AnalyticsFetcher(); data = f.fetch_video('video_id'); print(data.views)"
    Expected Result: Numeric view count
    Evidence: .sisyphus/evidence/task-15-analytics.txt
  ```

  **Commit**: YES
  - Message: `feat: add analytics fetcher`
  - Files: `brainrot/analytics/__init__.py`, `brainrot/analytics/fetcher.py`

---

- [ ] 16. Analytics Dashboard

  **What to do**:
  - Create `brainrot/dashboard/` with web-based dashboard
  - Use lightweight framework: Streamlit or FastAPI + simple HTML
  - Display: channel overview, recent videos, performance trends
  - Add charts: views over time, top videos, engagement rates
  - Implement filtering by date range, content type
  - Add comparison view: which content models perform best
  - Make dashboard read-only for MVP (no controls, just display)

  **Must NOT do**:
  - Do NOT add complex authentication (basic or none for MVP)
  - Do NOT add control features (just display)

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
    - Reason: UI/dashboard development
  - **Skills**: [`frontend-ui-ux`]
    - `frontend-ui-ux`: Dashboard layout and visualization

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 3
  - **Blocks**: Task 17
  - **Blocked By**: Task 15

  **References**:
  - Streamlit: `https://docs.streamlit.io/`

  **Acceptance Criteria**:
  - [ ] Dashboard displays channel metrics
  - [ ] Charts show performance trends
  - [ ] Dashboard accessible via browser

  **QA Scenarios**:
  ```
  Scenario: Dashboard loads and displays data
    Tool: Bash
    Steps:
      1. streamlit run brainrot/dashboard/app.py &
      2. curl http://localhost:8501
    Expected Result: HTML response with dashboard content
    Evidence: .sisyphus/evidence/task-16-dashboard.txt
  ```

  **Commit**: YES
  - Message: `feat: add analytics dashboard`
  - Files: `brainrot/dashboard/__init__.py`, `brainrot/dashboard/app.py`

---

- [ ] 17. Performance Tracking Agent

  **What to do**:
  - Create `brainrot/agents/performance_agent.py`
  - Implement agent that:
    - Analyzes video performance daily
    - Identifies top-performing content patterns
    - Detects underperforming content types
    - Generates recommendations (which topics/styles to focus on)
  - Add scoring system for content success (views, engagement, growth rate)
  - Implement alerting for viral videos (sudden view spike)
  - Create feedback loop to influence content generation priorities
  - Add weekly summary generation

  **Must NOT do**:
  - Do NOT auto-adjust without human review (MVP limitation)

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: Analytics logic and recommendation system
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 3
  - **Blocks**: Task 18
  - **Blocked By**: Task 15, Task 16

  **References**:
  - Simple scoring algorithms: weighted averages

  **Acceptance Criteria**:
  - [ ] Agent analyzes performance daily
  - [ ] Top performers identified
  - [ ] Recommendations generated

  **QA Scenarios**:
  ```
  Scenario: Performance agent generates report
    Tool: Bash
    Steps:
      1. python -c "from brainrot.agents.performance_agent import PerformanceAgent; a = PerformanceAgent(); report = a.generate_report(); print(len(report.recommendations) > 0)"
    Expected Result: True
    Evidence: .sisyphus/evidence/task-17-perf-agent.txt
  ```

  **Commit**: YES
  - Message: `feat: add performance tracking agent`
  - Files: `brainrot/agents/__init__.py`, `brainrot/agents/performance_agent.py`

---

- [ ] 18. Main Orchestration Pipeline

  **What to do**:
  - Create `brainrot/pipeline/orchestrator.py`
  - Implement `Pipeline` class that coordinates all components:
    - `run_daily()`: Full pipeline execution
    - `run_trend_fetch()`: Just fetch trends
    - `run_video_gen()`: Generate videos from queued trends
    - `run_upload()`: Upload queued videos
    - `run_analytics()`: Fetch and analyze performance
  - Add state management (what's been processed, what's pending)
  - Implement error handling and recovery (resume from failure point)
  - Add logging for full pipeline observability
  - Create configuration for pipeline behavior (frequency, limits)

  **Must NOT do**:
  - Do NOT allow parallel uploads (quota tracking issues)

  **Recommended Agent Profile**:
  - **Category**: `deep`
    - Reason: Complex orchestration with state management
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 3
  - **Blocks**: Task 19, Task 20, Task 22
  - **Blocked By**: Task 7, Task 8, Task 13, Task 14, Task 17

  **References**:
  - Pipeline patterns: ETL-style orchestration

  **Acceptance Criteria**:
  - [ ] Pipeline runs end-to-end
  - [ ] State persists across runs
  - [ ] Errors don't lose progress

  **QA Scenarios**:
  ```
  Scenario: Pipeline runs daily workflow
    Tool: Bash
    Steps:
      1. python -c "from brainrot.pipeline.orchestrator import Pipeline; p = Pipeline(); result = p.run_daily(); print(result.status)"
    Expected Result: "completed"
    Evidence: .sisyphus/evidence/task-18-pipeline.txt
  ```

  **Commit**: YES
  - Message: `feat: add main orchestration pipeline`
  - Files: `brainrot/pipeline/orchestrator.py`

---

- [ ] 19. End-to-End Integration Test

  **What to do**:
  - Create `tests/integration/test_e2e.py`
  - Test full pipeline from trend to upload:
    - Mock external APIs (Reddit, YouTube)
    - Use sample data for video generation
    - Verify output video is valid
  - Add test fixtures for all external dependencies
  - Create test mode that doesn't actually upload
  - Measure and assert on pipeline completion time

  **Must NOT do**:
  - Do NOT call real APIs in tests (use mocks)

  **Recommended Agent Profile**:
  - **Category**: `deep`
    - Reason: Complex integration testing
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 4
  - **Blocks**: Task 22
  - **Blocked By**: Task 18

  **References**:
  - pytest: `https://docs.pytest.org/`

  **Acceptance Criteria**:
  - [ ] E2E test passes
  - [ ] All external APIs mocked
  - [ ] Test completes in under 60 seconds

  **QA Scenarios**:
  ```
  Scenario: E2E test passes
    Tool: Bash
    Steps:
      1. pytest tests/integration/test_e2e.py -v
    Expected Result: All tests pass
    Evidence: .sisyphus/evidence/task-19-e2e.txt
  ```

  **Commit**: YES
  - Message: `test: add end-to-end integration tests`
  - Files: `tests/integration/test_e2e.py`

---

- [ ] 20. CLI Interface

  **What to do**:
  - Create `brainrot/cli.py` with Click-based CLI
  - Implement commands:
    - `brainrot run`: Start the pipeline
    - `brainrot trends`: Fetch and show current trends
    - `brainrot generate`: Generate a single video
    - `brainrot upload`: Upload queued videos
    - `brainrot status`: Show current pipeline state
    - `brainrot dashboard`: Launch analytics dashboard
  - Add verbose mode with detailed logging
  - Implement dry-run mode (no actual uploads)
  - Add configuration file support

  **Must NOT do**:
  - Do NOT require CLI for automation (scheduler runs independently)

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Standard CLI development
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 4
  - **Blocks**: Task 22
  - **Blocked By**: Task 18

  **References**:
  - Click: `https://click.palletsprojects.com/`

  **Acceptance Criteria**:
  - [ ] CLI commands work as expected
  - [ ] Help text is clear
  - [ ] Dry-run mode prevents uploads

  **QA Scenarios**:
  ```
  Scenario: CLI status command works
    Tool: Bash
    Steps:
      1. python -m brainrot.cli status
    Expected Result: Status information printed
    Evidence: .sisyphus/evidence/task-20-cli.txt
  ```

  **Commit**: YES
  - Message: `feat: add CLI interface`
  - Files: `brainrot/cli.py`, `brainrot/__main__.py`

---

- [ ] 21. Documentation

  **What to do**:
  - Create `README.md` with:
    - Project overview and goals
    - Installation instructions
    - Configuration guide
    - CLI usage examples
    - Architecture overview
  - Create `docs/setup.md` with detailed setup:
    - YouTube API credentials
    - Reddit API credentials
    - Ollama installation
    - First video generation
  - Add docstrings to all public functions
  - Create `docs/content-templates.md` explaining how to create new templates

  **Must NOT do**:
  - Do NOT document internal implementation details (focus on user-facing)

  **Recommended Agent Profile**:
  - **Category**: `writing`
    - Reason: Documentation writing
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 4
  - **Blocks**: None
  - **Blocked By**: Task 18

  **References**:
  - Good README format: Standard open-source conventions

  **Acceptance Criteria**:
  - [ ] README covers all setup steps
  - [ ] Docstrings present on public functions
  - [ ] Configuration guide is complete

  **QA Scenarios**:
  ```
  Scenario: README setup instructions work
    Tool: Bash
    Steps:
      1. Follow README setup steps from scratch
      2. Run `brainrot status`
    Expected Result: Command runs successfully
    Evidence: .sisyphus/evidence/task-21-docs.txt
  ```

  **Commit**: YES
  - Message: `docs: add comprehensive documentation`
  - Files: `README.md`, `docs/setup.md`, `docs/content-templates.md`

---

- [ ] 22. First Channel Setup + Validation

  **What to do**:
  - Create a new YouTube channel (or use existing)
  - Configure channel credentials in the system
  - Run the pipeline manually for first video:
    - Select a topic
    - Generate script
    - Create video
    - Upload to YouTube
  - Verify video appears on channel
  - Monitor initial performance for 48 hours
  - Adjust content strategy based on results

  **Must NOT do**:
  - Do NOT enable full automation yet (validate manually first)

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: Real-world validation and iteration
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 4
  - **Blocks**: F3 (Real channel QA)
  - **Blocked By**: Task 18, Task 19, Task 20

  **References**:
  - None (hands-on validation)

  **Acceptance Criteria**:
  - [ ] YouTube channel configured
  - [ ] First video uploaded successfully
  - [ ] Video has views within 48 hours

  **QA Scenarios**:
  ```
  Scenario: Video appears on YouTube
    Tool: Bash
    Steps:
      1. Run pipeline to generate and upload video
      2. Check YouTube channel for new video
    Expected Result: Video visible on channel
    Evidence: .sisyphus/evidence/task-22-first-video.png (screenshot)
  ```

  **Commit**: YES
  - Message: `feat: validate with first channel`
  - Files: `config/channel.yaml`

---

- [ ] 23. Production Deployment

  **What to do**:
  - Create `docker-compose.yml` for deployment
  - Configure for VPS or local server:
    - Scheduler container
    - Dashboard container
    - Volume mounts for data persistence
  - Add health checks for all services
  - Create deployment script (`scripts/deploy.sh`)
  - Add monitoring (basic: log files, container status)
  - Document deployment process

  **Must NOT do**:
  - Do NOT deploy to expensive cloud services (stay in budget)

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Containerization and deployment
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 4
  - **Blocks**: None
  - **Blocked By**: Task 18

  **References**:
  - Docker Compose: `https://docs.docker.com/compose/`

  **Acceptance Criteria**:
  - [ ] Docker Compose file works
  - [ ] Services restart on failure
  - [ ] Logs accessible

  **QA Scenarios**:
  ```
  Scenario: Docker deployment works
    Tool: Bash
    Steps:
      1. docker-compose up -d
      2. docker-compose ps
    Expected Result: All services running
    Evidence: .sisyphus/evidence/task-23-deploy.txt
  ```

  **Commit**: YES
  - Message: `feat: add production deployment configuration`
  - Files: `docker-compose.yml`, `Dockerfile`, `scripts/deploy.sh`

---

## Final Verification Wave (MANDATORY)

- [ ] F1. **Plan Compliance Audit** — `oracle`
  Read the plan end-to-end. For each "Must Have": verify implementation exists. For each "Must NOT Have": search codebase for forbidden patterns. Check evidence files exist in .sisyphus/evidence/. Compare deliverables against plan.
  Output: `Must Have [N/N] | Must NOT Have [N/N] | Tasks [N/N] | VERDICT: APPROVE/REJECT`

- [ ] F2. **Code Quality Review** — `unspecified-high`
  Run `mypy brainrot` + `ruff check brainrot` + `pytest`. Review all files for: `as any`/`# type: ignore`, empty except blocks, print statements, commented-out code, unused imports. Check AI slop: excessive comments, generic names.
  Output: `Type Check [PASS/FAIL] | Lint [PASS/FAIL] | Tests [N pass/N fail] | Files [N clean/N issues] | VERDICT`

- [ ] F3. **Real Channel QA** — `unspecified-high`
  Start from clean state. Generate a video end-to-end. Verify it uploads to YouTube. Check video quality (resolution, audio, captions). Wait 24 hours and verify analytics are tracked.
  Output: `Video [VALID/INVALID] | Upload [SUCCESS/FAIL] | Analytics [TRACKED/NOT TRACKED] | VERDICT`

- [ ] F4. **Scope Fidelity Check** — `deep`
  For each task: read "What to do", read actual implementation. Verify 1:1 — everything in spec was built, nothing beyond spec was built. Check "Must NOT do" compliance. Flag unaccounted changes.
  Output: `Tasks [N/N compliant] | Contamination [CLEAN/N issues] | Unaccounted [CLEAN/N files] | VERDICT`

---

## Commit Strategy

All commits follow conventional commit format:
- `feat:` for new features
- `fix:` for bug fixes
- `docs:` for documentation
- `test:` for tests
- `chore:` for maintenance

Each commit should be atomic and buildable.

---

## Success Criteria

### Verification Commands
```bash
# Run all tests
pytest

# Type check
mypy brainrot

# Lint
ruff check brainrot

# Generate a video
python -m brainrot.cli generate --topic "AI news" --template tech_news

# Check pipeline status
python -m brainrot.cli status
```

### Final Checklist
- [ ] All "Must Have" features present
- [ ] All "Must NOT Have" constraints respected
- [ ] All tests pass
- [ ] At least 1 video uploaded to YouTube successfully
- [ ] Dashboard accessible and showing data
- [ ] Pipeline runs daily without intervention

