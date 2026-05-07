"""Composer agent: image+audio per slide -> single MP4 via ffmpeg."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from mimocast.models.schemas import AudioClip, Deck, Slide
from mimocast.utils.files import ensure_dir
from mimocast.utils.logger import get_logger

log = get_logger(__name__)


class ComposerError(RuntimeError):
    pass


class Composer:
    def __init__(self, *, ffmpeg_bin: str | None = None):
        self.ffmpeg_bin = ffmpeg_bin or shutil.which("ffmpeg") or "ffmpeg"

    def compose(
        self,
        *,
        title: str,
        slides: list[Slide],
        audio: list[AudioClip],
        out_dir: Path,
    ) -> Deck:
        ensure_dir(out_dir)
        if len(slides) != len(audio):
            raise ComposerError(
                f"slide/audio count mismatch: {len(slides)} vs {len(audio)}"
            )

        if not _ffmpeg_available(self.ffmpeg_bin):
            log.warning(
                "composer: ffmpeg not found at %s — skipping video assembly. "
                "Install ffmpeg to enable mp4 output.",
                self.ffmpeg_bin,
            )
            return Deck(
                title=title,
                slides=slides,
                audio=audio,
                video_path=None,
                total_duration_s=sum(c.duration_s for c in audio),
            )

        segments = []
        for slide, clip in zip(slides, audio, strict=True):
            seg_path = out_dir / f"segment_{slide.index:02d}.mp4"
            self._make_segment(
                image=slide.image_path,
                audio=clip.audio_path,
                duration_s=clip.duration_s,
                out=seg_path,
            )
            segments.append(seg_path)

        final = out_dir / "deck.mp4"
        self._concat(segments, final)

        return Deck(
            title=title,
            slides=slides,
            audio=audio,
            video_path=final,
            total_duration_s=sum(c.duration_s for c in audio),
        )

    def _make_segment(self, *, image: Path, audio: Path, duration_s: float, out: Path) -> None:
        cmd = [
            self.ffmpeg_bin,
            "-y",
            "-loglevel",
            "error",
            "-loop",
            "1",
            "-i",
            str(image),
            "-i",
            str(audio),
            "-c:v",
            "libx264",
            "-tune",
            "stillimage",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-shortest",
            "-t",
            f"{max(duration_s, 1.0):.2f}",
            "-vf",
            "scale=1920:1080,format=yuv420p",
            str(out),
        ]
        _run(cmd)

    def _concat(self, segments: list[Path], final: Path) -> None:
        manifest = final.parent / "concat.txt"
        manifest.write_text(
            "\n".join(f"file '{seg.as_posix()}'" for seg in segments),
            encoding="utf-8",
        )
        cmd = [
            self.ffmpeg_bin,
            "-y",
            "-loglevel",
            "error",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(manifest),
            "-c",
            "copy",
            str(final),
        ]
        _run(cmd)


def _ffmpeg_available(binary: str) -> bool:
    return shutil.which(binary) is not None


def _run(cmd: list[str]) -> None:
    log.debug("composer: %s", " ".join(cmd))
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise ComposerError(
            f"ffmpeg failed (rc={proc.returncode}): {proc.stderr.strip() or proc.stdout.strip()}"
        )
