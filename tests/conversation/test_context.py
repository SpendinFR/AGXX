from __future__ import annotations

import sys
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from AGI_Evolutive.conversation import context  # noqa: E402
from AGI_Evolutive.utils.llm_service import LLMIntegrationError  # noqa: E402


class DummyMemory:
    def __init__(self, records):
        self._records = list(records)

    def get_recent_memories(self, n: int = 10):
        return list(self._records)[-n:]


class DummyUserModel:
    def __init__(self, persona=None):
        self._persona = persona or {}

    def describe(self):
        return {"id": "user-123", "persona": self._persona}


class StubLLM:
    def __init__(self, payload):
        self.payload = payload
        self.last_spec = None
        self.last_input = None

    def call_dict(self, spec_key, *, input_payload=None, **_: object):
        self.last_spec = spec_key
        self.last_input = input_payload or {}
        return self.payload


def _record(text, *, speaker="user", ts=None, kind="interaction", tags=None):
    return {
        "text": text,
        "speaker": speaker,
        "ts": time.time() if ts is None else ts,
        "kind": kind,
        "tags": tags or [],
    }


def test_context_builder_collects_recent_messages_and_persona(monkeypatch):
    records = [
        _record("Salut !", speaker="user", tags=["greeting"]),
        _record("Hello", speaker="assistant", tags=["reply"]),
    ]
    arch = SimpleNamespace(
        memory=DummyMemory(records),
        consolidator=SimpleNamespace(state={"lessons": ["priorité aux tests"]}),
        user_model=DummyUserModel(persona={"tone": "warm"}),
    )

    llm_response = {
        "summary": ["Conversation cordiale"],
        "topics": [
            {"rank": 1, "label": "salutations"},
            {"rank": 2, "label": "tests"},
        ],
        "key_moments": ["Salut -> Hello"],
        "user_style": {"prefers_long": False},
        "follow_up_questions": ["Comment puis-je aider davantage ?"],
        "recommended_actions": [{"label": "Proposer un plan"}],
        "alerts": ["Aucun"],
        "tone": "chaleureux",
    }
    stub = StubLLM(llm_response)
    builder = context.ContextBuilder(arch, llm_manager=stub)

    result = builder.build("Peux-tu m'aider ?")

    assert stub.last_spec == "conversation_context"
    assert stub.last_input["last_message"] == "Peux-tu m'aider ?"
    assert stub.last_input["persona"]["persona"]["tone"] == "warm"
    assert stub.last_input["lessons"] == ["priorité aux tests"]
    assert result["topics"] == ["salutations", "tests"]
    assert result["llm_topics"][0]["rank"] == 1
    assert result["user_style"]["prefers_long"] is False
    assert result["follow_up_questions"] == ["Comment puis-je aider davantage ?"]
    assert result["recommended_actions"][0]["label"] == "Proposer un plan"
    assert result["tone"] == "chaleureux"
    assert result["llm_summary"]["summary"] == ["Conversation cordiale"]


def test_context_builder_normalises_sparse_payload(monkeypatch):
    arch = SimpleNamespace(memory=DummyMemory([_record("ok")]), consolidator=None, user_model=None)
    stub = StubLLM({"summary": "Brève"})
    builder = context.ContextBuilder(arch, llm_manager=stub)

    result = builder.build("   ok   ")

    assert result["last_message"] == "ok"
    assert result["summary"] == ["Brève"]
    assert result["summary_text"] == "Brève"
    assert result["topics"] == []
    assert result["user_style"] == {}


def test_context_builder_raises_on_llm_error(monkeypatch):
    class FailingLLM:
        def call_dict(self, *_, **__):
            raise LLMIntegrationError("offline")

    arch = SimpleNamespace(memory=DummyMemory([]), consolidator=None, user_model=None)
    builder = context.ContextBuilder(arch, llm_manager=FailingLLM())

    with pytest.raises(context.ConversationContextError):
        builder.build("hello")
