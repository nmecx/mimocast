from __future__ import annotations

from pathlib import Path

import pytest

from mimocast.clients.mimo import MimoClient
from mimocast.config import Settings


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    return Settings(
        api_key=None,  # mock mode
        work_dir=tmp_path / "work",
        out_dir=tmp_path / "out",
        log_level="WARNING",
    )


@pytest.fixture
def mock_client(settings: Settings) -> MimoClient:
    return MimoClient(settings)


@pytest.fixture
def sample_markdown(tmp_path: Path) -> Path:
    p = tmp_path / "sample.md"
    p.write_text(
        """# How transformer attention works

Attention layers let each token attend to every other token in a sequence.
The mechanism uses three projections — queries, keys, and values — and a
softmax over the dot product of queries and keys to weight the values.

## Why it matters

Compared to recurrent networks, attention is parallelizable across the
sequence dimension, which is the core reason modern LLMs scale.

## Multi-head attention

Multiple heads let the model attend to different subspaces simultaneously.
The outputs are concatenated and projected back to the model dimension.
""",
        encoding="utf-8",
    )
    return p
