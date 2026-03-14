"""Asset manager for stock footage and media.

Provides unified interface for searching, downloading, caching,
and tracking usage of stock assets from multiple sources.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import requests

from brainrot.assets.sources.pexels import PexelsSource
from brainrot.assets.sources.pixabay import PixabaySource

logger = logging.getLogger(__name__)


class AssetManager:
    """Unified asset management for stock footage and media.

    Handles searching multiple sources, downloading and caching assets,
    and tracking usage to avoid repetition.

    Attributes:
        cache_dir: Directory for cached assets and usage tracking.
    """

    SOURCE_CLASSES: dict[str, type[PexelsSource | PixabaySource]] = {
        "pexels": PexelsSource,
        "pixabay": PixabaySource,
    }

    def __init__(self, cache_dir: Path | None = None) -> None:
        """Initialize asset manager.

        Args:
            cache_dir: Directory for caching assets. Defaults to ./cache/assets.
        """
        self.cache_dir = cache_dir or Path("./cache/assets")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self._usage_file = self.cache_dir / "asset_usage.json"
        self._sources: dict[str, PexelsSource | PixabaySource] = {}

    def _get_source(self, source_name: str) -> PexelsSource | PixabaySource:
        """Get or create a source instance."""
        if source_name not in self._sources:
            source_class = self.SOURCE_CLASSES.get(source_name)
            if not source_class:
                raise ValueError(f"Unknown source: {source_name}")
            self._sources[source_name] = source_class()
        return self._sources[source_name]

    def search(
        self,
        query: str,
        source: str = "pexels",
        limit: int = 10,
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        """Search for assets matching the query.

        Args:
            query: Search query string (keywords).
            source: Source to search ('pexels', 'pixabay').
            limit: Maximum number of results to return.
            **kwargs: Additional source-specific parameters.

        Returns:
            List of asset dictionaries.
        """
        source_instance = self._get_source(source)
        return source_instance.search(query, limit=limit, **kwargs)

    def search_all_sources(
        self,
        query: str,
        limit_per_source: int = 5,
    ) -> list[dict[str, Any]]:
        """Search all available sources for assets.

        Args:
            query: Search query string.
            limit_per_source: Max results per source.

        Returns:
            Combined list of assets from all sources.
        """
        results = []
        for source_name in self.SOURCE_CLASSES:
            try:
                assets = self.search(query, source=source_name, limit=limit_per_source)
                results.extend(assets)
            except Exception as e:
                logger.warning(f"Search failed for {source_name}: {e}")
        return results

    def download(self, asset_url: str, filename: str | None = None) -> Path:
        """Download an asset to the cache.

        Args:
            asset_url: URL of the asset to download.
            filename: Optional filename. Generated from URL if not provided.

        Returns:
            Path to the downloaded file.
        """
        if filename is None:
            parsed = urlparse(asset_url)
            filename = Path(parsed.path).name or f"asset_{datetime.now().timestamp()}"

        dest = self.cache_dir / filename
        return self._download_file(asset_url, dest)

    def _download_file(self, url: str, dest: Path) -> Path:
        """Download a file from URL to destination."""
        dest.parent.mkdir(parents=True, exist_ok=True)

        response = requests.get(url, stream=True, timeout=60)
        response.raise_for_status()

        with open(dest, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        logger.info(f"Downloaded asset to {dest}")
        return dest

    def get_cached(self, asset_id: str) -> Path | None:
        """Check if an asset is cached locally.

        Args:
            asset_id: Unique asset identifier.

        Returns:
            Path to cached file if found, None otherwise.
        """
        extension = ".mp4"
        patterns = [
            self.cache_dir / f"{asset_id}.mp4",
            self.cache_dir / f"{asset_id}.mov",
            self.cache_dir / f"{asset_id}.webm",
            self.cache_dir / f"{asset_id}.jpg",
            self.cache_dir / f"{asset_id}.png",
        ]

        for path in patterns:
            if path.exists():
                return path
        return None

    def track_usage(self, asset_id: str, context: str | None = None) -> None:
        """Record that an asset was used.

        Args:
            asset_id: Unique asset identifier.
            context: Optional context where asset was used (e.g., video title).
        """
        usage = self._load_usage()

        if asset_id not in usage:
            usage[asset_id] = {
                "count": 0,
                "first_used": None,
                "last_used": None,
                "contexts": [],
            }

        usage[asset_id]["count"] += 1
        now = datetime.utcnow().isoformat()

        if usage[asset_id]["first_used"] is None:
            usage[asset_id]["first_used"] = now
        usage[asset_id]["last_used"] = now

        if context:
            usage[asset_id]["contexts"].append(context)

        self._save_usage(usage)
        logger.debug(f"Tracked usage for asset {asset_id}")

    def get_usage_stats(self, asset_id: str) -> dict[str, Any] | None:
        """Get usage statistics for an asset.

        Args:
            asset_id: Unique asset identifier.

        Returns:
            Usage statistics dictionary or None if never used.
        """
        usage = self._load_usage()
        return usage.get(asset_id)

    def get_unused_assets(self, assets: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Filter out already-used assets.

        Args:
            assets: List of asset dictionaries.

        Returns:
            List of assets that haven't been used yet.
        """
        usage = self._load_usage()
        return [a for a in assets if a.get("id") not in usage]

    def get_least_used_assets(
        self,
        assets: list[dict[str, Any]],
        max_usage: int = 1,
    ) -> list[dict[str, Any]]:
        """Get assets with usage count at or below threshold.

        Args:
            assets: List of asset dictionaries.
            max_usage: Maximum usage count to include.

        Returns:
            Filtered list of least-used assets.
        """
        usage = self._load_usage()
        result = []

        for asset in assets:
            asset_id = asset.get("id")
            stats = usage.get(asset_id, {})
            if stats.get("count", 0) <= max_usage:
                result.append(asset)

        return result

    def _load_usage(self) -> dict[str, Any]:
        """Load usage tracking data from file."""
        if not self._usage_file.exists():
            return {}

        try:
            with open(self._usage_file) as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"Failed to load usage file: {e}")
            return {}

    def _save_usage(self, usage: dict[str, Any]) -> None:
        """Save usage tracking data to file."""
        with open(self._usage_file, "w") as f:
            json.dump(usage, f, indent=2)

    def clear_cache(self) -> int:
        """Clear all cached assets (does not affect usage tracking).

        Returns:
            Number of files removed.
        """
        count = 0
        for path in self.cache_dir.iterdir():
            if path.is_file() and path != self._usage_file:
                path.unlink()
                count += 1
        logger.info(f"Cleared {count} cached assets")
        return count

    def clear_usage_history(self) -> None:
        """Clear all usage tracking data."""
        if self._usage_file.exists():
            self._usage_file.unlink()
        logger.info("Cleared usage history")


class LocalAssetLibrary:
    """Manager for local custom footage and assets.

    Provides organization and categorization for user-provided
    footage and media files.
    """

    def __init__(self, library_dir: Path | None = None) -> None:
        """Initialize local asset library.

        Args:
            library_dir: Directory containing local assets.
        """
        self.library_dir = library_dir or Path("./local_assets")
        self.library_dir.mkdir(parents=True, exist_ok=True)

        self._metadata_file = self.library_dir / "library_metadata.json"
        self._metadata: dict[str, Any] = self._load_metadata()

    def add_asset(
        self,
        file_path: Path,
        category: str,
        tags: list[str] | None = None,
        mood: str | None = None,
    ) -> dict[str, Any]:
        """Add a local asset to the library.

        Args:
            file_path: Path to the asset file.
            category: Category for the asset (e.g., 'backgrounds', 'transitions').
            tags: Optional list of tags for searching.
            mood: Optional mood classification.

        Returns:
            Asset metadata dictionary.
        """
        import shutil

        dest_dir = self.library_dir / category
        dest_dir.mkdir(parents=True, exist_ok=True)

        dest_path = dest_dir / file_path.name
        if file_path != dest_path:
            shutil.copy2(file_path, dest_path)

        asset_id = f"local_{category}_{file_path.stem}"
        asset_metadata = {
            "id": asset_id,
            "path": str(dest_path),
            "filename": file_path.name,
            "category": category,
            "tags": tags or [],
            "mood": mood,
            "added_at": datetime.utcnow().isoformat(),
            "source": "local",
        }

        self._metadata[asset_id] = asset_metadata
        self._save_metadata()

        return asset_metadata

    def search(
        self,
        query: str | None = None,
        category: str | None = None,
        tags: list[str] | None = None,
        mood: str | None = None,
    ) -> list[dict[str, Any]]:
        """Search local assets by various criteria.

        Args:
            query: Text search in filename and tags.
            category: Filter by category.
            tags: Filter by tags (any match).
            mood: Filter by mood.

        Returns:
            List of matching asset metadata.
        """
        results = []

        for asset_id, asset in self._metadata.items():
            if category and asset.get("category") != category:
                continue

            if mood and asset.get("mood") != mood:
                continue

            if tags:
                asset_tags = set(asset.get("tags", []))
                if not asset_tags.intersection(tags):
                    continue

            if query:
                query_lower = query.lower()
                filename_match = query_lower in asset.get("filename", "").lower()
                tags_match = any(
                    query_lower in t.lower() for t in asset.get("tags", [])
                )
                if not (filename_match or tags_match):
                    continue

            results.append(asset)

        return results

    def get_categories(self) -> list[str]:
        """Get list of all categories in use."""
        categories = set()
        for asset in self._metadata.values():
            if cat := asset.get("category"):
                categories.add(cat)

        for path in self.library_dir.iterdir():
            if path.is_dir() and path.name != "__pycache__":
                categories.add(path.name)

        return sorted(categories)

    def get_by_mood(self, mood: str) -> list[dict[str, Any]]:
        """Get all assets with a specific mood."""
        return [a for a in self._metadata.values() if a.get("mood") == mood]

    def _load_metadata(self) -> dict[str, Any]:
        """Load library metadata from file."""
        if not self._metadata_file.exists():
            return {}

        try:
            with open(self._metadata_file) as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"Failed to load library metadata: {e}")
            return {}

    def _save_metadata(self) -> None:
        """Save library metadata to file."""
        with open(self._metadata_file, "w") as f:
            json.dump(self._metadata, f, indent=2)


class BackgroundMusicLibrary:
    """Manager for royalty-free background music."""

    MUSIC_SOURCES = {
        "pixabay": "https://pixabay.com/music/search/",
        "freesound": "https://freesound.org/search/",
        "mixkit": "https://mixkit.co/free-stock-music/",
    }

    def __init__(self, music_dir: Path | None = None) -> None:
        """Initialize music library.

        Args:
            music_dir: Directory for cached music files.
        """
        self.music_dir = music_dir or Path("./cache/music")
        self.music_dir.mkdir(parents=True, exist_ok=True)

        self._library_file = self.music_dir / "music_library.json"
        self._library: dict[str, Any] = self._load_library()

    def add_track(
        self,
        file_path: Path,
        title: str,
        mood: str | None = None,
        tempo: str | None = None,
        duration: float | None = None,
        source: str = "local",
        license_info: str = "Unknown",
    ) -> dict[str, Any]:
        """Add a music track to the library.

        Args:
            file_path: Path to the music file.
            title: Track title.
            mood: Mood classification (e.g., 'upbeat', 'calm', 'dramatic').
            tempo: Tempo classification (e.g., 'fast', 'medium', 'slow').
            duration: Duration in seconds.
            source: Source identifier.
            license_info: License information.

        Returns:
            Track metadata dictionary.
        """
        import shutil

        dest_path = self.music_dir / file_path.name
        if file_path != dest_path:
            shutil.copy2(file_path, dest_path)

        track_id = f"music_{file_path.stem}"
        track = {
            "id": track_id,
            "path": str(dest_path),
            "filename": file_path.name,
            "title": title,
            "mood": mood,
            "tempo": tempo,
            "duration": duration,
            "source": source,
            "license": license_info,
            "added_at": datetime.utcnow().isoformat(),
        }

        self._library[track_id] = track
        self._save_library()

        return track

    def search(
        self,
        mood: str | None = None,
        tempo: str | None = None,
        max_duration: float | None = None,
    ) -> list[dict[str, Any]]:
        """Search music tracks by criteria.

        Args:
            mood: Filter by mood.
            tempo: Filter by tempo.
            max_duration: Maximum duration in seconds.

        Returns:
            List of matching tracks.
        """
        results = []

        for track in self._library.values():
            if mood and track.get("mood") != mood:
                continue

            if tempo and track.get("tempo") != tempo:
                continue

            if max_duration and track.get("duration", float("inf")) > max_duration:
                continue

            results.append(track)

        return results

    def get_random_track(self, mood: str | None = None) -> dict[str, Any] | None:
        """Get a random track, optionally filtered by mood.

        Args:
            mood: Optional mood filter.

        Returns:
            Random track metadata or None if no tracks available.
        """
        import random

        tracks = self.search(mood=mood)
        return random.choice(tracks) if tracks else None

    def get_available_moods(self) -> list[str]:
        """Get list of all moods in use."""
        moods = set()
        for track in self._library.values():
            if mood := track.get("mood"):
                moods.add(mood)
        return sorted(moods)

    def _load_library(self) -> dict[str, Any]:
        """Load music library from file."""
        if not self._library_file.exists():
            return {}

        try:
            with open(self._library_file) as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"Failed to load music library: {e}")
            return {}

    def _save_library(self) -> None:
        """Save music library to file."""
        with open(self._library_file, "w") as f:
            json.dump(self._library, f, indent=2)
