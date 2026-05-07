"""Run mimocast end-to-end against examples/sample_doc.md in mock mode.

Usage::

    python examples/demo.py

Set MIMOCAST_API_KEY in your environment to switch to live MiMo V2.5.
"""

from __future__ import annotations

from pathlib import Path

from mimocast.config import Settings
from mimocast.orchestrator import Orchestrator
from mimocast.utils.logger import configure_logging, get_console

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "sample_doc.md"


def main() -> None:
    configure_logging("INFO")

    settings = Settings(
        api_key=None,  # mock mode
        work_dir=ROOT / ".mimocast",
        out_dir=ROOT / "out",
        log_level="INFO",
    )

    orch = Orchestrator(settings, max_sections=4, dry_run=True)
    result = orch.run(str(SOURCE))

    console = get_console()
    console.rule("[bold red]mimocast demo complete")
    console.print(f"run_id      : {result.state.run_id}")
    console.print(f"outline     : {result.state.outline.title if result.state.outline else '?'}")
    console.print(f"slides      : {len(result.deck.slides) if result.deck else 0}")
    console.print(f"audio clips : {len(result.deck.audio) if result.deck else 0}")
    console.print(f"out dir     : {settings.out_dir / result.state.run_id}")


if __name__ == "__main__":
    main()
