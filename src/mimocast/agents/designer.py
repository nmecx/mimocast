"""Designer agent: Outline -> rendered slide PNGs.

Layout: editorial / minimal — pale background, dark serif heading, bullet
glyphs, small footer with slide index. The Designer asks the MiMo
multimodal model to produce a short *image_prompt* per slide (used as
documentation / for downstream image-gen swap-ins) and renders the
actual slide deterministically with PIL so the output is testable and
free of API spend per render.
"""

from __future__ import annotations

import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from mimocast.clients.mimo import MimoClient
from mimocast.models.schemas import Outline, Slide
from mimocast.utils.files import ensure_dir
from mimocast.utils.logger import get_logger

log = get_logger(__name__)

_SLIDE_W = 1920
_SLIDE_H = 1080
_BG = (250, 246, 240)  # warm off-white
_FG = (33, 33, 33)
_ACCENT = (196, 60, 53)  # editorial red
_MUTED = (120, 120, 120)


class Designer:
    def __init__(self, client: MimoClient):
        self.client = client

    def render(self, outline: Outline, *, out_dir: Path) -> list[Slide]:
        ensure_dir(out_dir)
        slides: list[Slide] = []
        for i, section in enumerate(outline.sections, start=1):
            image_path = out_dir / f"slide_{i:02d}.png"
            image_prompt = self._image_prompt_for(outline.title, section.heading)
            _render_slide(
                path=image_path,
                title=outline.title,
                heading=section.heading,
                bullets=section.bullets,
                index=i,
                total=len(outline.sections),
            )
            slides.append(
                Slide(
                    index=i,
                    heading=section.heading,
                    bullets=section.bullets,
                    image_path=image_path,
                    image_prompt=image_prompt,
                )
            )
            log.info("designer: rendered %s", image_path.name)
        return slides

    def _image_prompt_for(self, title: str, heading: str) -> str:
        """Use the multimodal/reasoner model to produce a brief style prompt.

        We don't *need* this to render the slide (PIL handles that), but it
        documents the intent and is a hook for swapping in a real image-gen
        endpoint later. The cost is one short call per slide.
        """
        try:
            return self.client.reason(
                system=(
                    "You are an art director. In one sentence, describe a clean, "
                    "editorial-magazine style key visual for the slide. "
                    "No text in the image. Under 30 words."
                ),
                user=f"Deck: {title}\nSlide heading: {heading}",
                temperature=0.4,
            ).strip()
        except Exception as exc:
            log.warning("designer: image_prompt fallback (%s)", exc)
            return f"Editorial key visual for '{heading}' — minimal, neutral palette."


# ----------------------------------------------------------------------------
# Rendering helpers
# ----------------------------------------------------------------------------

def _font(size: int, *, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf" if bold
        else "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold
        else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/System/Library/Fonts/Supplemental/Times New Roman Bold.ttf" if bold
        else "/System/Library/Fonts/Supplemental/Times New Roman.ttf",
    ]
    for c in candidates:
        try:
            return ImageFont.truetype(c, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _render_slide(
    *,
    path: Path,
    title: str,
    heading: str,
    bullets: list[str],
    index: int,
    total: int,
) -> None:
    img = Image.new("RGB", (_SLIDE_W, _SLIDE_H), _BG)
    draw = ImageDraw.Draw(img)

    # Top brand strip
    draw.rectangle((0, 0, _SLIDE_W, 8), fill=_ACCENT)

    # Eyebrow / deck title
    eyebrow_font = _font(28)
    draw.text(
        (96, 72),
        title.upper()[:80],
        fill=_MUTED,
        font=eyebrow_font,
    )

    # Heading
    heading_font = _font(96, bold=True)
    wrapped_heading = "\n".join(textwrap.wrap(heading, width=26)[:3])
    draw.multiline_text(
        (96, 144),
        wrapped_heading,
        fill=_FG,
        font=heading_font,
        spacing=10,
    )

    # Bullets
    bullet_font = _font(44)
    y = 480
    for b in bullets[:6]:
        wrapped = textwrap.wrap(b, width=64)
        draw.text((120, y), "—", fill=_ACCENT, font=bullet_font)
        for j, line in enumerate(wrapped):
            draw.text((180, y + j * 56), line, fill=_FG, font=bullet_font)
        y += max(72, len(wrapped) * 56 + 24)
        if y > _SLIDE_H - 120:
            break

    # Footer
    footer_font = _font(24)
    draw.text(
        (96, _SLIDE_H - 64),
        f"mimocast  ·  {index:02d} / {total:02d}",
        fill=_MUTED,
        font=footer_font,
    )

    img.save(path, format="PNG", optimize=True)
