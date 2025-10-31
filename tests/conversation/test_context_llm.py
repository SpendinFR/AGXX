from __future__ import annotations

import sys
import time
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from AGI_Evolutive.conversation import context  # noqa: E402


class Memory:
    def get_recent_memories(self, n: int):
        now = time.time()
        return [
            {"text": "Premier", "ts": now - 30, "speaker": "user"},
            {"text": "Deuxième", "ts": now - 10, "speaker": "assistant"},
        ]


class StubManager:
    def __init__(self, payload):
        self.payload = payload
        self.last_payload = None

    def call_dict(self, spec_key, *, input_payload=None, **_kwargs):
        assert spec_key == "conversation_context"
        self.last_payload = input_payload
        return self.payload


def test_builder_exposes_last_result_and_extra_field():
    arch = SimpleNamespace(memory=Memory(), consolidator=None, user_model=None)
    manager = StubManager({"summary": ["Résumé"], "topics": ["priorité"]})
    builder = context.ContextBuilder(arch, llm_manager=manager)

    result = builder.build("Bonjour", extra={"source": "inbox"})

    assert manager.last_payload["extra"] == {"source": "inbox"}
    assert builder.last_result is not None
    assert builder.last_result.summary_bullets == ["Résumé"]
    assert result["topics"] == ["priorité"]
