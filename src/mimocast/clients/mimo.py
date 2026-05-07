"""Thin wrapper around the OpenAI-compatible MiMo API.

The same client serves three MiMo V2.5 capabilities:

* ``reason``  — text reasoner / structured-output generation.
* ``describe_image`` — multimodal vision (image-in, text-out).
* ``synthesize`` — text-to-speech.

When ``settings.mock_mode`` is true (no API key configured), every method
returns deterministic canned output so the full pipeline is exercisable
offline. This is what powers ``mimocast --mock`` and the test suite.
"""

from __future__ import annotations

import base64
import json
import wave
from dataclasses import dataclass
from pathlib import Path

import httpx
from openai import OpenAI
from openai._exceptions import APIConnectionError, APIError, RateLimitError
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from mimocast.config import Settings
from mimocast.utils.logger import get_logger

log = get_logger(__name__)


class MimoClientError(RuntimeError):
    """Raised when the MiMo API returns an unrecoverable error."""


@dataclass(frozen=True, slots=True)
class TtsResult:
    audio_bytes: bytes
    sample_rate: int
    duration_s: float
    container: str  # "wav" or "mp3"


class MimoClient:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._openai: OpenAI | None = None

    @property
    def mock(self) -> bool:
        return self.settings.mock_mode

    def _client(self) -> OpenAI:
        if self._openai is None:
            self._openai = OpenAI(
                api_key=self.settings.api_key or "mock",
                base_url=self.settings.base_url,
                timeout=self.settings.request_timeout_s,
                max_retries=0,
            )
        return self._openai

    @retry(
        retry=retry_if_exception_type((APIConnectionError, RateLimitError, httpx.TimeoutException)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        reraise=True,
    )
    def reason(
        self,
        *,
        system: str,
        user: str,
        json_schema: dict | None = None,
        temperature: float = 0.2,
    ) -> str:
        """Send a chat-completion to the reasoner. Returns raw assistant text."""
        if self.mock:
            return _mock_reason(user, json_schema)

        kwargs: dict = {
            "model": self.settings.reasoner_model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": temperature,
        }
        if json_schema:
            kwargs["response_format"] = {
                "type": "json_schema",
                "json_schema": {"name": "out", "schema": json_schema, "strict": True},
            }
        try:
            resp = self._client().chat.completions.create(**kwargs)
        except APIError as exc:
            raise MimoClientError(f"reason() failed: {exc}") from exc
        content = resp.choices[0].message.content or ""
        return content

    def reason_json(
        self,
        *,
        system: str,
        user: str,
        json_schema: dict,
        temperature: float = 0.2,
    ) -> dict:
        """Convenience wrapper that returns parsed JSON. Falls back to a single
        retry that asks the model to fix malformed output."""
        raw = self.reason(system=system, user=user, json_schema=json_schema, temperature=temperature)
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            log.warning("reason_json: malformed JSON, asking model to repair it")
            repaired = self.reason(
                system="Return ONLY valid JSON that matches the schema. No prose.",
                user=raw,
                json_schema=json_schema,
                temperature=0.0,
            )
            return json.loads(repaired)

    @retry(
        retry=retry_if_exception_type((APIConnectionError, RateLimitError, httpx.TimeoutException)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        reraise=True,
    )
    def describe_image(self, *, image_path: Path, prompt: str) -> str:
        """Multimodal: feed an image + prompt to the vision model, get a caption."""
        if self.mock:
            return _mock_caption(image_path, prompt)

        b64 = base64.b64encode(image_path.read_bytes()).decode("ascii")
        try:
            resp = self._client().chat.completions.create(
                model=self.settings.vision_model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/png;base64,{b64}"},
                            },
                        ],
                    }
                ],
                temperature=0.2,
            )
        except APIError as exc:
            raise MimoClientError(f"describe_image() failed: {exc}") from exc
        return resp.choices[0].message.content or ""

    @retry(
        retry=retry_if_exception_type((APIConnectionError, RateLimitError, httpx.TimeoutException)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        reraise=True,
    )
    def synthesize(self, *, text: str, voice: str | None = None) -> TtsResult:
        """Generate speech audio. Returns raw bytes ready to be written to disk."""
        if self.mock:
            return _mock_tts(text, demo=self.settings.demo_tts)

        voice_id = voice or self.settings.tts_voice
        try:
            resp = self._client().audio.speech.create(
                model=self.settings.tts_model,
                voice=voice_id,
                input=text,
                response_format="mp3",
            )
            audio_bytes = resp.read()
        except APIError as exc:
            raise MimoClientError(f"synthesize() failed: {exc}") from exc
        # Estimate duration: 150 wpm -> ~0.4s/word as a conservative default.
        words = max(1, len(text.split()))
        return TtsResult(
            audio_bytes=audio_bytes,
            sample_rate=24_000,
            duration_s=words * 0.4,
            container="mp3",
        )


# ----------------------------------------------------------------------------
# Mock implementations used when MIMOCAST_API_KEY is absent.
# ----------------------------------------------------------------------------

def _mock_reason(user: str, json_schema: dict | None) -> str:
    if json_schema is None:
        return f"[mock-mimo-reasoner] {user[:120]}…"
    # Deterministic canned outline derived from the user text.
    head = user.strip().splitlines()[0][:80] or "Untitled Document"
    payload = {
        "title": head,
        "subtitle": "A mimocast mock-mode walkthrough",
        "target_language": "en",
        "estimated_duration_s": 90.0,
        "sections": [
            {
                "heading": "What this is",
                "bullets": [
                    "Every section below is generated offline by the mock reasoner.",
                    "Wire MIMOCAST_API_KEY to swap in real MiMo V2.5 output.",
                    "The pipeline is otherwise identical end-to-end.",
                ],
                "speaker_notes": (
                    "Welcome. This deck was assembled by mimocast in mock mode. "
                    "Each slide pairs a concise outline with a short narration so "
                    "you can preview the full pipeline without spending tokens."
                ),
            },
            {
                "heading": "How the pipeline runs",
                "bullets": [
                    "Reader extracts plain text from your source.",
                    "Summarizer turns it into a structured outline.",
                    "Designer renders editorial slides; Narrator voices them.",
                    "Composer stitches everything into an MP4.",
                ],
                "speaker_notes": (
                    "Four agents cooperate in sequence. Each one writes to disk "
                    "so a crash mid-run can be recovered with the recover command."
                ),
            },
            {
                "heading": "Why MiMo V2.5",
                "bullets": [
                    "Reasoner handles long, multilingual context natively.",
                    "Multimodal vision turns figures into accurate captions.",
                    "TTS produces studio-grade narration in many voices.",
                ],
                "speaker_notes": (
                    "Three model classes from one provider keeps latency low and "
                    "the orchestration simple. Token Plan pricing makes long-form "
                    "decks economical to produce at scale."
                ),
            },
        ],
    }
    return json.dumps(payload, ensure_ascii=False)


def _mock_caption(image_path: Path, prompt: str) -> str:
    return (
        f"[mock-mimo-vision] {image_path.name}: editorial-style key art with "
        f"clean typography, neutral palette, and ample whitespace — matching "
        f"the prompt '{prompt[:60]}…'"
    )


def _mock_tts(text: str, *, demo: bool = False) -> TtsResult:
    """Mock-mode TTS.

    By default returns a silent WAV whose duration matches what the real
    MiMo model would have spoken (so Composer timings stay accurate).

    When ``demo=True`` (set via ``MIMOCAST_DEMO_TTS=1``), tries gTTS as a
    free, audible substitute so demo MP4s actually have narration. This is
    *not* a substitute for real MiMo TTS — never label demo-TTS output as
    MiMo provenance.
    """
    if demo:
        result = _try_gtts(text)
        if result is not None:
            return result
        log.warning("demo_tts: gTTS unavailable, falling back to silent WAV")

    return _silent_wav(text)


def _silent_wav(text: str) -> TtsResult:
    import io

    words = max(1, len(text.split()))
    duration_s = max(1.0, words * 0.4)
    sample_rate = 24_000
    n_frames = int(duration_s * sample_rate)
    silence = b"\x00\x00" * n_frames

    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sample_rate)
        w.writeframes(silence)

    return TtsResult(
        audio_bytes=buf.getvalue(),
        sample_rate=sample_rate,
        duration_s=duration_s,
        container="wav",
    )


def _try_gtts(text: str) -> TtsResult | None:
    """Best-effort gTTS synthesis. Returns None on any failure."""
    try:
        import io

        from gtts import gTTS  # type: ignore[import-not-found]
    except ImportError:
        return None

    try:
        buf = io.BytesIO()
        gTTS(text=text, lang="en", slow=False).write_to_fp(buf)
        audio_bytes = buf.getvalue()
        if not audio_bytes:
            return None
        # Estimate duration (gTTS doesn't expose it). 150 wpm baseline.
        words = max(1, len(text.split()))
        duration_s = max(1.0, words * 0.42)
        return TtsResult(
            audio_bytes=audio_bytes,
            sample_rate=24_000,
            duration_s=duration_s,
            container="mp3",
        )
    except Exception as exc:
        log.warning("gTTS synthesis failed: %s", exc)
        return None
