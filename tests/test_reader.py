from __future__ import annotations

from pathlib import Path

import pytest

from mimocast.agents.reader import Reader


def test_reads_markdown(sample_markdown: Path) -> None:
    doc = Reader().ingest(str(sample_markdown))
    assert doc.title  # derived from filename or first line
    assert "attention" in doc.text.lower()
    assert doc.word_count > 30
    assert doc.language == "en"


def test_reads_chinese_text(tmp_path: Path) -> None:
    p = tmp_path / "zh.txt"
    p.write_text("注意力机制让每个 token 关注序列中的其他 token。" * 8, encoding="utf-8")
    doc = Reader().ingest(str(p))
    assert doc.language == "zh"


def test_unknown_extension_raises(tmp_path: Path) -> None:
    p = tmp_path / "x.docx"
    p.write_bytes(b"binary stuff")
    with pytest.raises(ValueError, match="unsupported file extension"):
        Reader().ingest(str(p))


def test_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        Reader().ingest(str(tmp_path / "missing.md"))
