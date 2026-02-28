# fetchers/auto_registry.py
import importlib
import pkgutil
import inspect
from typing import Dict
from fetchers.base import BaseFetcher


def build_registry() -> Dict[str, BaseFetcher]:
    """扫描 fetchers/ 包，找所有 BaseFetcher 子类，按 platform_name 注册"""
    registry: Dict[str, BaseFetcher] = {}

    import fetchers as pkg
    for _, module_name, _ in pkgutil.iter_modules(pkg.__path__):
        if module_name in ("base", "auto_registry"):
            continue
        module = importlib.import_module(f"fetchers.{module_name}")
        for _, cls in inspect.getmembers(module, inspect.isclass):
            if (
                issubclass(cls, BaseFetcher)
                and cls is not BaseFetcher
                and hasattr(cls, "platform_name")
            ):
                registry[cls.platform_name] = cls()

    return registry
