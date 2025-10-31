"""LLM-first contextual inference module.

The historical implementation combined several online learners (logistic
regression, Platt calibration, beta updates, drift detectors) to estimate the
agent's runtime/workspace/context and decide whether to update the identity
model.  The refactored module only compiles an observation snapshot, performs a
single LLM call and applies the returned directive.  No heuristic fallback is
kept: if the LLM cannot provide guidance the caller receives an exception.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, Mapping, Optional

from AGI_Evolutive.utils.llm_service import LLMIntegrationError, get_llm_manager


class ContextInferenceError(RuntimeError):
    """Raised when the LLM directive cannot be produced or applied."""


def _normalise_string(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, str):
        cleaned = value.strip()
        return cleaned or None
    cleaned = str(value).strip()
    return cleaned or None


def _normalise_mapping(value: Any) -> Dict[str, Any]:
    if not isinstance(value, Mapping):
        return {}
    return {str(key): val for key, val in value.items()}


def _normalise_sequence(value: Any) -> list[str]:
    if value is None:
        return []
    items: list[str] = []
    if isinstance(value, str):
        cleaned = value.strip()
        if cleaned:
            items.append(cleaned)
    elif isinstance(value, Iterable):
        for element in value:
            if element is None:
                continue
            text = str(element).strip()
            if text:
                items.append(text)
    seen = set()
    ordered: list[str] = []
    for item in items:
        if item not in seen:
            ordered.append(item)
            seen.add(item)
    return ordered[:12]


def _snapshot_self_model(arch: Any) -> Dict[str, Any]:
    self_model = getattr(arch, "self_model", None)
    if self_model and hasattr(self_model, "state"):
        state = getattr(self_model, "state", {})
        if isinstance(state, Mapping):
            identity = state.get("identity")
            return {"identity": identity}
    return {}


def _recent_memories(arch: Any, limit: int = 5) -> list[Dict[str, Any]]:
    memory = getattr(arch, "memory", None)
    if not memory or not hasattr(memory, "get_recent_memories"):
        return []
    try:
        entries = memory.get_recent_memories(limit=limit)
    except Exception:
        return []
    snapshots: list[Dict[str, Any]] = []
    if isinstance(entries, Iterable):
        for entry in entries:
            if not isinstance(entry, Mapping):
                continue
            snapshot: Dict[str, Any] = {}
            for key in ("kind", "role", "text", "summary", "ts"):
                if key in entry:
                    snapshot[str(key)] = entry[key]
            snapshots.append(snapshot)
    return snapshots[:limit]


def _job_manager_snapshot(arch: Any) -> Dict[str, Any]:
    job_manager = getattr(arch, "job_manager", None)
    if not job_manager:
        return {}
    snapshot: Dict[str, Any] = {}
    for attr in ("paths", "active_jobs", "workspace"):
        value = getattr(job_manager, attr, None)
        if value is not None:
            snapshot[attr] = value
    return snapshot


@dataclass
class WhereState:
    runtime: Optional[str] = None
    workspace: Optional[str] = None
    context: Optional[str] = None
    summary: Optional[str] = None

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> "WhereState":
        if not isinstance(payload, Mapping):
            return cls()
        return cls(
            runtime=_normalise_string(payload.get("runtime")),
            workspace=_normalise_string(payload.get("workspace")),
            context=_normalise_string(payload.get("context")),
            summary=_normalise_string(payload.get("summary")),
        )

    def is_complete(self) -> bool:
        return bool(self.runtime or self.workspace or self.context)

    def to_mapping(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {}
        if self.runtime:
            data["runtime"] = self.runtime
        if self.workspace:
            data["workspace"] = self.workspace
        if self.context:
            data["context"] = self.context
        if self.summary:
            data["summary"] = self.summary
        return data


@dataclass
class WhereDirective:
    """Directive returned by the LLM with contextual information."""

    where: WhereState
    confidence: Optional[float] = None
    should_update: bool = False
    actions: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    telemetry: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> "WhereDirective":
        if not isinstance(payload, Mapping):
            raise ContextInferenceError("LLM payload must be a mapping")
        where = WhereState.from_payload(payload.get("where") or payload)
        confidence_value = payload.get("confidence")
        try:
            confidence = None if confidence_value is None else float(confidence_value)
        except (TypeError, ValueError):
            confidence = None
        should_update = bool(payload.get("should_update", False))
        actions = _normalise_sequence(payload.get("actions"))
        notes = _normalise_sequence(payload.get("notes"))
        telemetry = _normalise_mapping(payload.get("telemetry"))
        return cls(
            where=where,
            confidence=confidence,
            should_update=should_update,
            actions=actions,
            notes=notes,
            telemetry=telemetry,
        )

    def apply_to_arch(self, arch: Any) -> None:
        if not self.should_update or not self.where.is_complete():
            return
        self_model = getattr(arch, "self_model", None)
        if not self_model or not hasattr(self_model, "set_identity_patch"):
            raise ContextInferenceError("Architecture cannot persist identity patch")
        payload = {"where": self.where.to_mapping()}
        try:
            self_model.set_identity_patch(payload)
        except Exception as exc:  # pragma: no cover - escalates to caller
            raise ContextInferenceError(str(exc)) from exc

    def to_mapping(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {
            "where": self.where.to_mapping(),
            "should_update": self.should_update,
            "actions": list(self.actions),
            "notes": list(self.notes),
        }
        if self.confidence is not None:
            data["confidence"] = max(0.0, min(1.0, float(self.confidence)))
        if self.telemetry:
            data["telemetry"] = dict(self.telemetry)
        return data


def _build_payload(arch: Any) -> Dict[str, Any]:
    last = getattr(arch, "_where_last", {})
    if not isinstance(last, Mapping):
        last = {}
    observation = {
        "timestamp": time.time(),
        "last": _normalise_mapping(last.get("directive") or {}),
        "identity": _snapshot_self_model(arch),
        "job_manager": _job_manager_snapshot(arch),
        "recent_memories": _recent_memories(arch),
    }
    try:
        observation["homeostasis"] = getattr(getattr(arch, "homeostasis", None), "state", None)
    except Exception:
        pass
    return observation


def infer_where_and_apply(arch: Any) -> Dict[str, Any]:
    """Infer the contextual "where" state using a single LLM call."""

    manager = get_llm_manager()
    payload = _build_payload(arch)
    try:
        response = manager.call_dict(
            "cognition_context_inference", input_payload=payload
        )
    except LLMIntegrationError as exc:
        raise ContextInferenceError(str(exc)) from exc

    directive = WhereDirective.from_payload(response)
    directive.apply_to_arch(arch)

    arch._where_last = {
        "stamp": time.time(),
        "directive": directive.to_mapping(),
    }
    return directive.to_mapping()
