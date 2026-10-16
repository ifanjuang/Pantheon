"""Bounded figure crops from one exact vault PDF page, located by caption.

A figure is a drawing or embedded-image region of the page together with the
caption that names it (« Figure 28 … », « Tableau 1 … », « Schéma … »). The
crop shows what the PDF draws; it is not inspected content until the reader has
compared it with the question, and it is never Evidence.

PyMuPDF is imported lazily so the Markdown readers do not depend on it.
"""

from __future__ import annotations

import re
import time
from pathlib import Path

MAX_PDF_BYTES = 200 * 1024 * 1024
MAX_FIGURES = 4
MAX_PAGES_SEARCHED = 2
MAX_IMAGE_BYTES = 2 * 1024 * 1024
RENDER_DPI = 144
SEARCH_SECONDS = 8  # a common word on every page must not stall the reader
MIN_REGION_PT = 36  # below this, a rule, logo or pictogram
CAPTION = re.compile(r"^\s*(figure|fig\.?|sch[ée]ma|tableau|planche|d[ée]tail)\s*n?°?\s*\d+", re.IGNORECASE)


class FigureError(ValueError):
    pass


def _mu():
    try:
        import pymupdf
    except ImportError as exc:  # pragma: no cover - deployment check
        raise FigureError("PDF figure reading needs PyMuPDF in the vault reader runtime") from exc
    return pymupdf


def _merge(rects: list, gap: float) -> list:
    merged = True
    while merged:
        merged = False
        out: list = []
        for rect in rects:
            for index, other in enumerate(out):
                if (rect + (-gap, -gap, gap, gap)).intersects(other):
                    out[index] = other | rect
                    merged = True
                    break
            else:
                out.append(rect)
        rects = out
    return rects


def _regions(page, mu) -> list:
    rects = list(page.cluster_drawings(x_tolerance=8, y_tolerance=8))
    rects += [mu.Rect(info["bbox"]) for info in page.get_image_info()]
    full = page.rect.width * 0.98
    return [
        rect for rect in _merge(rects, 12)
        if rect.width >= MIN_REGION_PT and rect.height >= MIN_REGION_PT and rect.width < full
    ]


def _captions(page, mu) -> list[tuple[object, str]]:
    return [
        (mu.Rect(block[:4]), " ".join(block[4].split()))
        for block in page.get_text("blocks")
        if CAPTION.match(block[4])
    ]


def _nearest(caption, regions: list):
    """The drawing a caption names: just above it, else just below it."""
    def distance(region) -> float:
        if region.x1 < caption.x0 - 20 or region.x0 > caption.x1 + 200:
            return float("inf")
        if region.y1 <= caption.y0 + 5:
            return caption.y0 - region.y1
        return region.y0 - caption.y1 + 40
    best = min(regions, key=distance, default=None)
    return best if best is not None and distance(best) < 120 else None


def page_figures(page, mu) -> list[dict]:
    regions = _regions(page, mu)
    figures = []
    for rect, text in _captions(page, mu):
        region = _nearest(rect, regions)
        if region is None:
            continue
        figures.append({"caption": text, "rect": region | rect})
    if not figures:  # an uncaptioned drawing is offered only when the page names none
        figures = [{"caption": "", "rect": region} for region in regions
                   if region.height * region.width > 120 * 80]
    figures.sort(key=lambda f: (f["rect"].y0, f["rect"].x0))
    return figures


def _render(page, rect, mu) -> bytes:
    clip = (rect + (-6, -6, 6, 2)) & page.rect
    dpi = RENDER_DPI
    while True:
        data = page.get_pixmap(clip=clip, dpi=dpi).tobytes("png")
        if len(data) <= MAX_IMAGE_BYTES or dpi <= 72:
            return data
        dpi = int(dpi * 0.75)


def _fold(value: str) -> str:
    return " ".join(value.casefold().split())


def _names(needle: str, caption: str) -> bool:
    """« Figure 3 » names Figure 3, not Figure 30."""
    return re.search(re.escape(_fold(needle)) + r"(?!\d)", _fold(caption)) is not None


def _locate(doc, needle: str, mu) -> list[int]:
    """Pages whose caption names *needle* (and that draw something) first; else the
    first pages that mention it. Captions are read before the costlier drawing scan."""
    captioned, mentioned = [], []
    deadline = time.monotonic() + SEARCH_SECONDS
    for number in range(doc.page_count):
        if time.monotonic() > deadline:
            break
        current = doc[number]
        if not current.search_for(needle, quads=False):
            continue
        if any(_names(needle, text) for _, text in _captions(current, mu)) and _regions(current, mu):
            captioned.append(number + 1)
            if len(captioned) >= MAX_PAGES_SEARCHED:
                break
        elif len(mentioned) < MAX_PAGES_SEARCHED:
            mentioned.append(number + 1)
    return captioned or mentioned


def read_figures(path: Path, page: int = 0, text: str = "", max_items: int = 3) -> tuple[dict, list[bytes]]:
    """Figures of one page (1-based), or of the first pages whose text contains *text*."""
    mu = _mu()
    if not 1 <= max_items <= MAX_FIGURES:
        raise FigureError(f"max_items must be between 1 and {MAX_FIGURES}")
    if path.stat().st_size > MAX_PDF_BYTES:
        raise FigureError("PDF source exceeds the bounded reader limit")
    needle = " ".join(text.split())
    if not page and len(needle) < 4:
        raise FigureError("give a page number or at least four characters of text to locate")
    with mu.open(path) as doc:
        if page:
            if not 1 <= page <= doc.page_count:
                raise FigureError(f"page must be between 1 and {doc.page_count}")
            pages = [page]
        else:
            pages = _locate(doc, needle, mu)
        items, images = [], []
        for number in pages:
            current = doc[number - 1]
            figures = page_figures(current, mu)
            if needle:  # the figure the text names comes first
                figures.sort(key=lambda f: not _names(needle, f["caption"]))
            for figure in figures:
                if len(items) >= max_items:
                    break
                images.append(_render(current, figure["rect"], mu))
                items.append({
                    "page": number,
                    "caption": figure["caption"],
                    "caption_found": bool(figure["caption"]),
                    "image": len(images),
                })
        return {
            "pages_examined": pages,
            "page_count": doc.page_count,
            "located_by": "page" if page else "text",
            "figures": items,
        }, images
