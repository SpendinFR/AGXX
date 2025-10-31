"""LLM-first goal prioritisation orchestrator.

The legacy implementation maintained a wide range of adaptive heuristics
(perceptrons, Thompson samplers, regex-based urgency detection, ontological
expansion, etc.) to compute a single priority score for each plan.  In the new
architecture the entire backlog evaluation is delegated to the LLM: this module
only gathers the minimal context, performs a single structured call and applies
the directive to the planner state.  No fallback or local scoring remains.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Optional, Sequence

from AGI_Evolutive.utils.llm_service import LLMIntegrationError, get_llm_manager


class PrioritizationError(RuntimeError):
    """Raised when the prioritiser cannot complete the LLM workflow."""


def _normalise_string(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, str):
        cleaned = value.strip()
        return cleaned or None
    cleaned = str(value).strip()
    return cleaned or None


def _normalise_tags(value: Any) -> List[str]:
    if value is None:
        return []
    tags: List[str] = []
    if isinstance(value, str):
        cleaned = value.strip()
        if cleaned:
            tags.append(cleaned)
    elif isinstance(value, Iterable):
        for item in value:
            if item is None:
                continue
            tag = str(item).strip()
            if tag:
                tags.append(tag)
    deduped: List[str] = []
    seen = set()
    for tag in tags:
        if tag not in seen:
            deduped.append(tag)
            seen.add(tag)
    return deduped[:16]


def _normalise_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number:  # NaN
        return None
    return number


def _normalise_mapping(value: Any) -> Dict[str, Any]:
    if not isinstance(value, Mapping):
        return {}
    return {str(key): val for key, val in value.items()}


def _normalise_sequence(value: Any, *, max_items: int = 12) -> List[str]:
    if value is None:
        return []
    result: List[str] = []
    if isinstance(value, str):
        cleaned = value.strip()
        if cleaned:
            result.append(cleaned)
    elif isinstance(value, Iterable):
        for item in value:
            if item is None:
                continue
            text = str(item).strip()
            if text:
                result.append(text)
            if len(result) >= max_items:
                break
    deduped: List[str] = []
    seen = set()
    for item in result:
        if item not in seen:
            deduped.append(item)
            seen.add(item)
    return deduped[:max_items]


@dataclass
class GoalSnapshot:
    """Normalised view over a planner goal sent to the LLM."""

    goal_id: str
    title: Optional[str] = None
    summary: Optional[str] = None
    status: Optional[str] = None
    lane: Optional[str] = None
    priority_hint: Optional[float] = None
    tags: List[str] = field(default_factory=list)
    parent: Optional[str] = None
    owner: Optional[str] = None
    metrics: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    steps: List[str] = field(default_factory=list)

    @classmethod
    def from_plan(cls, goal_id: str, plan: Mapping[str, Any]) -> "GoalSnapshot":
        title = _normalise_string(
            plan.get("title")
            or plan.get("name")
            or plan.get("summary")
            or plan.get("description")
        )
        summary = _normalise_string(plan.get("summary") or plan.get("description"))
        status = _normalise_string(plan.get("status") or plan.get("state"))
        lane = _normalise_string(plan.get("lane") or plan.get("category"))
        priority_hint = _normalise_float(plan.get("priority"))
        tags = _normalise_tags(plan.get("tags"))
        parent = _normalise_string(plan.get("parent"))
        owner = _normalise_string(plan.get("owner"))
        metrics = _normalise_mapping(plan.get("metrics"))
        metadata = _normalise_mapping(plan.get("metadata"))
        dependencies = _normalise_sequence(plan.get("dependencies") or plan.get("depends_on"))
        steps: List[str] = []
        raw_steps = plan.get("steps")
        if isinstance(raw_steps, Iterable):
            for step in raw_steps:
                if isinstance(step, Mapping):
                    desc = _normalise_string(
                        step.get("summary")
                        or step.get("description")
                        or step.get("title")
                    )
                    if desc:
                        steps.append(desc)
                elif isinstance(step, str):
                    cleaned = step.strip()
                    if cleaned:
                        steps.append(cleaned)
                if len(steps) >= 8:
                    break
        return cls(
            goal_id=goal_id,
            title=title,
            summary=summary,
            status=status,
            lane=lane,
            priority_hint=priority_hint,
            tags=tags,
            parent=parent,
            owner=owner,
            metrics=metrics,
            metadata=metadata,
            dependencies=dependencies,
            steps=steps,
        )

    def to_payload(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {"goal_id": self.goal_id}
        if self.title:
            payload["title"] = self.title
        if self.summary:
            payload["summary"] = self.summary
        if self.status:
            payload["status"] = self.status
        if self.lane:
            payload["lane"] = self.lane
        if self.priority_hint is not None:
            payload["priority_hint"] = self.priority_hint
        if self.tags:
            payload["tags"] = list(self.tags)
        if self.parent:
            payload["parent"] = self.parent
        if self.owner:
            payload["owner"] = self.owner
        if self.metrics:
            payload["metrics"] = dict(self.metrics)
        if self.metadata:
            payload["metadata"] = dict(self.metadata)
        if self.dependencies:
            payload["dependencies"] = list(self.dependencies)
        if self.steps:
            payload["steps"] = list(self.steps)
        return payload


@dataclass
class PrioritizedGoal:
    """Structured priority returned by the LLM."""

    goal_id: str
    priority: float
    tags: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)
    confidence: Optional[float] = None
    status: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> Optional["PrioritizedGoal"]:
        goal_id = _normalise_string(payload.get("goal_id") or payload.get("id"))
        if not goal_id:
            return None
        priority = _normalise_float(payload.get("priority"))
        if priority is None:
            priority = 0.0
        priority = max(0.0, min(1.0, priority))
        tags = _normalise_tags(payload.get("tags"))
        notes = _normalise_sequence(payload.get("notes"))
        confidence = _normalise_float(payload.get("confidence"))
        status = _normalise_string(payload.get("status"))
        metadata = _normalise_mapping(payload.get("metadata"))
        return cls(
            goal_id=goal_id,
            priority=priority,
            tags=tags,
            notes=notes,
            confidence=confidence,
            status=status,
            metadata=metadata,
        )

    def apply_to_plan(self, plan: MutableMapping[str, Any]) -> None:
        plan["priority"] = self.priority
        if self.tags:
            plan["tags"] = list(self.tags)
        if self.status:
            plan["status"] = self.status
        if self.metadata:
            plan.setdefault("llm_priority", {}).update(self.metadata)
        if self.notes:
            existing = plan.setdefault("priority_notes", [])
            if isinstance(existing, list):
                for note in self.notes:
                    if note not in existing:
                        existing.append(note)

    def to_mapping(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {
            "goal_id": self.goal_id,
            "priority": self.priority,
            "tags": list(self.tags),
        }
        if self.notes:
            data["notes"] = list(self.notes)
        if self.confidence is not None:
            data["confidence"] = max(0.0, min(1.0, float(self.confidence)))
        if self.status:
            data["status"] = self.status
        if self.metadata:
            data["metadata"] = dict(self.metadata)
        return data


@dataclass
class PrioritizationDirective:
    """Full LLM response for a prioritisation cycle."""

    priorities: List[PrioritizedGoal]
    summary: Optional[str] = None
    global_notes: List[str] = field(default_factory=list)

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> "PrioritizationDirective":
        if not isinstance(payload, Mapping):
            raise PrioritizationError("LLM payload must be a mapping for prioritisation")
        summary = _normalise_string(payload.get("summary"))
        global_notes = _normalise_sequence(payload.get("global_notes"))
        priorities: List[PrioritizedGoal] = []
        raw_priorities = payload.get("priorities") or payload.get("goals")
        if isinstance(raw_priorities, Iterable):
            for item in raw_priorities:
                if not isinstance(item, Mapping):
                    continue
                parsed = PrioritizedGoal.from_payload(item)
                if parsed:
                    priorities.append(parsed)
        if not priorities:
            raise PrioritizationError("LLM response did not contain any priorities")
        return cls(priorities=priorities, summary=summary, global_notes=global_notes)

    def to_mapping(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {
            "priorities": [priority.to_mapping() for priority in self.priorities]
        }
        if self.summary:
            data["summary"] = self.summary
        if self.global_notes:
            data["global_notes"] = list(self.global_notes)
        return data


def _planner_plans(planner: Any) -> Dict[str, MutableMapping[str, Any]]:
    plans: Dict[str, MutableMapping[str, Any]] = {}
    if planner is None:
        return plans
    state = getattr(planner, "state", None)
    if isinstance(state, Mapping):
        raw = state.get("plans")
        if isinstance(raw, Mapping):
            for key, value in raw.items():
                if isinstance(value, MutableMapping):
                    plans[str(key)] = value
                elif isinstance(value, Mapping):
                    plans[str(key)] = dict(value)
    if not plans:
        raw_plans = getattr(planner, "plans", None)
        if isinstance(raw_plans, Mapping):
            for key, value in raw_plans.items():
                if isinstance(value, MutableMapping):
                    plans[str(key)] = value
                elif isinstance(value, Mapping):
                    plans[str(key)] = dict(value)
    return plans


def _global_context(arch: Any) -> Dict[str, Any]:
    context: Dict[str, Any] = {}
    try:
        context["last_output"] = getattr(arch, "last_output_text", None)
    except Exception:
        pass
    try:
        context["last_user_id"] = getattr(arch, "last_user_id", None)
    except Exception:
        pass
    try:
        homeostasis = getattr(arch, "homeostasis", None)
        directive = getattr(homeostasis, "last_directive", None)
        if directive:
            context["homeostasis"] = directive
    except Exception:
        pass
    try:
        identity = getattr(getattr(arch, "self_model", None), "state", {}).get("identity")
        if identity:
            context["identity"] = identity
    except Exception:
        pass
    try:
        planner_state = getattr(getattr(arch, "planner", None), "state", {})
        if isinstance(planner_state, Mapping):
            context["planner_state"] = {
                "lane": planner_state.get("lane"),
                "meta": planner_state.get("meta"),
            }
    except Exception:
        pass
    return {k: v for k, v in context.items() if v is not None}


class GoalPrioritizer:
    """Facade exposing a LLM-only prioritisation workflow."""

    def __init__(self, arch: Any):
        self.arch = arch
        self.logger = getattr(arch, "logger", None)
        self._manager = get_llm_manager()
        # Maintain attribute for backwards compatibility (may be replaced later).
        self.trigger_bus = getattr(arch, "trigger_bus", None)

    def _call_llm(self, snapshots: Sequence[GoalSnapshot]) -> PrioritizationDirective:
        payload = {
            "backlog_size": len(snapshots),
            "goals": [snap.to_payload() for snap in snapshots],
            "context": _global_context(self.arch),
        }
        try:
            response = self._manager.call_dict(
                "cognition_goal_prioritizer", input_payload=payload
            )
        except LLMIntegrationError as exc:  # pragma: no cover - propagates upstream
            if self.logger:
                try:
                    self.logger.error("LLM prioritisation failed", exc_info=True)
                except Exception:
                    pass
            raise PrioritizationError(str(exc)) from exc
        return PrioritizationDirective.from_payload(response)

    def _plans_and_snapshots(self) -> Dict[str, GoalSnapshot]:
        planner = getattr(self.arch, "planner", None)
        plans = _planner_plans(planner)
        snapshots: Dict[str, GoalSnapshot] = {}
        for goal_id, plan in plans.items():
            if not isinstance(plan, Mapping):
                continue
            snapshots[goal_id] = GoalSnapshot.from_plan(goal_id, plan)
        return snapshots

    def reprioritize_all(self) -> Optional[PrioritizationDirective]:
        snapshots = self._plans_and_snapshots()
        if not snapshots:
            return None
        directive = self._call_llm(list(snapshots.values()))
        planner = getattr(self.arch, "planner", None)
        plans = _planner_plans(planner)
        for priority in directive.priorities:
            plan = plans.get(priority.goal_id)
            if not plan:
                continue
            priority.apply_to_plan(plan)
        if self.logger:
            try:
                self.logger.info(
                    "prioritization.completed",
                    extra={
                        "summary": directive.summary,
                        "global_notes": directive.global_notes,
                    },
                )
            except Exception:
                pass
        return directive

    def score_goal(self, goal_id: str, plan: MutableMapping[str, Any]) -> Dict[str, Any]:
        snapshot = GoalSnapshot.from_plan(goal_id, plan)
        directive = self._call_llm([snapshot])
        priority = next(
            (p for p in directive.priorities if p.goal_id == goal_id),
            directive.priorities[0],
        )
        priority.apply_to_plan(plan)
        return priority.to_mapping()

    # Compatibility helper for previous API
    def reprioritize_and_export(self) -> Dict[str, Any]:
        directive = self.reprioritize_all()
        return directive.to_mapping() if directive else {"priorities": []}
