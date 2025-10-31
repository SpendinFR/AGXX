"""LLM orchestrator for mining social interaction rules."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Sequence

from AGI_Evolutive.utils.jsonsafe import json_sanitize
from AGI_Evolutive.utils.llm_service import LLMIntegrationError, get_llm_manager

from .interaction_rule import InteractionRule


def _ensure_sequence(value: Any) -> list[Any]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return list(value)
    if value is None:
        return []
    return [value]


@dataclass
class InteractionMiner:
    arch: Any | None = None
    spec_key: str = "social_interaction_miner"
    llm_manager: Any | None = None

    def __post_init__(self) -> None:
        if self.llm_manager is None:
            self.llm_manager = get_llm_manager()

    # ------------------------------------------------------------------
    def mine_text(self, text: str, *, source: str = "inbox") -> list[InteractionRule]:
        payload = self._payload_from_text(text or "", source=source)
        response = self._call_spec(self.spec_key, payload)
        return self._rules_from_response(response)

    def mine_turns(
        self,
        turns: Iterable[Mapping[str, Any]],
        *,
        source: str = "conversation",
    ) -> list[InteractionRule]:
        payload = {
            "source": source,
            "turns": [
                {"speaker": str(turn.get("speaker") or ""), "text": str(turn.get("text") or "")}
                for turn in _ensure_sequence(list(turns))
                if isinstance(turn, Mapping)
            ][-20:],
        }
        response = self._call_spec(self.spec_key, payload)
        return self._rules_from_response(response)

    def schedule_self_evaluation(
        self,
        *,
        rule: Mapping[str, Any],
        arch: Any | None = None,
    ) -> Mapping[str, Any] | None:
        payload = {
            "rule": json_sanitize(rule),
            "arch_context": self._lightweight_arch_snapshot(arch or self.arch),
        }
        response = self._call_spec("social_rule_self_evaluation", payload)
        if not isinstance(response, Mapping):
            return None
        return dict(response)

    # ------------------------------------------------------------------
    def _payload_from_text(self, text: str, *, source: str) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "source": source,
            "text": text,
            "user_id": getattr(self.arch, "user_id", None) if self.arch else None,
        }
        return payload

    def _call_spec(self, key: str, payload: Mapping[str, Any]) -> Mapping[str, Any] | None:
        try:
            response = self.llm_manager.call_dict(key, input_payload=json_sanitize(payload))
        except LLMIntegrationError:
            raise
        if not isinstance(response, Mapping):
            return None
        return response

    def _rules_from_response(self, response: Mapping[str, Any] | None) -> list[InteractionRule]:
        if not isinstance(response, Mapping):
            return []
        rules_payload = response.get("rules") or response.get("suggested_rules")
        rules: list[InteractionRule] = []
        for item in _ensure_sequence(rules_payload):
            if isinstance(item, Mapping):
                rules.append(InteractionRule.from_mapping(item))
        return rules

    def _lightweight_arch_snapshot(self, arch: Any | None) -> Mapping[str, Any]:
        if arch is None:
            return {}
        snapshot: dict[str, Any] = {}
        for attr in ("persona_id", "user_id", "channel"):
            value = getattr(arch, attr, None)
            if value is not None:
                snapshot[attr] = value
        return snapshot
