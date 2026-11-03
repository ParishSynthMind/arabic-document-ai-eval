from arabic_eval.extract import load_schema
from arabic_eval.scoring import exact_match, normalised_match, score_document


def test_exact_vs_normalised():
    assert exact_match("شركة الواحة", "شركة الواحة")
    assert not exact_match("شركة الواحة", "شركة الواحه")
    assert normalised_match("شركة الواحة", "شركة الواحه", "string")
    assert normalised_match("100234567800003", "١٠٠٢٣٤٥٦٧٨٠٠٠٠٣", "string")
    assert not exact_match("100234567800003", "١٠٠٢٣٤٥٦٧٨٠٠٠٠٣")
    assert normalised_match(6615.0, "٦٬٦١٥٫٠٠", "number") and not exact_match(6615.0, "٦٬٦١٥٫٠٠")
    assert exact_match(6615.0, 6615)
    assert normalised_match("2026-10-15", "15/10/2026", "date")
    assert not normalised_match("2026-10-15", "2026-10-16", "date")
    assert not normalised_match("abc", None, "string")


def test_score_document_counts_flags():
    schema = load_schema("receipt_ar")
    expected = {"merchant_name": "بقالة الخير", "receipt_number": "5531", "receipt_date": "2026-11-02",
                "payment_method": "cash", "vat_amount": 3.0, "total_amount": 63.0}
    got = {k: {"value": v, "confidence": "high"} for k, v in expected.items()}
    got["total_amount"] = {"value": 36.0, "confidence": "low"}
    got["vat_amount"] = {"value": 30.0, "confidence": "high"}
    s = score_document(expected, {"fields": got, "needs_review": [{"field": "total_amount", "reason": "x"}]}, schema)
    assert s["normalised"] == 4 and s["exact"] == 4
    assert s["wrong_flagged"] == 1 and s["wrong_unflagged"] == 1
