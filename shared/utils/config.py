"""Backward-compatible re-export.

config.py has been split into:
  - settings.py      — Settings dataclass (schema only)
  - config_loader.py — .env parsing and load_settings()

Import from here or directly from the new modules.
"""

from utils.config_loader import load_settings
from utils.settings import Settings

__all__ = ["Settings", "load_settings"]
