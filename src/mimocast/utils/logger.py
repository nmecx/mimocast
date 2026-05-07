"""Rich-backed logging that the CLI and library share."""

from __future__ import annotations

import logging
from typing import Final

from rich.console import Console
from rich.logging import RichHandler

_CONSOLE: Final[Console] = Console(stderr=True)
_CONFIGURED = False


def configure_logging(level: str = "INFO") -> None:
    global _CONFIGURED
    if _CONFIGURED:
        logging.getLogger().setLevel(level.upper())
        return

    handler = RichHandler(
        console=_CONSOLE,
        show_time=True,
        show_path=False,
        rich_tracebacks=True,
        markup=True,
    )
    logging.basicConfig(
        level=level.upper(),
        format="%(message)s",
        datefmt="[%X]",
        handlers=[handler],
    )
    logging.getLogger("httpx").setLevel("WARNING")
    logging.getLogger("openai").setLevel("WARNING")
    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


def get_console() -> Console:
    return _CONSOLE
