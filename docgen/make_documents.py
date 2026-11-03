"""Render the synthetic Arabic test set: HTML -> digital PDF -> page image.

    python docgen/make_documents.py

Writes, for every document in specs.py:
  dataset/pdf/<id>.pdf        digital PDF with a text layer (the "born digital" version)
  dataset/images/<id>.png     the page image used for OCR and Claude vision
                              (a clean 200 dpi render, a degraded "scan", or a 110 dpi low-res render)
  dataset/text/<id>.txt       the document's words in logical reading order, for OCR word recall
  dataset/ground_truth.json   the expected field values

Layout is done by WeasyPrint (Pango/HarfBuzz), which shapes Arabic and lays out
right-to-left text properly. The font is the bundled Tajawal
(SIL Open Font Licence), so the output is the same on any machine.
On macOS with Homebrew, run with DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib.
"""
from __future__ import annotations

import html
import json
import random
import re
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from arabic_eval.normalize import to_arabic_indic  # noqa: E402
from docgen import specs  # noqa: E402

OUT = ROOT / "dataset"
FONTS = ROOT / "fonts"

MONTHS_AR = ["يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو", "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر"]
CURRENCY_AR = {"AED": "درهم إماراتي", "SAR": "ريال سعودي", "USD": "دولار أمريكي"}


# ---------- formatting helpers ----------

def digits(text, style):
    return to_arabic_indic(text) if style.startswith("indic") else str(text)


def money(n, style):
    s = f"{n:,.2f}"
    if style == "indic_sep":
        return to_arabic_indic(s.replace(",", "٬").replace(".", "٫"))
    return digits(s, style)


def fmt_date(iso, style, date_style="dmy"):
    y, m, d = iso.split("-")
    if date_style == "iso":
        s = iso
    elif date_style == "monthname":
        return f"{digits(int(d), style)} {MONTHS_AR[int(m) - 1]} {digits(y, style)}"
    else:
        s = f"{d}/{m}/{y}"
    return digits(s, style)


CSS = f"""
@font-face {{ font-family: Tajawal; font-weight: normal; src: url('{(FONTS / "Tajawal-Regular.ttf").as_uri()}'); }}
@font-face {{ font-family: Tajawal; font-weight: bold; src: url('{(FONTS / "Tajawal-Bold.ttf").as_uri()}'); }}
@page {{ size: A4; margin: 16mm 15mm; }}
body {{ font-family: Tajawal; font-size: 12.5pt; color: #111; }}
h1 {{ font-size: 21pt; margin: 0 0 2mm 0; }}
h2 {{ font-size: 16pt; text-align: center; margin: 6mm 0 4mm; border-top: 2px solid #333; border-bottom: 2px solid #333; padding: 2mm 0; }}
.en {{ direction: ltr; unicode-bidi: isolate; }}
.muted {{ color: #444; font-size: 11pt; }}
table {{ width: 100%; border-collapse: collapse; margin: 3mm 0; }}
td, th {{ border: 1px solid #555; padding: 1.6mm 2.4mm; text-align: right; vertical-align: top; }}
th {{ background: #e6e6e6; }}
td.num {{ text-align: left; direction: ltr; unicode-bidi: isolate; white-space: nowrap; }}
table.meta td {{ border: none; padding: 0.8mm 0; }}
table.totals {{ width: 55%; margin-right: auto; margin-left: 0; }}
.watermark {{ position: fixed; top: 110mm; left: 10mm; font-size: 70pt; color: rgba(200,0,0,0.12); transform: rotate(-25deg); }}
"""


def page(body, extra_css=""):
    return f'<!doctype html><html lang="ar" dir="rtl"><head><meta charset="utf-8"><style>{CSS}{extra_css}</style></head><body>{body}</body></html>'


def lbl(ar, en, bilingual):
    return f'{ar} <span class="en">/ {en}</span>' if bilingual else ar


# ---------- document templates ----------

def invoice_html(s):
    st, bi = s["digits"], s["bilingual"]
    sub, vat, tot = specs.invoice_totals(s)
    e = html.escape
    head = f"<h1>{e(s['supplier'])}</h1>"
    if s.get("supplier_en"):
        head += f'<div class="en" style="font-size:14pt">{e(s["supplier_en"])}</div>'
    head += f'<div class="muted">{lbl("الرقم الضريبي للمورد", "Supplier TRN", bi)}: {digits(s["trn"], st)}</div>'
    head += '<div class="muted">العنوان: شارع الميناء، مبنى ١٤، المكتب ٣٠٢ - عنوان تجريبي</div>'
    if s["date_style"] == "hijri":
        date_cell = f'{digits(s["hijri"], st)} هـ الموافق {fmt_date(s["date"], st)} م'
    else:
        date_cell = fmt_date(s["date"], st, s["date_style"])
    meta = (
        '<table class="meta">'
        f'<tr><td>{lbl("رقم الفاتورة", "Invoice No.", bi)}:</td><td>{digits(s["number"], st)}</td></tr>'
        f'<tr><td>{lbl("تاريخ الفاتورة", "Invoice date", bi)}:</td><td>{date_cell}</td></tr>'
        f'<tr><td>{lbl("العميل", "Customer", bi)}:</td><td>{e(s["customer"])}</td></tr>'
        f'<tr><td>{lbl("العملة", "Currency", bi)}:</td><td>{CURRENCY_AR[s["currency"]]}</td></tr>'
        "</table>"
    )
    rows = "".join(
        f"<tr><td>{digits(i, st)}</td><td>{e(it['desc'])}</td><td class='num'>{digits(it['qty'], st)}</td>"
        f"<td class='num'>{money(it['price'], st)}</td><td class='num'>{money(it['qty'] * it['price'], st)}</td></tr>"
        for i, it in enumerate(s["items"], 1)
    )
    items = (
        f"<table><tr><th>{digits('#', st)}</th><th>{lbl('البيان', 'Description', bi)}</th><th>{lbl('الكمية', 'Qty', bi)}</th>"
        f"<th>{lbl('سعر الوحدة', 'Unit price', bi)}</th><th>{lbl('المبلغ', 'Amount', bi)}</th></tr>{rows}</table>"
    )
    vat_pct = digits(s["vat_rate"], st) + "٪"
    totals = (
        '<table class="totals">'
        f"<tr><td>{lbl('المجموع قبل الضريبة', 'Subtotal', bi)}</td><td class='num'>{money(sub, st)}</td></tr>"
        f"<tr><td>{lbl('ضريبة القيمة المضافة', 'VAT', bi)} {vat_pct}</td><td class='num'>{money(vat, st)}</td></tr>"
        f"<tr><th>{lbl('الإجمالي المستحق', 'Total due', bi)}</th><th class='num' style='text-align:left'>{money(tot, st)}</th></tr>"
        "</table>"
    )
    foot = '<p class="muted">يرجى السداد خلال ٣٠ يوماً من تاريخ الفاتورة. هذه فاتورة تجريبية لأغراض الاختبار.</p>'
    title = f"<h2>{lbl('فاتورة ضريبية', 'Tax Invoice', bi)}</h2>"
    extra = ""
    if s["render"] == "lowres":
        extra = "body { font-size: 9pt; } h1 { font-size: 14pt; } h2 { font-size: 11pt; }"
    return page(head + title + meta + items + totals + foot, extra)


def receipt_html(s):
    st = s["digits"]
    tot, vat = specs.receipt_totals(s)
    e = html.escape
    rows = "".join(
        f"<tr><td>{e(it['desc'])}<br><span class='muted'>{digits(it['qty'], st)} × {money(it['price'], st)}</span></td>"
        f"<td class='num'>{money(it['qty'] * it['price'], st)}</td></tr>"
        for it in s["items"]
    )
    pay = "نقداً" if s["payment"] == "cash" else "بطاقة ائتمان (مدى/فيزا) ****" + digits("4417", st)
    body = (
        f"<h1 style='text-align:center'>{e(s['merchant'])}</h1>"
        "<div class='muted' style='text-align:center'>فرع تجريبي - هاتف " + digits("04 000 0000", st) + "</div>"
        f"<p>رقم الإيصال: {digits(s['number'], st)}<br>التاريخ: {fmt_date(s['date'], st)} &nbsp; الوقت: {digits('18:42', st)}</p>"
        f"<table>{rows}</table>"
        f"<table class='meta'><tr><td><b>الإجمالي شامل الضريبة</b></td><td class='num'><b>{money(tot, st)}</b> درهم</td></tr>"
        f"<tr><td>منها ضريبة القيمة المضافة {digits(5, st)}٪</td><td class='num'>{money(vat, st)}</td></tr>"
        f"<tr><td>طريقة الدفع</td><td>{pay}</td></tr></table>"
        "<p style='text-align:center'>شكراً لزيارتكم</p>"
    )
    extra = "@page { size: 80mm 190mm; margin: 5mm; } body { font-size: 10.5pt; } h1 { font-size: 15pt; } td, th { border: none; border-bottom: 1px dashed #777; padding: 1mm; }"
    return page(body, extra)


def licence_html(s):
    st = s["digits"]
    e = html.escape
    rows = [
        ("رقم الرخصة", "Licence No.", digits(s["number"], st)),
        ("الاسم التجاري", "Trade name", f"{e(s['trade_ar'])}<br><span class='en'>{e(s['trade_en'])}</span>"),
        ("الشكل القانوني", "Legal form", e(s["legal_form"])),
        ("النشاط الرئيسي", "Main activity", e(s["activity"])),
        ("تاريخ الإصدار", "Issue date", fmt_date(s["issue"], st)),
        ("تاريخ الانتهاء", "Expiry date", fmt_date(s["expiry"], st)),
    ]
    table = "".join(f"<tr><th style='width:38%'>{a} <span class='en'>/ {b}</span></th><td>{v}</td></tr>" for a, b, v in rows)
    body = (
        "<div class='watermark'>SAMPLE عينة</div>"
        "<h1 style='text-align:center'>مكتب التنمية الاقتصادية - مدينة الواحة</h1>"
        "<div class='en' style='text-align:center'>Oasis City Economic Office (fictional authority)</div>"
        f"<h2>رخصة تجارية <span class='en'>/ Commercial Licence</span></h2><table>{table}</table>"
        "<p class='muted'>هذه وثيقة نموذجية لأغراض الاختبار فقط وليست صادرة عن أي جهة حكومية حقيقية.</p>"
    )
    return page(body)


# ---------- rendering ----------

def html_to_text(doc_html: str) -> str:
    """The document's words in logical (reading) order, for OCR word-recall scoring."""
    body = re.sub(r"(?s)<style>.*?</style>", "", doc_html)
    body = re.sub(r"(?s)<div class='watermark'>.*?</div>", "", body)
    body = re.sub(r"<(br|/tr|/p|/h1|/h2|/div)[^>]*>", "\n", body)
    body = re.sub(r"<[^>]+>", " ", body)
    lines = [" ".join(html.unescape(line).split()) for line in body.split("\n")]
    return "\n".join(line for line in lines if line)


def degrade(img: Image.Image, seed: int) -> Image.Image:
    """Make a clean render look like an office scan: slight tilt, blur, grey paper, speckle, JPEG."""
    rnd = random.Random(seed)
    g = img.convert("L")
    g = g.rotate(rnd.uniform(-2.2, 2.2), resample=Image.BICUBIC, expand=True, fillcolor=245)
    g = g.filter(ImageFilter.GaussianBlur(0.9))
    a = np.asarray(g).astype(np.float32)
    a = 40 + a * 0.80  # washed-out contrast, grey paper
    rng = np.random.default_rng(seed)
    a += rng.normal(0, 9, a.shape)
    speck = rng.random(a.shape)
    a[speck < 0.0015] = 30
    a[speck > 0.9985] = 250
    g = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    tmp = OUT / "_tmp.jpg"
    g.save(tmp, quality=55)
    g = Image.open(tmp).convert("L")
    g.load()
    tmp.unlink()
    return g


def render(doc_id: str, doc_html: str, mode: str, seed: int) -> None:
    import pypdfium2 as pdfium
    import weasyprint

    pdf_path = OUT / "pdf" / f"{doc_id}.pdf"
    weasyprint.HTML(string=doc_html, base_url=str(ROOT)).write_pdf(pdf_path)
    dpi = 110 if mode == "lowres" else 200
    pdf = pdfium.PdfDocument(str(pdf_path))
    img = pdf[0].render(scale=dpi / 72).to_pil().convert("RGB")
    pdf.close()
    if mode == "scan":
        img = degrade(img, seed)
    img.save(OUT / "images" / f"{doc_id}.png", optimize=True)
    (OUT / "text" / f"{doc_id}.txt").write_text(html_to_text(doc_html) + "\n", encoding="utf-8")


def main() -> int:
    for sub in ("pdf", "images", "text"):
        (OUT / sub).mkdir(parents=True, exist_ok=True)
    seed = 7
    for s in specs.INVOICES:
        render(s["id"], invoice_html(s), s["render"], seed := seed + 1)
    for s in specs.RECEIPTS:
        render(s["id"], receipt_html(s), s["render"], seed := seed + 1)
    for s in specs.LICENCES:
        render(s["id"], licence_html(s), s["render"], seed := seed + 1)
    for s in specs.HOLDOUT_INVOICES:
        render(s["id"], invoice_html(s), s["render"], seed := seed + 1)
    for s in specs.HOLDOUT_LICENCES:
        render(s["id"], licence_html(s), s["render"], seed := seed + 1)
    gt = specs.ground_truth()
    (OUT / "ground_truth.json").write_text(json.dumps(gt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    hold = specs.ground_truth(holdout=True)
    (OUT / "ground_truth_holdout.json").write_text(json.dumps(hold, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {len(gt)} documents + {len(hold)} holdout documents to {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
