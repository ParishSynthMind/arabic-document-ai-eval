import shutil
from pathlib import Path

import numpy as np
import pytest
from PIL import Image, ImageDraw

from arabic_eval import ocr as ocr_mod
from arabic_eval.normalize import strip_marks
from arabic_eval.pdftext import pdf_text, visual_to_logical

ROOT = Path(__file__).resolve().parent.parent


def test_visual_order_is_reversed_back():
    # how pdfplumber returns the Arabic word "فاتورة" from a digital PDF: letters in visual order
    assert visual_to_logical("ةروتاف") == "فاتورة"
    assert "فاتورة" in visual_to_logical("Tax Invoice - ةروتاف")


def test_pdf_text_layer_raw_vs_fixed():
    pdf = ROOT / "dataset" / "pdf" / "lic01_bi_western.pdf"
    raw, fixed = pdf_text(pdf, fix_rtl=False), pdf_text(pdf, fix_rtl=True)
    assert "رخصة تجارية" not in raw  # reversed letters
    assert "رخصة تجارية" in fixed


def test_otsu_splits_two_levels():
    a = np.array([[20] * 50 + [230] * 50] * 10, dtype=np.uint8)
    t = ocr_mod.otsu_threshold(a)
    assert 20 <= t < 230


def test_estimate_skew_finds_rotation():
    img = Image.new("L", (800, 600), 255)
    d = ImageDraw.Draw(img)
    for y in range(60, 560, 40):
        d.rectangle([60, y, 740, y + 12], fill=0)
    tilted = img.rotate(2.0, resample=Image.BICUBIC, fillcolor=255)
    assert abs(ocr_mod.estimate_skew(tilted) + 2.0) <= 0.5


def test_preprocess_returns_binary_image():
    img = Image.open(ROOT / "dataset" / "images" / "inv09_ar_lowres.png")
    out = ocr_mod.preprocess(img)
    assert max(out.size) >= 2000
    assert set(np.unique(np.asarray(out))) <= {0, 255}


@pytest.mark.skipif(shutil.which("tesseract") is None or not (ROOT / "tessdata" / "best" / "ara.traineddata").exists(),
                    reason="needs tesseract and scripts/get_tessdata.sh")
def test_real_arabic_ocr_reads_clean_licence():
    text = ocr_mod.ocr(Image.open(ROOT / "dataset" / "images" / "lic01_bi_western.png"), "ara-best")
    text = strip_marks(text)  # Tesseract adds bidi direction marks around mixed runs
    assert "رخصة تجارية" in text and "CN-4471209" in text and "16/03/2027" in text
