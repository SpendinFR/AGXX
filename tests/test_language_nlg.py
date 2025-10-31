import sys
from pathlib import Path
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from AGI_Evolutive.language import nlg


class _StubLLMManager:
    def __init__(self, responses: list[Mapping[str, Any]]):
        self._responses = list(responses)
        self.calls: list[tuple[str, Mapping[str, Any]]] = []

    def call_dict(self, spec_key: str, *, input_payload: Mapping[str, Any], **_: Any):
        self.calls.append((spec_key, dict(input_payload)))
        if not self._responses:
            raise AssertionError(f"Unexpected call for spec {spec_key}: {input_payload}")
        return self._responses.pop(0)


def test_apply_mai_bids_updates_context(monkeypatch):
    manager = _StubLLMManager(
        [
            {
                "message": "Réponse finale polie.",
                "sections": [
                    {"name": "introduction", "text": "Merci pour la clarté de ta question."},
                    {"name": "body", "text": "Voici ma recommandation complète."},
                ],
                "applied_actions": [{"origin": "llm", "hint": "structured_sections"}],
                "meta": {"confidence": 0.87},
            }
        ]
    )
    monkeypatch.setattr(nlg, "get_llm_manager", lambda: manager)

    context = nlg.NLGContext("Base brute", apply_hint=lambda text, hint: f"{hint}:{text}")
    result = nlg.apply_mai_bids_to_nlg(
        context,
        state={"dialogue": {"turn": 3}, "memory": {"last_summary": "memo"}},
        predicate_registry=None,
        contract={"goal": "support"},
        reasoning={"summary": "analyse"},
        metadata={"style": {"tone": "calme"}, "diagnostic": "ok"},
        llm_manager=manager,
    )

    assert context.text == "Réponse finale polie."
    assert result.sections[0]["text"].startswith("Merci")
    assert context.meta["confidence"] == 0.87
    assert context.applied_hints()[0]["hint"] == "structured_sections"

    spec_key, payload = manager.calls[0]
    assert spec_key == "language_nlg"
    assert payload["mode"] == "reply"
    assert payload["contract"]["goal"] == "support"
    assert payload["metadata"]["diagnostic"] == "ok"


def test_generation_falls_back_to_base_text_when_empty_response():
    manager = _StubLLMManager([{}])
    service = nlg.LanguageGeneration(llm_manager=manager)

    request = nlg.NLGRequest(base_text="Base text only")
    result = service.generate(request)

    assert result.message == "Base text only"
    assert result.sections == []
    assert service.last_result is result


def test_paraphrase_light_uses_paraphrase_mode(monkeypatch):
    manager = _StubLLMManager([
        {"message": "Version paraphrasée."}
    ])
    monkeypatch.setattr(nlg, "get_llm_manager", lambda: manager)

    output = nlg.paraphrase_light("Original", tone="doux", llm_manager=manager)

    assert output == "Version paraphrasée."
    spec_key, payload = manager.calls[0]
    assert spec_key == "language_nlg"
    assert payload["mode"] == "paraphrase"
    assert payload["metadata"]["tone"] == "doux"
