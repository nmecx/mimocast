from __future__ import annotations

from pathlib import Path

from mimocast.agents.narrator import Narrator
from mimocast.models.schemas import Outline, OutlineSection


def _outline() -> Outline:
    return Outline(
        title="Narrator Test",
        sections=[
            OutlineSection(
                heading="Slide A",
                bullets=["x"],
                speaker_notes=("Lorem ipsum dolor sit amet, consectetur adipiscing elit. " * 2),
            ),
            OutlineSection(
                heading="Slide B",
                bullets=["y"],
                speaker_notes=("Sed do eiusmod tempor incididunt ut labore et dolore magna. " * 2),
            ),
        ],
    )


def test_narrator_writes_audio(mock_client, tmp_path: Path) -> None:
    clips = Narrator(mock_client).narrate(_outline(), out_dir=tmp_path)
    assert len(clips) == 2
    for clip in clips:
        assert clip.audio_path.exists()
        assert clip.audio_path.stat().st_size > 0
        assert clip.duration_s > 0
    assert clips[0].transcript.startswith("Lorem")
    assert clips[1].transcript.startswith("Sed do")
