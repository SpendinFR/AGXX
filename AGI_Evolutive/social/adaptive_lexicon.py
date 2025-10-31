"""LLM-first adaptive lexicon orchestration."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Mapping, MutableMapping, Sequence

from AGI_Evolutive.utils.jsonsafe import json_sanitize
from AGI_Evolutive.utils.llm_service import LLMIntegrationError, get_llm_manager

LOGGER = logging.getLogger(__name__)


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


@dataclass
class LexiconState:
    """Represents the LLM-managed lexicon snapshot."""

    tokens: tuple[Mapping[str, Any], ...] = field(default_factory=tuple)
    dormant_tokens: tuple[Mapping[str, Any], ...] = field(default_factory=tuple)
    metadata: Mapping[str, Any] = field(default_factory=dict)

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any] | None) -> "LexiconState":
        if not isinstance(payload, Mapping):
            return cls()
        active = tuple(
            _ensure_mapping(item) for item in _ensure_sequence(payload.get("tokens"))
        )
        dormant = tuple(
            _ensure_mapping(item) for item in _ensure_sequence(payload.get("dormant_tokens"))
        )
        metadata = _ensure_mapping(payload.get("metadata"))
        return cls(tokens=active, dormant_tokens=dormant, metadata=metadata)

    def to_dict(self) -> dict[str, Any]:
        return {
            "tokens": [dict(item) for item in self.tokens],
            "dormant_tokens": [dict(item) for item in self.dormant_tokens],
            "metadata": dict(self.metadata),
        }


@dataclass
class AdaptiveLexicon:
    """Delegates lexicon management to the social_adaptive_lexicon LLM spec."""

    arch: Any
    spec_key: str = "social_adaptive_lexicon"
    llm_manager: Any | None = None

    def __post_init__(self) -> None:
        if self.llm_manager is None:
            self.llm_manager = get_llm_manager()
        container = getattr(self.arch, "_adaptive_lexicon_state", None)
        if not isinstance(container, dict):
            container = {}
            setattr(self.arch, "_adaptive_lexicon_state", container)
        self._state_container = container

    # ------------------------------------------------------------------
    # state management helpers
    def _current_state(self) -> LexiconState:
        return LexiconState.from_payload(self._state_container.get("state"))

    def _persist_response(self, response: Mapping[str, Any]) -> None:
        state = LexiconState.from_payload(response.get("state"))
        self._state_container["state"] = state.to_dict()
        self._state_container["last_response"] = json_sanitize(response)

    def _base_payload(
        self,
        message: str,
        *,
        mode: str,
        reward: float | None = None,
        confidence: float | None = None,
        user_id: str | None = None,
        context: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "mode": mode,
            "message": message or "",
            "state": self._current_state().to_dict(),
            "user_id": user_id or getattr(self.arch, "user_id", None),
        }
        if reward is not None:
            payload["reward"] = max(0.0, min(1.0, float(reward)))
        if confidence is not None:
            payload["confidence"] = max(0.0, min(1.0, float(confidence)))
        if isinstance(context, Mapping):
            payload["context"] = json_sanitize(context)
        return payload

    def _call_llm(self, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        try:
            response = self.llm_manager.call_dict(
                self.spec_key,
                input_payload=json_sanitize(payload),
            )
        except LLMIntegrationError:
            LOGGER.exception("Adaptive lexicon LLM call failed")
            raise
        if not isinstance(response, Mapping):
            return {}
        self._persist_response(response)
        return response

    # ------------------------------------------------------------------
    # public API mirroring the legacy surface
    def match(
        self,
        user_msg: str,
        polarity: str = "pos",
        user_id: str | None = None,
        *,
        context: Mapping[str, Any] | None = None,
    ) -> bool:
        payload = self._base_payload(
            user_msg,
            mode="match",
            user_id=user_id,
            context=context,
        )
        payload["polarity"] = polarity
        response = self._call_llm(payload)
        return bool(response.get("matched", False))

    def observe_message(
        self,
        user_msg: str,
        *,
        reward01: float,
        confidence: float = 0.5,
        user_id: str | None = None,
        context: Mapping[str, Any] | None = None,
    ) -> Mapping[str, Any]:
        payload = self._base_payload(
            user_msg,
            mode="observe",
            reward=reward01,
            confidence=confidence,
            user_id=user_id,
            context=context,
        )
        response = self._call_llm(payload)
        return _ensure_mapping(response)

    # compatibility helpers -------------------------------------------------
    def last_response(self) -> Mapping[str, Any]:
        stored = self._state_container.get("last_response")
        return _ensure_mapping(stored)
