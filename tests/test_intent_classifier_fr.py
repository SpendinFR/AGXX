import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from AGI_Evolutive.io.intent_classifier import (  # noqa: E402
    IntentIngestionOrchestrator,
    analyze,
)


class StubManager:
    def __init__(self, payload):
        self.payload = payload
        self.calls = []

    def call_dict(self, spec_key, *, input_payload=None, **kwargs):
        self.calls.append({"spec": spec_key, "payload": input_payload, "kwargs": kwargs})
        return self.payload


def test_analyze_returns_structured_result():
    manager = StubManager(
        {
            "intent": {"label": "question", "confidence": 0.78, "rationale": "L'énoncé est interrogatif."},
            "tone": "curious",
            "priority": "low",
            "summary": "Demande un état des lieux des sauvegardes.",
            "follow_up_questions": ["Faut-il inclure les rapports détaillés ?"],
            "safety": {"flags": []},
            "entities": [{"type": "ressource", "value": "sauvegardes", "role": "subject"}],
        }
    )
    orchestrator = IntentIngestionOrchestrator(manager=manager)

    result = orchestrator.analyze("Peux-tu vérifier les sauvegardes ?", context={"channel": "cli"})

    assert result.label == "QUESTION"
    assert pytest.approx(result.confidence, rel=1e-6) == 0.78
    assert result.rationale == "L'énoncé est interrogatif."
    assert result.tone == "curious"
    assert result.priority == "low"
    assert result.summary.startswith("Demande un état des lieux")
    assert result.follow_up_questions == ("Faut-il inclure les rapports détaillés ?",)
    assert result.entities[0]["type"] == "ressource"
    assert manager.calls[0]["spec"] == "intent_ingestion"
    assert manager.calls[0]["payload"]["utterance"] == "Peux-tu vérifier les sauvegardes ?"
    assert manager.calls[0]["payload"]["context"] == {"channel": "cli"}


def test_global_analyze_reuses_default_orchestrator(monkeypatch):
    manager = StubManager({"intent": {"label": "info", "confidence": 0.51}})
    monkeypatch.setattr(
        "AGI_Evolutive.io.intent_classifier.get_llm_manager", lambda: manager
    )

    result = analyze("Je partage les résultats du test.")

    assert result.label == "INFO"
    assert len(manager.calls) == 1


def test_invalid_response_raises_value_error():
    orchestrator = IntentIngestionOrchestrator(manager=StubManager({"intent": "COMMAND"}))

    with pytest.raises(ValueError):
        orchestrator.analyze("Exécute le rapport weekly")
