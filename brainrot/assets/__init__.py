"""Asset management for stock footage, local assets, and music.

This package provides unified access to stock footage sources,
local asset libraries, and background music management.
"""

from brainrot.assets.manager import AssetManager, BackgroundMusicLibrary, LocalAssetLibrary
from brainrot.assets.sources.pexels import PexelsSource
from brainrot.assets.sources.pixabay import PixabaySource

__all__ = [
    "AssetManager",
    "BackgroundMusicLibrary",
    "LocalAssetLibrary",
    "PexelsSource",
    "PixabaySource",
]
