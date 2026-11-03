"""The support chatbot's /chat decision path, run in three configurations.

This mirrors website-support-chatbot's app/main.py chat() step for step
(human-request check, retrieval, "no hits means I don't know", model call,
server-side citation check) without the web server, rate limits or database,
so the Arabic changes can be measured on their own:

  original        the chatbot exactly as published: English tokenizer, English
                  human-request phrases, original system prompt
  arabic-search   only the Arabic tokenizer swapped in
  arabic-full     Arabic tokenizer, plus Arabic human-request phrases, a rule to
                  reply in the visitor's language, and a small-knowledge-base
                  fallback (no keyword hits -> give the model every section, which
                  lets an English question be answered from Arabic docs)
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from vendor.support_chatbot import guardrails, kb as base_kb
from vendor.support_chatbot.llm import SYSTEM_PROMPT as BASE_PROMPT
from vendor.support_chatbot.llm import ClaudeAnswerer

from .kb_ar import ArabicKnowledgeBase, tokenize as ar_tokenize

# The chatbot's own fixed replies (app/main.py), with Arabic versions for arabic-full.
DONT_KNOW = "I don't have that in our help docs. Would you like me to pass your question to the team?"
HUMAN_OK = "Of course. Leave your name, email and question, and a person from the team will get back to you."
DONT_KNOW_AR = "لا تتوفر لدي هذه المعلومة في مستندات المساعدة. هل تريد أن أحوّل سؤالك إلى الفريق؟"
HUMAN_OK_AR = "بالتأكيد. اترك اسمك وبريدك الإلكتروني وسؤالك، وسيتواصل معك أحد أفراد الفريق."

# Arabic (MSA and Gulf) ways of asking for a person. Checked before any model call, like the English list.
HUMAN_REQUEST_AR = re.compile(
    r"(موظف|انسان|إنسان|شخص حقيقي|خدمة العملاء|ممثل|"
    r"(ا|أ)(كلم|تكلم|حاكي|تواصل)\s*(مع)?\s*(احد|أحد|حد|شخص|موظف|الفريق|الدعم)|اتصلوا\s*(بي|علي|عليّ))"
)

LANGUAGE_RULE = """

Language: reply in the same language as the visitor's question (Arabic question -> Arabic answer, \
English question -> English answer), even when the knowledge base is in a different language. For Arabic, \
use clear Modern Standard Arabic that a Gulf customer reads naturally, and write numbers with Western digits."""

SMALL_KB_CHARS = 8000


class ArabicAwareAnswerer(ClaudeAnswerer):
    """The chatbot's ClaudeAnswerer with the language rule added to its system prompt."""

    def __init__(self, company: str, extra_rule: str = "", **kw):
        super().__init__(company, **kw)
        self.extra_rule = extra_rule
        self.usage = {"calls": 0, "input_tokens": 0, "output_tokens": 0}

    def answer(self, question, history, hits):
        import vendor.support_chatbot.llm as llm_mod

        original = llm_mod.SYSTEM_PROMPT
        llm_mod.SYSTEM_PROMPT = BASE_PROMPT + self.extra_rule
        try:
            result = super().answer(question, history, hits)
        finally:
            llm_mod.SYSTEM_PROMPT = original
        self.usage["calls"] += 1
        self.usage["input_tokens"] += result.input_tokens
        self.usage["output_tokens"] += result.output_tokens
        return result


@dataclass
class ChatReply:
    status: str  # answered | not_in_knowledge_base | needs_human | handover
    reply: str
    citations: list = field(default_factory=list)
    model_called: bool = False
    retrieved: list = field(default_factory=list)


@dataclass
class Bot:
    name: str
    kb: base_kb.KnowledgeBase
    answerer: object
    arabic_human_check: bool = False
    small_kb_fallback: bool = False
    arabic_fixed_replies: bool = False
    top_k: int = 5

    def chat(self, message: str, history=()) -> ChatReply:
        message = guardrails.clean_text(message)
        arabic = self.arabic_fixed_replies and bool(re.search(r"[؀-ۿ]", message))
        if guardrails.wants_human(message) or (self.arabic_human_check and HUMAN_REQUEST_AR.search(message)):
            return ChatReply("handover", HUMAN_OK_AR if arabic else HUMAN_OK)
        hits = self.kb.search(message, self.top_k)
        if not hits and self.small_kb_fallback and sum(len(c.text) for c in self.kb.chunks) <= SMALL_KB_CHARS:
            hits = [base_kb.Hit(c, 0.0) for c in self.kb.chunks]
            self.answerer.max_sections = max(self.answerer.max_sections, len(hits))
        if not hits:
            return ChatReply("not_in_knowledge_base", DONT_KNOW_AR if arabic else DONT_KNOW)
        result = self.answerer.answer(message, list(history), hits)
        retrieved = [h.chunk.heading for h in hits]
        citations = []
        for i in dict.fromkeys(result.citations):
            if isinstance(i, int) and 1 <= i <= len(hits):
                c = {"source": hits[i - 1].chunk.source, "heading": hits[i - 1].chunk.heading}
                if c not in citations:
                    citations.append(c)
        if result.status == "answered" and citations:
            return ChatReply("answered", result.answer, citations, True, retrieved)
        if result.status == "needs_human":
            return ChatReply("needs_human", result.answer or HUMAN_OK, [], True, retrieved)
        text = result.answer if result.status == "not_in_knowledge_base" and result.answer else DONT_KNOW
        return ChatReply("not_in_knowledge_base", text, [], True, retrieved)


def build_bots(kb_dir: Path, company: str, client=None) -> dict:
    original_kb = ArabicKnowledgeBase.from_dir(kb_dir, tokenize_fn=base_kb.tokenize)  # same BM25, original tokenizer
    arabic_kb = ArabicKnowledgeBase.from_dir(kb_dir, tokenize_fn=ar_tokenize)
    return {
        "original": Bot("original", original_kb, ArabicAwareAnswerer(company, client=client)),
        "arabic-search": Bot("arabic-search", arabic_kb, ArabicAwareAnswerer(company, client=client)),
        "arabic-full": Bot("arabic-full", arabic_kb, ArabicAwareAnswerer(company, LANGUAGE_RULE, client=client),
                           arabic_human_check=True, small_kb_fallback=True, arabic_fixed_replies=True),
    }
