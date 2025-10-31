"""LLM-first social critic orchestrator."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Mapping, MutableMapping

from AGI_Evolutive.utils.jsonsafe import json_sanitize
from AGI_Evolutive.utils.llm_service import LLMIntegrationError, get_llm_manager

from .adaptive_lexicon import AdaptiveLexicon
from .interaction_rule import InteractionRule

LOGGER = logging.getLogger(__name__)


def _ensure_mapping(value: Any) -> MutableMapping[str, Any]:
    if isinstance(value, Mapping):
        return {str(key): val for key, val in value.items()}
    return {}


def _coerce_float(value: Any, *, default: float = 0.0) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    if number != number:  # NaN guard
        return default
    return number


@dataclass
class SocialCritic:
    arch: Any
    outcome_spec: str = "social_interaction_outcome"
    analysis_spec: str = "social_conversation_analysis"
    rewrite_spec: str = "social_conversation_rewrite"
    rule_update_spec: str = "social_rule_update"
    simulation_spec: str = "social_simulation_score"
    llm_manager: Any | None = None
    lexicon: AdaptiveLexicon | None = None
    _last_outcome: Mapping[str, Any] | None = field(default=None, init=False)

    def __post_init__(self) -> None:
        if self.llm_manager is None:
            self.llm_manager = get_llm_manager()
        if self.lexicon is None:
            self.lexicon = getattr(self.arch, "lexicon", None)
            if not isinstance(self.lexicon, AdaptiveLexicon):
                self.lexicon = AdaptiveLexicon(self.arch, llm_manager=self.llm_manager)
                setattr(self.arch, "lexicon", self.lexicon)

    # ------------------------------------------------------------------
    def compute_outcome(
        self,
        user_msg: str,
        decision_trace: Mapping[str, Any] | None = None,
        *,
        pre_ctx: Mapping[str, Any] | None = None,
        post_ctx: Mapping[str, Any] | None = None,
    ) -> Mapping[str, Any]:
        payload = {
            "message": user_msg or "",
            "decision_trace": json_sanitize(decision_trace or {}),
            "pre_context": json_sanitize(pre_ctx) if isinstance(pre_ctx, Mapping) else None,
            "post_context": json_sanitize(post_ctx) if isinstance(post_ctx, Mapping) else None,
            "arch": self._arch_snapshot(),
        }
        response = self._call_spec(self.outcome_spec, payload)
        outcome = self._normalize_outcome(response)
        self._last_outcome = outcome
        self._record_outcome(outcome)
        return outcome

    def analyze(self, text: str) -> Mapping[str, Any]:
        response = self._call_spec(self.analysis_spec, {"text": text or "", "arch": self._arch_snapshot()})
        return _ensure_mapping(response)

    def rewrite(self, text: str) -> str:
        response = self._call_spec(self.rewrite_spec, {"text": text or "", "arch": self._arch_snapshot()})
        if isinstance(response, Mapping):
            rewritten = response.get("rewritten") or response.get("revision")
            if isinstance(rewritten, str) and rewritten.strip():
                return rewritten
        return text

    def score(self, simulation_snapshot: Mapping[str, Any] | None) -> float:
        response = self._call_spec(
            self.simulation_spec,
            {"simulation": json_sanitize(simulation_snapshot or {}), "arch": self._arch_snapshot()},
        )
        if isinstance(response, Mapping):
            return float(response.get("score", 0.0) or 0.0)
        return 0.0

    def update_rule_with_outcome(
        self,
        rule_id: str,
        outcome: Mapping[str, Any],
    ) -> Mapping[str, Any] | None:
        existing = self._fetch_rule(rule_id)
        payload = {
            "rule": existing or {"id": rule_id},
            "outcome": json_sanitize(outcome or {}),
            "arch": self._arch_snapshot(),
        }
        response = self._call_spec(self.rule_update_spec, payload)
        if not isinstance(response, Mapping):
            return None
        rule_payload = response.get("rule") or response
        if not isinstance(rule_payload, Mapping):
            return None
        rule = InteractionRule.from_mapping(rule_payload)
        self._persist_rule(rule)
        return rule.to_dict()

    def last_outcome(self) -> Mapping[str, Any] | None:
        return self._last_outcome

    # ------------------------------------------------------------------
    def _call_spec(self, key: str, payload: Mapping[str, Any]) -> Mapping[str, Any] | None:
        try:
            response = self.llm_manager.call_dict(key, input_payload=json_sanitize(payload))
        except LLMIntegrationError:
            LOGGER.exception("Social critic spec %s failed", key)
            raise
        if not isinstance(response, Mapping):
            return None
        return response

    def _normalize_outcome(self, payload: Mapping[str, Any] | None) -> Mapping[str, Any]:
        data = _ensure_mapping(payload)
        normalized = {
            "reward": round(max(0.0, min(1.0, _coerce_float(data.get("reward"), default=0.5))), 4),
            "confidence": round(max(0.0, min(1.0, _coerce_float(data.get("confidence"), default=0.5))), 3),
            "signals": _ensure_mapping(data.get("signals")),
            "notes": data.get("notes"),
        }
        if "lexicon_updates" in data:
            normalized["lexicon_updates"] = data.get("lexicon_updates")
        normalized.update({k: v for k, v in data.items() if k not in normalized})
        return normalized

    def _record_outcome(self, outcome: Mapping[str, Any]) -> None:
        memory = getattr(self.arch, "memory", None)
        if not memory or not hasattr(memory, "add_memory"):
            return
        try:
            memory.add_memory(
                {
                    "kind": "social_outcome",
                    "timestamp": outcome.get("timestamp") or getattr(self.arch, "now", None),
                    "payload": json_sanitize(outcome),
                }
            )
        except Exception:
            LOGGER.debug("Failed to persist social outcome", exc_info=True)

    def _fetch_rule(self, rule_id: str) -> Mapping[str, Any] | None:
        memory = getattr(self.arch, "memory", None)
        if not memory or not hasattr(memory, "get_recent_memories"):
            return None
        try:
            rules = memory.get_recent_memories(kind="interaction_rule", limit=200) or []
        except Exception:
            return None
        for item in rules:
            if isinstance(item, Mapping) and item.get("id") == rule_id:
                return item
        return None

    def _persist_rule(self, rule: InteractionRule) -> None:
        memory = getattr(self.arch, "memory", None)
        if not memory:
            return
        payload = rule.to_dict()
        try:
            if hasattr(memory, "update_memory"):
                memory.update_memory(payload)
            elif hasattr(memory, "add_memory"):
                memory.add_memory(payload)
        except Exception:
            LOGGER.debug("Failed to persist rule update", exc_info=True)

    def _arch_snapshot(self) -> Mapping[str, Any]:
        snapshot: dict[str, Any] = {}
        for attr in ("persona_id", "user_id", "channel", "voice_profile"):
            value = getattr(self.arch, attr, None)
            if value is not None:
                snapshot[attr] = value
        return snapshot
