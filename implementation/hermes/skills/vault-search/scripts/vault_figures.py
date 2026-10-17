"""Bounded figures and page text from one exact vault PDF.

Page text is the PDF's own text layer, read without conversion or OCR; a page
without one (a scan) is returned as an image for the reader to look at.

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
MAX_NATIVE_SIDE = 2400  # pixels; a larger embedded image is halved until it fits
SEARCH_SECONDS = 8  # a common word on every page must not stall the reader
MAX_PAGES_READ = 3
MAX_PAGE_CHARS = 6000
MIN_TEXT_CHARS = 40  # below this a page is treated as a scan
SCAN_DPI = 110
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
        figures.append({"caption": text, "rect": region | rect, "region": region})
    if not figures:  # an uncaptioned drawing is offered only when the page names none
        figures = [{"caption": "", "rect": region, "region": region} for region in regions
                   if region.height * region.width > 120 * 80]
    figures.sort(key=lambda f: (f["rect"].y0, f["rect"].x0))
    return figures


def _embedded(page, region, mu) -> bytes | None:
    """The figure's own image when it is one embedded image and nothing is drawn or
    written over it: full source resolution. Otherwise None, and the region is
    rendered so labels, dimensions and vector strokes stay with the drawing."""
    inside = [info for info in page.get_image_info(xrefs=True)
              if region.contains(mu.Rect(info["bbox"]) + (-2, -2, 2, 2)) or region.intersects(mu.Rect(info["bbox"]))]
    if len(inside) != 1 or not inside[0].get("xref"):
        return None
    box = mu.Rect(inside[0]["bbox"])
    if box.get_area() < 0.85 * region.get_area():
        return None
    inner = box + (4, 4, -4, -4)
    if any(inner.intersects(mu.Rect(b[:4])) for b in page.get_text("blocks")):
        return None
    background = 0.5 * page.rect.get_area()  # a page-wide fill is not drawn over the figure
    if any(inner.intersects(d["rect"]) for d in page.get_drawings()
           if 4 < d["rect"].get_area() < background):
        return None
    try:
        pix = mu.Pixmap(page.parent, inside[0]["xref"])
        if pix.alpha:
            pix = mu.Pixmap(pix, 0)
        if pix.colorspace and pix.colorspace.n not in (1, 3):
            pix = mu.Pixmap(mu.csRGB, pix)
        while max(pix.width, pix.height) > MAX_NATIVE_SIDE:
            pix.shrink(1)
        data = pix.tobytes("png")
    except (RuntimeError, ValueError):
        return None
    return data if len(data) <= MAX_IMAGE_BYTES else None


def _render(page, rect, mu, dpi: int = RENDER_DPI) -> bytes:
    clip = (rect + (-6, -6, 6, 2)) & page.rect
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
    max_items = min(max(int(max_items), 1), MAX_FIGURES)  # more than the bound is not an error
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
                native = _embedded(current, figure["region"], mu)
                images.append(native or _render(current, figure["rect"], mu))
                items.append({
                    "page": number,
                    "caption": figure["caption"],
                    "caption_found": bool(figure["caption"]),
                    # embedded_image: the PDF's own picture, caption given here only;
                    # page_crop: the rendered region, caption included in the image.
                    "rendering": "embedded_image" if native else "page_crop",
                    "image": len(images),
                })
        return {
            "pages_examined": pages,
            "page_count": doc.page_count,
            "located_by": "page" if page else "text",
            "figures": items,
        }, images


def _mentions(doc, needle: str, limit: int) -> list[int]:
    """First pages whose text contains *needle*, within the search time budget."""
    found = []
    deadline = time.monotonic() + SEARCH_SECONDS
    for number in range(doc.page_count):
        if time.monotonic() > deadline or len(found) >= limit:
            break
        if doc[number].search_for(needle, quads=False):
            found.append(number + 1)
    return found


def read_pages(path: Path, page: int = 0, text: str = "", max_pages: int = 2) -> tuple[dict, list[bytes]]:
    """Text of a page (1-based) and the next ones, or of the first pages containing *text*."""
    mu = _mu()
    max_pages = min(max(int(max_pages), 1), MAX_PAGES_READ)
    if path.stat().st_size > MAX_PDF_BYTES:
        raise FigureError("PDF source exceeds the bounded reader limit")
    needle = " ".join(text.split())
    if not page and len(needle) < 4:
        raise FigureError("give a page number or at least four characters of text to locate")
    with mu.open(path) as doc:
        if page:
            if not 1 <= page <= doc.page_count:
                raise FigureError(f"page must be between 1 and {doc.page_count}")
            pages = list(range(page, min(page + max_pages, doc.page_count + 1)))
        else:
            pages = _mentions(doc, needle, max_pages)
        items, images = [], []
        for number in pages:
            current = doc[number - 1]
            body = current.get_text("text").strip()
            item = {"page": number, "citation": f"{path.name}, p. {number}"}
            if len(body) < MIN_TEXT_CHARS:  # a scan: its image, not an OCR guess
                images.append(_render(current, current.rect, mu, SCAN_DPI))
                item.update(text_layer=False, image=len(images))
            else:
                item.update(text_layer=True, text=body[:MAX_PAGE_CHARS],
                            truncated=len(body) > MAX_PAGE_CHARS)
            items.append(item)
        return {
            "pages_examined": pages,
            "page_count": doc.page_count,
            "located_by": "page" if page else "text",
            "pages": items,
        }, images
