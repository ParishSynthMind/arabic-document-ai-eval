"""The 14 synthetic test documents and their ground truth.

Everything here is invented: company names, TRNs, licence numbers, amounts.
No real people or businesses. The trade-licence pages are issued by a made-up
authority and carry a SAMPLE watermark so they can't pass as real documents.

Each spec says which variant it tests (digit style, language mix, date
format, render quality). Ground truth is stored in canonical form: names as
printed in Arabic, numbers as plain numbers, IDs and dates in Western digits,
dates as YYYY-MM-DD.
"""
from __future__ import annotations


def _items(*rows):
    return [{"desc": d, "qty": q, "price": p} for d, q, p in rows]


INVOICES = [
    dict(id="inv01_ar_western", note="Arabic only, Western digits, clean print",
         supplier="شركة الواحة للتجارة العامة ذ.م.م", supplier_en=None, trn="100234567800003",
         number="INV-2026-0451", date="2026-10-12", customer="مؤسسة النخيل للمقاولات",
         currency="AED", vat_rate=5, digits="western", date_style="dmy", bilingual=False,
         items=_items(("أوراق طباعة A4 (كرتون)", 12, 85.00), ("حبر طابعة أسود", 4, 210.00), ("ملفات بلاستيكية", 30, 6.50)),
         render="clean"),
    dict(id="inv02_ar_indic", note="Arabic only, Arabic-Indic digits everywhere",
         supplier="مؤسسة الريان للأجهزة الكهربائية", supplier_en=None, trn="100387612400003",
         number="2026/118", date="2026-09-03", customer="فندق اللؤلؤة الزرقاء",
         currency="AED", vat_rate=5, digits="indic", date_style="dmy", bilingual=False,
         items=_items(("مكيف سبليت ١٫٥ طن", 3, 1450.00), ("تركيب وتشغيل", 3, 250.00)),
         render="clean"),
    dict(id="inv03_bi_western", note="Bilingual Arabic/English labels, Western digits",
         supplier="شركة صقر الخليج للخدمات اللوجستية", supplier_en="Gulf Falcon Logistics Services LLC", trn="100512908700003",
         number="GF-77812", date="2026-10-28", customer="Desert Rose Trading FZE",
         currency="AED", vat_rate=5, digits="western", date_style="iso", bilingual=True,
         items=_items(("شحن بري دبي - أبوظبي / Road freight Dubai - Abu Dhabi", 2, 1800.00), ("تخزين (أسبوع) / Storage (week)", 1, 640.00)),
         render="clean"),
    dict(id="inv04_bi_indic_monthname", note="Bilingual, Arabic-Indic digits, date written with an Arabic month name",
         supplier="شركة البيان لتقنية المعلومات", supplier_en="Al Bayan IT Company", trn="100678123400003",
         number="BY-3309", date="2026-10-15", customer="مدرسة الأفق الخاصة",
         currency="AED", vat_rate=5, digits="indic", date_style="monthname", bilingual=True,
         items=_items(("ترخيص برنامج محاسبة (سنة) / Accounting software licence (1 year)", 1, 4200.00), ("تدريب الموظفين / Staff training", 6, 350.00)),
         render="clean"),
    dict(id="inv05_ar_indic_separators", note="Arabic-Indic digits with Arabic thousands (٬) and decimal (٫) separators",
         supplier="شركة المرجان للمعدات الطبية", supplier_en=None, trn="100845561200003",
         number="MR-1042", date="2026-08-21", customer="عيادة الشفاء التخصصية",
         currency="AED", vat_rate=5, digits="indic_sep", date_style="dmy", bilingual=False,
         items=_items(("جهاز قياس ضغط رقمي", 15, 189.90), ("سرير فحص طبي", 2, 3250.00), ("قفازات طبية (علبة)", 40, 22.75)),
         render="clean"),
    dict(id="inv06_ar_scanned", note="Arabic only, Western digits, scanned (tilted, blurred, speckled)",
         supplier="مطبعة الفجر الحديثة", supplier_en=None, trn="100923347100003",
         number="F-2026-0098", date="2026-10-05", customer="جمعية البر الخيرية",
         currency="AED", vat_rate=5, digits="western", date_style="dmy", bilingual=False,
         items=_items(("طباعة كتيبات ملونة", 500, 4.20), ("تصميم غلاف", 1, 450.00)),
         render="scan"),
    dict(id="inv07_bi_indic_scanned", note="Bilingual, Arabic-Indic digits, scanned",
         supplier="شركة الصحراء الذهبية للسياحة", supplier_en="Golden Desert Tourism Co.", trn="100456789100003",
         number="GDT-5521", date="2026-11-01", customer="Blue Horizon Events LLC",
         currency="AED", vat_rate=5, digits="indic", date_style="dmy", bilingual=True,
         items=_items(("رحلة سفاري صحراوية / Desert safari", 24, 275.00), ("عشاء بدوي / Bedouin dinner", 24, 95.00)),
         render="scan"),
    dict(id="inv08_ar_hijri", note="Hijri and Gregorian dates both printed; Saudi invoice, SAR, 15% VAT",
         supplier="شركة رمال نجد للتوريدات", supplier_en=None, trn="310245678900003",
         number="RN-44/1448", date="2026-10-25", hijri="1448/05/14", customer="مستشفى الرعاية الأولى",
         currency="SAR", vat_rate=15, digits="indic", date_style="hijri", bilingual=False,
         items=_items(("مستلزمات تعقيم", 120, 18.50), ("أكياس نفايات طبية", 60, 12.00)),
         render="clean"),
    dict(id="inv09_ar_lowres", note="Small 9pt type rendered at low resolution (110 dpi)",
         supplier="مؤسسة الأمانة للأدوات المكتبية", supplier_en=None, trn="100311224400003",
         number="AM-20817", date="2026-07-30", customer="شركة الضياء للاستشارات",
         currency="AED", vat_rate=5, digits="western", date_style="dmy", bilingual=False,
         items=_items(("دباسة مكتبية", 10, 35.00), ("أقلام حبر جاف (علبة)", 25, 18.00), ("دفاتر ملاحظات", 50, 9.50)),
         render="lowres"),
    dict(id="inv10_ar_tashkeel_usd", note="Supplier name printed with vowel marks (tashkeel); priced in US dollars",
         supplier="شَرِكَةُ السَّلامِ لِلتَّرجَمَةِ", supplier_en=None, trn="100733418900003",
         number="SL-0612", date="2026-06-18", customer="Northwind Legal Partners",
         currency="USD", vat_rate=5, digits="western", date_style="dmy", bilingual=False,
         items=_items(("ترجمة قانونية (صفحة)", 40, 22.00), ("تصديق الترجمة", 1, 60.00)),
         render="clean"),
]

RECEIPTS = [
    dict(id="rcp01_ar_western", note="Narrow till receipt, Arabic, Western digits, card payment",
         merchant="مقهى الياسمين", number="R-88213", date="2026-10-30", payment="card",
         digits="western", render="clean",
         items=_items(("قهوة عربية", 2, 15.00), ("كرك", 3, 8.00), ("كعكة تمر", 2, 12.00))),
    dict(id="rcp02_ar_indic_scanned", note="Till receipt, Arabic-Indic digits, cash, faded scan",
         merchant="بقالة الخير", number="5531", date="2026-11-02", payment="cash",
         digits="indic", render="scan",
         items=_items(("حليب طازج ١ لتر", 2, 6.75), ("خبز عربي", 3, 2.50), ("أرز بسمتي ٥ كجم", 1, 42.00))),
]

LICENCES = [
    dict(id="lic01_bi_western", note="Trade-licence style page, bilingual, Western digits",
         number="CN-4471209", trade_ar="الواحة للتجارة العامة", trade_en="AL WAHA GENERAL TRADING",
         legal_form="شركة ذات مسؤولية محدودة", activity="تجارة المواد الغذائية بالجملة",
         issue="2024-03-17", expiry="2027-03-16", digits="western", render="clean"),
    dict(id="lic02_bi_indic_scanned", note="Trade-licence style page, Arabic-Indic digits, scanned",
         number="CN-5532871", trade_ar="نجمة الشرق للمقاولات", trade_en="EASTERN STAR CONTRACTING",
         legal_form="مؤسسة فردية", activity="مقاولات المباني",
         issue="2025-01-09", expiry="2026-12-31", digits="indic", render="scan"),
]


# Held out: made after the Arabic checks in arabic_eval/extract.py were written from the
# first live run, to test those checks on documents they were not designed around.
HOLDOUT_INVOICES = [
    dict(id="hold01_ar_indic_sep_scanned", note="HOLDOUT. Arabic-Indic separators, scanned, five-figure amounts",
         supplier="شركة الأفق الأخضر للمعدات الزراعية", supplier_en=None, trn="100562718300003",
         number="AK-7730", date="2026-09-14", customer="مزرعة الواحات الخضراء",
         currency="AED", vat_rate=5, digits="indic_sep", date_style="dmy", bilingual=False,
         items=_items(("مضخة ري كهربائية", 6, 2875.00), ("أنابيب ري (لفة ١٠٠ متر)", 25, 410.50)),
         render="scan"),
    dict(id="hold02_bi_indic_ids", note="HOLDOUT. Bilingual, Arabic-Indic digits, IDs with letters and slashes",
         supplier="شركة النور للأنظمة الأمنية", supplier_en="Al Noor Security Systems LLC", trn="100937261500003",
         number="NS/26-0417", date="2026-10-02", customer="Marina Heights Owners Association",
         currency="AED", vat_rate=5, digits="indic", date_style="monthname", bilingual=True,
         items=_items(("كاميرا مراقبة خارجية / Outdoor CCTV camera", 16, 640.00), ("جهاز تسجيل / NVR recorder", 2, 1950.00)),
         render="clean"),
    dict(id="hold03_ar_indic_sep_clean", note="HOLDOUT. Arabic-Indic separators, clean, six-figure total",
         supplier="مؤسسة البناء المتين للمقاولات", supplier_en=None, trn="100418829600003",
         number="BM-2026-0093", date="2026-07-07", customer="شركة أبراج الخليج العقارية",
         currency="AED", vat_rate=5, digits="indic_sep", date_style="dmy", bilingual=False,
         items=_items(("أعمال خرسانة (متر مكعب)", 180, 520.00), ("حديد تسليح (طن)", 14, 3150.00)),
         render="clean"),
]
HOLDOUT_LICENCES = [
    dict(id="hold04_lic_indic_scanned", note="HOLDOUT. Licence page, Arabic-Indic digits, scanned",
         number="CN-6618204", trade_ar="لمسة الإبداع للديكور", trade_en="CREATIVE TOUCH DECOR",
         legal_form="شركة الشخص الواحد ذات المسؤولية المحدودة", activity="أعمال الديكور الداخلي",
         issue="2025-06-22", expiry="2026-06-21", digits="indic", render="scan"),
]


def invoice_totals(spec):
    subtotal = round(sum(i["qty"] * i["price"] for i in spec["items"]), 2)
    vat = round(subtotal * spec["vat_rate"] / 100, 2)
    return subtotal, vat, round(subtotal + vat, 2)


def receipt_totals(spec):
    """Till receipts in the UAE usually print prices VAT-inclusive; VAT is shown as 5/105 of the total."""
    total = round(sum(i["qty"] * i["price"] for i in spec["items"]), 2)
    vat = round(total * 5 / 105, 2)
    return total, vat


def ground_truth(holdout: bool = False) -> dict:
    out = {}
    for s in (HOLDOUT_INVOICES if holdout else INVOICES):
        sub, vat, tot = invoice_totals(s)
        out[s["id"]] = {"schema": "invoice_ar", "note": s["note"], "render": s["render"], "fields": {
            "supplier_name": s["supplier"], "supplier_trn": s["trn"], "invoice_number": s["number"],
            "invoice_date": s["date"], "customer_name": s["customer"], "currency": s["currency"],
            "subtotal": sub, "vat_amount": vat, "total_amount": tot}}
    for s in ([] if holdout else RECEIPTS):
        tot, vat = receipt_totals(s)
        out[s["id"]] = {"schema": "receipt_ar", "note": s["note"], "render": s["render"], "fields": {
            "merchant_name": s["merchant"], "receipt_number": s["number"], "receipt_date": s["date"],
            "payment_method": s["payment"], "vat_amount": vat, "total_amount": tot}}
    for s in (HOLDOUT_LICENCES if holdout else LICENCES):
        out[s["id"]] = {"schema": "trade_licence", "note": s["note"], "render": s["render"], "fields": {
            "licence_number": s["number"], "trade_name_ar": s["trade_ar"], "trade_name_en": s["trade_en"],
            "legal_form": s["legal_form"], "main_activity": s["activity"],
            "issue_date": s["issue"], "expiry_date": s["expiry"]}}
    return out
