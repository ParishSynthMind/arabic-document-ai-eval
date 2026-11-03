"""Live extraction run: every document through every input path, scored per field.

    python scripts/run_extraction_eval.py                  # all methods, all documents
    python scripts/run_extraction_eval.py --methods vision --docs inv01_ar_western
    python scripts/run_extraction_eval.py --score-only     # rebuild the tables from saved results

Methods (how the document reaches Claude):
  pdf-raw     PDF text layer as pdfplumber returns it (ai-document-extractor's default for digital PDFs)
  pdf-fixed   the same text with the right-to-left fix (bidi reordering)
  ocr-eng     page image -> Tesseract English only (ai-document-extractor's default for scans)
  ocr-ara     page image -> Tesseract Arabic + English (tessdata_best)
  ocr-prep    page image -> preprocessing -> Tesseract Arabic + English
  vision      page image straight to Claude, no OCR

Every raw model reply is saved to results/extraction/<method>/<doc>.json as soon as it
arrives, and an existing file is never re-requested, so a crashed run resumes where it
stopped and re-scoring costs nothing. Needs ANTHROPIC_API_KEY for anything not yet saved.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from arabic_eval.extract import ArabicExtractor, check, load_schema  # noqa: E402
from arabic_eval.ocr import ocr  # noqa: E402
from arabic_eval.pdftext import pdf_text  # noqa: E402
from arabic_eval.scoring import score_document  # noqa: E402

DATA = ROOT / "dataset"
OUT = ROOT / "results" / "extraction"
METHODS = ["pdf-raw", "pdf-fixed", "ocr-eng", "ocr-ara", "ocr-prep", "vision"]
OCR_SETTING = {"ocr-eng": "eng", "ocr-ara": "ara-best", "ocr-prep": "ara-prep"}
PRICE_IN, PRICE_OUT = 2.00, 10.00  # USD per million tokens, Claude Sonnet 5.5 list price


def document_text(method: str, doc_id: str):
    if method == "vision":
        return None
    if method.startswith("pdf"):
        return pdf_text(DATA / "pdf" / f"{doc_id}.pdf", fix_rtl=(method == "pdf-fixed"))
    return ocr(Image.open(DATA / "images" / f"{doc_id}.png"), OCR_SETTING[method])


def run(methods, docs, gt) -> None:
    extractor = None
    for method in methods:
        (OUT / method).mkdir(parents=True, exist_ok=True)
        for doc_id in docs:
            path = OUT / method / f"{doc_id}.json"
            if path.exists():
                continue
            extractor = extractor or ArabicExtractor()
            schema = load_schema(gt[doc_id]["schema"])
            text = document_text(method, doc_id)
            t0 = time.time()
            before = dict(extractor.usage)
            try:
                raw = (extractor.from_image(DATA / "images" / f"{doc_id}.png", schema) if text is None
                       else extractor.from_text(text, schema))
                error = None
            except Exception as e:  # recorded, not hidden: a failed call scores as all-wrong
                raw, error = {}, f"{type(e).__name__}: {e}"
            record = {"doc": doc_id, "method": method, "model": extractor.model, "raw": raw, "error": error,
                      "document_text": text, "seconds": round(time.time() - t0, 1),
                      "input_tokens": extractor.usage["input_tokens"] - before["input_tokens"],
                      "output_tokens": extractor.usage["output_tokens"] - before["output_tokens"]}
            path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"{method:9} {doc_id:28} {record['seconds']:5}s {'ERROR ' + error if error else 'ok'}", flush=True)
    if extractor:
        u = extractor.usage
        cost = u["input_tokens"] / 1e6 * PRICE_IN + u["output_tokens"] / 1e6 * PRICE_OUT
        print(f"this run: {u['calls']} calls, {u['input_tokens']} in / {u['output_tokens']} out tokens, about ${cost:.2f}")


def score_all(methods, docs, gt) -> dict:
    per = {}
    for method in methods:
        for doc_id in docs:
            path = OUT / method / f"{doc_id}.json"
            if not path.exists():
                continue
            rec = json.loads(path.read_text(encoding="utf-8"))
            schema = load_schema(gt[doc_id]["schema"])
            s = score_document(gt[doc_id]["fields"], check(rec["raw"], schema, rec["document_text"], extra_checks=False), schema)
            plus = score_document(gt[doc_id]["fields"], check(rec["raw"], schema, rec["document_text"]), schema)
            s.update(plus_flagged=plus["flagged"], plus_wrong_unflagged=plus["wrong_unflagged"], plus_rows=plus["rows"])
            s.update(doc=doc_id, method=method, error=rec["error"],
                     input_tokens=rec["input_tokens"], output_tokens=rec["output_tokens"], seconds=rec["seconds"])
            per[(method, doc_id)] = s
    return per


def tables(per: dict, methods, docs, gt) -> str:
    pct = lambda a, b: f"{a / b:.0%}" if b else "-"
    out = ["## Accuracy by method (all documents)", "",
           "Review columns: base = ai-document-extractor's checks; +checks = with the Arabic checks added (totals add up, uncertain IDs from images, amounts reviewed together).", "",
           "| Method | Fields | Exact match | Normalised match | Sent to review (base) | Wrong, not flagged (base) | Sent to review (+checks) | Wrong, not flagged (+checks) | Avg cost per doc |",
           "|---|---|---|---|---|---|---|---|---|"]
    for m in methods:
        rows = [per[(m, d)] for d in docs if (m, d) in per]
        if not rows:
            continue
        t = sum(r["total"] for r in rows)
        cost = sum(r["input_tokens"] / 1e6 * PRICE_IN + r["output_tokens"] / 1e6 * PRICE_OUT for r in rows) / len(rows)
        out.append(f"| {m} | {t} | {pct(sum(r['exact'] for r in rows), t)} | **{pct(sum(r['normalised'] for r in rows), t)}** | "
                   f"{sum(r['flagged'] for r in rows)} | {sum(r['wrong_unflagged'] for r in rows)} | "
                   f"{sum(r['plus_flagged'] for r in rows)} | **{sum(r['plus_wrong_unflagged'] for r in rows)}** | ${cost:.3f} |")
    out += ["", "## Normalised accuracy per document", "",
            "| Document | Variant | " + " | ".join(methods) + " |", "|---|---|" + "---|" * len(methods)]
    for d in docs:
        cells = []
        for m in methods:
            r = per.get((m, d))
            cells.append(f"{r['normalised']}/{r['total']}" if r else "-")
        out.append(f"| {d} | {gt[d]['note']} | " + " | ".join(cells) + " |")
    fields = {}
    for (m, d), r in per.items():
        for row in r["rows"]:
            f = fields.setdefault(row["field"], {})
            a = f.setdefault(m, [0, 0])
            a[0] += row["normalised"]
            a[1] += 1
    out += ["", "## Normalised accuracy per field", "", "| Field | " + " | ".join(methods) + " |", "|---|" + "---|" * len(methods)]
    for name, by in fields.items():
        out.append(f"| {name} | " + " | ".join(pct(*by[m]) if m in by else "-" for m in methods) + " |")
    return "\n".join(out) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--methods", nargs="*", default=METHODS)
    ap.add_argument("--docs", nargs="*")
    ap.add_argument("--score-only", action="store_true")
    ap.add_argument("--holdout", action="store_true", help="the 4 documents made after the Arabic checks were written")
    args = ap.parse_args(argv)
    global OUT
    name = "extraction_holdout" if args.holdout else "extraction"
    OUT = ROOT / "results" / name
    gt = json.loads((DATA / ("ground_truth_holdout.json" if args.holdout else "ground_truth.json")).read_text(encoding="utf-8"))
    docs = args.docs or list(gt)
    if not args.score_only:
        run(args.methods, docs, gt)
    methods = [m for m in METHODS if (OUT / m).exists()]
    per = score_all(methods, list(gt), gt)
    md = tables(per, methods, list(gt), gt)
    (ROOT / "results" / f"{name}_results.md").write_text(md, encoding="utf-8")
    detail = [dict(r, rows=r["rows"]) for r in per.values()]
    (ROOT / "results" / f"{name}_scores.json").write_text(json.dumps(detail, ensure_ascii=False, indent=2), encoding="utf-8")
    print(md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
