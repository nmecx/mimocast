"""Orchestrator: glues agents together with crash-recoverable state."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
)

from mimocast.agents import Composer, Designer, Narrator, Reader, Summarizer
from mimocast.clients.mimo import MimoClient
from mimocast.config import Settings
from mimocast.models.schemas import Deck, Phase, RunState
from mimocast.utils.files import ensure_dir, hash_source, read_json, write_json
from mimocast.utils.logger import get_console, get_logger

log = get_logger(__name__)


@dataclass(slots=True)
class RunResult:
    state: RunState
    deck: Deck | None
    state_path: Path


class Orchestrator:
    def __init__(self, settings: Settings, *, max_sections: int = 6, dry_run: bool = False):
        self.settings = settings
        self.max_sections = max_sections
        self.dry_run = dry_run
        self.client = MimoClient(settings)
        self.reader = Reader()
        self.summarizer = Summarizer(self.client)
        self.designer = Designer(self.client)
        self.narrator = Narrator(self.client)
        self.composer = Composer()

    # ------------------------------------------------------------------
    # Public entry points
    # ------------------------------------------------------------------

    def run(self, source: str) -> RunResult:
        run_id = f"{hash_source(source)}-{uuid4().hex[:6]}"
        state = RunState(
            run_id=run_id,
            source=source,
            mode="dry-run" if self.dry_run else ("mock" if self.client.mock else "live"),
        )
        return self._drive(state)

    def recover(self, run_id: str) -> RunResult:
        state_path = self._state_path(run_id)
        if not state_path.exists():
            raise FileNotFoundError(f"no run state at {state_path}")
        raw = read_json(state_path)
        state = RunState.model_validate(raw)
        log.info("orchestrator: resuming %s from phase=%s", run_id, state.phase)
        return self._drive(state)

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _state_path(self, run_id: str) -> Path:
        return ensure_dir(self.settings.work_dir) / f"{run_id}.json"

    def _persist(self, state: RunState) -> Path:
        state.touch()
        path = self._state_path(state.run_id)
        write_json(path, state)
        return path

    def _run_out_dir(self, run_id: str) -> Path:
        return ensure_dir(self.settings.out_dir / run_id)

    def _drive(self, state: RunState) -> RunResult:
        run_out = self._run_out_dir(state.run_id)
        console = get_console()

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TimeElapsedColumn(),
            console=console,
            transient=False,
        ) as progress:
            task = progress.add_task("starting", total=5)

            try:
                # 1. READ
                if state.phase == Phase.READ:
                    progress.update(task, description="reading source")
                    state.document = self.reader.ingest(state.source)
                    state.phase = Phase.SUMMARIZE
                    self._persist(state)
                progress.advance(task)

                # 2. SUMMARIZE
                if state.phase == Phase.SUMMARIZE:
                    progress.update(task, description="summarizing with MiMo reasoner")
                    assert state.document is not None
                    state.outline = self.summarizer.summarize(
                        state.document, max_sections=self.max_sections
                    )
                    state.phase = Phase.DESIGN
                    self._persist(state)
                progress.advance(task)

                # 3. DESIGN
                if state.phase == Phase.DESIGN:
                    progress.update(task, description="designing slides (MiMo multimodal)")
                    assert state.outline is not None
                    slides = self.designer.render(state.outline, out_dir=run_out / "slides")
                    state.deck = Deck(title=state.outline.title, slides=slides, audio=[])
                    state.phase = Phase.NARRATE
                    self._persist(state)
                progress.advance(task)

                # 4. NARRATE
                if state.phase == Phase.NARRATE:
                    progress.update(task, description="narrating with MiMo TTS")
                    assert state.outline is not None and state.deck is not None
                    audio = self.narrator.narrate(state.outline, out_dir=run_out / "audio")
                    state.deck = state.deck.model_copy(update={"audio": audio})
                    state.phase = Phase.COMPOSE
                    self._persist(state)
                progress.advance(task)

                # 5. COMPOSE
                if state.phase == Phase.COMPOSE:
                    if self.dry_run:
                        log.info("orchestrator: dry-run, skipping video composition")
                    else:
                        progress.update(task, description="composing mp4")
                        assert state.deck is not None
                        state.deck = self.composer.compose(
                            title=state.deck.title,
                            slides=state.deck.slides,
                            audio=state.deck.audio,
                            out_dir=run_out / "video",
                        )
                    state.phase = Phase.DONE
                    self._persist(state)
                progress.advance(task)

            except Exception as exc:
                state.error = repr(exc)
                self._persist(state)
                log.exception("orchestrator: failed in phase=%s", state.phase)
                raise

        return RunResult(state=state, deck=state.deck, state_path=self._state_path(state.run_id))
