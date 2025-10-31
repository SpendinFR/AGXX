from __future__ import annotations

import pathlib
import sys
from typing import Any, Dict, List, Mapping, Optional

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from AGI_Evolutive.autonomy.auto_evolution import AutoEvolutionCoordinator, AutoEvolutionOutcome
from AGI_Evolutive.autonomy.auto_signals import AutoSignalRegistry


class StubLLMManager:
    def __init__(self, responses: Mapping[str, Mapping[str, Any]]) -> None:
        self.responses = {str(key): dict(value) for key, value in responses.items()}
        self.calls: List[tuple[str, Dict[str, Any]]] = []

    def call_dict(self, spec_key: str, *, input_payload: Optional[Mapping[str, Any]] = None, **_: Any) -> Mapping[str, Any]:
        self.calls.append((spec_key, dict(input_payload or {})))
        try:
            return self.responses[spec_key]
        except KeyError:  # pragma: no cover - defensive
            raise AssertionError(f"Unexpected spec requested: {spec_key}")


@pytest.fixture()
def stub_manager() -> StubLLMManager:
    return StubLLMManager(
        {
            "auto_evolution": {
                "accepted": True,
                "intention": {
                    "action_type": "reflect",
                    "description": "Consolider la découverte",
                },
                "evaluation": {
                    "score": 0.88,
                    "alignment": 0.81,
                },
                "signals": [
                    {
                        "name": "impact",
                        "metric": "impact_score",
                        "direction": "above",
                        "target": 0.8,
                        "weight": 1.2,
                    }
                ],
                "follow_up": ["Rédiger un rapport"],
                "metadata": {"llm": True},
            },
            "auto_signal_registration": {
                "signals": [
                    {
                        "name": "impact",
                        "metric": "impact_score",
                        "direction": "above",
                        "target": 0.8,
                        "weight": 1.2,
                        "source": "llm",
                        "last_value": 0.71,
                        "last_source": "llm",
                    }
                ]
            },
        }
    )


def test_auto_evolution_tick_invokes_llm_and_registers_signals(stub_manager: StubLLMManager) -> None:
    registry = AutoSignalRegistry(llm_manager=stub_manager)
    coordinator = AutoEvolutionCoordinator(signal_registry=registry, llm_manager=stub_manager)

    outcome = coordinator.tick(
        memory_snapshot={"timeline": {"combined": []}},
        recent_insights=[{"id": "abc", "kind": "lesson", "text": "Nouvelle compétence"}],
        active_modules=[{"name": "Memory"}],
    )

    assert isinstance(outcome, AutoEvolutionOutcome)
    assert outcome.intention["action_type"] == "reflect"
    assert stub_manager.calls[0][0] == "auto_evolution"
    assert stub_manager.calls[0][1]["memory"]["timeline"] == {"combined": []}
    assert stub_manager.calls[1][0] == "auto_signal_registration"
    signals = registry.get_signals("reflect")
    assert signals and signals[0].metric == "impact_score"
    assert signals[0].last_value == pytest.approx(0.71)


def test_auto_evolution_handles_missing_signals(stub_manager: StubLLMManager) -> None:
    stub_manager.responses["auto_evolution"] = {
        "accepted": False,
        "intention": {"action_type": "plan"},
        "evaluation": {},
        "signals": [],
    }
    registry = AutoSignalRegistry(llm_manager=stub_manager)
    coordinator = AutoEvolutionCoordinator(signal_registry=registry, llm_manager=stub_manager)

    outcome = coordinator.tick(memory_snapshot={})

    assert outcome.accepted is False
    assert registry.get_signals("plan") == []
    assert stub_manager.calls[0][0] == "auto_evolution"
    # When no signals are returned we should not call the registration contract.
    assert all(call[0] != "auto_signal_registration" for call in stub_manager.calls[1:])
