# fetchers/__init__.py
from fetchers.auto_registry import build_registry

REGISTRY = build_registry()

__all__ = ["REGISTRY"]
