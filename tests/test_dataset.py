import json
from pathlib import Path

from docgen import specs

ROOT = Path(__file__).resolve().parent.parent


def test_ground_truth_matches_specs_and_files():
    gt = json.loads((ROOT / "dataset" / "ground_truth.json").read_text(encoding="utf-8"))
    assert gt == json.loads(json.dumps(specs.ground_truth(), ensure_ascii=False))
    assert len(gt) >= 12
    for doc_id in gt:
        for sub, ext in (("pdf", "pdf"), ("images", "png"), ("text", "txt")):
            assert (ROOT / "dataset" / sub / f"{doc_id}.{ext}").exists()


def test_invoice_totals_add_up():
    for s in specs.INVOICES:
        sub, vat, tot = specs.invoice_totals(s)
        assert abs(sub + vat - tot) < 0.005
        assert abs(vat - sub * s["vat_rate"] / 100) < 0.006
