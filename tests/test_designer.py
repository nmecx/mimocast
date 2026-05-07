from __future__ import annotations

from pathlib import Path

from PIL import Image

from mimocast.agents.designer import Designer
from mimocast.models.schemas import Outline, OutlineSection


def _outline() -> Outline:
    return Outline(
        title="A Mimocast Test Deck",
        sections=[
            OutlineSection(
                heading="Section One",
                bullets=["First bullet", "Second bullet"],
                speaker_notes="This is enough text to satisfy the schema.",
            ),
            OutlineSection(
                heading="Section Two",
                bullets=["Only one bullet here"],
                speaker_notes="Second slide narration body — at least twenty chars.",
            ),
        ],
    )


def test_designer_renders_each_section(mock_client, tmp_path: Path) -> None:
    slides = Designer(mock_client).render(_outline(), out_dir=tmp_path)
    assert len(slides) == 2
    for slide in slides:
        assert slide.image_path.exists()
        with Image.open(slide.image_path) as img:
            assert img.size == (1920, 1080)
        assert slide.image_prompt
