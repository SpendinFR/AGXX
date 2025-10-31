"""LLM-first natural language generation module.

The historical implementation relied on a maze of bandits, EMAs, custom
lexical heuristics and MAI handlers to gradually massage a base text into the
final answer.  The refactor collapses all of these micro-steps into a single
LLM orchestration call that returns the completed message, the sections to
surface and the moderation/safety annotations.

A light façade (`NLGContext`, `apply_mai_bids_to_nlg`, `paraphrase_light`) is
kept so the rest of the codebase can progressively migrate without dealing
with the removed heuristics.  Each helper now delegates to the same structured
LLM contract and simply exposes the resulting payload.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Optional, Sequence

from AGI_Evolutive.utils.llm_service import LLMIntegrationError, get_llm_manager


class LanguageGenerationError(RuntimeError):
    """Raised when the LLM output cannot satisfy the generation contract."""


def _coerce_string(value: Any) -> Optional[str]:
    if isinstance(value, str):
        stripped = value.strip()
        if stripped:
            return stripped
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


def _coerce_mapping(value: Any) -> Dict[str, Any]:
    if isinstance(value, Mapping):
        return {str(key): val for key, val in value.items()}
    return {}


def _coerce_sections(value: Any) -> List[Dict[str, str]]:
    sections: List[Dict[str, str]] = []
    if isinstance(value, Mapping):
        for key, val in value.items():
            text = _coerce_string(val)
            if text:
                sections.append({"name": str(key), "text": text})
        return sections
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        for item in value:
            if isinstance(item, Mapping):
                name = _coerce_string(item.get("name")) or _coerce_string(item.get("title"))
                text = _coerce_string(item.get("text")) or _coerce_string(item.get("content"))
                if text:
                    sections.append({"name": name or "section", "text": text})
    return sections


def _coerce_actions(value: Any) -> List[Dict[str, Any]]:
    if not isinstance(value, Iterable) or isinstance(value, (str, bytes)):
        return []
    actions: List[Dict[str, Any]] = []
    for item in value:
        if isinstance(item, Mapping):
            actions.append({str(key): val for key, val in item.items()})
    return actions


def _assemble_sections(sections: Sequence[Mapping[str, Any]]) -> str:
    parts: List[str] = []
    for section in sections:
        text = _coerce_string(section.get("text"))
        if text:
            parts.append(text)
    return "\n\n".join(parts).strip()


@dataclass
class NLGRequest:
    """Structured payload forwarded to the LLM generation spec."""

    base_text: str
    surface: Optional[str] = None
    dialogue: Optional[Mapping[str, Any]] = None
    reasoning: Optional[Mapping[str, Any]] = None
    contract: Optional[Mapping[str, Any]] = None
    style: Optional[Mapping[str, Any]] = None
    memory: Optional[Mapping[str, Any]] = None
    hints: Sequence[Mapping[str, Any]] = field(default_factory=tuple)
    mode: str = "reply"
    metadata: Optional[Mapping[str, Any]] = None

    def build_payload(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {"base_text": self.base_text, "mode": self.mode}
        if self.surface:
            payload["surface"] = self.surface
        if self.dialogue:
            payload["dialogue_state"] = _coerce_mapping(self.dialogue)
        if self.reasoning:
            payload["reasoning"] = _coerce_mapping(self.reasoning)
        if self.contract:
            payload["contract"] = _coerce_mapping(self.contract)
        if self.style:
            payload["style_preferences"] = _coerce_mapping(self.style)
        if self.memory:
            payload["memory"] = _coerce_mapping(self.memory)
        if self.hints:
            payload["applied_actions"] = [dict(item) for item in self.hints]
        if self.metadata:
            payload["metadata"] = _coerce_mapping(self.metadata)
        return payload


@dataclass
class NLGResult:
    """Normalized representation of the LLM response."""

    message: str
    sections: List[Dict[str, str]] = field(default_factory=list)
    tone: Optional[str] = None
    applied_actions: List[Dict[str, Any]] = field(default_factory=list)
    safety_notes: List[str] = field(default_factory=list)
    meta: Dict[str, Any] = field(default_factory=dict)
    raw: MutableMapping[str, Any] = field(default_factory=dict)

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any], *, fallback_text: str) -> "NLGResult":
        if not isinstance(payload, Mapping):
            raise LanguageGenerationError("LLM payload must be a mapping")

        message = _coerce_string(payload.get("message"))
        sections = _coerce_sections(payload.get("sections") or payload.get("structured_sections"))
        if not message:
            assembled = _assemble_sections(sections)
            message = assembled or fallback_text.strip()
        tone = _coerce_string(payload.get("tone"))
        actions = _coerce_actions(payload.get("applied_actions"))
        safety_notes = _coerce_string_list(payload.get("safety_notes") or payload.get("alerts"))
        meta = _coerce_mapping(payload.get("meta"))
        raw: MutableMapping[str, Any] = dict(payload)
        if sections and "sections" not in raw:
            raw["sections"] = [dict(section) for section in sections]
        return cls(
            message=message,
            sections=sections,
            tone=tone,
            applied_actions=actions,
            safety_notes=safety_notes,
            meta=meta,
            raw=raw,
        )


class LanguageGeneration:
    """Thin wrapper around the LLM manager for natural language generation."""

    def __init__(self, *, llm_manager=None) -> None:
        self._manager = llm_manager or get_llm_manager()
        self.last_result: Optional[NLGResult] = None

    def generate(self, request: NLGRequest) -> NLGResult:
        payload = request.build_payload()
        try:
            response = self._manager.call_dict(
                "language_nlg",
                input_payload=payload,
            )
        except LLMIntegrationError as exc:
            raise LanguageGenerationError(str(exc)) from exc
        if response is None:
            raise LanguageGenerationError("LLM returned no payload")
        result = NLGResult.from_payload(response, fallback_text=request.base_text)
        self.last_result = result
        return result


_default_generator = LanguageGeneration()


class NLGContext:
    """Compatibility façade storing the evolving reply text."""

    def __init__(self, base_text: str, apply_hint=None):
        self.base_text = base_text or ""
        self.text = self.base_text.strip()
        self._apply_hint = apply_hint or (lambda text, hint: text)
        self.actions: List[Dict[str, Any]] = []
        self.sections: List[Dict[str, str]] = []
        self.meta: Dict[str, Any] = {}
        self.raw: MutableMapping[str, Any] = {}

    def register_custom_action(self, origin: str, hint: str) -> None:
        entry = {"origin": origin, "hint": hint}
        if entry not in self.actions:
            self.actions.append(entry)

    def applied_hints(self) -> List[Dict[str, Any]]:
        return list(self.actions)

    def update_from_result(self, result: NLGResult) -> None:
        self.text = result.message
        self.sections = list(result.sections)
        self.meta = dict(result.meta)
        self.raw = dict(result.raw)
        if result.applied_actions:
            self.actions = [dict(item) for item in result.applied_actions]


def generate_reply(request: NLGRequest, *, llm_manager=None) -> NLGResult:
    if llm_manager is None:
        generator = _default_generator
    else:
        generator = LanguageGeneration(llm_manager=llm_manager)
    return generator.generate(request)


def apply_mai_bids_to_nlg(
    nlg_context: NLGContext,
    state: Optional[Mapping[str, Any]],
    predicate_registry: Optional[Mapping[str, Any]],
    *,
    contract: Optional[Mapping[str, Any]] = None,
    reasoning: Optional[Mapping[str, Any]] = None,
    metadata: Optional[Mapping[str, Any]] = None,
    llm_manager=None,
) -> NLGResult:
    """Generate the final reply via the LLM and update ``nlg_context``."""

    state = state or {}
    request = NLGRequest(
        base_text=nlg_context.text or nlg_context.base_text,
        surface=nlg_context.base_text,
        dialogue=state.get("dialogue"),
        reasoning=reasoning,
        contract=contract,
        style=metadata.get("style") if metadata else None,
        memory=state.get("memory"),
        hints=nlg_context.applied_hints(),
        metadata=metadata,
    )
    result = generate_reply(request, llm_manager=llm_manager)
    nlg_context.update_from_result(result)
    return result


def paraphrase_light(
    text: str,
    *,
    tone: Optional[str] = None,
    hints: Optional[Sequence[Mapping[str, Any]]] = None,
    llm_manager=None,
) -> str:
    """Return a lightly paraphrased text produced by the LLM contract."""

    metadata: Dict[str, Any] = {"variant": "light_paraphrase"}
    if tone:
        metadata["tone"] = tone
    request = NLGRequest(
        base_text=text,
        mode="paraphrase",
        hints=hints or (),
        metadata=metadata,
    )
    result = generate_reply(request, llm_manager=llm_manager)
    return result.message


def join_tokens(tokens: Iterable[str]) -> str:
    """Minimal token join helper kept for backwards compatibility."""

    return " ".join(str(tok) for tok in tokens if tok is not None).replace("  ", " ").strip()
