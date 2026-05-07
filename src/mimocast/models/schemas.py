"""Domain schemas for the mimocast pipeline."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, NonNegativeFloat, PositiveInt


class Phase(StrEnum):
    READ = "read"
    SUMMARIZE = "summarize"
    DESIGN = "design"
    NARRATE = "narrate"
    COMPOSE = "compose"
    DONE = "done"


class Document(BaseModel):
    model_config = ConfigDict(frozen=True)

    title: str
    source: str = Field(description="Original URL or filesystem path.")
    text: str = Field(description="Cleaned plain text extracted from the source.")
    word_count: PositiveInt
    language: str = Field(default="en", description="ISO 639-1 code; auto-detected when possible.")


class OutlineSection(BaseModel):
    heading: str
    bullets: list[str] = Field(min_length=1, max_length=6)
    speaker_notes: str = Field(
        description="What the narrator should actually say for this slide. 30-90 seconds.",
        min_length=20,
    )


class Outline(BaseModel):
    title: str
    subtitle: str | None = None
    sections: list[OutlineSection] = Field(min_length=2, max_length=20)
    target_language: str = Field(default="en")
    estimated_duration_s: NonNegativeFloat = 0.0


class Slide(BaseModel):
    index: PositiveInt
    heading: str
    bullets: list[str]
    image_path: Path
    image_prompt: str
    visual_style: str = Field(default="minimal-editorial")


class AudioClip(BaseModel):
    slide_index: PositiveInt
    audio_path: Path
    duration_s: NonNegativeFloat
    transcript: str
    voice: str


class Deck(BaseModel):
    title: str
    slides: list[Slide]
    audio: list[AudioClip]
    video_path: Path | None = None
    total_duration_s: NonNegativeFloat = 0.0

    def is_complete(self) -> bool:
        return (
            len(self.slides) == len(self.audio)
            and self.video_path is not None
            and self.video_path.exists()
        )


class RunState(BaseModel):
    """Persisted to ~/.mimocast/<run_id>.json so we can resume after a crash."""

    model_config = ConfigDict(use_enum_values=True)

    run_id: str
    source: str
    phase: Phase = Phase.READ
    started_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    document: Document | None = None
    outline: Outline | None = None
    deck: Deck | None = None
    error: str | None = None
    mode: Literal["live", "mock", "dry-run"] = "live"

    def touch(self) -> None:
        self.updated_at = datetime.now(UTC)
