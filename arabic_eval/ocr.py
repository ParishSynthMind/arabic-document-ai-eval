"""Tesseract OCR set up for Arabic, plus the image clean-up that helps it.

Four OCR settings are compared in the evaluation:

  eng        English model only, which is what ai-document-extractor does out of the box
  ara-fast   Arabic + English, tessdata_fast models (small, quick)
  ara-best   Arabic + English, tessdata_best models (larger, slower, more accurate)
  ara-prep   ara-best after preprocessing: deskew, upscale small images, denoise, binarise

The trained models live in tessdata/<fast|best>/ (downloaded by
scripts/get_tessdata.sh) so results don't depend on which language packs the
machine happens to have.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter, ImageOps

ROOT = Path(__file__).resolve().parent.parent
TESSDATA = ROOT / "tessdata"

OCR_SETTINGS = {
    "eng": {"lang": "eng", "data": "best", "prep": False},
    "ara-fast": {"lang": "ara+eng", "data": "fast", "prep": False},
    "ara-best": {"lang": "ara+eng", "data": "best", "prep": False},
    "ara-prep": {"lang": "ara+eng", "data": "best", "prep": True},
}


def otsu_threshold(gray: np.ndarray) -> int:
    hist = np.bincount(gray.ravel(), minlength=256).astype(np.float64)
    total = gray.size
    cum = np.cumsum(hist)
    cum_mean = np.cumsum(hist * np.arange(256))
    best_t, best_var = 127, -1.0
    for t in range(1, 255):
        w0, w1 = cum[t], total - cum[t]
        if w0 == 0 or w1 == 0:
            continue
        m0 = cum_mean[t] / w0
        m1 = (cum_mean[-1] - cum_mean[t]) / w1
        var = w0 * w1 * (m0 - m1) ** 2
        if var > best_var:
            best_t, best_var = t, var
    return best_t


def estimate_skew(gray: Image.Image, max_angle: float = 4.0, step: float = 0.25) -> float:
    """Angle (degrees) that makes text lines most horizontal, found by testing small
    rotations and keeping the one whose row-sum profile is sharpest."""
    small = gray.copy()
    small.thumbnail((900, 900))
    a = np.asarray(small)
    ink = (a < otsu_threshold(a)).astype(np.uint8) * 255
    img = Image.fromarray(ink)
    best, best_score = 0.0, -1.0
    for angle in np.arange(-max_angle, max_angle + 1e-9, step):
        rows = np.asarray(img.rotate(angle, resample=Image.NEAREST, fillcolor=0)).sum(axis=1).astype(np.float64)
        score = float(np.sum(np.diff(rows) ** 2))
        if score > best_score:
            best, best_score = float(angle), score
    return best


def preprocess(image: Image.Image) -> Image.Image:
    g = ImageOps.grayscale(image)
    if max(g.size) < 2000:  # low-resolution page: upscale so letters are big enough for the model
        scale = 2000 / max(g.size)
        g = g.resize((round(g.width * scale), round(g.height * scale)), Image.LANCZOS)
    angle = estimate_skew(g)
    if abs(angle) >= 0.25:
        g = g.rotate(angle, resample=Image.BICUBIC, expand=True, fillcolor=255)
    g = g.filter(ImageFilter.MedianFilter(3))
    g = ImageOps.autocontrast(g, cutoff=1)
    a = np.asarray(g)
    return Image.fromarray(np.where(a > otsu_threshold(a), 255, 0).astype(np.uint8))


def ocr(image: Image.Image, setting: str = "ara-best") -> str:
    import pytesseract

    cfg = OCR_SETTINGS[setting]
    img = preprocess(image) if cfg["prep"] else image.convert("L")
    data_dir = TESSDATA / cfg["data"]
    if not (data_dir / "ara.traineddata").exists():
        raise FileNotFoundError(f"{data_dir} has no Arabic model; run scripts/get_tessdata.sh")
    # psm 4 (single column of variable-size text) matches ai-document-extractor's default
    return pytesseract.image_to_string(img, lang=cfg["lang"], config=f'--psm 4 --tessdata-dir "{data_dir}"')
