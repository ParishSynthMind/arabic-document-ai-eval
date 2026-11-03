"""Offline OCR check (no API calls): what share of each document's words does each OCR setting recover?

    python scripts/ocr_word_recall.py            # writes results/ocr_word_recall.{json,md}

Word recall = ground-truth words found in the OCR output (as a multiset), after
Arabic normalisation (digits, alef forms, tashkeel). Word order is ignored, so a
correctly read word on the "wrong" side of a right-to-left line still counts.
Also reports the same for the PDF text layer, raw and with the RTL fix.
"""
from __future__ import annotations

import json
import sys
import time
from collections import Counter
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from arabic_eval.normalize import normalise_text  # noqa: E402
from arabic_eval.ocr import OCR_SETTINGS, ocr  # noqa: E402
from arabic_eval.pdftext import pdf_text  # noqa: E402

DATA = ROOT / "dataset"


def words(text: str) -> Counter:
    return Counter(w for w in (normalise_text(t) for t in text.split()) if w)


def recall(truth: str, got: str) -> float:
    t, g = words(truth), words(got)
    return sum(min(n, g[w]) for w, n in t.items()) / max(1, sum(t.values()))


def main() -> int:
    gt = json.loads((DATA / "ground_truth.json").read_text(encoding="utf-8"))
    out_dir = ROOT / "results" / "ocr_text"
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    for doc_id, meta in gt.items():
        truth = (DATA / "text" / f"{doc_id}.txt").read_text(encoding="utf-8")
        row = {"doc": doc_id, "render": meta["render"]}
        img = Image.open(DATA / "images" / f"{doc_id}.png")
        for setting in OCR_SETTINGS:
            t0 = time.time()
            text = ocr(img, setting)
            (out_dir / f"{doc_id}.{setting}.txt").write_text(text, encoding="utf-8")
            row[setting] = round(recall(truth, text), 3)
            row[f"{setting}_secs"] = round(time.time() - t0, 1)
        for name, fix in (("pdf-raw", False), ("pdf-fixed", True)):
            text = pdf_text(DATA / "pdf" / f"{doc_id}.pdf", fix_rtl=fix)
            (out_dir / f"{doc_id}.{name}.txt").write_text(text, encoding="utf-8")
            row[name] = round(recall(truth, text), 3)
        rows.append(row)
        print(doc_id, {k: v for k, v in row.items() if not k.endswith("secs")}, flush=True)
    cols = list(OCR_SETTINGS) + ["pdf-raw", "pdf-fixed"]
    (ROOT / "results" / "ocr_word_recall.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    md = ["| Document | Render | " + " | ".join(cols) + " |", "|---|---|" + "---|" * len(cols)]
    for r in rows:
        md.append(f"| {r['doc']} | {r['render']} | " + " | ".join(f"{r[c]:.0%}" for c in cols) + " |")
    md.append("| **Average** | | " + " | ".join(f"**{sum(r[c] for r in rows) / len(rows):.0%}**" for c in cols) + " |")
    secs = " · ".join(f"{s}: {sum(r[s + '_secs'] for r in rows) / len(rows):.1f}s" for s in OCR_SETTINGS)
    md.append(f"\nAverage OCR time per page: {secs}")
    (ROOT / "results" / "ocr_word_recall.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
