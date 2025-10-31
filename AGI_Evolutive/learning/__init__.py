"""LLM-first learning orchestrators.

Ce module remplace les pipelines d'apprentissage historiques basés sur des
heuristiques multiples par une poignée d'orchestrateurs minimalistes qui ne
font qu'une seule chose : préparer le contexte, appeler un contrat LLM et
appliquer la réponse structurée.  Chaque composant conserve uniquement l'état
nécessaire pour la persistance et l'observabilité.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, MutableMapping, Optional, Sequence

from AGI_Evolutive.utils.llm_service import LLMIntegrationError, get_llm_manager

__all__ = [
    "ExperientialLearning",
    "MetaLearning",
    "TransferLearning",
    "ReinforcementLearning",
    "CuriosityEngine",
]


def _ensure_mapping(value: Any) -> MutableMapping[str, Any]:
    if isinstance(value, Mapping):
        return {str(k): v for k, v in value.items()}
    return {}


def _ensure_list(value: Any) -> list[Any]:
    if isinstance(value, str):
        cleaned = value.strip()
        return [cleaned] if cleaned else []
    if isinstance(value, Iterable) and not isinstance(value, (bytes, bytearray)):
        return [item for item in value]
    return []


def _coerce_float(
    value: Any,
    *,
    default: float = 0.0,
    minimum: Optional[float] = None,
    maximum: Optional[float] = None,
) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        number = default
    if number != number:  # NaN
        number = default
    if minimum is not None and number < minimum:
        number = minimum
    if maximum is not None and number > maximum:
        number = maximum
    return number


@dataclass
class LearningEpisodeOutcome:
    """Normalized payload returned by ``experiential_learning_cycle``."""

    summary: str
    confidence: float
    actions: list[Mapping[str, Any]]
    memory_updates: list[Mapping[str, Any]]
    metrics: Mapping[str, Any]
    notes: list[str]
    raw: Mapping[str, Any] = field(default_factory=dict)

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> "LearningEpisodeOutcome":
        mapping = _ensure_mapping(payload)
        summary = str(mapping.get("summary") or "").strip()
        confidence = _coerce_float(
            mapping.get("confidence"),
            default=0.6,
            minimum=0.0,
            maximum=1.0,
        )
        actions = [
            _ensure_mapping(item)
            for item in _ensure_list(mapping.get("actions"))
            if isinstance(item, Mapping)
        ]
        mem_updates = [
            _ensure_mapping(item)
            for item in _ensure_list(mapping.get("memory_updates"))
            if isinstance(item, Mapping)
        ]
        metrics = _ensure_mapping(mapping.get("metrics"))
        notes = [
            str(note).strip()
            for note in _ensure_list(mapping.get("notes"))
            if str(note).strip()
        ]
        return cls(
            summary=summary,
            confidence=confidence,
            actions=actions,
            memory_updates=mem_updates,
            metrics=metrics,
            notes=notes,
            raw=mapping,
        )


class _LLMBackedComponent:
    """Utility base-class that provides the LLM manager plumbing."""

    def __init__(self, *, llm_manager=None) -> None:
        self._manager = llm_manager

    def _manager_or_default(self):
        manager = self._manager
        if manager is None:
            manager = get_llm_manager()
        return manager

    def _call_spec(
        self,
        spec_key: str,
        payload: Mapping[str, Any] | None,
        *,
        extra: Sequence[str] | None = None,
    ) -> Mapping[str, Any]:
        manager = self._manager_or_default()
        response = manager.call_dict(
            spec_key,
            input_payload=_ensure_mapping(payload or {}),
            extra_instructions=extra,
        )
        if not isinstance(response, Mapping):  # pragma: no cover - defensive
            raise LLMIntegrationError(
                f"Spec '{spec_key}' returned a non-mapping payload",
            )
        return response


class ExperientialLearning(_LLMBackedComponent):
    """Single-call experiential learning loop orchestrated by the LLM."""

    def __init__(
        self,
        cognitive_architecture: Any | None = None,
        *,
        history_limit: int = 50,
        llm_manager=None,
    ) -> None:
        super().__init__(llm_manager=llm_manager)
        self.cognitive_architecture = cognitive_architecture
        self._history_limit = max(1, int(history_limit))
        self._history: list[LearningEpisodeOutcome] = []
        self._last_self_assessment: MutableMapping[str, Any] | None = None
        self._curriculum_log: list[Mapping[str, Any]] = []

    # ------------------------------------------------------------------
    def _snapshot_architecture(self) -> Mapping[str, Any]:
        arch = self.cognitive_architecture
        if arch is None:
            return {}
        snapshot: dict[str, Any] = {}
        try:
            snapshot["active_goal"] = getattr(arch.goals, "current_goal_id", None)
        except Exception:
            pass
        for attr in ("global_activation", "last_output_text", "reflective_mode"):
            try:
                snapshot[attr] = getattr(arch, attr)
            except Exception:
                continue
        try:
            telemetry = getattr(arch, "telemetry", None)
            if telemetry and hasattr(telemetry, "recent_events"):
                snapshot["recent_events"] = telemetry.recent_events(5)  # type: ignore[attr-defined]
        except Exception:
            pass
        return {k: v for k, v in snapshot.items() if v is not None}

    def process_experience(
        self,
        experience: Mapping[str, Any],
        *,
        extra: Mapping[str, Any] | None = None,
    ) -> LearningEpisodeOutcome:
        payload = {
            "experience": _ensure_mapping(experience),
            "architecture": self._snapshot_architecture(),
        }
        if extra:
            payload["extra"] = _ensure_mapping(extra)
        response = self._call_spec("experiential_learning_cycle", payload)
        outcome = LearningEpisodeOutcome.from_payload(response)
        self._history.append(outcome)
        if len(self._history) > self._history_limit:
            self._history.pop(0)
        return outcome

    def self_assess_concept(
        self,
        concept: str,
        *,
        context: Mapping[str, Any] | None = None,
    ) -> Mapping[str, Any]:
        payload = {
            "concept": concept,
            "context": self._snapshot_architecture(),
        }
        if context:
            payload["context"].update(_ensure_mapping(context))
        response = self._call_spec("learning_self_assessment", payload)
        self._last_self_assessment = _ensure_mapping(response)
        return dict(self._last_self_assessment)

    def on_auto_intention_promoted(
        self,
        event: Mapping[str, Any],
        evaluation: Mapping[str, Any] | None = None,
        self_assessment: Mapping[str, Any] | None = None,
    ) -> Mapping[str, Any]:
        payload = {
            "event": _ensure_mapping(event),
            "evaluation": _ensure_mapping(evaluation or {}),
            "self_assessment": _ensure_mapping(self_assessment or {}),
            "history": [entry.raw for entry in self._history[-5:]],
        }
        response = self._call_spec("learning_auto_curriculum", payload)
        response_mapping = _ensure_mapping(response)
        self._curriculum_log.append(response_mapping)
        if len(self._curriculum_log) > self._history_limit:
            self._curriculum_log.pop(0)
        return dict(response_mapping)

    # ------------------------------------------------------------------
    def to_state(self) -> Mapping[str, Any]:
        return {
            "history": [entry.raw for entry in self._history[-self._history_limit :]],
            "last_self_assessment": dict(self._last_self_assessment or {}),
            "curriculum_log": list(self._curriculum_log[-self._history_limit :]),
        }

    def from_state(self, state: Mapping[str, Any]) -> None:
        self._history = [
            LearningEpisodeOutcome.from_payload(item)
            for item in _ensure_list(state.get("history"))
            if isinstance(item, Mapping)
        ]
        self._last_self_assessment = _ensure_mapping(
            state.get("last_self_assessment")
        ) or None
        self._curriculum_log = [
            _ensure_mapping(item)
            for item in _ensure_list(state.get("curriculum_log"))
            if isinstance(item, Mapping)
        ]


class MetaLearning(_LLMBackedComponent):
    """Delegates global learning adjustments to ``learning_meta_controller``."""

    def __init__(self, *, llm_manager=None, history_limit: int = 100) -> None:
        super().__init__(llm_manager=llm_manager)
        self._history_limit = max(1, int(history_limit))
        self._feedback_log: list[Mapping[str, Any]] = []
        self._curriculum_history: list[Mapping[str, Any]] = []

    def register_feedback(
        self,
        module: str,
        *,
        score: float,
        prediction: float | None = None,
        error: float | None = None,
        context: Mapping[str, Any] | None = None,
    ) -> Mapping[str, Any]:
        payload = {
            "module": module,
            "score": _coerce_float(score, minimum=0.0, maximum=1.0),
            "prediction": _coerce_float(prediction, default=0.0),
            "error": _coerce_float(error, default=0.0),
            "context": _ensure_mapping(context or {}),
            "history": list(self._feedback_log[-10:]),
        }
        response = self._call_spec("learning_meta_controller", payload)
        response_mapping = _ensure_mapping(response)
        self._feedback_log.append({
            "module": module,
            "payload": payload,
            "adjustments": response_mapping,
        })
        if len(self._feedback_log) > self._history_limit:
            self._feedback_log.pop(0)
        return dict(response_mapping)

    def propose_curriculum(
        self,
        *,
        focus: Sequence[str] | None = None,
        extra: Mapping[str, Any] | None = None,
    ) -> Mapping[str, Any]:
        payload = {
            "focus_modules": list(focus) if focus else None,
            "feedback": list(self._feedback_log[-10:]),
        }
        if extra:
            payload["extra"] = _ensure_mapping(extra)
        response = self._call_spec("learning_curriculum_planner", payload)
        mapping = _ensure_mapping(response)
        self._curriculum_history.append(mapping)
        if len(self._curriculum_history) > self._history_limit:
            self._curriculum_history.pop(0)
        return dict(mapping)

    def to_state(self) -> Mapping[str, Any]:
        return {
            "feedback_log": list(self._feedback_log[-self._history_limit :]),
            "curriculum_history": list(self._curriculum_history[-self._history_limit :]),
        }

    def from_state(self, state: Mapping[str, Any]) -> None:
        self._feedback_log = [
            _ensure_mapping(item)
            for item in _ensure_list(state.get("feedback_log"))
            if isinstance(item, Mapping)
        ]
        self._curriculum_history = [
            _ensure_mapping(item)
            for item in _ensure_list(state.get("curriculum_history"))
            if isinstance(item, Mapping)
        ]


class TransferLearning(_LLMBackedComponent):
    """LLM-backed knowledge transfer planner."""

    def __init__(self, *, llm_manager=None, history_limit: int = 100) -> None:
        super().__init__(llm_manager=llm_manager)
        self._domains: dict[str, Mapping[str, Any]] = {}
        self._history_limit = max(1, int(history_limit))
        self._transfer_log: list[Mapping[str, Any]] = []

    def register_domain(
        self,
        domain_name: str,
        payload: Mapping[str, Any],
    ) -> None:
        self._domains[domain_name] = _ensure_mapping(payload)

    def attempt_transfer(
        self,
        source: str,
        target: str,
        *,
        kinds: Sequence[str] | None = None,
        goal: str | None = None,
    ) -> Mapping[str, Any]:
        payload = {
            "source": source,
            "target": target,
            "goal": goal,
            "requested_kinds": list(kinds) if kinds else None,
            "source_state": self._domains.get(source, {}),
            "target_state": self._domains.get(target, {}),
            "history": list(self._transfer_log[-10:]),
        }
        response = self._call_spec("learning_transfer_mapping", payload)
        mapping = _ensure_mapping(response)
        self._transfer_log.append(mapping)
        if len(self._transfer_log) > self._history_limit:
            self._transfer_log.pop(0)
        updated_target = mapping.get("updated_target")
        if isinstance(updated_target, Mapping):
            self._domains[target] = _ensure_mapping(updated_target)
        return dict(mapping)

    def to_state(self) -> Mapping[str, Any]:
        return {
            "domains": dict(self._domains),
            "transfer_log": list(self._transfer_log[-self._history_limit :]),
        }

    def from_state(self, state: Mapping[str, Any]) -> None:
        self._domains = {
            str(name): _ensure_mapping(payload)
            for name, payload in _ensure_mapping(state.get("domains")).items()
        }
        self._transfer_log = [
            _ensure_mapping(item)
            for item in _ensure_list(state.get("transfer_log"))
            if isinstance(item, Mapping)
        ]


class ReinforcementLearning(_LLMBackedComponent):
    """Delegates policy selection/updates to ``learning_reinforcement_policy``."""

    def __init__(self, *, llm_manager=None, history_limit: int = 100) -> None:
        super().__init__(llm_manager=llm_manager)
        self._history_limit = max(1, int(history_limit))
        self._policy_log: list[Mapping[str, Any]] = []
        self._last_decision: Mapping[str, Any] | None = None

    def step(
        self,
        *,
        state: Mapping[str, Any],
        actions: Sequence[str],
        reward: float | None = None,
        context: Mapping[str, Any] | None = None,
    ) -> Mapping[str, Any]:
        payload = {
            "state": _ensure_mapping(state),
            "candidate_actions": list(actions),
            "recent_decisions": list(self._policy_log[-10:]),
        }
        if reward is not None:
            payload["reward"] = _coerce_float(reward, default=0.0)
        if context:
            payload["context"] = _ensure_mapping(context)
        response = self._call_spec("learning_reinforcement_policy", payload)
        mapping = _ensure_mapping(response)
        self._policy_log.append(mapping)
        if len(self._policy_log) > self._history_limit:
            self._policy_log.pop(0)
        self._last_decision = mapping
        return dict(mapping)

    def choose_action(
        self,
        state: str,
        actions: Sequence[str],
        *,
        context: Mapping[str, Any] | None = None,
    ) -> str:
        decision = self.step(
            state={"label": state},
            actions=actions,
            context=context,
        )
        action = decision.get("action")
        if isinstance(action, str) and action.strip():
            return action.strip()
        if actions:
            return actions[0]
        return ""

    def update_value(
        self,
        state: str,
        reward: float,
        next_state: Optional[str] = None,
        context: Mapping[str, Any] | None = None,
    ) -> float:
        # ``step`` already captured the update signal.  We expose the estimated
        # value so callers depending on the legacy API keep working.
        if not self._last_decision:
            decision = self.step(
                state={"label": state, "next_state": next_state},
                actions=[],
                reward=reward,
                context=context,
            )
        else:
            decision = self._last_decision
        return _coerce_float(decision.get("estimated_value"), default=0.0)

    def to_state(self) -> Mapping[str, Any]:
        return {
            "policy_log": list(self._policy_log[-self._history_limit :]),
        }

    def from_state(self, state: Mapping[str, Any]) -> None:
        self._policy_log = [
            _ensure_mapping(item)
            for item in _ensure_list(state.get("policy_log"))
            if isinstance(item, Mapping)
        ]
        self._last_decision = self._policy_log[-1] if self._policy_log else None


class CuriosityEngine(_LLMBackedComponent):
    """Intrinsic reward estimator orchestrated by ``learning_curiosity_update``."""

    def __init__(self, *, llm_manager=None, history_limit: int = 200) -> None:
        super().__init__(llm_manager=llm_manager)
        self._history_limit = max(1, int(history_limit))
        self._history: list[Mapping[str, Any]] = []
        self.curiosity_level: float = 0.5

    def stimulate(
        self,
        stimulus: str,
        *,
        context: Mapping[str, Any] | None = None,
    ) -> float:
        payload = {
            "stimulus": stimulus,
            "context": _ensure_mapping(context or {}),
            "history": list(self._history[-10:]),
            "curiosity_level": self.curiosity_level,
        }
        response = self._call_spec("learning_curiosity_update", payload)
        mapping = _ensure_mapping(response)
        reward = _coerce_float(
            mapping.get("reward"),
            default=0.0,
            minimum=-1.0,
            maximum=1.0,
        )
        self.curiosity_level = _coerce_float(
            mapping.get("curiosity_level"),
            default=self.curiosity_level,
            minimum=0.0,
            maximum=1.0,
        )
        self._history.append(mapping)
        if len(self._history) > self._history_limit:
            self._history.pop(0)
        return reward

    def to_state(self) -> Mapping[str, Any]:
        return {
            "curiosity_level": self.curiosity_level,
            "history": list(self._history[-self._history_limit :]),
        }

    def from_state(self, state: Mapping[str, Any]) -> None:
        self.curiosity_level = _coerce_float(
            state.get("curiosity_level"),
            default=0.5,
            minimum=0.0,
            maximum=1.0,
        )
        self._history = [
            _ensure_mapping(item)
            for item in _ensure_list(state.get("history"))
            if isinstance(item, Mapping)
        ]
