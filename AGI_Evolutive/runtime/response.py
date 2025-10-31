"""Runtime response helpers routed through documented LLM contracts."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Tuple

from AGI_Evolutive.utils.jsonsafe import json_sanitize
from AGI_Evolutive.utils.llm_service import (
    LLMIntegrationError,
    LLMUnavailableError,
    get_llm_manager,
)


@dataclass
class RuntimeResponseFormatter:
    llm_manager: Any | None = None
    format_spec: str = "response_formatter"
    contract_spec: str = "response_contract"
    last_contract: Mapping[str, Any] | None = field(default=None, init=False)

    def __post_init__(self) -> None:
        if self.llm_manager is None:
            self.llm_manager = get_llm_manager()

    # ------------------------------------------------------------------
    def normalize_contract(self, contract: Mapping[str, Any] | None) -> Mapping[str, Any]:
        payload = {
            "contract": json_sanitize(contract or {}),
            "previous": json_sanitize(self.last_contract or {}),
        }
        try:
            response = self.llm_manager.call_dict(self.contract_spec, input_payload=payload)
        except (LLMUnavailableError, LLMIntegrationError):
            response = None
        if isinstance(response, Mapping):
            self.last_contract = dict(response)
            return dict(response)
        self.last_contract = contract or {}
        return dict(contract or {})

    # ------------------------------------------------------------------
    def format_reasoning(
        self,
        reasoning: str,
        *,
        metadata: Mapping[str, Any] | None = None,
    ) -> Tuple[str, Mapping[str, Any] | None]:
        payload = {
            "reasoning": reasoning,
            "metadata": json_sanitize(metadata or {}),
            "previous": json_sanitize(self.last_contract or {}),
        }
        try:
            response = self.llm_manager.call_dict(self.format_spec, input_payload=payload)
        except (LLMUnavailableError, LLMIntegrationError):
            return reasoning, None
        if not isinstance(response, Mapping):
            return reasoning, None
        message = str(response.get("message") or response.get("summary") or reasoning)
        diagnostics = response.get("diagnostics")
        if isinstance(diagnostics, Mapping):
            return message, dict(diagnostics)
        return message, None

    # ------------------------------------------------------------------
    def format_reply(
        self,
        base_text: str,
        *,
        contract: Mapping[str, Any] | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> Mapping[str, Any]:
        normalized = self.normalize_contract(contract)
        payload = {
            "base_text": base_text,
            "contract": json_sanitize(normalized),
            "metadata": json_sanitize(metadata or {}),
        }
        try:
            response = self.llm_manager.call_dict(self.format_spec, input_payload=payload)
        except (LLMUnavailableError, LLMIntegrationError):
            return {"message": base_text, "contract": normalized}
        if not isinstance(response, Mapping):
            return {"message": base_text, "contract": normalized}
        message = str(response.get("message") or base_text)
        return {"message": message, "contract": normalized, "raw": dict(response)}


_FORMATTER: RuntimeResponseFormatter | None = None


def _formatter() -> RuntimeResponseFormatter:
    global _FORMATTER
    if _FORMATTER is None:
        _FORMATTER = RuntimeResponseFormatter()
    return _FORMATTER


def humanize_reasoning_block(text: str) -> Tuple[str, Mapping[str, Any] | None]:
    if not text:
        return "", None
    return _formatter().format_reasoning(text)


def ensure_contract(contract: Mapping[str, Any] | None) -> Mapping[str, Any]:
    return _formatter().normalize_contract(contract)


def format_agent_reply(base_text: str, **contract: Any) -> str:
    formatted = _formatter().format_reply(base_text, contract=contract)
    return formatted.get("message", base_text)
