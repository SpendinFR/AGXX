"""LLM-first conversation context builder.

This module collapses the historical heuristic stack (TTL caches, online topic
learning, persona overrides, sequence mining, etc.) into a single structured
LLM call.  The builder now gathers the minimal conversational state (recent
messages, persona hints, consolidated lessons) and delegates the full
contextualisation work to the model.  The returned payload is normalised and
exposed through a compact dictionary for the rest of the runtime.
"""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Optional

from AGI_Evolutive.utils.llm_service import LLMIntegrationError, get_llm_manager


class ConversationContextError(RuntimeError):
    """Raised when the LLM conversation context cannot be produced."""


def _normalize_text(text: str) -> str:
    normalized = unicodedata.normalize("NFKC", text or "")
    return normalized.strip()


def _coerce_float(value: Any) -> Optional[float]:
    try:
        number = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    if number != number:  # NaN
        return None
    return number


def _coerce_string(value: Any) -> Optional[str]:
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


def _coerce_mapping(value: Any) -> Dict[str, Any]:
    if not isinstance(value, Mapping):
        return {}
    return {str(key): val for key, val in value.items()}


def _coerce_action_list(value: Any) -> List[Dict[str, Any]]:
    if not isinstance(value, Iterable):
        return []
    actions: List[Dict[str, Any]] = []
    for item in value:
        if isinstance(item, Mapping):
            action = {str(k): v for k, v in item.items()}
            if action:
                actions.append(action)
    return actions


@dataclass
class ConversationMessage:
    """Snapshot of a recent conversational exchange."""

    speaker: Optional[str]
    text: str
    ts: Optional[float] = None
    kind: Optional[str] = None
    tags: List[str] = field(default_factory=list)

    @classmethod
    def from_memory(cls, memo: Mapping[str, Any]) -> "ConversationMessage":
        speaker = _coerce_string(
            memo.get("speaker")
            or memo.get("role")
            or memo.get("author")
            or memo.get("source")
        )
        text = _normalize_text(str(memo.get("text") or memo.get("content") or ""))
        ts = _coerce_float(memo.get("ts") or memo.get("timestamp") or memo.get("t"))
        kind = _coerce_string(memo.get("kind") or memo.get("memory_type"))
        raw_tags = memo.get("tags")
        tags = [tag for tag in _coerce_string_list(raw_tags)]
        return cls(speaker=speaker, text=text, ts=ts, kind=kind, tags=tags)

    def to_payload(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {"text": self.text}
        if self.speaker:
            payload["speaker"] = self.speaker
        if self.ts is not None:
            payload["ts"] = self.ts
        if self.kind:
            payload["kind"] = self.kind
        if self.tags:
            payload["tags"] = list(self.tags)
        return payload


@dataclass
class LLMConversationContext:
    """Normalised view of the LLM response."""

    last_message: str
    recent_messages: List[ConversationMessage]
    summary_bullets: List[str] = field(default_factory=list)
    summary_text: Optional[str] = None
    topics: List[str] = field(default_factory=list)
    topics_meta: List[Mapping[str, Any]] = field(default_factory=list)
    key_moments: List[str] = field(default_factory=list)
    user_style: Dict[str, Any] = field(default_factory=dict)
    follow_up_questions: List[str] = field(default_factory=list)
    recommended_actions: List[Dict[str, Any]] = field(default_factory=list)
    alerts: List[str] = field(default_factory=list)
    tone: Optional[str] = None
    notes: List[str] = field(default_factory=list)
    meta: Dict[str, Any] = field(default_factory=dict)
    raw: MutableMapping[str, Any] = field(default_factory=dict)

    @classmethod
    def from_payload(
        cls,
        payload: Mapping[str, Any],
        *,
        last_message: str,
        recent_messages: List[ConversationMessage],
    ) -> "LLMConversationContext":
        if not isinstance(payload, Mapping):
            raise ConversationContextError("LLM payload must be a mapping")

        summary_field = payload.get("summary")
        summary_bullets = _coerce_string_list(summary_field)
        summary_text = _coerce_string(payload.get("summary_text"))
        if summary_text is None and isinstance(summary_field, str):
            summary_text = summary_field.strip()

        topics_meta: List[Mapping[str, Any]] = []
        topics: List[str] = []
        for item in payload.get("topics") or []:
            if isinstance(item, Mapping):
                label = _coerce_string(item.get("label") or item.get("topic"))
                if label:
                    topics.append(label)
                topics_meta.append({str(k): v for k, v in item.items()})
            elif isinstance(item, str):
                cleaned = item.strip()
                if cleaned:
                    topics.append(cleaned)

        key_moments = _coerce_string_list(payload.get("key_moments"))
        follow_ups = _coerce_string_list(payload.get("follow_up_questions"))
        alerts = _coerce_string_list(payload.get("alerts"))
        notes = _coerce_string_list(payload.get("notes"))
        tone = _coerce_string(payload.get("tone"))
        user_style = _coerce_mapping(payload.get("user_style"))
        meta = _coerce_mapping(payload.get("meta"))
        recommended_actions = _coerce_action_list(payload.get("recommended_actions"))

        raw: MutableMapping[str, Any] = dict(payload)
        return cls(
            last_message=last_message,
            recent_messages=recent_messages,
            summary_bullets=summary_bullets,
            summary_text=summary_text,
            topics=topics,
            topics_meta=topics_meta,
            key_moments=key_moments,
            user_style=user_style,
            follow_up_questions=follow_ups,
            recommended_actions=recommended_actions,
            alerts=alerts,
            tone=tone,
            notes=notes,
            meta=meta,
            raw=raw,
        )

    def to_dict(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {
            "last_message": self.last_message,
            "recent_messages": [msg.to_payload() for msg in self.recent_messages],
            "summary": list(self.summary_bullets),
            "summary_text": self.summary_text,
            "topics": list(self.topics),
            "key_moments": list(self.key_moments),
            "user_style": dict(self.user_style),
            "follow_up_questions": list(self.follow_up_questions),
            "recommended_actions": [dict(action) for action in self.recommended_actions],
            "alerts": list(self.alerts),
            "tone": self.tone,
            "notes": list(self.notes),
            "meta": dict(self.meta),
            "llm_summary": dict(self.raw),
        }
        if self.topics_meta:
            data["llm_topics"] = [dict(item) for item in self.topics_meta]
        return data


class ContextBuilder:
    """Conversation context orchestrator relying exclusively on the LLM."""

    def __init__(
        self,
        arch,
        *,
        llm_spec: str = "conversation_context",
        recent_limit: int = 12,
        llm_manager=None,
    ) -> None:
        self.arch = arch
        self._llm_spec = llm_spec
        self._recent_limit = max(1, int(recent_limit))
        self._llm_manager = llm_manager or get_llm_manager()
        self._last_result: Optional[LLMConversationContext] = None

    @property
    def last_result(self) -> Optional[LLMConversationContext]:
        return self._last_result

    def _memory_source(self):
        return getattr(self.arch, "memory", None)

    def _recent_messages(self) -> List[ConversationMessage]:
        source = self._memory_source()
        if source is None:
            return []
        try:
            records = source.get_recent_memories(n=self._recent_limit)
        except TypeError:
            records = source.get_recent_memories(limit=self._recent_limit)
        except Exception:
            return []
        messages: List[ConversationMessage] = []
        for memo in records:
            if isinstance(memo, Mapping):
                message = ConversationMessage.from_memory(memo)
                if message.text:
                    messages.append(message)
        return messages[-self._recent_limit :]

    def _lessons(self) -> List[str]:
        consolidator = getattr(self.arch, "consolidator", None)
        if not consolidator:
            return []
        state = getattr(consolidator, "state", {})
        lessons = state.get("lessons") if isinstance(state, Mapping) else None
        return _coerce_string_list(lessons)

    def _persona(self) -> Mapping[str, Any]:
        user_model = getattr(self.arch, "user_model", None)
        if user_model and hasattr(user_model, "describe"):
            try:
                desc = user_model.describe() or {}
            except Exception:
                desc = {}
            if isinstance(desc, Mapping):
                return desc
        return {}

    def build(
        self,
        user_message: str,
        *,
        extra: Optional[Mapping[str, Any]] = None,
    ) -> Dict[str, Any]:
        last_message = _normalize_text(user_message)
        recent = self._recent_messages()
        persona = self._persona()
        lessons = self._lessons()

        payload: Dict[str, Any] = {
            "last_message": last_message,
            "recent_messages": [msg.to_payload() for msg in recent],
        }
        if persona:
            payload["persona"] = dict(persona)
        if lessons:
            payload["lessons"] = list(lessons)
        if extra:
            payload["extra"] = _coerce_mapping(extra)

        try:
            response = self._llm_manager.call_dict(
                self._llm_spec,
                input_payload=payload,
            )
        except LLMIntegrationError as exc:  # pragma: no cover - integration failure propagated
            raise ConversationContextError(str(exc)) from exc

        result = LLMConversationContext.from_payload(
            response,
            last_message=last_message,
            recent_messages=recent,
        )
        self._last_result = result
        return result.to_dict()


__all__ = [
    "ConversationContextError",
    "ConversationMessage",
    "ContextBuilder",
    "LLMConversationContext",
]
