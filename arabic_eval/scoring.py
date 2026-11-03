"""Per-field scoring against ground truth: exact match and normalised match.

exact       the value is exactly the canonical answer: same characters for text,
            the same number, the same YYYY-MM-DD string for dates.
normalised  the same thing read correctly, written a little differently: Arabic
            letter forms, vowel marks, digit style, spaces and punctuation folded
            for text; numbers equal to the cent; any parseable date that is the same day.

The gap between the two shows how much clean-up a client would need downstream.
"""
from __future__ import annotations

from .normalize import normalise_text, parse_date, parse_number


def exact_match(expected, got) -> bool:
    if got is None:
        return expected is None
    if isinstance(expected, (int, float)) and not isinstance(expected, bool):
        return isinstance(got, (int, float)) and not isinstance(got, bool) and float(got) == float(expected)
    return isinstance(got, str) and got == expected


def normalised_match(expected, got, ftype: str) -> bool:
    if got is None or expected is None:
        return got is None and expected is None
    if ftype == "number":
        n = parse_number(got)
        return n is not None and abs(n - float(expected)) < 0.005
    if ftype == "date":
        return parse_date(str(got)) == expected
    return normalise_text(got) == normalise_text(expected)


def score_document(expected: dict, result: dict, schema) -> dict:
    flagged = {r["field"] for r in result.get("needs_review", [])}
    rows = []
    for spec in schema.fields:
        want = expected[spec.name]
        got = result["fields"][spec.name]["value"]
        norm = normalised_match(want, got, spec.type)
        rows.append({"field": spec.name, "expected": want, "got": got,
                     "confidence": result["fields"][spec.name]["confidence"],
                     "exact": exact_match(want, got), "normalised": norm,
                     "flagged": spec.name in flagged})
    return {
        "rows": rows, "total": len(rows),
        "exact": sum(r["exact"] for r in rows),
        "normalised": sum(r["normalised"] for r in rows),
        "wrong_flagged": sum(not r["normalised"] and r["flagged"] for r in rows),
        "wrong_unflagged": sum(not r["normalised"] and not r["flagged"] for r in rows),
        "flagged": len(flagged),
    }
