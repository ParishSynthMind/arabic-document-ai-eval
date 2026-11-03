from pathlib import Path

from arabic_eval.chat import HUMAN_OK_AR, build_bots
from arabic_eval.kb_ar import stem_ar, tokenize
from arabic_eval.rubric import arabic_share, facts_ok, language_ok, status_ok
from fakes import FakeClient
from vendor.support_chatbot import kb as base_kb

ROOT = Path(__file__).resolve().parent.parent
KB = ROOT / "chatbot" / "knowledge_base_ar"


def test_original_tokenizer_sees_no_arabic():
    assert base_kb.tokenize("كم سعر تنظيف المكيف؟") == []
    assert tokenize("كم سعر تنظيف المكيفات؟") == ["سعر", "تنظيف", "مكيف"]


def test_light_stemmer():
    assert stem_ar("المكيفات") == "مكيف"
    assert stem_ar("ولد") == "ولد"  # short word: single-letter prefix not stripped


def test_arabic_retrieval_finds_section():
    bots = build_bots(KB, "Test", client=FakeClient())
    assert bots["original"].kb.search("كم سعر تنظيف المكيف السبليت؟") == []
    assert bots["arabic-search"].kb.search("كم سعر تنظيف المكيف السبليت؟")[0].chunk.heading == "تنظيف المكيفات"


def test_original_bot_never_calls_model_for_arabic():
    client = FakeClient()
    r = build_bots(KB, "Test", client=client)["original"].chat("هل تعملون يوم الجمعة؟")
    assert r.status == "not_in_knowledge_base" and not r.model_called and client.calls == []


def test_arabic_human_request_is_free_and_answered_in_arabic():
    client = FakeClient()
    bots = build_bots(KB, "Test", client=client)
    assert bots["arabic-search"].chat("أبي أكلم موظف لو سمحت").status != "handover"
    r = bots["arabic-full"].chat("أبي أكلم موظف لو سمحت")
    assert r.status == "handover" and r.reply == HUMAN_OK_AR and client.calls == []


def test_citations_checked_and_language_rule_sent():
    client = FakeClient({"status": "answered", "answer": "150 درهم للوحدة.", "citations": [1, 99]})
    r = build_bots(KB, "Test", client=client)["arabic-full"].chat("كم سعر تنظيف المكيف؟")
    assert r.status == "answered" and len(r.citations) == 1  # 99 dropped: not a section we sent
    assert "same language as the visitor" in client.calls[0]["system"]


def test_answered_without_valid_citation_becomes_dont_know():
    client = FakeClient({"status": "answered", "answer": "نعم", "citations": []})
    r = build_bots(KB, "Test", client=client)["arabic-search"].chat("كم سعر تنظيف المكيف؟")
    assert r.status == "not_in_knowledge_base"


def test_small_kb_fallback_lets_english_question_through():
    client = FakeClient({"status": "answered", "answer": "Yes, 199 AED.", "citations": [3]})
    bots = build_bots(KB, "Test", client=client)
    assert bots["arabic-search"].chat("Emergency plumber at the weekend?").status == "not_in_knowledge_base"
    r = bots["arabic-full"].chat("Emergency plumber at the weekend?")
    assert r.model_called and len(r.retrieved) == len(bots["arabic-full"].kb.chunks)


def test_rubric_helpers():
    assert arabic_share("مرحبا hello") > 0.4
    assert language_ok("السعر 150 درهم", "ar") and language_ok("It costs 150 AED", "en")
    assert facts_ok("التكلفة ٤٥٠ درهماً", [["450"]])
    assert not facts_ok("التكلفة 400", [["450"]])
    assert status_ok("handover", ["needs_human"])
