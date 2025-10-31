"""LLM-managed social interaction rule primitives."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, MutableMapping, Sequence

from AGI_Evolutive.utils.jsonsafe import json_sanitize
from AGI_Evolutive.utils.llm_service import LLMIntegrationError, get_llm_manager


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return low
    return max(low, min(high, number))


def _ensure_mapping(value: Any) -> MutableMapping[str, Any]:
    if isinstance(value, Mapping):
        return {str(key): val for key, val in value.items()}
    return {}


def _ensure_sequence(value: Any) -> list[Any]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return list(value)
    if value is None:
        return []
    return [value]


@dataclass(frozen=True)
class Predicate:
    key: str
    operator: str
    value: Any = None
    weight: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "operator": self.operator,
            "value": self.value,
            "weight": self.weight,
        }

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "Predicate":
        data = _ensure_mapping(payload)
        return cls(
            key=str(data.get("key") or data.get("name") or "context"),
            operator=str(data.get("operator") or data.get("op") or "eq"),
            value=data.get("value"),
            weight=float(data.get("weight", 1.0) or 1.0),
        )


@dataclass(frozen=True)
class TacticSpec:
    name: str
    params: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "params": dict(self.params)}

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "TacticSpec":
        data = _ensure_mapping(payload)
        return cls(name=str(data.get("name") or data.get("tactic") or ""), params=_ensure_mapping(data.get("params")))


@dataclass
class InteractionRule:
    """Lightweight container around an LLM-derived interaction rule."""

    id: str
    title: str
    tactic: TacticSpec
    predicates: tuple[Predicate, ...]
    confidence: float = 0.7
    rationale: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "InteractionRule":
        data = _ensure_mapping(payload)
        rule_id = str(data.get("id") or data.get("rule_id") or uuid.uuid4())
        tactic = TacticSpec.from_mapping(data.get("tactic") or {})
        predicates = tuple(
            Predicate.from_mapping(item) for item in _ensure_sequence(data.get("predicates") or data.get("context_predicates"))
        )
        return cls(
            id=rule_id,
            title=str(data.get("title") or data.get("label") or tactic.name or "interaction_rule"),
            tactic=tactic,
            predicates=predicates,
            confidence=clamp(data.get("confidence", 0.7)),
            rationale=data.get("rationale") or data.get("explanation"),
            metadata=_ensure_mapping(data.get("metadata")),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "tactic": self.tactic.to_dict(),
            "predicates": [pred.to_dict() for pred in self.predicates],
            "confidence": self.confidence,
            "rationale": self.rationale,
            "metadata": dict(self.metadata),
        }


class ContextBuilder:
    """Builds a social interaction context via a single LLM call."""

    def __init__(self, arch: Any, *, llm_manager: Any | None = None, spec_key: str = "social_interaction_context") -> None:
        self.arch = arch
        self.spec_key = spec_key
        self.llm_manager = llm_manager or get_llm_manager()

    # ------------------------------------------------------------------
    @classmethod
    def build(
        cls,
        arch: Any,
        extra: Mapping[str, Any] | None = None,
        *,
        llm_manager: Any | None = None,
    ) -> Mapping[str, Any]:
        return cls(arch, llm_manager=llm_manager).snapshot(extra=extra)

    # ------------------------------------------------------------------
    def snapshot(self, extra: Mapping[str, Any] | None = None) -> Mapping[str, Any]:
        payload = self._payload(extra=extra)
        try:
            response = self.llm_manager.call_dict(
                self.spec_key,
                input_payload=json_sanitize(payload),
            )
        except LLMIntegrationError:
            raise
        if not isinstance(response, Mapping):
            return payload
        sanitized = _ensure_mapping(response)
        sanitized.setdefault("baseline", payload.get("baseline"))
        return sanitized

    # ------------------------------------------------------------------
    def _payload(self, extra: Mapping[str, Any] | None = None) -> dict[str, Any]:
        return {
            "baseline": self._baseline_context(),
            "history": self._conversation_history(),
            "agent_state": self._agent_state(),
            "extra": json_sanitize(extra) if isinstance(extra, Mapping) else None,
        }

    def _baseline_context(self) -> Mapping[str, Any]:
        baseline: dict[str, Any] = {}
        for attr in ("persona_id", "persona_profile", "voice_profile", "user_id"):
            value = getattr(self.arch, attr, None)
            if value is not None:
                baseline[attr] = value
        try:
            memory = getattr(self.arch, "memory", None)
            if memory and hasattr(memory, "current_topics"):
                baseline["topics"] = list(memory.current_topics() or [])  # type: ignore[arg-type]
        except Exception:
            pass
        return baseline

    def _conversation_history(self) -> list[Mapping[str, Any]]:
        history: list[Mapping[str, Any]] = []
        turns = getattr(self.arch, "conversation_history", None)
        if isinstance(turns, Iterable):
            for turn in list(turns)[-8:]:
                if isinstance(turn, Mapping):
                    speaker = str(turn.get("speaker") or turn.get("role") or "")
                    text = str(turn.get("text") or turn.get("content") or "")
                    if text:
                        history.append({"speaker": speaker, "text": text})
        return history

    def _agent_state(self) -> Mapping[str, Any]:
        state: dict[str, Any] = {}
        for attr in ("pending_questions", "mood", "persona_alignment"):
            value = getattr(self.arch, attr, None)
            if value is not None:
                state[attr] = value
        try:
            qm = getattr(self.arch, "question_manager", None)
            if qm:
                state["pending_questions_count"] = len(getattr(qm, "pending_questions", []) or [])
        except Exception:
            pass
        try:
            planner = getattr(self.arch, "planner", None)
            if planner and hasattr(planner, "active_goals"):
                active = list(planner.active_goals())  # type: ignore[arg-type]
                state["active_goals"] = active[:5]
        except Exception:
            pass
        state["timestamp"] = time.time()
        return state
