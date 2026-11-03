import json
from types import SimpleNamespace


class FakeMessages:
    def __init__(self, replies):
        self.replies = list(replies)
        self.calls = []

    def create(self, **kw):
        self.calls.append(kw)
        payload = self.replies.pop(0)
        return SimpleNamespace(
            stop_reason="end_turn",
            content=[SimpleNamespace(type="text", text=json.dumps(payload, ensure_ascii=False))],
            usage=SimpleNamespace(input_tokens=100, output_tokens=20),
        )


class FakeClient:
    def __init__(self, *replies):
        self.beta = SimpleNamespace(messages=FakeMessages(replies))

    @property
    def calls(self):
        return self.beta.messages.calls
