"""Render the README images in media/ from the saved results (no API calls).

    DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib python scripts/make_media.py   # macOS + Homebrew
"""
from __future__ import annotations

import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

FONT = (ROOT / "fonts" / "Tajawal-Regular.ttf").as_uri()
FONT_B = (ROOT / "fonts" / "Tajawal-Bold.ttf").as_uri()
CSS = f"""
@font-face {{ font-family: T; src: url('{FONT}'); }}
@font-face {{ font-family: T; font-weight: bold; src: url('{FONT_B}'); }}
@page {{ size: 1600px {{height}}px; margin: 0; }}
body {{ font-family: T; margin: 0; padding: 36px 44px; background: #f6f7f9; color: #1b1f24; }}
h1 {{ font-size: 34px; margin: 0 0 4px; }} .sub {{ color: #57606a; font-size: 19px; margin-bottom: 22px; }}
table {{ border-collapse: collapse; font-size: 21px; background: white; }}
th, td {{ padding: 9px 14px; border-bottom: 1px solid #d8dee4; text-align: left; }}
th {{ background: #eaeef2; }} td.n {{ text-align: right; font-variant-numeric: tabular-nums; }}
.good {{ color: #1a7f37; font-weight: bold; }} .bad {{ color: #cf222e; font-weight: bold; }}
.card {{ background: white; border: 1px solid #d8dee4; border-radius: 10px; padding: 12px 16px; margin-bottom: 12px; }}
.q {{ direction: rtl; text-align: right; font-size: 22px; font-weight: bold; }}
.a {{ direction: rtl; text-align: right; font-size: 20px; color: #24292f; margin-top: 4px; }}
.a.en, .q.en {{ direction: ltr; text-align: left; }}
.tag {{ font-size: 15px; color: #57606a; }}
"""


def render(body: str, out: Path, height: int) -> None:
    import pypdfium2 as pdfium
    import weasyprint

    pdf = out.with_suffix(".pdf")
    weasyprint.HTML(string=f"<html><head><meta charset='utf-8'><style>{CSS.replace('{height}', str(height))}</style></head><body>{body}</body></html>").write_pdf(pdf)
    doc = pdfium.PdfDocument(str(pdf))
    doc[0].render(scale=2).to_pil().convert("RGB").save(out, optimize=True)
    doc.close()
    pdf.unlink()


def method_rows(md: str) -> list:
    rows = []
    for line in md.splitlines():
        m = re.match(r"\| (pdf-raw|pdf-fixed|ocr-eng|ocr-ara|ocr-prep|vision) \| (\d+) \| (\d+)% \| \*\*(\d+)%\*\* \| (\d+) \| (\d+) \| (\d+) \| \*\*(\d+)\*\*", line)
        if m:
            rows.append(m.groups())
    return rows


LABEL = {
    "pdf-raw": "Digital PDF, text layer as-is",
    "pdf-fixed": "Digital PDF, text 'fixed' right-to-left",
    "ocr-eng": "Scan, Tesseract English only (the old default)",
    "ocr-ara": "Scan, Tesseract Arabic + English",
    "ocr-prep": "Scan, clean-up + Tesseract Arabic",
    "vision": "Page image straight to Claude (no OCR)",
}


def extraction_image() -> None:
    rows = method_rows((ROOT / "results" / "extraction_results.md").read_text(encoding="utf-8"))
    trs = "".join(
        f"<tr><td>{LABEL[m]}</td><td class='n {'good' if int(norm) >= 90 else 'bad' if int(norm) < 70 else ''}'>{norm}%</td>"
        f"<td class='n'>{plus_flag}</td><td class='n {'good' if wu == '0' else 'bad'}'>{wu}</td></tr>"
        for m, total, exact, norm, flag, wu_base, plus_flag, wu in rows
    )
    img = (ROOT / "dataset" / "images" / "inv07_bi_indic_scanned.png").as_uri()
    body = f"""
    <h1>Arabic invoices, receipts and licences: field extraction, measured</h1>
    <div class='sub'>14 synthetic printed documents, 116 fields, Claude Sonnet 5.5. Tested live on 3 November 2026.</div>
    <table style='float:left; width: 1020px'>
      <tr><th>How the document reached Claude</th><th>Fields right</th><th>Sent to review</th><th>Wrong and NOT flagged</th></tr>
      {trs}
    </table>
    <img src='{img}' style='float:right; width: 430px; border: 1px solid #d8dee4;'>
    <div style='clear:left; padding-top: 18px; width: 1020px; font-size: 19px; color:#57606a'>
      "Fields right" ignores harmless differences (digit style, letter forms). "Wrong and not flagged" is the number that matters:
      errors that would reach your books without a person seeing them. Right: one of the scanned test invoices (Arabic-Indic digits).
    </div>"""
    render(body, ROOT / "media" / "extraction-results.png", 600)


def chatbot_image() -> None:
    picks = ["q06", "q07", "q11", "q12"]
    cards = ""
    for q in picks:
        rec = json.loads((ROOT / "results" / "chat" / "arabic-full" / f"{q}.json").read_text(encoding="utf-8"))
        en = " en" if rec["question"]["lang"] == "en" else ""
        cards += (f"<div class='card'><div class='tag'>{html.escape(rec['question']['kind'])}</div>"
                  f"<div class='q{en}'>{html.escape(rec['question']['question'])}</div>"
                  f"<div class='a{en}'>{html.escape(rec['reply']['reply'])}</div></div>")
    md = (ROOT / "results" / "chat_results.md").read_text(encoding="utf-8")
    scores = dict(re.findall(r"\| (original|arabic-search|arabic-full) \|.*\*\*(\d+/60) \(", md))
    body = f"""
    <h1>Support chatbot answering in Arabic, from Arabic help docs</h1>
    <div class='sub'>15 questions (Gulf dialect, Arabic-Indic digits, a prompt injection, one in English), 4-point rubric. Tested live on 3 November 2026.</div>
    <table style='margin-bottom: 16px'><tr><th>Chatbot version</th><th>Score</th></tr>
      <tr><td>As published (English-only search)</td><td class='n bad'>{scores['original']}</td></tr>
      <tr><td>Arabic search added</td><td class='n'>{scores['arabic-search']}</td></tr>
      <tr><td>Arabic search + Arabic handover + reply-language rule</td><td class='n good'>{scores['arabic-full']}</td></tr></table>
    {cards}"""
    render(body, ROOT / "media" / "arabic-chatbot.png", 780)


if __name__ == "__main__":
    (ROOT / "media").mkdir(exist_ok=True)
    extraction_image()
    chatbot_image()
    print("wrote media/extraction-results.png and media/arabic-chatbot.png")
