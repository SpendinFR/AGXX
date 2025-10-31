"""LLM-first semantic understanding module.

This refactor removes the historical heuristic pipeline in favour of a single
structured call to the LLM integration layer.  The contract expects the model to
return the complete semantic bundle (intent, acts, slots, needs, questions,
metadata, ...).  The module only validates the payload, updates the dialogue
state and exposes the result under the legacy :class:`UtteranceFrame` shape.
"""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Optional

from AGI_Evolutive.utils.llm_service import LLMIntegrationError, get_llm_manager

from .dialogue_state import DialogueState
from .frames import DialogueAct, UtteranceFrame


class SemanticUnderstandingError(RuntimeError):
    """Raised when the LLM understanding contract cannot be fulfilled."""


def _normalize(text: str) -> str:
    normalized = unicodedata.normalize("NFKC", text or "")
    return normalized.strip()


def _coerce_confidence(value: Any, *, default: float = 0.5) -> float:
    try:
        number = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        number = default
    if number != number:  # NaN check without math import
        return default
    return max(0.0, min(1.0, number))


def _coerce_optional_string(value: Any) -> Optional[str]:
    if isinstance(value, str):
        cleaned = value.strip()
        if cleaned:
            return cleaned
    return None


def _coerce_string_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, str):
        value = [value]
    result: List[str] = []
    if isinstance(value, Iterable):
        for item in value:
            if isinstance(item, str):
                cleaned = item.strip()
                if cleaned:
                    result.append(cleaned)
    return result


def _coerce_dialogue_acts(value: Any) -> List[DialogueAct]:
    acts: List[DialogueAct] = []
    if value is None:
        return acts
    if isinstance(value, str):
        value = [value]
    if not isinstance(value, Iterable):
        return acts
    for item in value:
        if isinstance(item, DialogueAct):
            acts.append(item)
            continue
        if not isinstance(item, str):
            continue
        key = item.strip().upper()
        if not key:
            continue
        try:
            acts.append(DialogueAct[key])
        except KeyError:
            # Allow values like "ask" instead of "ASK"
            try:
                acts.append(DialogueAct[item.strip().upper()])
            except Exception:
                continue
    # Preserve input order without duplicates
    seen = set()
    ordered: List[DialogueAct] = []
    for act in acts:
        if act not in seen:
            ordered.append(act)
            seen.add(act)
    return ordered


def _coerce_mapping(value: Any) -> Dict[str, Any]:
    if not isinstance(value, Mapping):
        return {}
    return {str(key): val for key, val in value.items()}


def _coerce_slots(value: Any) -> Dict[str, Any]:
    slots = _coerce_mapping(value)
    clean: Dict[str, Any] = {}
    for key, val in slots.items():
        normalized_key = key.strip()
        if not normalized_key:
            continue
        clean[normalized_key] = val
    return clean


@dataclass
class LLMUnderstandingResult:
    """Normalized view of the LLM payload."""

    text: str
    normalized_text: str
    intent: str
    confidence: float
    uncertainty: float
    acts: List[DialogueAct] = field(default_factory=list)
    slots: Dict[str, Any] = field(default_factory=dict)
    unknown_terms: List[str] = field(default_factory=list)
    needs: List[str] = field(default_factory=list)
    follow_up_questions: List[str] = field(default_factory=list)
    canonical_query: Optional[str] = None
    tone: Optional[str] = None
    meta: Dict[str, Any] = field(default_factory=dict)
    raw: MutableMapping[str, Any] = field(default_factory=dict)

    @classmethod
    def from_payload(
        cls,
        payload: Mapping[str, Any],
        *,
        original_text: str,
    ) -> "LLMUnderstandingResult":
        if not isinstance(payload, Mapping):
            raise SemanticUnderstandingError("LLM payload must be a mapping")

        normalized_text = _coerce_optional_string(
            payload.get("normalized_text") or payload.get("normalized")
        ) or _normalize(original_text)
        intent = _coerce_optional_string(payload.get("intent")) or "inform"
        confidence = _coerce_confidence(payload.get("confidence"), default=0.5)
        uncertainty = _coerce_confidence(payload.get("uncertainty"), default=0.35)
        acts = _coerce_dialogue_acts(payload.get("acts") or payload.get("dialogue_acts"))
        slots = _coerce_slots(payload.get("slots"))
        unknown_terms = _coerce_string_list(payload.get("unknown_terms"))
        needs = _coerce_string_list(payload.get("needs"))
        follow_up = _coerce_string_list(
            payload.get("follow_up_questions") or payload.get("followups")
        )
        canonical_query = _coerce_optional_string(payload.get("canonical_query"))
        tone = _coerce_optional_string(payload.get("tone"))
        meta = _coerce_mapping(payload.get("meta"))
        summary = _coerce_optional_string(payload.get("summary"))
        if summary and "summary" not in meta:
            meta["summary"] = summary

        raw: MutableMapping[str, Any] = dict(payload)
        return cls(
            text=original_text,
            normalized_text=normalized_text,
            intent=intent,
            confidence=confidence,
            uncertainty=uncertainty,
            acts=acts,
            slots=slots,
            unknown_terms=unknown_terms,
            needs=needs,
            follow_up_questions=follow_up,
            canonical_query=canonical_query,
            tone=tone,
            meta=meta,
            raw=raw,
        )

    def to_frame(self) -> UtteranceFrame:
        meta = dict(self.meta)
        if self.canonical_query:
            meta.setdefault("canonical_query", self.canonical_query)
        if self.tone:
            meta.setdefault("tone", self.tone)
        meta.setdefault("llm_understanding", dict(self.raw))
        if self.follow_up_questions:
            meta.setdefault("follow_up_questions", list(self.follow_up_questions))
        return UtteranceFrame(
            text=self.text,
            normalized_text=self.normalized_text,
            intent=self.intent,
            confidence=self.confidence,
            uncertainty=self.uncertainty,
            acts=list(self.acts),
            slots=dict(self.slots),
            unknown_terms=list(self.unknown_terms),
            needs=list(self.needs),
            meta=meta,
        )


class SemanticUnderstanding:
    """LLM orchestrator for semantic understanding."""

    def __init__(
        self,
        *,
        llm_manager=None,
        llm_spec: str = "language_understanding",
        state: Optional[DialogueState] = None,
    ) -> None:
        self.state = state or DialogueState()
        self._llm_spec = llm_spec
        self._llm_manager = llm_manager or get_llm_manager()
        self._last_result: Optional[LLMUnderstandingResult] = None

    @property
    def last_result(self) -> Optional[LLMUnderstandingResult]:
        return self._last_result

    def parse_utterance(self, text: str, context: Optional[Dict[str, Any]] = None) -> UtteranceFrame:
        raw_text = text or ""
        normalized = _normalize(raw_text)
        payload = {
            "utterance": raw_text,
            "normalized": normalized,
            "context": dict(context or {}),
            "dialogue_state": self.state.to_dict(),
        }

        try:
            response = self._llm_manager.call_dict(
                self._llm_spec,
                input_payload=payload,
            )
        except LLMIntegrationError as exc:  # pragma: no cover - integration failure propagated
            raise SemanticUnderstandingError(str(exc)) from exc

        result = LLMUnderstandingResult.from_payload(response, original_text=raw_text)
        frame = result.to_frame()

        for question in result.follow_up_questions:
            self.state.add_pending_question(question)
        for term in frame.unknown_terms:
            self.state.remember_unknown_term(term)

        self.state.update_with_frame(frame.to_dict())
        self._last_result = result
        return frame


__all__ = ["LLMUnderstandingResult", "SemanticUnderstanding", "SemanticUnderstandingError"]
