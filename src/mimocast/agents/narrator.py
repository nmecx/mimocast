"""Narrator agent: Outline -> per-slide audio clips via MiMo TTS."""

from __future__ import annotations

from pathlib import Path

from mimocast.clients.mimo import MimoClient
from mimocast.models.schemas import AudioClip, Outline
from mimocast.utils.files import ensure_dir
from mimocast.utils.logger import get_logger

log = get_logger(__name__)


class Narrator:
    def __init__(self, client: MimoClient, *, voice: str | None = None):
        self.client = client
        self.voice = voice or client.settings.tts_voice

    def narrate(self, outline: Outline, *, out_dir: Path) -> list[AudioClip]:
        ensure_dir(out_dir)
        clips: list[AudioClip] = []
        for i, section in enumerate(outline.sections, start=1):
            transcript = section.speaker_notes
            result = self.client.synthesize(text=transcript, voice=self.voice)
            audio_path = out_dir / f"narration_{i:02d}.{result.container}"
            audio_path.write_bytes(result.audio_bytes)
            log.info(
                "narrator: %s (%.1fs, %s)",
                audio_path.name,
                result.duration_s,
                result.container,
            )
            clips.append(
                AudioClip(
                    slide_index=i,
                    audio_path=audio_path,
                    duration_s=result.duration_s,
                    transcript=transcript,
                    voice=self.voice,
                )
            )
        return clips
