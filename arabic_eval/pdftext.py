"""Reading the text layer of a digital Arabic PDF.

pdfplumber (used by ai-document-extractor) returns each line in *visual*
order, left to right as drawn on the page. For Arabic that means every word
comes out reversed: "فاتورة" is returned as "ةروتاف". Running the Unicode bidi
algorithm over each line turns visual order back into logical (reading) order.
"""
from __future__ import annotations

from pathlib import Path


def visual_to_logical(text: str) -> str:
    from bidi import get_display

    return "\n".join(get_display(line) for line in text.split("\n"))


def pdf_text(path: str | Path, fix_rtl: bool) -> str:
    import pdfplumber

    pages = []
    with pdfplumber.open(str(path)) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            t = page.extract_text() or ""
            pages.append(f"--- page {i} ---\n{visual_to_logical(t) if fix_rtl else t}")
    return "\n\n".join(pages)
