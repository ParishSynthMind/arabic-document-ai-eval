"""Arabic text normalisation, used for scoring and for search.

Arabic has several ways to write "the same" text, and a fair comparison has to
fold them together:
- Arabic-Indic digits (٠١٢٣٤٥٦٧٨٩) and Persian/Urdu digits (۰۱۲۳۴۵۶۷۸۹) become 0-9.
- The Arabic decimal separator (٫) becomes "." and the thousands separator (٬) is dropped.
- Short vowel marks (tashkeel) and the stretching character (tatweel, ـ) are removed.
- Alef forms (أ إ آ ٱ) become ا, alef maqsura (ى) becomes ي, taa marbuta (ة) becomes ه.
- Bidi control characters that PDF tools leave behind are removed.

`normalise_text` is deliberately aggressive: it is for "did the model read the
same thing", not for display.
"""
from __future__ import annotations

import re
from datetime import date

ARABIC_INDIC = "٠١٢٣٤٥٦٧٨٩"
PERSIAN = "۰۱۲۳۴۵۶۷۸۹"
DIGITS = str.maketrans(ARABIC_INDIC + PERSIAN, "0123456789" * 2)
TO_ARABIC_INDIC = str.maketrans("0123456789", ARABIC_INDIC)

TASHKEEL = re.compile(r"[ؐ-ًؚ-ٰٟۖ-ۭ]")
TATWEEL = "ـ"
BIDI_CONTROLS = re.compile(r"[‎‏‪-‮⁦-⁩؜]")
LETTER_FOLD = str.maketrans({"أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا", "ى": "ي", "ة": "ه", "ؤ": "و", "ئ": "ي"})

ARABIC_MONTHS = {
    # Gregorian month names as used in the Gulf (Levantine names in brackets are not used here)
    "يناير": 1, "فبراير": 2, "مارس": 3, "أبريل": 4, "ابريل": 4, "إبريل": 4, "مايو": 5, "يونيو": 6,
    "يوليو": 7, "أغسطس": 8, "اغسطس": 8, "سبتمبر": 9, "أكتوبر": 10, "اكتوبر": 10, "نوفمبر": 11, "ديسمبر": 12,
}


def to_western_digits(text: str) -> str:
    return str(text).translate(DIGITS)


def to_arabic_indic(text: str) -> str:
    return str(text).translate(TO_ARABIC_INDIC)


def strip_marks(text: str) -> str:
    return BIDI_CONTROLS.sub("", TASHKEEL.sub("", str(text)).replace(TATWEEL, ""))


def normalise_text(text) -> str:
    """Fold everything that shouldn't count as a difference, then drop spaces and punctuation."""
    t = strip_marks(to_western_digits(text)).translate(LETTER_FOLD).lower()
    t = t.replace("٫", ".").replace("٬", "").replace("،", ",")
    return re.sub(r"[\s\W_]+", "", t)


def parse_number(value):
    """A number from an int/float or from text such as '١٬٢٥٠٫٥٠', '1,250.50 AED' or '1 250,50'.

    Returns None when there is no number in it."""
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    t = to_western_digits(strip_marks(value)).replace("٬", ",").replace("٫", ".")
    m = re.search(r"-?\d[\d,\s]*(?:\.\d+)?", t)
    if not m:
        return None
    raw = re.sub(r"[\s,]", "", m.group(0))
    try:
        return float(raw)
    except ValueError:
        return None


def parse_date(value):
    """An ISO date string from ISO text, DD/MM/YYYY, or '15 أكتوبر 2026'. None if it can't tell."""
    if value is None:
        return None
    t = to_western_digits(strip_marks(value)).strip()
    m = re.fullmatch(r"(\d{4})-(\d{1,2})-(\d{1,2})", t)
    if m:
        y, mo, d = map(int, m.groups())
    else:
        m = re.fullmatch(r"(\d{1,2})[/.\-](\d{1,2})[/.\-](\d{4})", t)
        if m:
            d, mo, y = map(int, m.groups())
        else:
            m = re.fullmatch(r"(\d{1,2})\s+(\S+)\s+(\d{4})", t)
            if not m or m.group(2) not in ARABIC_MONTHS:
                return None
            d, y, mo = int(m.group(1)), int(m.group(3)), ARABIC_MONTHS[m.group(2)]
    try:
        return date(y, mo, d).isoformat()
    except ValueError:
        return None
