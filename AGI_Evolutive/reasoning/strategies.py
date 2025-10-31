"""LLM-first reasoning directive orchestrator.

This module used to combine multiple heuristic strategies (online classifiers,
scorers, Thompson sampling, etc.) to propose hypotheses, questions and action
plans.  The refactor collapses everything into a single structured LLM call
that delivers the complete reasoning directive at once.  The only logic left in
Python is responsible for light normalisation, dataclass representations and
compatibility helpers for the rest of the architecture.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Optional, Sequence

from AGI_Evolutive.utils.llm_service import LLMIntegrationError, get_llm_manager


class ReasoningFailure(RuntimeError):
    """Raised when the reasoning orchestrator cannot complete the LLM workflow."""


# ---------------------------------------------------------------------------
# Normalisation helpers
# ---------------------------------------------------------------------------

def _normalise_text(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, str):
        text = value.strip()
        return text or None
    text = str(value).strip()
    return text or None


def _normalise_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        number = float(value)
    else:
        try:
            number = float(str(value))
        except (TypeError, ValueError):
            return None
    if number != number:  # NaN
        return None
    if number in (float("inf"), float("-inf")):
        return None
    return number


def _normalise_sequence(value: Any, *, max_items: int = 12) -> List[str]:
    if value is None:
        return []
    items: List[str] = []
    if isinstance(value, str):
        text = value.strip()
        if text:
            items.append(text)
    elif isinstance(value, Iterable):
        for entry in value:
            text = _normalise_text(entry)
            if text:
                items.append(text)
            if len(items) >= max_items:
                break
    deduped: List[str] = []
    seen = set()
    for item in items:
        if item not in seen:
            deduped.append(item)
            seen.add(item)
    return deduped[:max_items]


def _normalise_mapping(value: Any, *, max_list_items: int = 16) -> Dict[str, Any]:
    if not isinstance(value, Mapping):
        return {}
    payload: Dict[str, Any] = {}
    for key, raw in value.items():
        if raw is None:
            continue
        key_str = str(key)
        if isinstance(raw, Mapping):
            payload[key_str] = _normalise_mapping(raw, max_list_items=max_list_items)
            continue
        if isinstance(raw, (list, tuple, set)):
            normalised_list: List[Any] = []
            for item in raw:
                normalised = _normalise_value(item, max_list_items=max_list_items)
                if normalised is not None:
                    normalised_list.append(normalised)
                if len(normalised_list) >= max_list_items:
                    break
            payload[key_str] = normalised_list
            continue
        normalised = _normalise_value(raw, max_list_items=max_list_items)
        if normalised is not None:
            payload[key_str] = normalised
    return payload


def _normalise_value(value: Any, *, max_list_items: int = 16) -> Any:
    if value is None:
        return None
    if isinstance(value, (bool, int)):
        return int(value)
    if isinstance(value, float):
        return _normalise_float(value)
    if isinstance(value, Mapping):
        return _normalise_mapping(value, max_list_items=max_list_items)
    if isinstance(value, (list, tuple, set)):
        result: List[Any] = []
        for item in value:
            normalised = _normalise_value(item, max_list_items=max_list_items)
            if normalised is not None:
                result.append(normalised)
            if len(result) >= max_list_items:
                break
        return result
    text = _normalise_text(value)
    if text is not None:
        return text
    return None


def _clamp_confidence(value: Optional[float]) -> Optional[float]:
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return max(0.0, min(1.0, number))


# ---------------------------------------------------------------------------
# Dataclasses describing the LLM response
# ---------------------------------------------------------------------------

@dataclass
class ReasoningQuestion:
    text: str
    priority: Optional[int] = None
    rationale: Optional[str] = None

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> "ReasoningQuestion":
        text = _normalise_text(payload.get("text") or payload.get("question") or payload)
        if not text:
            text = "Clarifier le besoin utilisateur"
        priority = None
        if "priority" in payload:
            try:
                priority = int(payload.get("priority"))
            except (TypeError, ValueError):
                priority = None
        rationale = _normalise_text(payload.get("rationale") or payload.get("notes"))
        return cls(text=text, priority=priority, rationale=rationale)

    def to_dict(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {"text": self.text}
        if self.priority is not None:
            data["priority"] = int(self.priority)
        if self.rationale:
            data["rationale"] = self.rationale
        return data


@dataclass
class ReasoningAction:
    label: str
    utility: Optional[float] = None
    priority: Optional[int] = None
    notes: List[str] = field(default_factory=list)

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> "ReasoningAction":
        label = _normalise_text(payload.get("label") or payload.get("action") or payload)
        if not label:
            label = "Continuer le raisonnement"
        utility = _clamp_confidence(_normalise_float(payload.get("utility")))
        priority = None
        if "priority" in payload:
            try:
                priority = int(payload.get("priority"))
            except (TypeError, ValueError):
                priority = None
        notes = _normalise_sequence(
            payload.get("notes")
            or payload.get("rationale")
            or payload.get("justification")
            or [],
            max_items=6,
        )
        return cls(label=label, utility=utility, priority=priority, notes=notes)

    def to_dict(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {"label": self.label}
        if self.utility is not None:
            data["utility"] = float(self.utility)
        if self.priority is not None:
            data["priority"] = int(self.priority)
        if self.notes:
            data["notes"] = list(self.notes)
        return data


@dataclass
class ReasoningProposal:
    label: str
    summary: Optional[str] = None
    confidence: Optional[float] = None
    rationale: Optional[str] = None
    supporting_evidence: List[str] = field(default_factory=list)
    actions: List[ReasoningAction] = field(default_factory=list)
    tests: List[Dict[str, Any]] = field(default_factory=list)

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> "ReasoningProposal":
        label = _normalise_text(payload.get("label") or payload.get("name") or payload)
        if not label:
            label = "Hypothèse"
        summary = _normalise_text(payload.get("summary") or payload.get("hypothesis"))
        confidence = _clamp_confidence(_normalise_float(payload.get("confidence")))
        rationale = _normalise_text(payload.get("rationale") or payload.get("notes"))
        supporting = _normalise_sequence(payload.get("support") or payload.get("evidence") or [])
        actions: List[ReasoningAction] = []
        raw_actions = payload.get("actions")
        if isinstance(raw_actions, Iterable):
            for entry in raw_actions:
                if isinstance(entry, Mapping):
                    actions.append(ReasoningAction.from_payload(entry))
        tests: List[Dict[str, Any]] = []
        raw_tests = payload.get("tests")
        if isinstance(raw_tests, Iterable):
            for entry in raw_tests:
                if isinstance(entry, Mapping):
                    tests.append(_normalise_mapping(entry))
        return cls(
            label=label,
            summary=summary,
            confidence=confidence,
            rationale=rationale,
            supporting_evidence=supporting,
            actions=actions,
            tests=tests,
        )

    def to_dict(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {"label": self.label}
        if self.summary:
            payload["summary"] = self.summary
        if self.confidence is not None:
            payload["confidence"] = float(self.confidence)
        if self.rationale:
            payload["rationale"] = self.rationale
        if self.supporting_evidence:
            payload["supporting_evidence"] = list(self.supporting_evidence)
        if self.actions:
            payload["actions"] = [action.to_dict() for action in self.actions]
        if self.tests:
            payload["tests"] = [dict(test) for test in self.tests]
        return payload


@dataclass
class ReasoningEpisodeDirective:
    """Structured reasoning output returned by the LLM orchestrator."""

    summary: str
    confidence: Optional[float]
    hypothesis: Dict[str, Any]
    proposals: List[ReasoningProposal] = field(default_factory=list)
    tests: List[Dict[str, Any]] = field(default_factory=list)
    questions: List[ReasoningQuestion] = field(default_factory=list)
    actions: List[ReasoningAction] = field(default_factory=list)
    learning: List[str] = field(default_factory=list)
    notes: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    cost: Optional[float] = None
    duration: Optional[float] = None
    raw: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> "ReasoningEpisodeDirective":
        summary = _normalise_text(payload.get("summary")) or "Synthèse indisponible"
        confidence = _clamp_confidence(_normalise_float(payload.get("confidence")))
        hypothesis = _normalise_mapping(payload.get("hypothesis") or {})
        proposals: List[ReasoningProposal] = []
        raw_proposals = payload.get("proposals")
        if isinstance(raw_proposals, Iterable):
            for entry in raw_proposals:
                if isinstance(entry, Mapping):
                    proposals.append(ReasoningProposal.from_payload(entry))
        tests: List[Dict[str, Any]] = []
        raw_tests = payload.get("tests")
        if isinstance(raw_tests, Iterable):
            for entry in raw_tests:
                if isinstance(entry, Mapping):
                    tests.append(_normalise_mapping(entry))
                else:
                    text = _normalise_text(entry)
                    if text:
                        tests.append({"description": text})
        questions: List[ReasoningQuestion] = []
        raw_questions = payload.get("questions") or payload.get("follow_up_questions")
        if isinstance(raw_questions, Iterable):
            for entry in raw_questions:
                if isinstance(entry, Mapping):
                    questions.append(ReasoningQuestion.from_payload(entry))
                else:
                    question_text = _normalise_text(entry)
                    if question_text:
                        questions.append(ReasoningQuestion(text=question_text))
        actions: List[ReasoningAction] = []
        raw_actions = payload.get("actions")
        if isinstance(raw_actions, Iterable):
            for entry in raw_actions:
                if isinstance(entry, Mapping):
                    actions.append(ReasoningAction.from_payload(entry))
                else:
                    label = _normalise_text(entry)
                    if label:
                        actions.append(ReasoningAction(label=label))
        learning = _normalise_sequence(payload.get("learning") or payload.get("insights") or [])
        notes = _normalise_text(payload.get("notes") or payload.get("rationale"))
        metadata = _normalise_mapping(payload.get("metadata") or {})
        cost = _normalise_float(payload.get("cost"))
        duration = _normalise_float(payload.get("time") or payload.get("duration"))
        raw = _normalise_mapping(payload)
        return cls(
            summary=summary,
            confidence=confidence,
            hypothesis=hypothesis,
            proposals=proposals,
            tests=tests,
            questions=questions,
            actions=actions,
            learning=learning,
            notes=notes,
            metadata=metadata,
            cost=cost,
            duration=duration,
            raw=raw,
        )

    def to_dict(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "summary": self.summary,
            "confidence": self.confidence,
            "hypothesis": dict(self.hypothesis),
            "proposals": [proposal.to_dict() for proposal in self.proposals],
            "tests": [dict(test) for test in self.tests],
            "questions": [question.to_dict() for question in self.questions],
            "actions": [action.to_dict() for action in self.actions],
            "learning": list(self.learning),
            "notes": self.notes,
            "metadata": dict(self.metadata),
            "cost": self.cost,
            "duration": self.duration,
            "raw_llm_result": dict(self.raw),
        }
        if self.confidence is not None:
            payload["final_confidence"] = float(self.confidence)
        else:
            payload["final_confidence"] = None
        chosen = self.hypothesis.get("label") or self.hypothesis.get("summary") or self.hypothesis.get("title")
        if chosen:
            payload["chosen_hypothesis"] = chosen
        legacy_tests = []
        for test in self.tests:
            text = (
                _normalise_text(test.get("description"))
                or _normalise_text(test.get("summary"))
                or _normalise_text(test.get("label"))
            )
            if text:
                legacy_tests.append(text)
        if legacy_tests:
            payload["tests_text"] = legacy_tests
        if self.notes:
            payload.setdefault("notes", self.notes)
        return payload


# ---------------------------------------------------------------------------
# Public orchestration helper
# ---------------------------------------------------------------------------

def run_reasoning_episode(
    *,
    prompt: str,
    context: Optional[Mapping[str, Any]] = None,
    toolkit: Optional[Mapping[str, Any]] = None,
    llm_manager: Any | None = None,
) -> ReasoningEpisodeDirective:
    """Execute the reasoning LLM contract once and return a structured directive."""

    if not isinstance(prompt, str) or not prompt.strip():
        raise ValueError("reasoning prompt must be a non-empty string")
    payload: Dict[str, Any] = {"prompt": prompt.strip()}
    if context:
        context_payload = _normalise_mapping(context)
        if context_payload:
            payload["context"] = context_payload
    if toolkit:
        toolkit_payload = _normalise_mapping(toolkit)
        if toolkit_payload:
            payload["toolkit"] = toolkit_payload
    manager = llm_manager or get_llm_manager()
    try:
        response = manager.call_dict("reasoning_episode", input_payload=payload)
    except LLMIntegrationError as exc:  # pragma: no cover - defensive
        raise ReasoningFailure(f"reasoning_episode failed: {exc}") from exc
    if not isinstance(response, Mapping):
        raise ReasoningFailure("reasoning_episode returned an invalid payload")
    return ReasoningEpisodeDirective.from_payload(response)


__all__ = [
    "ReasoningAction",
    "ReasoningEpisodeDirective",
    "ReasoningFailure",
    "ReasoningProposal",
    "ReasoningQuestion",
    "run_reasoning_episode",
]
