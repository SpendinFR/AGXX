"""Identity mission orchestration backed by a single LLM call."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, Mapping, Optional

from AGI_Evolutive.utils.jsonsafe import json_sanitize
from AGI_Evolutive.utils.llm_contracts import enforce_llm_contract
from AGI_Evolutive.utils.llm_service import try_call_llm_dict


logger = logging.getLogger(__name__)


@dataclass
class IdentityMissionDirective:
    """Structured payload returned by the `identity_mission` LLM spec."""

    mission: Dict[str, str] = field(default_factory=dict)
    statement: Optional[str] = None
    priorities: Iterable[Mapping[str, Any]] = field(default_factory=tuple)
    follow_up: Iterable[Mapping[str, Any]] = field(default_factory=tuple)
    notes: Iterable[str] = field(default_factory=tuple)
    telemetry: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> "IdentityMissionDirective":
        mission: Dict[str, str] = {}
        statement: Optional[str] = None
        priorities = []
        follow_up = []
        notes = []
        telemetry: Dict[str, Any] = {}

        mission_block = payload.get("mission")
        if isinstance(mission_block, Mapping):
            for key, value in mission_block.items():
                if not isinstance(key, str):
                    continue
                if isinstance(value, str):
                    text = value.strip()
                    if text:
                        mission[key] = text

        mission_text = payload.get("mission_text") or payload.get("mission_statement")
        if isinstance(mission_text, str):
            statement = mission_text.strip() or None

        for raw_priority in payload.get("priorities", []):
            if isinstance(raw_priority, Mapping):
                priorities.append({
                    str(k): raw_priority[k]
                    for k in raw_priority
                    if isinstance(k, str)
                })

        for raw_action in payload.get("follow_up", []):
            if isinstance(raw_action, Mapping):
                follow_up.append({
                    str(k): raw_action[k]
                    for k in raw_action
                    if isinstance(k, str)
                })

        raw_notes = payload.get("notes")
        if isinstance(raw_notes, str):
            stripped = raw_notes.strip()
            if stripped:
                notes.append(stripped)
        elif isinstance(raw_notes, Iterable):
            for entry in raw_notes:
                if isinstance(entry, str):
                    stripped = entry.strip()
                    if stripped:
                        notes.append(stripped)

        if isinstance(payload.get("telemetry"), Mapping):
            telemetry = {
                str(k): payload["telemetry"][k]
                for k in payload["telemetry"]
                if isinstance(k, str)
            }

        return cls(
            mission=mission,
            statement=statement,
            priorities=tuple(priorities),
            follow_up=tuple(follow_up),
            notes=tuple(notes),
            telemetry=telemetry,
        )


def _ensure_state(arch: Any) -> Dict[str, Any]:
    state = getattr(arch, "_identity_mission_state", None)
    if isinstance(state, dict):
        return state
    state = {
        "mission": {},
        "history": [],
        "last_updated": None,
    }
    setattr(arch, "_identity_mission_state", state)
    return state


def _collect_context(arch: Any) -> Dict[str, Any]:
    context: Dict[str, Any] = {}

    homeostasis = getattr(arch, "homeostasis", None)
    if homeostasis is not None:
        try:
            state = getattr(homeostasis, "state", {})
            drives = (state or {}).get("drives", {})
            rewards = (state or {}).get("rewards", {})
            context["homeostasis"] = {
                "drives": json_sanitize(drives),
                "rewards": json_sanitize(rewards),
            }
        except Exception:
            pass

    planner = getattr(arch, "planner", None)
    if planner is not None and hasattr(planner, "active_plan"):
        try:
            plan = planner.active_plan()
            if plan:
                context["active_plan"] = json_sanitize(plan)
        except Exception:
            pass

    memory = getattr(arch, "memory", None)
    store = getattr(memory, "store", None) if memory is not None else None
    if store is not None and hasattr(store, "get_recent"):
        try:
            context["recent_memories"] = json_sanitize(store.get_recent(5) or [])
        except Exception:
            pass

    return context


def recommend_and_apply_mission(
    arch: Any,
    *,
    threshold: float = 0.75,
    delta_gate: float = 0.10,
    signals: Optional[Mapping[str, Any]] = None,
) -> IdentityMissionDirective:
    """Call the LLM once and persist the resulting mission directive."""

    state = _ensure_state(arch)
    payload = {
        "state": {
            "mission": json_sanitize(state.get("mission", {})),
            "mission_statement": state.get("mission_statement"),
            "history": json_sanitize(state.get("history", [])[-10:]),
        },
        "threshold": float(threshold),
        "delta_gate": float(delta_gate),
        "signals": json_sanitize(signals or {}),
        "context": _collect_context(arch),
        "timestamp": time.time(),
    }

    llm_raw = try_call_llm_dict(
        "identity_mission",
        input_payload=payload,
        logger=logger,
    )
    cleaned = enforce_llm_contract("identity_mission", llm_raw)
    directive = IdentityMissionDirective.from_payload(cleaned)

    state["mission"] = dict(directive.mission)
    if directive.statement:
        state["mission_statement"] = directive.statement
    if directive.notes:
        state.setdefault("notes", []).append({
            "ts": time.time(),
            "notes": list(directive.notes),
        })
    history = state.setdefault("history", [])
    history.append(
        {
            "ts": time.time(),
            "mission": dict(directive.mission),
            "statement": directive.statement,
            "priorities": list(directive.priorities),
            "follow_up": list(directive.follow_up),
            "telemetry": directive.telemetry,
        }
    )
    if len(history) > 30:
        del history[:-30]

    state["last_updated"] = time.time()
    setattr(arch, "_identity_mission_state", state)

    return directive


__all__ = ["IdentityMissionDirective", "recommend_and_apply_mission"]

