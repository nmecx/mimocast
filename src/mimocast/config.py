"""Runtime configuration loaded from env / .env via pydantic-settings."""

from __future__ import annotations

from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="MIMOCAST_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    api_key: str | None = Field(default=None, description="MiMo API key. None = mock mode.")
    base_url: str = Field(default="https://api.xiaomimimo.com/v1")

    reasoner_model: str = Field(default="mimo-v2.5-reasoner")
    vision_model: str = Field(default="mimo-v2.5-vision")
    tts_model: str = Field(default="mimo-v2.5-tts")
    tts_voice: str = Field(default="mimo-female-warm")

    work_dir: Path = Field(default=Path("~/.mimocast"))
    out_dir: Path = Field(default=Path("./out"))

    log_level: str = Field(default="INFO")

    request_timeout_s: float = Field(default=60.0)
    max_retries: int = Field(default=3)

    # Demo-only: when in mock mode, route TTS through a free fallback (gTTS)
    # so the generated MP4 has audible narration. NOT a substitute for real
    # MiMo TTS — keep this off when producing artefacts that claim to be MiMo.
    demo_tts: bool = Field(default=False)

    @field_validator("work_dir", "out_dir", mode="before")
    @classmethod
    def _expand(cls, v: str | Path) -> Path:
        return Path(str(v)).expanduser().resolve()

    @property
    def mock_mode(self) -> bool:
        return not self.api_key


def get_settings(**overrides: object) -> Settings:
    return Settings(**overrides)  # type: ignore[arg-type]
