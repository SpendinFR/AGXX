"""LLM orchestrator for selecting conversational tactics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from AGI_Evolutive.utils.jsonsafe import json_sanitize
from AGI_Evolutive.utils.llm_service import LLMIntegrationError, get_llm_manager

from .interaction_rule import ContextBuilder, InteractionRule


@dataclass
class TacticSelector:
    arch: Any
    spec_key: str = "social_tactic_selector"
    llm_manager: Any | None = None

    def __post_init__(self) -> None:
        if self.llm_manager is None:
            self.llm_manager = get_llm_manager()

    def pick(
        self,
        ctx: Mapping[str, Any] | None = None,
    ) -> tuple[Mapping[str, Any] | None, Mapping[str, Any] | None]:
        context = ctx or ContextBuilder.build(self.arch)
        payload = {
            "context": json_sanitize(context),
            "arch": self._arch_snapshot(),
        }
        response = self._call_spec(self.spec_key, payload)
        if not isinstance(response, Mapping):
            return None, None
        rule_payload = response.get("selected_rule") or response.get("rule")
        meta = response.get("meta") if isinstance(response.get("meta"), Mapping) else {}
        if isinstance(rule_payload, Mapping):
            rule = InteractionRule.from_mapping(rule_payload)
            return rule.to_dict(), dict(meta)
        return None, dict(meta)

    # ------------------------------------------------------------------
    def _call_spec(self, key: str, payload: Mapping[str, Any]) -> Mapping[str, Any] | None:
        try:
            return self.llm_manager.call_dict(key, input_payload=json_sanitize(payload))
        except LLMIntegrationError:
            raise

    def _arch_snapshot(self) -> Mapping[str, Any]:
        snapshot: dict[str, Any] = {}
        for attr in ("persona_id", "user_id", "channel"):
            value = getattr(self.arch, attr, None)
            if value is not None:
                snapshot[attr] = value
        return snapshot
