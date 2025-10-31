import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from AGI_Evolutive.io.intent_classifier import IntentIngestionOrchestrator  # noqa: E402


class RecordingManager:
    def __init__(self, response):
        self.response = response
        self.records = []

    def call_dict(self, spec_key, *, input_payload=None, **kwargs):
        self.records.append({"spec": spec_key, "payload": input_payload, "kwargs": kwargs})
        return self.response


def test_orchestrator_passes_metadata_and_parses_flags():
    manager = RecordingManager(
        {
            "intent": {"label": "command", "confidence": 0.88, "rationale": "Demande explicite d'action."},
            "tone": "direct",
            "sentiment": "neutral",
            "priority": "high",
            "urgency": "immédiat",
            "summary": "Exécuter une sauvegarde complète",
            "follow_up_questions": [],
            "safety": {"flags": ["requires_confirmation", "policy_alert"]},
        }
    )
    orchestrator = IntentIngestionOrchestrator(manager=manager)

    result = orchestrator.analyze(
        "Lance immédiatement une sauvegarde complète.",
        context={"channel": "terminal"},
        metadata={"conversation_id": "abc-123"},
    )

    assert result.label == "COMMAND"
    assert result.safety_flags == ("requires_confirmation", "policy_alert")
    assert manager.records[0]["spec"] == "intent_ingestion"
    assert manager.records[0]["payload"]["metadata"] == {"conversation_id": "abc-123"}


def test_missing_intent_mapping_raises():
    manager = RecordingManager({"tone": "calm"})
    orchestrator = IntentIngestionOrchestrator(manager=manager)

    with pytest.raises(ValueError):
        orchestrator.analyze("Bonjour")
