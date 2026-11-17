"""EU AI Act Art. 50: the chat surface says it is an AI on the first reply and on every handover."""
from pathlib import Path

from arabic_eval.chat import HUMAN_OK, HUMAN_OK_AR, Disclosure, build_bots
from fakes import FakeClient

KB = Path(__file__).resolve().parent.parent / "chatbot" / "knowledge_base_ar"
EN = "I'm an AI assistant for Test."
AR = "أنا مساعد ذكاء اصطناعي لدى Test."
ANSWER = {"status": "answered", "answer": "150 درهم للوحدة.", "citations": [1]}


def bots(*replies, disclosure=None):
    return build_bots(KB, "Test", client=FakeClient(*replies), disclosure=disclosure or Disclosure())


def test_first_reply_discloses_then_not_again():
    bot = bots(ANSWER, ANSWER)["arabic-full"]
    first = bot.chat("كم سعر تنظيف المكيف؟", conversation_id="c1")
    assert first.disclosure == AR and first.text.startswith(AR) and first.reply == "150 درهم للوحدة."
    second = bot.chat("كم سعر تنظيف المكيف؟", conversation_id="c1")
    assert second.disclosure == "" and second.text == "150 درهم للوحدة."


def test_new_or_reset_conversation_discloses_again():
    bot = bots(ANSWER, ANSWER, ANSWER, ANSWER)["arabic-full"]
    bot.chat("كم سعر تنظيف المكيف؟", conversation_id="c1")
    assert bot.chat("كم سعر تنظيف المكيف؟", conversation_id="c2").disclosure == AR   # new session id
    bot.forget("c1")                                                                    # store reset
    assert bot.chat("كم سعر تنظيف المكيف؟", conversation_id="c1").disclosure == AR


def test_without_an_id_history_decides():
    bot = bots(ANSWER, ANSWER)["arabic-full"]
    assert bot.chat("كم سعر تنظيف المكيف؟").disclosure == AR
    hist = [{"role": "user", "text": "مرحبا"}, {"role": "assistant", "text": "أهلا"}]
    assert bot.chat("كم سعر تنظيف المكيف؟", history=hist).disclosure == ""


def test_handover_always_says_an_ai_is_passing_to_a_person():
    bot = bots()["arabic-full"]
    first = bot.chat("أبي أكلم موظف لو سمحت", conversation_id="c1")
    assert first.reply == HUMAN_OK_AR and "ذكاء اصطناعي" in first.disclosure and "أحد أفراد الفريق" in first.disclosure
    again = bot.chat("I want to talk to a human", conversation_id="c1")      # not the first message
    assert again.reply == HUMAN_OK and again.disclosure.startswith("I'm an AI assistant for Test")
    assert "person" in again.disclosure


def test_model_needs_human_is_a_handover_too():
    bot = bots({"status": "needs_human", "answer": "A person can help.", "citations": []})["arabic-search"]
    bot.chat("x", conversation_id="c0")  # use up the first-message disclosure (no hits, no model call)
    r = bot.chat("كم سعر تنظيف المكيف؟", conversation_id="c0")
    assert r.status == "needs_human" and "AI assistant" in r.disclosure


def test_every_bot_and_fixed_reply_path_discloses_first():
    no = {"status": "not_in_knowledge_base", "answer": "I don't have that.", "citations": []}
    for name in ("original", "arabic-search", "arabic-full"):  # arabic-full asks the model (small-KB fallback)
        r = bots(no)[name].chat("Do you sell cars?", conversation_id="new")
        assert r.status == "not_in_knowledge_base" and r.disclosure == EN, name


def test_blank_text_without_written_request_keeps_the_default():
    d = Disclosure.from_env({"AI_DISCLOSURE": "", "AI_DISCLOSURE_AR": "  "})
    assert d.first("Test", False) == EN and d.first("Test", True) == AR
    r = bots(disclosure=d)["original"].chat("Do you sell cars?")
    assert r.disclosure == EN
    assert Disclosure.from_env({"AI_DISCLOSURE_REMOVED_BY_WRITTEN_REQUEST": "  "}).first("Test", False) == EN


def test_removed_only_with_a_recorded_written_request():
    d = Disclosure.from_env({"AI_DISCLOSURE_REMOVED_BY_WRITTEN_REQUEST": "2026-11-17, email from client ops"})
    bot = bots(ANSWER, disclosure=d)["arabic-full"]
    r = bot.chat("هل تعملون يوم الجمعة؟")
    assert r.disclosure == "" and r.text == r.reply
    assert bot.chat("أبي أكلم موظف").disclosure == ""


def test_custom_text():
    d = Disclosure.from_env({"AI_DISCLOSURE": "You are chatting with an AI for {company}."})
    assert bots(disclosure=d)["original"].chat("Do you sell cars?").disclosure == "You are chatting with an AI for Test."
