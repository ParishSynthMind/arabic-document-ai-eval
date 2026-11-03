"""Live chatbot run: 15 questions (14 Arabic, 1 English) x 3 configurations, scored on a 4-point rubric.

    python scripts/run_chat_eval.py                 # runs what isn't saved yet, then scores
    python scripts/run_chat_eval.py --score-only    # rebuild the tables from saved replies

Each reply and its grade are saved to results/chat/<config>/<question>.json as soon as they
arrive, so a crashed run resumes. Also writes the offline retrieval check (no API calls).
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from arabic_eval.chat import ChatReply, build_bots  # noqa: E402
from arabic_eval.rubric import Judge, score  # noqa: E402

KB = ROOT / "chatbot" / "knowledge_base_ar"
COMPANY = "Nakhla Home Maintenance (نخلة للصيانة المنزلية)"
OUT = ROOT / "results" / "chat"
CONFIGS = ["original", "arabic-search", "arabic-full"]
PRICE_IN, PRICE_OUT = 2.00, 10.00


def retrieval_check(bots, questions) -> str:
    lines = ["| Question | Kind | Expected section | original: top hit | arabic: top hit |", "|---|---|---|---|---|"]
    found = {"original": 0, "arabic-search": 0}
    answerable = [q for q in questions if q["section"]]
    for q in questions:
        tops = {}
        for name in ("original", "arabic-search"):
            hits = bots[name].kb.search(q["question"], 5)
            tops[name] = hits[0].chunk.heading if hits else "(no hits)"
            if q["section"] and any(h.chunk.heading == q["section"] for h in hits):
                found[name] += 1
        lines.append(f"| {q['id']} | {q['kind']} | {q['section'] or '-'} | {tops['original']} | {tops['arabic-search']} |")
    lines.append(f"\nExpected section in the top 5: original {found['original']}/{len(answerable)}, "
                 f"Arabic tokenizer {found['arabic-search']}/{len(answerable)}.")
    return "\n".join(lines)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--score-only", action="store_true")
    args = ap.parse_args(argv)
    questions = json.loads((ROOT / "chatbot" / "questions.json").read_text(encoding="utf-8"))
    kb_text = "\n\n".join(p.read_text(encoding="utf-8") for p in sorted(KB.glob("*.md")))
    client = None
    if not args.score_only:
        import anthropic

        client = anthropic.Anthropic()
    bots = build_bots(KB, COMPANY, client=client or object())
    judge = Judge(kb_text, client=client) if client else None
    for name in CONFIGS:
        (OUT / name).mkdir(parents=True, exist_ok=True)
        for q in questions:
            path = OUT / name / f"{q['id']}.json"
            if path.exists() or args.score_only:
                continue
            reply = bots[name].chat(q["question"])
            if reply.model_called:
                grounded, reason = judge.grounded(q["question"], reply.reply)
            else:
                grounded, reason = True, "fixed reply, no claims"
            rec = {"question": q, "config": name, "reply": asdict(reply), "grounded": grounded, "judge_reason": reason}
            path.write_text(json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"{name:14} {q['id']} {reply.status:22} {reply.reply[:70]}", flush=True)
    if client:
        calls = sum(b.answerer.usage["calls"] for b in bots.values()) + judge.usage["calls"]
        tin = sum(b.answerer.usage["input_tokens"] for b in bots.values()) + judge.usage["input_tokens"]
        tout = sum(b.answerer.usage["output_tokens"] for b in bots.values()) + judge.usage["output_tokens"]
        print(f"this run: {calls} calls, {tin} in / {tout} out tokens, about ${tin / 1e6 * PRICE_IN + tout / 1e6 * PRICE_OUT:.2f}")

    rows, totals = [], {}
    for q in questions:
        cells = []
        for name in CONFIGS:
            rec = json.loads((OUT / name / f"{q['id']}.json").read_text(encoding="utf-8"))
            s = score(q, ChatReply(**rec["reply"]), rec["grounded"])
            t = totals.setdefault(name, {"status": 0, "language": 0, "facts": 0, "grounded": 0, "total": 0})
            for k in t:
                t[k] += s[k]
            cells.append(f"{s['total']}/4")
        rows.append(f"| {q['id']} | {q['kind']} | " + " | ".join(cells) + " |")
    n = len(questions)
    md = ["## Rubric totals", "", "| Configuration | Right route | Right language | Required facts | Grounded | **Score** |", "|---|---|---|---|---|---|"]
    for name in CONFIGS:
        t = totals[name]
        md.append(f"| {name} | {t['status']}/{n} | {t['language']}/{n} | {t['facts']}/{n} | {t['grounded']}/{n} | "
                  f"**{t['total']}/{4 * n} ({t['total'] / (4 * n):.0%})** |")
    md += ["", "## Per question", "", "| Question | Kind | " + " | ".join(CONFIGS) + " |", "|---|---|" + "---|" * len(CONFIGS)] + rows
    md += ["", "## Retrieval check (offline, no API calls)", "", retrieval_check(bots, questions)]
    text = "\n".join(md) + "\n"
    (ROOT / "results" / "chat_results.md").write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
