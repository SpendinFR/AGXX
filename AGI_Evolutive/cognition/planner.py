"""LLM-first goal planning orchestrator.

This module replaces the historical adaptive metrics, bandits and heuristics
with a single structured call to the LLM integration layer. The planner now
normalises the LLM payload, persists it for follow-up cycles and exposes a
minimal imperative API for the rest of the architecture (meta cognition,
orchestrator, etc.).
"""

from __future__ import annotations

import json
import logging
import os
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Optional, Sequence

from AGI_Evolutive.core.config import cfg
from AGI_Evolutive.utils.jsonsafe import json_sanitize
from AGI_Evolutive.utils.llm_service import LLMIntegrationError, get_llm_manager

LOGGER = logging.getLogger(__name__)

_PLANS = cfg()["PLANS_PATH"]


class PlannerError(RuntimeError):
    """Raised when the LLM payload cannot be normalised."""


def _coerce_str(value: Any, default: str = "") -> str:
    if isinstance(value, str):
        cleaned = value.strip()
        if cleaned:
            return cleaned
    return default


def _coerce_float(value: Any, *, default: float = 0.5, lo: float = 0.0, hi: float = 1.0) -> float:
    try:
        number = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        number = default
    if number != number:
        number = default
    return max(lo, min(hi, number))


def _coerce_list(value: Any) -> List[str]:
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


@dataclass
class PlannerStep:
    """Normalised view of a single step returned by the LLM."""

    id: str
    description: str
    priority: float
    depends_on: List[str] = field(default_factory=list)
    status: str = "todo"
    action_type: str = "plan_step"
    notes: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    raw: MutableMapping[str, Any] = field(default_factory=dict)

    @classmethod
    def from_payload(cls, entry: Mapping[str, Any], *, index: int) -> "PlannerStep":
        if not isinstance(entry, Mapping):
            raise PlannerError("each plan entry must be a mapping")
        description = _coerce_str(entry.get("description"))
        if not description:
            raise PlannerError("plan entries require a non-empty description")
        raw_id = entry.get("id")
        if isinstance(raw_id, str) and raw_id.strip():
            step_id = raw_id.strip()
        else:
            step_id = f"llm_step_{index + 1}"
        depends_on = _coerce_list(entry.get("depends_on"))
        priority = _coerce_float(entry.get("priority"), default=0.6)
        action_type = _coerce_str(entry.get("action_type"), default="plan_step")
        notes = _coerce_list(entry.get("notes"))
        metadata = _coerce_mapping(entry.get("metadata"))
        raw = dict(entry)
        return cls(
            id=step_id,
            description=description,
            priority=priority,
            depends_on=depends_on,
            action_type=action_type,
            notes=notes,
            metadata=metadata,
            raw=raw,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "desc": self.description,
            "status": self.status,
            "priority": self.priority,
            "depends_on": list(self.depends_on),
            "action": {"type": self.action_type, "payload": {"step_id": self.id}},
            "notes": list(self.notes),
            "metadata": dict(self.metadata),
            "raw": dict(self.raw),
        }


@dataclass
class PlannerPlan:
    """Container storing the LLM plan and its metadata."""

    goal_id: str
    description: str
    steps: List[PlannerStep]
    summary: Optional[str] = None
    risks: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)
    raw: MutableMapping[str, Any] = field(default_factory=dict)

    @classmethod
    def from_payload(
        cls,
        payload: Mapping[str, Any],
        *,
        goal_id: str,
        description: str,
    ) -> "PlannerPlan":
        if not isinstance(payload, Mapping):
            raise PlannerError("LLM planner payload must be a mapping")
        plan_entries = payload.get("plan")
        if not isinstance(plan_entries, Sequence):
            raise PlannerError("LLM planner payload must expose a 'plan' list")
        steps: List[PlannerStep] = []
        for idx, entry in enumerate(plan_entries):
            try:
                step = PlannerStep.from_payload(entry, index=idx)
            except PlannerError as exc:
                LOGGER.debug("Skipping malformed plan entry %s: %s", entry, exc)
                continue
            steps.append(step)
        if not steps:
            raise PlannerError("LLM planner returned an empty plan")
        summary = _coerce_str(payload.get("summary"), default="") or None
        risks = _coerce_list(payload.get("risks"))
        notes = _coerce_list(payload.get("notes"))
        return cls(
            goal_id=goal_id,
            description=description,
            steps=steps,
            summary=summary,
            risks=risks,
            notes=notes,
            raw=dict(payload),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "goal_id": self.goal_id,
            "description": self.description,
            "summary": self.summary,
            "risks": list(self.risks),
            "notes": list(self.notes),
            "steps": [step.to_dict() for step in self.steps],
            "llm": dict(self.raw),
        }

    def next_step(self) -> Optional[PlannerStep]:
        for step in self.steps:
            if step.status in {"todo", "doing"}:
                return step
        return None


class Planner:
    """High-level planner orchestrating goal decomposition via the LLM."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._state: Dict[str, Any] = {"plans": {}, "updated_at": time.time()}
        self._manager = get_llm_manager()
        self._load()

    # ------------------------------------------------------------------
    # Persistence helpers
    # ------------------------------------------------------------------
    def _load(self) -> None:
        if not os.path.exists(_PLANS):
            return
        try:
            with open(_PLANS, "r", encoding="utf-8") as handle:
                data = json.load(handle)
        except Exception as exc:  # pragma: no cover - defensive
            LOGGER.warning("Failed to load planner state", exc_info=exc)
            return
        if isinstance(data, Mapping):
            with self._lock:
                self._state.update(data)

    def _save(self) -> None:
        with self._lock:
            self._state["updated_at"] = time.time()
            os.makedirs(os.path.dirname(_PLANS), exist_ok=True)
            with open(_PLANS, "w", encoding="utf-8") as handle:
                json.dump(json_sanitize(self._state), handle, ensure_ascii=False, indent=2)

    # ------------------------------------------------------------------
    # LLM orchestration
    # ------------------------------------------------------------------
    def _call_llm(self, goal: Dict[str, Any], context: Mapping[str, Any]) -> PlannerPlan:
        try:
            response = self._manager.call_dict(
                "planner_support",
                input_payload={"goal": goal, "context": dict(context)},
            )
        except LLMIntegrationError as exc:  # pragma: no cover - passthrough
            raise PlannerError(f"LLM planner call failed: {exc}") from exc
        goal_id = goal.get("id") or goal.get("goal_id") or goal.get("name")
        if not isinstance(goal_id, str) or not goal_id:
            raise PlannerError("goal identifier is required for planning")
        description = _coerce_str(goal.get("description") or goal.get("desc") or "")
        return PlannerPlan.from_payload(response, goal_id=goal_id, description=description)

    def _store_plan(self, plan: PlannerPlan) -> Dict[str, Any]:
        with self._lock:
            state_plan = plan.to_dict()
            self._state.setdefault("plans", {})[plan.goal_id] = state_plan
            self._save()
            return dict(state_plan)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def plan_for_goal(
        self,
        goal_id: str,
        description: str,
        *,
        context: Optional[Mapping[str, Any]] = None,
    ) -> Dict[str, Any]:
        goal = {"id": goal_id, "description": description}
        plan = self._call_llm(goal, context or {})
        return self._store_plan(plan)

    def refresh_plan(self, goal: Mapping[str, Any]) -> Dict[str, Any]:
        goal_id = _coerce_str(goal.get("id") or goal.get("goal_id") or goal.get("name"))
        if not goal_id:
            raise PlannerError("refresh_plan requires a goal id")
        description = _coerce_str(goal.get("description") or goal.get("desc") or "")
        plan = self._call_llm({"id": goal_id, "description": description}, goal.get("context") or {})
        return self._store_plan(plan)

    def frame(self, goal: Any, stop_rules: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        goal_payload: Dict[str, Any] = {}
        if isinstance(goal, Mapping):
            goal_payload = dict(goal)
        elif hasattr(goal, "__dict__"):
            goal_payload = {k: getattr(goal, k) for k in dir(goal) if not k.startswith("_")}
        else:
            goal_payload = {"id": str(goal), "description": str(goal)}
        plan_dict = self.refresh_plan(goal_payload)
        steps = plan_dict.get("steps", []) if isinstance(plan_dict, Mapping) else []
        options: List[Dict[str, Any]] = []
        for step in steps:
            if not isinstance(step, Mapping):
                continue
            option = {
                "id": step.get("id"),
                "action": {"type": step.get("action", {}).get("type", "plan_step")},
                "description": step.get("desc"),
                "priority": float(step.get("priority", 0.5)),
                "depends_on": step.get("depends_on", []),
                "status": step.get("status"),
                "notes": step.get("notes", []),
            }
            options.append(option)
        options.sort(key=lambda opt: opt.get("priority", 0.0), reverse=True)
        return {
            "goal": {
                "id": plan_dict.get("goal_id"),
                "description": plan_dict.get("description"),
            },
            "plan": plan_dict,
            "options": options,
            "stop_rules": stop_rules or {},
            "summary": plan_dict.get("summary"),
            "notes": plan_dict.get("notes"),
            "risks": plan_dict.get("risks"),
        }

    def add_step(self, goal_id: str, description: str) -> str:
        step_id = f"manual_{int(time.time() * 1000)}"
        with self._lock:
            plan = self._state.setdefault("plans", {}).setdefault(
                goal_id, {"goal_id": goal_id, "description": "", "steps": []}
            )
            entry = {
                "id": step_id,
                "desc": description,
                "status": "todo",
                "priority": 0.5,
                "depends_on": [],
                "action": {"type": "plan_step", "payload": {"step_id": step_id}},
                "notes": ["ajout manuel"],
                "metadata": {"source": "manual"},
            }
            plan.setdefault("steps", []).append(entry)
            self._save()
        return step_id

    def pop_next_action(self, goal_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            plan = self._state.get("plans", {}).get(goal_id)
            if not isinstance(plan, Mapping):
                return None
            for step in plan.get("steps", []):
                if not isinstance(step, Mapping):
                    continue
                if step.get("status") not in {"todo", "blocked"}:
                    continue
                retry_at = step.get("retry_at")
                if isinstance(retry_at, (int, float)) and retry_at > time.time():
                    continue
                step["status"] = "doing"
                step.pop("retry_at", None)
                step["last_emitted_at"] = time.time()
                self._save()
                return dict(step)
        return None

    def mark_action_done(
        self,
        goal_id: str,
        step_id: str,
        success: Optional[bool] = None,
        *,
        result: Optional[Mapping[str, Any]] = None,
    ) -> None:
        with self._lock:
            plan = self._state.get("plans", {}).get(goal_id)
            if not isinstance(plan, Mapping):
                return
            for step in plan.get("steps", []):
                if not isinstance(step, MutableMapping):
                    continue
                if step.get("id") != step_id:
                    continue
                now = time.time()
                reported_success = None
                if isinstance(result, Mapping):
                    if "success" in result:
                        reported_success = bool(result.get("success"))
                success_flag = bool(success if success is not None else reported_success if reported_success is not None else True)
                history_entry = {
                    "ts": now,
                    "event": "completed",
                    "success": success_flag,
                }
                if isinstance(result, Mapping):
                    if "reason" in result:
                        history_entry["reason"] = result.get("reason")
                    if reported_success is not None:
                        history_entry["reported_success"] = reported_success
                history = step.setdefault("history", [])
                history.append(history_entry)
                if success_flag:
                    step["status"] = "done"
                    step.pop("retry_at", None)
                else:
                    step["status"] = "todo"
                    step["retry_at"] = now + 120.0
                step["last_update"] = now
                break
            self._save()

    def pending_goals(self) -> List[Dict[str, Any]]:
        with self._lock:
            plans = self._state.get("plans", {})
            results: List[Dict[str, Any]] = []
            for plan in plans.values():
                if not isinstance(plan, Mapping):
                    continue
                steps = plan.get("steps", [])
                if any(step.get("status") in {"todo", "doing", "blocked"} for step in steps if isinstance(step, Mapping)):
                    results.append(dict(plan))
            return results

    def plans_snapshot(self) -> Dict[str, Dict[str, Any]]:
        with self._lock:
            plans = self._state.get("plans", {})
            return {gid: dict(plan) for gid, plan in plans.items() if isinstance(plan, Mapping)}

    @property
    def state(self) -> Dict[str, Any]:
        with self._lock:
            return json.loads(json.dumps(self._state))

    @property
    def lock(self) -> threading.RLock:
        return self._lock
