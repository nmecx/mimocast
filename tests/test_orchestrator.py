from __future__ import annotations

from pathlib import Path

from mimocast.config import Settings
from mimocast.models.schemas import Phase
from mimocast.orchestrator import Orchestrator


def test_orchestrator_dry_run_completes(settings: Settings, sample_markdown: Path) -> None:
    orch = Orchestrator(settings, max_sections=3, dry_run=True)
    result = orch.run(str(sample_markdown))

    assert result.state.phase == Phase.DONE
    assert result.state.error is None
    assert result.state.outline is not None
    assert result.deck is not None
    assert len(result.deck.slides) >= 2
    assert len(result.deck.audio) == len(result.deck.slides)
    # Dry-run skips ffmpeg, so video_path stays unset.
    assert result.deck.video_path is None
    # State JSON exists
    assert result.state_path.exists()


def test_orchestrator_recover_round_trip(settings: Settings, sample_markdown: Path) -> None:
    orch = Orchestrator(settings, max_sections=2, dry_run=True)
    first = orch.run(str(sample_markdown))
    run_id = first.state.run_id

    # New orchestrator instance, simulating a fresh process.
    second = Orchestrator(settings, max_sections=2, dry_run=True).recover(run_id)
    assert second.state.run_id == run_id
    assert second.state.phase == Phase.DONE


def test_orchestrator_state_is_progressive(settings: Settings, sample_markdown: Path) -> None:
    orch = Orchestrator(settings, max_sections=2, dry_run=True)
    result = orch.run(str(sample_markdown))
    raw = result.state_path.read_text()
    # Persisted JSON should at least mention the four interior phases reached.
    assert "outline" in raw and "deck" in raw and "slides" in raw
