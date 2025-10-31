"""LLM-first intent ingestion orchestrator.

This module consolidates all historical preprocessing, heuristic pattern
matching, and fallback models into a single call to the local LLM.  The
response is normalised into :class:`IntentIngestionResult` so that the rest of
the runtime manipulates a structured object with the complete bundle of
insights (intent label, confidence, tone, urgency, safety, etc.).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Iterable, Mapping, MutableMapping

from AGI_Evolutive.utils.llm_service import get_llm_manager


@dataclass(frozen=True)
class IntentIngestionResult:
    """Structured view of the LLM intent analysis."""

    label: str
    confidence: float
    rationale: str | None
    tone: str | None
    sentiment: str | None
    priority: str | None
    urgency: str | None
    safety_flags: tuple[str, ...]
    summary: str | None
    follow_up_questions: tuple[str, ...]
    entities: tuple[Mapping[str, Any], ...]
    raw_response: Mapping[str, Any] = field(repr=False, default_factory=dict)

    def as_dict(self) -> Mapping[str, Any]:
        """Return a JSON-serialisable representation of the analysis."""

        return {
            "label": self.label,
            "confidence": self.confidence,
            "rationale": self.rationale,
            "tone": self.tone,
            "sentiment": self.sentiment,
            "priority": self.priority,
            "urgency": self.urgency,
            "safety_flags": list(self.safety_flags),
            "summary": self.summary,
            "follow_up_questions": list(self.follow_up_questions),
            "entities": [dict(entity) for entity in self.entities],
            "raw_response": dict(self.raw_response),
        }


class IntentIngestionOrchestrator:
    """Facade responsible for invoking the LLM intent ingestion spec."""

    def __init__(self, *, manager=None):
        self._manager = manager or get_llm_manager()

    def analyze(
        self,
        utterance: str,
        *,
        context: Mapping[str, Any] | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> IntentIngestionResult:
        """Analyse *utterance* via the LLM and return a structured result."""

        if not isinstance(utterance, str) or not utterance.strip():
            raise ValueError("utterance must be a non-empty string")

        payload: MutableMapping[str, Any] = {"utterance": utterance.strip()}
        if context:
            payload["context"] = dict(context)
        if metadata:
            payload["metadata"] = dict(metadata)

        response = self._manager.call_dict(
            "intent_ingestion",
            input_payload=payload,
        )
        return _parse_llm_response(response)


_default_orchestrator: IntentIngestionOrchestrator | None = None


def analyze(
    utterance: str,
    *,
    context: Mapping[str, Any] | None = None,
    metadata: Mapping[str, Any] | None = None,
    orchestrator: IntentIngestionOrchestrator | None = None,
) -> IntentIngestionResult:
    """Convenience wrapper using a shared orchestrator instance."""

    if orchestrator is None:
        global _default_orchestrator
        if _default_orchestrator is None:
            _default_orchestrator = IntentIngestionOrchestrator()
        orchestrator = _default_orchestrator
    return orchestrator.analyze(utterance, context=context, metadata=metadata)


def _parse_llm_response(response: Any) -> IntentIngestionResult:
    if not isinstance(response, Mapping):
        raise ValueError("intent_ingestion LLM response must be a mapping")

    intent_section = response.get("intent")
    if not isinstance(intent_section, Mapping):
        raise ValueError("intent field must be a mapping with label/confidence")

    label = _clean_label(intent_section.get("label"))
    confidence = _coerce_float(intent_section.get("confidence"), default=0.0)
    rationale = _optional_str(
        intent_section.get("rationale")
        or intent_section.get("justification")
        or intent_section.get("reason")
    )

    tone = _optional_str(response.get("tone"))
    sentiment = _optional_str(response.get("sentiment"))
    priority = _optional_str(response.get("priority"))
    urgency = _optional_str(response.get("urgency"))
    summary = _optional_str(response.get("summary"))

    follow_up_questions = _collect_strings(
        response.get("follow_up")
        or response.get("follow_up_questions")
        or response.get("next_questions")
    )

    safety_flags = _collect_strings(
        (response.get("safety") or {}).get("flags")
        if isinstance(response.get("safety"), Mapping)
        else None
    )
    if not safety_flags:
        safety_flags = _collect_strings(response.get("safety_flags"))

    entities = _collect_entities(response.get("entities"))

    raw_response = MappingProxyType(dict(response))

    return IntentIngestionResult(
        label=label,
        confidence=confidence,
        rationale=rationale,
        tone=tone,
        sentiment=sentiment,
        priority=priority,
        urgency=urgency,
        safety_flags=safety_flags,
        summary=summary,
        follow_up_questions=follow_up_questions,
        entities=entities,
        raw_response=raw_response,
    )


def _clean_label(value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("intent label must be a non-empty string")
    cleaned = value.strip().upper().replace(" ", "_")
    return cleaned


def _optional_str(value: Any) -> str | None:
    if isinstance(value, str):
        cleaned = value.strip()
        return cleaned or None
    return None


def _coerce_float(value: Any, *, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def _collect_strings(candidate: Any) -> tuple[str, ...]:
    if candidate is None:
        return tuple()
    if isinstance(candidate, str):
        cleaned = candidate.strip()
        return (cleaned,) if cleaned else tuple()
    if isinstance(candidate, Mapping):
        return _collect_strings(candidate.get("items"))
    if isinstance(candidate, Iterable):
        values: list[str] = []
        for item in candidate:
            if isinstance(item, str):
                cleaned = item.strip()
                if cleaned:
                    values.append(cleaned)
        return tuple(values)
    return tuple()


def _collect_entities(candidate: Any) -> tuple[Mapping[str, Any], ...]:
    if candidate is None:
        return tuple()
    if isinstance(candidate, Mapping):
        return (_normalise_entity(candidate),)
    if isinstance(candidate, Iterable):
        values = []
        for item in candidate:
            if isinstance(item, Mapping):
                values.append(_normalise_entity(item))
        return tuple(values)
    return tuple()


def _normalise_entity(entity: Mapping[str, Any]) -> Mapping[str, Any]:
    normalised: dict[str, Any] = {}
    for key, value in entity.items():
        if isinstance(key, str):
            normalised[key] = value
    return MappingProxyType(normalised)


__all__ = [
    "IntentIngestionResult",
    "IntentIngestionOrchestrator",
    "analyze",
]
