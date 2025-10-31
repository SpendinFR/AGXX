"""LLM-first helpers for representing utterances."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Mapping, Optional

from AGI_Evolutive.utils.llm_service import LLMIntegrationError, get_llm_manager


class DialogueAct(Enum):
    ASK = auto()
    INFORM = auto()
    REQUEST = auto()
    FEEDBACK_POS = auto()
    FEEDBACK_NEG = auto()
    GREET = auto()
    BYE = auto()
    THANKS = auto()
    META_HELP = auto()
    CLARIFY = auto()
    REFLECT = auto()


@dataclass
class UtteranceFrame:
    text: str
    normalized_text: str
    intent: str
    confidence: float
    uncertainty: float
    acts: List[DialogueAct] = field(default_factory=list)
    slots: Dict[str, Any] = field(default_factory=dict)
    unknown_terms: List[str] = field(default_factory=list)
    needs: List[str] = field(default_factory=list)
    meta: Dict[str, Any] = field(default_factory=dict)

    @property
    def surface_form(self) -> str:
        return self.text

    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "normalized_text": self.normalized_text,
            "intent": self.intent,
            "confidence": self.confidence,
            "uncertainty": self.uncertainty,
            "acts": [act.name for act in self.acts],
            "slots": dict(self.slots),
            "unknown_terms": list(self.unknown_terms),
            "needs": list(self.needs),
            "meta": dict(self.meta),
        }

    @classmethod
    def from_llm_payload(cls, payload: Mapping[str, Any], *, original_text: str) -> "UtteranceFrame":
        if not isinstance(payload, Mapping):
            raise LLMIntegrationError("LLM frame payload must be a mapping")

        normalized = str(payload.get("normalized_text") or payload.get("normalized") or original_text).strip()
        if not normalized:
            normalized = original_text

        intent = str(payload.get("intent") or "inform").strip() or "inform"
        confidence = float(payload.get("confidence") or 0.55)
        uncertainty = float(payload.get("uncertainty") or 0.35)
        confidence = max(0.0, min(1.0, confidence))
        uncertainty = max(0.0, min(1.0, uncertainty))

        acts: List[DialogueAct] = []
        for item in payload.get("acts") or payload.get("dialogue_acts") or []:
            if isinstance(item, DialogueAct):
                acts.append(item)
                continue
            if isinstance(item, str):
                key = item.strip().upper()
                try:
                    acts.append(DialogueAct[key])
                except KeyError:
                    continue

        slots: Dict[str, Any] = {}
        raw_slots = payload.get("slots")
        if isinstance(raw_slots, Mapping):
            for key, value in raw_slots.items():
                if isinstance(key, str) and key.strip():
                    slots[key.strip()] = value

        unknown_terms: List[str] = []
        raw_unknowns = payload.get("unknown_terms")
        if isinstance(raw_unknowns, list):
            for term in raw_unknowns:
                if isinstance(term, str) and term.strip():
                    unknown_terms.append(term.strip())

        needs: List[str] = []
        raw_needs = payload.get("needs")
        if isinstance(raw_needs, list):
            for need in raw_needs:
                if isinstance(need, str) and need.strip():
                    needs.append(need.strip())

        meta: Dict[str, Any] = {}
        raw_meta = payload.get("meta")
        if isinstance(raw_meta, Mapping):
            meta.update({str(k): v for k, v in raw_meta.items()})
        summary = payload.get("summary")
        if isinstance(summary, str) and summary.strip():
            meta.setdefault("summary", summary.strip())
        meta.setdefault("llm_payload", dict(payload))

        return cls(
            text=original_text,
            normalized_text=normalized,
            intent=intent,
            confidence=confidence,
            uncertainty=uncertainty,
            acts=acts,
            slots=slots,
            unknown_terms=unknown_terms,
            needs=needs,
            meta=meta,
        )


def analyze_utterance(
    text: str,
    *,
    normalized_text: Optional[str] = None,
    intent_hint: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
    llm_manager=None,
    llm_spec: str = "language_frames",
) -> UtteranceFrame:
    manager = llm_manager or get_llm_manager()
    payload = {
        "utterance": text or "",
        "normalized": normalized_text or (text or "").strip(),
        "intent_hint": intent_hint,
        "context": dict(context or {}),
    }
    response = manager.call_dict(llm_spec, input_payload=payload)
    return UtteranceFrame.from_llm_payload(response, original_text=text or "")


__all__ = ["DialogueAct", "UtteranceFrame", "analyze_utterance"]
