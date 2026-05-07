"""mimocast CLI."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from rich.panel import Panel
from rich.table import Table

from mimocast import __version__
from mimocast.config import get_settings
from mimocast.orchestrator import Orchestrator
from mimocast.utils.logger import configure_logging, get_console

app = typer.Typer(
    add_completion=False,
    help="MiMo Studio Orchestrator — turn a document into a narrated video deck.",
    no_args_is_help=True,
)


@app.callback()
def _root(
    log_level: Annotated[
        str, typer.Option("--log-level", "-L", help="DEBUG / INFO / WARNING / ERROR")
    ] = "INFO",
) -> None:
    configure_logging(log_level)


@app.command()
def version() -> None:
    """Print mimocast version."""
    typer.echo(f"mimocast {__version__}")


@app.command()
def run(
    source: Annotated[
        str, typer.Argument(help="Path or URL to a PDF / .md / .txt / web page.")
    ],
    out_dir: Annotated[
        Path | None, typer.Option("--out", help="Override output directory.")
    ] = None,
    max_sections: Annotated[
        int, typer.Option("--max-sections", "-n", help="Max slides in the deck (2-12).")
    ] = 6,
    mock: Annotated[
        bool, typer.Option("--mock", help="Force mock mode even if MIMOCAST_API_KEY is set.")
    ] = False,
    dry_run: Annotated[
        bool, typer.Option("--dry-run", help="Skip ffmpeg composition; produce slides + audio only.")
    ] = False,
    demo_tts: Annotated[
        bool,
        typer.Option(
            "--demo-tts",
            help=(
                "Mock-mode only: route TTS through gTTS for audible demo audio. "
                "NOT a substitute for real MiMo TTS — do not label output as MiMo."
            ),
        ),
    ] = False,
) -> None:
    """Generate a narrated MP4 from SOURCE."""
    overrides: dict = {}
    if out_dir is not None:
        overrides["out_dir"] = out_dir
    if mock:
        overrides["api_key"] = None
    if demo_tts:
        overrides["demo_tts"] = True
    settings = get_settings(**overrides)

    console = get_console()
    console.print(
        Panel.fit(
            f"[bold]mimocast[/bold] · run\n"
            f"source: {source}\n"
            f"mode:   {'mock' if settings.mock_mode else 'live'}"
            f"{'  (dry-run)' if dry_run else ''}\n"
            f"out:    {settings.out_dir}",
            border_style="red",
        )
    )

    orch = Orchestrator(settings, max_sections=max_sections, dry_run=dry_run)
    result = orch.run(source)
    _print_summary(result, settings_label="run")


@app.command()
def recover(
    run_id: Annotated[str, typer.Argument(help="The run_id printed at the start of a previous run.")],
    dry_run: Annotated[bool, typer.Option("--dry-run")] = False,
) -> None:
    """Resume a previously-crashed run from the last persisted phase."""
    settings = get_settings()
    orch = Orchestrator(settings, dry_run=dry_run)
    result = orch.recover(run_id)
    _print_summary(result, settings_label="recover")


@app.command(name="list")
def list_runs() -> None:
    """List persisted runs in the work dir."""
    settings = get_settings()
    work_dir = settings.work_dir
    work_dir.mkdir(parents=True, exist_ok=True)

    rows = sorted(work_dir.glob("*.json"))
    table = Table(title=f"Runs in {work_dir}")
    table.add_column("run_id", style="bold")
    table.add_column("phase")
    table.add_column("source")
    table.add_column("updated")

    for path in rows:
        try:
            import json

            payload = json.loads(path.read_text())
        except Exception:
            continue
        table.add_row(
            payload.get("run_id", path.stem),
            str(payload.get("phase", "?")),
            (payload.get("source") or "")[:60],
            (payload.get("updated_at") or "")[:19],
        )
    get_console().print(table)


def _print_summary(result, *, settings_label: str) -> None:
    console = get_console()
    state = result.state
    table = Table(title=f"mimocast {settings_label} summary", show_header=False)
    table.add_column("key", style="bold")
    table.add_column("value")
    table.add_row("run_id", state.run_id)
    table.add_row("phase", str(state.phase))
    table.add_row("mode", state.mode)
    table.add_row("source", state.source)
    if state.outline:
        table.add_row("title", state.outline.title)
        table.add_row("sections", str(len(state.outline.sections)))
    if result.deck:
        table.add_row("slides", str(len(result.deck.slides)))
        table.add_row("audio clips", str(len(result.deck.audio)))
        table.add_row("total duration", f"{result.deck.total_duration_s:.1f}s")
        if result.deck.video_path:
            table.add_row("video", str(result.deck.video_path))
    table.add_row("state", str(result.state_path))
    if state.error:
        table.add_row("[red]error[/red]", state.error)
    console.print(table)


if __name__ == "__main__":
    app()
