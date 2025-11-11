"""Configuration utilities for the Meshcore heatmap project."""

from dataclasses import dataclass, field
import os
from functools import lru_cache
from pathlib import Path
from typing import Optional


@dataclass
class Settings:
    """Lightweight settings object backed by environment variables."""

    project_root: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent)
    data_dir: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent / "data")
    database_url: str = field(default_factory=lambda: os.getenv("DATABASE_URL", "sqlite:///data/meshcore_heatmap_dev.db"))
    map_tile_url: Optional[str] = field(default_factory=lambda: os.getenv("MAP_TILE_URL"))
    heatmap_min_opacity: float = field(default_factory=lambda: float(os.getenv("HEATMAP_MIN_OPACITY", 0.3)))
    heatmap_radius: int = field(default_factory=lambda: int(os.getenv("HEATMAP_RADIUS", 18)))
    heatmap_blur: int = field(default_factory=lambda: int(os.getenv("HEATMAP_BLUR", 15)))
    heatmap_max_zoom: int = field(default_factory=lambda: int(os.getenv("HEATMAP_MAX_ZOOM", 18)))


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached settings instance."""
    config = Settings()
    config.data_dir.mkdir(parents=True, exist_ok=True)
    return config


settings = get_settings()


