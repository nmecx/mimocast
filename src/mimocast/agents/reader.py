"""Reader agent: turns a source (PDF / .txt / .md / http URL) into a ``Document``."""

from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import urlparse

import httpx

from mimocast.models.schemas import Document
from mimocast.utils.logger import get_logger

log = get_logger(__name__)

_HTTP_TIMEOUT = 30.0
_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")


class Reader:
    def ingest(self, source: str) -> Document:
        log.info("reader: ingesting %s", source)
        parsed = urlparse(source)
        if parsed.scheme in {"http", "https"}:
            text, title = self._fetch_url(source)
        else:
            path = Path(source).expanduser().resolve()
            if not path.exists():
                raise FileNotFoundError(source)
            text, title = self._read_path(path)
            source = str(path)

        cleaned = _normalize(text)
        if not cleaned:
            raise ValueError(f"reader: extracted empty text from {source}")

        return Document(
            title=title or _derive_title(cleaned),
            source=source,
            text=cleaned,
            word_count=max(1, len(cleaned.split())),
            language=_detect_language(cleaned),
        )

    def _read_path(self, path: Path) -> tuple[str, str]:
        suffix = path.suffix.lower()
        if suffix == ".pdf":
            return _read_pdf(path), path.stem
        if suffix in {".txt", ".md", ".markdown", ".rst"}:
            return path.read_text(encoding="utf-8", errors="replace"), path.stem
        raise ValueError(f"reader: unsupported file extension '{suffix}'")

    def _fetch_url(self, url: str) -> tuple[str, str]:
        with httpx.Client(timeout=_HTTP_TIMEOUT, follow_redirects=True) as client:
            resp = client.get(url, headers={"User-Agent": "mimocast/0.1"})
            resp.raise_for_status()
        ctype = resp.headers.get("content-type", "")
        if "pdf" in ctype:
            tmp = Path("/tmp") / f"mimocast_{abs(hash(url))}.pdf"
            tmp.write_bytes(resp.content)
            return _read_pdf(tmp), urlparse(url).path.rsplit("/", 1)[-1] or url
        body = resp.text
        title = _extract_html_title(body) or urlparse(url).netloc
        return _strip_html(body), title


def _read_pdf(path: Path) -> str:
    from pypdf import PdfReader

    reader = PdfReader(str(path))
    pages = []
    for page in reader.pages:
        try:
            pages.append(page.extract_text() or "")
        except Exception as exc:
            log.warning("pdf page extract failed: %s", exc)
    return "\n\n".join(pages)


def _strip_html(body: str) -> str:
    return _TAG_RE.sub(" ", body)


def _extract_html_title(body: str) -> str | None:
    m = re.search(r"<title[^>]*>(.*?)</title>", body, flags=re.IGNORECASE | re.DOTALL)
    return _normalize(m.group(1)) if m else None


def _normalize(text: str) -> str:
    return _WS_RE.sub(" ", text).strip()


def _derive_title(text: str) -> str:
    first_line = text.strip().splitlines()[0] if text.strip() else "Untitled"
    return first_line[:120]


def _detect_language(text: str) -> str:
    sample = text[:2000]
    counts = {
        "zh": sum(1 for c in sample if "\u4e00" <= c <= "\u9fff"),
        "ja": sum(1 for c in sample if "\u3040" <= c <= "\u30ff"),
        "ko": sum(1 for c in sample if "\uac00" <= c <= "\ud7af"),
        "ar": sum(1 for c in sample if "\u0600" <= c <= "\u06ff"),
    }
    top = max(counts, key=counts.get)
    return top if counts[top] > 20 else "en"
