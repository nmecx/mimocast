"""mimocast — MiMo Studio Orchestrator."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("mimocast")
except PackageNotFoundError:  # pragma: no cover - editable install w/o build
    __version__ = "0.1.0"

__all__ = ["__version__"]
