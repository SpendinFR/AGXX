import json
import pathlib
import sys
import unicodedata
from types import SimpleNamespace
from typing import Any, Dict, Mapping, Optional

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from AGI_Evolutive.autonomy.auto_signals import AutoSignalRegistry, extract_keywords
from AGI_Evolutive.io.action_interface import Action, ActionInterface, CognitiveDomain
from AGI_Evolutive.self_improver.skill_acquisition import SkillSandboxManager


class _DummyMetacog:
    def __init__(self):
        self.calls = []

    def trigger_reflection(self, *, trigger, domain, urgency, depth):
        # record inputs to assert fallback behaviour
        self.calls.append({
            "trigger": trigger,
            "domain": domain,
            "urgency": urgency,
            "depth": depth,
        })
        return SimpleNamespace(duration=1.0, quality_score=0.75)


def test_reflect_action_falls_back_to_reasoning_domain(tmp_path):
    interface = ActionInterface(
        path_log=str(tmp_path / "actions.jsonl"),
        output_dir=str(tmp_path / "out"),
    )
    dummy = _DummyMetacog()
    # bind without exposing CognitiveDomain attribute to force fallback
    interface.bind(metacog=dummy)

    act = Action(id="a1", type="reflect", payload={}, priority=0.5)

    result = interface._h_reflect(act)

    assert result["ok"] is True
    assert dummy.calls, "Metacognition module should be invoked"
    call = dummy.calls[0]
    assert call["domain"] is CognitiveDomain.REASONING


def test_simulate_fallback_when_simulator_missing(tmp_path):
    interface = ActionInterface(
        path_log=str(tmp_path / "actions.jsonl"),
        output_dir=str(tmp_path / "out"),
    )

    act = Action(id="sim1", type="simulate", payload={"desc": "test"}, priority=0.5)

    result = interface._h_simulate(act)

    assert result["ok"] is True
    assert result["simulated"] is False
    assert result["reason"] == "simulator_unavailable"
    assert result["success"] is False


def test_execute_log_action_records_entry(tmp_path):
    out_dir = tmp_path / "out"
    interface = ActionInterface(
        path_log=str(tmp_path / "actions.jsonl"),
        output_dir=str(out_dir),
    )

    result = interface.execute({"type": "log", "text": "Bonjour", "level": "info"})

    assert result["ok"] is True

    log_path = out_dir / "log_entries.jsonl"
    assert log_path.exists(), "log handler should persist entries"
    lines = log_path.read_text(encoding="utf-8").strip().splitlines()
    assert lines, "log file should contain at least one entry"
    payload = json.loads(lines[-1])
    assert payload["text"] == "Bonjour"


def test_plan_step_handler_creates_record(tmp_path):
    out_dir = tmp_path / "out"
    interface = ActionInterface(
        path_log=str(tmp_path / "actions.jsonl"),
        output_dir=str(out_dir),
    )

    act = Action(
        id="ps1",
        type="plan_step",
        payload={"description": "Lister les ressources", "goal_id": "g1"},
        priority=0.5,
    )

    result = interface._h_plan_step(act)

    assert result["ok"] is True
    assert result["description"] == "Lister les ressources"

    record_path = out_dir / "plan_steps.jsonl"
    assert record_path.exists()
    entries = [json.loads(line) for line in record_path.read_text(encoding="utf-8").splitlines()]
    assert entries[-1]["description"] == "Lister les ressources"


class _MemoryStub:
    def __init__(self):
        self.records = []

    def search(self, query, top_k=8):
        return [
            {"kind": "knowledge", "content": f"Info sur {query}", "importance": 0.8},
            {"kind": "example", "content": f"Exemple pratique {query}"},
        ]

    def add_memory(self, payload):
        self.records.append(payload)
        return f"mem-{len(self.records)}"


class _LanguageStub:
    def practice(self, payload):  # type: ignore[no-untyped-def]
        return {
            "success": True,
            "summary": "Plan validé avec implémentation.",
            "feedback": "Plan validé avec implémentation.",
            "implementation": {
                "operations": {
                    "consigner": {
                        "type": "python",
                        "code": (
                            "value = inputs.get('value', 'ok')\n"
                            "result = {'ok': True, 'value': value}\n"
                        ),
                    }
                },
                "steps": [
                    {"op": "consigner", "inputs": {"value": "appris"}, "store_as": "note"},
                ],
            },
        }

    def reply(self, intent, data, pragmatic):
        topic = data.get("topic", "action")
        return f"Plan validé pour {topic}."


def test_unknown_action_goes_through_skill_sandbox(tmp_path):
    out_dir = tmp_path / "out"
    interface = ActionInterface(
        path_log=str(tmp_path / "actions.jsonl"),
        output_dir=str(out_dir),
    )

    memory = _MemoryStub()
    language = _LanguageStub()
    skills = SkillSandboxManager(
        storage_dir=str(tmp_path / "skills"),
        min_trials=2,
        success_threshold=0.4,
        run_async=False,
        approval_required=True,
        training_interval=0.0,
    )
    skills.bind(memory=memory, language=language)

    interface.bind(memory=memory, language=language, skills=skills)

    act = Action(
        id="skill-1",
        type="perform_magic",
        payload={"description": "Créer un tour de magie", "requirements": ["magie", "présentation"]},
        priority=0.5,
    )

    first = skills.handle_simulation(act, interface)

    assert first["ok"] is False
    assert first["reason"] in {"skill_waiting_user_approval", "skill_training_in_progress"}

    approve = interface.execute(
        {
            "type": "review_skill_candidate",
            "payload": {
                "action_type": "perform_magic",
                "decision": "approve",
                "reviewer": "tester",
            },
        }
    )

    assert approve["ok"] is True
    assert approve["skill"]["status"] == "active"

    second = interface.execute({"type": "perform_magic", "payload": {"audience": "demo"}})

    assert second["ok"] is True
    assert "summary" in second


class _StubSignalLLM:
    def __init__(self, responses: Mapping[str, Mapping[str, Any]]) -> None:
        self.responses = {str(key): dict(value) for key, value in responses.items()}
        self.calls: list[tuple[str, Dict[str, Any]]] = []

    def call_dict(self, spec_key: str, *, input_payload: Optional[Mapping[str, Any]] = None, **_: Any) -> Mapping[str, Any]:
        self.calls.append((spec_key, dict(input_payload or {})))
        return self.responses[spec_key]


def test_auto_intention_signals_adjust_reward(tmp_path):
    stub = _StubSignalLLM(
        {
            "auto_signal_derivation": {
                "signals": [
                    {
                        "name": "relation_depth",
                        "metric": "relation_depth_score",
                        "direction": "above",
                        "target": 0.75,
                        "weight": 1.1,
                    },
                    {
                        "name": "trust_guard",
                        "metric": "trust_risk",
                        "direction": "below",
                        "target": 0.2,
                        "weight": 0.6,
                    },
                ]
            },
            "auto_signal_registration": {
                "signals": [
                    {
                        "name": "relation_depth",
                        "metric": "relation_depth_score",
                        "direction": "above",
                        "target": 0.75,
                        "weight": 1.1,
                        "last_value": 0.65,
                    },
                    {
                        "name": "trust_guard",
                        "metric": "trust_risk",
                        "direction": "below",
                        "target": 0.2,
                        "weight": 0.6,
                        "last_value": 0.25,
                    },
                ]
            },
            "auto_signal_keywords": {"keywords": ["relation", "empathie", "durable"]},
        }
    )

    interface = ActionInterface(
        path_log=str(tmp_path / "actions.jsonl"),
        output_dir=str(tmp_path / "out"),
    )
    registry = AutoSignalRegistry(llm_manager=stub)
    interface.bind(auto_signals=registry)

    event = {
        "action_type": "build_relationship",
        "description": "Développer une relation durable et empathique",
        "requirements": ["confiance", "partage"],
        "metadata": {"keywords": ["relation", "empathie", "durable"]},
    }
    evaluation = {"score": 0.72, "significance": 0.78, "alignment": 0.74}
    interface.on_auto_intention_promoted(event, evaluation, None)

    signals = registry.get_signals("build_relationship")
    metrics = {sig.metric for sig in signals}
    assert {"relation_depth_score", "trust_risk"} <= metrics

    fragments = set(
        extract_keywords(
            event["description"],
            " ".join(event["requirements"]),
            " ".join(event["metadata"]["keywords"]),
            llm_manager=stub,
        )
    )
    assert fragments == {"relation", "empathie", "durable"}

    base_action = Action(id="rel-1", type="build_relationship", payload={}, priority=0.5)
    base_action.status = "done"
    base_action.result = {
        "metrics": {
            "relation_depth_score": 0.9,
            "trust_risk": 0.1,
        }
    }

    registry.bulk_record("build_relationship", base_action.result["metrics"], source="test")

    reward_positive = interface._shape_reward(base_action)

    weak_action = Action(id="rel-2", type="build_relationship", payload={}, priority=0.5)
    weak_action.status = "done"
    weak_action.result = {
        "metrics": {
            "relation_depth_score": 0.55,
            "trust_risk": 0.35,
        }
    }

    registry.bulk_record("build_relationship", weak_action.result["metrics"], source="test")

    reward_weak = interface._shape_reward(weak_action)

    assert reward_positive > reward_weak


def test_manual_signal_payloads_are_augmented(tmp_path):
    stub = _StubSignalLLM(
        {
            "auto_signal_derivation": {
                "signals": [
                    {
                        "name": "relationship_quality",
                        "metric": "relationship_quality",
                        "direction": "above",
                        "target": 0.8,
                    }
                ]
            },
            "auto_signal_registration": {
                "signals": [
                    {
                        "name": "build_relationship__custom",
                        "metric": "custom_metric",
                        "direction": "above",
                        "target": 0.9,
                    },
                    {
                        "name": "relationship_quality",
                        "metric": "relationship_quality",
                        "direction": "above",
                        "target": 0.8,
                    },
                ]
            },
            "auto_signal_keywords": {"keywords": ["relation", "empathie", "durable"]},
        }
    )

    interface = ActionInterface(
        path_log=str(tmp_path / "actions.jsonl"),
        output_dir=str(tmp_path / "out"),
    )
    registry = AutoSignalRegistry(llm_manager=stub)
    interface.bind(auto_signals=registry)

    event = {
        "action_type": "build_relationship",
        "description": "Développer une relation durable et empathique",
        "signals": [
            {
                "name": "build_relationship__custom",
                "metric": "custom_metric",
                "target": 0.9,
                "direction": "above",
            }
        ],
        "metadata": {"keywords": ["relation", "empathie", "durable"]},
    }

    interface.on_auto_intention_promoted(event, {"score": 0.7}, None)

    signals = registry.get_signals("build_relationship")
    metrics = {sig.metric for sig in signals}
    assert {"custom_metric", "relationship_quality"} <= metrics

    keywords = extract_keywords(
        event["description"],
        " ".join(event.get("requirements", [])),
        " ".join(event["metadata"]["keywords"]),
        llm_manager=stub,
    )
    assert keywords == ["relation", "empathie", "durable"]
