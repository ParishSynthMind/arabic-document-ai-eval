"""Arabic-aware search for the support chatbot's knowledge base.

The chatbot's BM25 tokenizer only keeps [a-z0-9] runs, so an Arabic question
produces no search terms at all, retrieval returns nothing, and the bot says
"I don't know" without ever asking the model. This module adds an Arabic
tokenizer and plugs it into the same BM25 class:

- letters are normalised (alef forms, taa marbuta, alef maqsura, tashkeel,
  tatweel, Arabic-Indic digits) so spelling variants match;
- light stemming strips one common prefix (و, ال, بال, لل, ...) and one
  common suffix (ات, ون, ين, ها, ...), so "المكيفات" and "مكيف" meet;
- a short list of Arabic function words is dropped;
- English words still go through the original tokenizer.

It is a light stemmer, not a morphological analyser: it will not join broken
plurals (e.g. فني / فنيين works, but غرفة / غرف only through the prefix rule).
"""
from __future__ import annotations

import math
import re
from collections import Counter
from pathlib import Path
from typing import List

from vendor.support_chatbot import kb as base_kb

from .normalize import LETTER_FOLD, strip_marks, to_western_digits

AR_STOPWORDS = {
    "في", "من", "علي", "على", "الي", "إلى", "الى", "عن", "مع", "هل", "ما", "ماذا", "كم", "كيف", "متي", "متى", "اين",
    "هو", "هي", "انا", "انت", "نحن", "انتم", "هذا", "هذه", "ذلك", "تلك", "التي", "الذي", "اللي", "او", "ثم", "لو",
    "ان", "انه", "كان", "كانت", "يوجد", "توجد", "فيه", "في", "عند", "عندي", "عندكم", "لي", "لكم", "شو", "ابي", "ابغي",
    "سماحت", "سمحت", "بعد", "قبل", "كل", "اي", "ايش", "وش", "لا", "نعم", "ال",
}
AR_STOPWORDS = {w.translate(LETTER_FOLD) for w in AR_STOPWORDS}

PREFIXES = ("وال", "بال", "كال", "فال", "لل", "ال", "و", "ب", "ل")
SUFFIXES = ("ات", "ون", "ين", "ان", "ها", "هم", "كم", "نا", "يه", "ه", "ي")
ARABIC_WORD = re.compile(r"[ء-ي٠-٩ٮ-ۓ]+")


def normalise_word(w: str) -> str:
    return strip_marks(to_western_digits(w)).translate(LETTER_FOLD)


def stem_ar(w: str) -> str:
    for p in PREFIXES:
        # single-letter prefixes (و ب ل) only when a long word remains, so "ولد" stays "ولد"
        if w.startswith(p) and len(w) - len(p) >= (3 if len(p) > 1 else 4):
            w = w[len(p):]
            break
    for s in SUFFIXES:
        if w.endswith(s) and len(w) - len(s) >= 3:
            w = w[: -len(s)]
            break
    return w


def tokenize(text: str) -> List[str]:
    clean = strip_marks(to_western_digits(text))
    out = []
    for m in ARABIC_WORD.findall(clean):
        w = normalise_word(m)
        if len(w) < 2 or w in AR_STOPWORDS:
            continue
        out.append(stem_ar(w))
    out.extend(base_kb.tokenize(clean))  # English words and numbers, unchanged behaviour
    return out


class ArabicKnowledgeBase(base_kb.KnowledgeBase):
    """The chatbot's BM25 knowledge base, indexing and searching with `tokenize_fn`.

    The base class calls its module-level tokenizer directly, so the two methods
    that tokenize are repeated here with the tokenizer as a parameter. The BM25
    maths is the same."""

    def __init__(self, chunks, k1: float = 1.5, b: float = 0.75, tokenize_fn=tokenize):
        self.tokenize_fn = tokenize_fn
        self.chunks = chunks
        self.k1, self.b = k1, b
        self._tokens = [tokenize_fn(c.text) for c in chunks]
        self._tf = [Counter(t) for t in self._tokens]
        n = len(chunks)
        self._avgdl = (sum(len(t) for t in self._tokens) / n) if n else 0.0
        df = Counter()
        for toks in self._tokens:
            df.update(set(toks))
        self._idf = {term: math.log(1 + (n - d + 0.5) / (d + 0.5)) for term, d in df.items()}

    @classmethod
    def from_dir(cls, directory: Path, tokenize_fn=tokenize) -> "ArabicKnowledgeBase":
        chunks = []
        for path in sorted(Path(directory).glob("*.md")):
            chunks.extend(base_kb.chunk_markdown(path.read_text(encoding="utf-8"), path.name))
        if not chunks:
            raise RuntimeError(f"No markdown documents found in {directory}")
        return cls(chunks, tokenize_fn=tokenize_fn)

    def search(self, query: str, k: int = 4):
        terms = self.tokenize_fn(query)
        hits = []
        for i, tf in enumerate(self._tf):
            dl = len(self._tokens[i])
            score = 0.0
            for term in terms:
                f = tf.get(term)
                if not f:
                    continue
                idf = self._idf.get(term, 0.0)
                score += idf * f * (self.k1 + 1) / (f + self.k1 * (1 - self.b + self.b * dl / self._avgdl))
            if score > 0:
                hits.append(base_kb.Hit(self.chunks[i], score))
        hits.sort(key=lambda h: h.score, reverse=True)
        return hits[:k]
