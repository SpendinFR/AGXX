"""LLM-first reasoning system orchestrator.

The original implementation maintained a complex web of online learners,
bandits and rule-based modules to derive a single reasoning episode.  The new
version delegates the entire reasoning workflow to the ``reasoning_episode`` LLM
contract: Python only assembles context/toolkit payloads, invokes the LLM once
and persists the structured directive for downstream consumers.
"""

from __future__ import annotations

import time
from typing import Any, Dict, Iterable, List, Mapping, Optional

from AGI_Evolutive.utils.llm_service import get_llm_manager

from .strategies import ReasoningEpisodeDirective, run_reasoning_episode

__all__ = ["ReasoningSystem", "ReasoningEpisodeDirective"]


# ---------------------------------------------------------------------------
# Local normalisation helpers (mirroring the strategy module utilities)
# ---------------------------------------------------------------------------

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
            items = []
            for entry in raw:
                normalised = _normalise_value(entry, max_list_items=max_list_items)
                if normalised is not None:
                    items.append(normalised)
                if len(items) >= max_list_items:
                    break
            payload[key_str] = items
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
        try:
            number = float(value)
        except (TypeError, ValueError):
            return None
        if number != number or number in (float("inf"), float("-inf")):
            return None
        return number
    if isinstance(value, Mapping):
        return _normalise_mapping(value, max_list_items=max_list_items)
    if isinstance(value, (list, tuple, set)):
        result = []
        for entry in value:
            normalised = _normalise_value(entry, max_list_items=max_list_items)
            if normalised is not None:
                result.append(normalised)
            if len(result) >= max_list_items:
                break
        return result
    if isinstance(value, str):
        text = value.strip()
        return text or None
    text = str(value).strip()
    return text or None


# ---------------------------------------------------------------------------
# Reasoning orchestrator
# ---------------------------------------------------------------------------


class ReasoningSystem:
    """High-level reasoning orchestrator delegating to a single LLM call."""

    def __init__(
        self,
        architecture: Any,
        memory_system: Any | None = None,
        perception_system: Any | None = None,
        *,
        llm_manager: Any | None = None,
    ) -> None:
        self.arch = architecture
        self.memory = memory_system
        self.perception = perception_system
        self._manager = llm_manager or get_llm_manager()
        self.history: List[Dict[str, Any]] = []
        self.last_directive: Optional[ReasoningEpisodeDirective] = None

    # ------------------------------------------------------------------
    def reason_about(
        self,
        prompt: str,
        *,
        context: Optional[Mapping[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Run a full reasoning episode through a single LLM call."""

        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError("reason_about requires a non-empty prompt")

        payload_context = self._compose_context(prompt=prompt, extra=context)
        toolkit = self._compose_toolkit()
        directive = run_reasoning_episode(
            prompt=prompt.strip(),
            context=payload_context,
            toolkit=toolkit,
            llm_manager=self._manager,
        )
        record = directive.to_dict()
        record["timestamp"] = time.time()
        self.history.append(record)
        self.history = self.history[-200:]
        self.last_directive = directive
        self._persist_episode(record)
        return record

    # ------------------------------------------------------------------
    def _compose_context(
        self,
        *,
        prompt: str,
        extra: Optional[Mapping[str, Any]],
    ) -> Dict[str, Any]:
        context: Dict[str, Any] = {"prompt_preview": prompt[:256]}
        if extra:
            context.update(_normalise_mapping(extra))
        context.update(self._architecture_snapshot())
        return context

    def _compose_toolkit(self) -> Dict[str, Any]:
        toolkit: Dict[str, Any] = {}
        memory_snapshot = self._memory_snapshot()
        if memory_snapshot:
            toolkit["memory"] = memory_snapshot
        perception_snapshot = self._call_describe(self.perception)
        if perception_snapshot:
            toolkit["perception"] = perception_snapshot
        tools_snapshot = self._call_describe(getattr(self.arch, "tool_manager", None))
        if tools_snapshot:
            toolkit["tools"] = tools_snapshot
        planner_snapshot = self._call_describe(getattr(self.arch, "planner", None))
        if planner_snapshot:
            toolkit["planner"] = planner_snapshot
        return toolkit

    def _architecture_snapshot(self) -> Dict[str, Any]:
        snapshot: Dict[str, Any] = {}
        identity = self._extract_identity()
        if identity:
            snapshot["identity"] = identity
        style = getattr(getattr(self.arch, "style_policy", None), "current_mode", None)
        if style:
            snapshot["style_mode"] = style
        intents = self._extract_intents()
        if intents:
            snapshot["user_intents"] = intents
        homeostasis = getattr(getattr(self.arch, "homeostasis", None), "last_directive", None)
        if isinstance(homeostasis, Mapping):
            snapshot["homeostasis"] = _normalise_mapping(homeostasis)
        return snapshot

    def _extract_identity(self) -> Dict[str, Any]:
        self_model = getattr(self.arch, "self_model", None)
        identity: Dict[str, Any] = {}
        if isinstance(getattr(self_model, "identity", None), Mapping):
            raw_identity = getattr(self_model, "identity")
            identity = _normalise_mapping(raw_identity, max_list_items=12)
        persona = getattr(self_model, "persona", None)
        if isinstance(persona, Mapping):
            identity.setdefault("persona", _normalise_mapping(persona))
        return identity

    def _extract_intents(self) -> List[Dict[str, Any]]:
        intent_model = getattr(self.arch, "intent_model", None)
        if intent_model is None:
            return []
        try:
            constraints = intent_model.as_constraints()
        except Exception:
            return []
        intents: List[Dict[str, Any]] = []
        if isinstance(constraints, Iterable):
            for entry in constraints:
                if not isinstance(entry, Mapping):
                    continue
                intents.append(_normalise_mapping(entry, max_list_items=8))
                if len(intents) >= 12:
                    break
        return intents

    def _memory_snapshot(self) -> Dict[str, Any]:
        manager = getattr(self.memory, "semantic_manager", None)
        if manager and hasattr(manager, "describe_for_reasoning"):
            try:
                snapshot = manager.describe_for_reasoning()
            except Exception:
                snapshot = None
            if isinstance(snapshot, Mapping):
                return _normalise_mapping(snapshot, max_list_items=12)
        memory_store = getattr(self.memory, "store", None)
        if memory_store and hasattr(memory_store, "latest_highlights"):
            try:
                highlights = memory_store.latest_highlights(limit=10)
            except Exception:
                highlights = None
            if isinstance(highlights, Iterable):
                return {"highlights": list(highlights)}
        return {}

    def _call_describe(self, component: Any) -> Dict[str, Any]:
        if component is None:
            return {}
        for attr in ("describe_for_reasoning", "describe", "snapshot"):
            method = getattr(component, attr, None)
            if callable(method):
                try:
                    data = method()
                except Exception:
                    data = None
                if isinstance(data, Mapping):
                    return _normalise_mapping(data)
        return {}

    def _persist_episode(self, record: Mapping[str, Any]) -> None:
        logger = getattr(self.arch, "logger", None)
        if logger and hasattr(logger, "write"):
            try:
                logger.write(
                    "reasoning.episode",
                    **{k: v for k, v in record.items() if k != "raw_llm_result"},
                )
            except Exception:
                pass


# The refactor intentionally removes legacy helpers (bandits, Thompson samplers,
# online regressions, etc.).  The ReasoningSystem now depends solely on the LLM
# directive, keeping this module lightweight and auditable.
