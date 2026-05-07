"""Summarizer agent: Document -> Outline via MiMo reasoner with strict JSON schema."""

from __future__ import annotations

from mimocast.clients.mimo import MimoClient
from mimocast.models.schemas import Document, Outline
from mimocast.utils.logger import get_logger

log = get_logger(__name__)

_SYSTEM = """You are an editorial producer for short narrated video decks.
Given a source document, produce a JSON outline with 3-8 sections.
Each section becomes one slide. Bullets are punchy (<= 12 words).
Speaker notes are 2-4 sentences in the document's primary language and
read aloud naturally. Never invent facts not in the source."""

_SCHEMA: dict = {
    "type": "object",
    "additionalProperties": False,
    "required": ["title", "sections", "target_language"],
    "properties": {
        "title": {"type": "string", "minLength": 3, "maxLength": 120},
        "subtitle": {"type": ["string", "null"]},
        "target_language": {"type": "string", "minLength": 2, "maxLength": 8},
        "estimated_duration_s": {"type": "number", "minimum": 0},
        "sections": {
            "type": "array",
            "minItems": 2,
            "maxItems": 12,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["heading", "bullets", "speaker_notes"],
                "properties": {
                    "heading": {"type": "string", "minLength": 2, "maxLength": 80},
                    "bullets": {
                        "type": "array",
                        "minItems": 1,
                        "maxItems": 6,
                        "items": {"type": "string", "minLength": 2, "maxLength": 140},
                    },
                    "speaker_notes": {"type": "string", "minLength": 20, "maxLength": 800},
                },
            },
        },
    },
}


class Summarizer:
    def __init__(self, client: MimoClient):
        self.client = client

    def summarize(self, doc: Document, *, max_sections: int = 6) -> Outline:
        log.info(
            "summarizer: %s words, language=%s, target_sections<=%d",
            doc.word_count,
            doc.language,
            max_sections,
        )

        # Cap text we send to the model to avoid runaway prompt cost.
        snippet = doc.text[:18_000]

        user = (
            f"Source title: {doc.title}\n"
            f"Source language: {doc.language}\n"
            f"Target sections: at most {max_sections}\n\n"
            f"=== BEGIN DOCUMENT ===\n{snippet}\n=== END DOCUMENT ==="
        )
        payload = self.client.reason_json(system=_SYSTEM, user=user, json_schema=_SCHEMA)

        # Ensure target language is filled even if the model omitted it.
        payload.setdefault("target_language", doc.language)
        payload["sections"] = payload["sections"][:max_sections]

        outline = Outline.model_validate(payload)
        outline = outline.model_copy(
            update={"estimated_duration_s": _estimate_duration(outline)}
        )
        log.info(
            "summarizer: produced outline '%s' with %d sections (~%.1fs)",
            outline.title,
            len(outline.sections),
            outline.estimated_duration_s,
        )
        return outline


def _estimate_duration(outline: Outline) -> float:
    total_words = sum(len(s.speaker_notes.split()) for s in outline.sections)
    return round(total_words * 0.4, 2)
