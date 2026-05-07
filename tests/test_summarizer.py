from __future__ import annotations

from mimocast.agents.reader import Reader
from mimocast.agents.summarizer import Summarizer
from mimocast.clients.mimo import MimoClient


def test_summarizer_produces_valid_outline(mock_client: MimoClient, sample_markdown):
    doc = Reader().ingest(str(sample_markdown))
    outline = Summarizer(mock_client).summarize(doc, max_sections=4)

    assert outline.title
    assert 2 <= len(outline.sections) <= 4
    for section in outline.sections:
        assert section.heading
        assert 1 <= len(section.bullets) <= 6
        assert len(section.speaker_notes) >= 20

    assert outline.estimated_duration_s > 0


def test_summarizer_caps_sections(mock_client, sample_markdown):
    doc = Reader().ingest(str(sample_markdown))
    outline = Summarizer(mock_client).summarize(doc, max_sections=2)
    assert len(outline.sections) <= 2
