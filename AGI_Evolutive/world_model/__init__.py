"""LLM-backed world model facades."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Any, Deque, Mapping, MutableMapping

from AGI_Evolutive.utils.jsonsafe import json_sanitize
from AGI_Evolutive.utils.llm_service import (
    LLMIntegrationError,
    LLMUnavailableError,
    get_llm_manager,
)


@dataclass
class WorldModelOrchestrator:
    domain: str
    arch: Any | None = None
    memory: Any | None = None
    llm_manager: Any | None = None
    spec_key: str = "world_model"
    history: Deque[Mapping[str, Any]] = field(default_factory=lambda: deque(maxlen=100), init=False)

    def __post_init__(self) -> None:
        if self.llm_manager is None:
            self.llm_manager = get_llm_manager()

    # ------------------------------------------------------------------
    def invoke(self, intent: str, payload: Mapping[str, Any] | None = None) -> Mapping[str, Any]:
        request = {
            "domain": self.domain,
            "intent": intent,
            "payload": json_sanitize(payload or {}),
            "history": list(self.history),
            "arch": self._arch_snapshot(),
        }
        try:
            response = self.llm_manager.call_dict(self.spec_key, input_payload=request)
        except (LLMUnavailableError, LLMIntegrationError):
            response = None
        if isinstance(response, Mapping):
            snapshot = dict(response)
            self.history.append({"intent": intent, "response": snapshot})
            return snapshot
        return {}

    # ------------------------------------------------------------------
    def _arch_snapshot(self) -> Mapping[str, Any]:
        arch = self.arch
        if arch is None:
            return {}
        snapshot: MutableMapping[str, Any] = {}
        for attr in ("current_mode", "phenomenal_kernel_state", "global_slowdown"):
            value = getattr(arch, attr, None)
            if value is not None:
                snapshot[attr] = json_sanitize(value)
        return snapshot


class PhysicsEngine(WorldModelOrchestrator):
    def __init__(self, cognitive_architecture: Any | None = None, memory_system: Any | None = None, **kwargs: Any) -> None:
        super().__init__("physics", arch=cognitive_architecture, memory=memory_system, **kwargs)

    def step(self, context: Mapping[str, Any] | None = None) -> Mapping[str, Any]:
        return self.invoke("step", context)

    def project(self, proposal: Mapping[str, Any]) -> Mapping[str, Any]:
        return self.invoke("project", proposal)


class SocialModel(WorldModelOrchestrator):
    def __init__(self, cognitive_architecture: Any | None = None, **kwargs: Any) -> None:
        super().__init__("social", arch=cognitive_architecture, **kwargs)

    def simulate(self, interaction: Mapping[str, Any]) -> Mapping[str, Any]:
        return self.invoke("simulate", interaction)

    def diagnose(self, context: Mapping[str, Any]) -> Mapping[str, Any]:
        return self.invoke("diagnose", context)


class TemporalReasoning(WorldModelOrchestrator):
    def __init__(self, cognitive_architecture: Any | None = None, **kwargs: Any) -> None:
        super().__init__("temporal", arch=cognitive_architecture, **kwargs)

    def plan(self, scenario: Mapping[str, Any]) -> Mapping[str, Any]:
        return self.invoke("plan", scenario)

    def assess(self, timeline: Mapping[str, Any]) -> Mapping[str, Any]:
        return self.invoke("assess", timeline)


class SpatialReasoning(WorldModelOrchestrator):
    def __init__(self, cognitive_architecture: Any | None = None, **kwargs: Any) -> None:
        super().__init__("spatial", arch=cognitive_architecture, **kwargs)

    def infer(self, layout: Mapping[str, Any]) -> Mapping[str, Any]:
        return self.invoke("infer", layout)

    def route(self, request: Mapping[str, Any]) -> Mapping[str, Any]:
        return self.invoke("route", request)
