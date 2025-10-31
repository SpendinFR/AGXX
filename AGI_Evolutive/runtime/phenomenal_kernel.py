"""Phenomenological state orchestrated through dedicated LLM contracts."""

from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Deque, Mapping, MutableMapping, Sequence

from AGI_Evolutive.utils.jsonsafe import json_sanitize
from AGI_Evolutive.utils.llm_service import (
    LLMIntegrationError,
    LLMUnavailableError,
    get_llm_manager,
)


@dataclass
class SystemAlert:
    """High level alert injected into the phenomenal kernel."""

    kind: str
    intensity: float = 1.0
    slowdown: float | None = None
    duration: float = 30.0
    timestamp: float = field(default_factory=lambda: float(time.time()))

    def expired(self, now: float | None = None) -> bool:
        now = float(now or time.time())
        return now - self.timestamp >= self.duration

    def to_payload(self, now: float | None = None) -> Mapping[str, Any]:
        remaining = max(0.0, self.duration - (float(now or time.time()) - self.timestamp))
        payload: MutableMapping[str, Any] = {
            "kind": self.kind,
            "intensity": float(self.intensity),
            "remaining": remaining,
        }
        if self.slowdown is not None:
            payload["slowdown"] = float(self.slowdown)
        return payload


@dataclass
class PhenomenalKernel:
    """Delegate phenomenal state updates to the LLM."""

    llm_manager: Any | None = None
    spec_key: str = "phenomenal_kernel"
    alerts: Deque[SystemAlert] = field(default_factory=deque, init=False)
    state: Mapping[str, Any] = field(default_factory=dict, init=False)

    def __post_init__(self) -> None:
        if self.llm_manager is None:
            self.llm_manager = get_llm_manager()

    # ------------------------------------------------------------------
    def register_alert(
        self,
        kind: str,
        *,
        intensity: float = 1.0,
        slowdown: float | None = None,
        duration: float = 30.0,
        timestamp: float | None = None,
    ) -> None:
        if not kind:
            return
        alert = SystemAlert(
            kind=str(kind),
            intensity=float(intensity),
            slowdown=slowdown,
            duration=float(max(0.5, duration)),
            timestamp=float(timestamp) if timestamp is not None else float(time.time()),
        )
        self.alerts.append(alert)

    # ------------------------------------------------------------------
    def update(
        self,
        *,
        emotional_state: Mapping[str, Any] | None = None,
        novelty: float | None = None,
        belief: float | None = None,
        progress: float | None = None,
        extrinsic_reward: float | None = None,
        hedonic_signal: float | None = None,
        fatigue: float | None = None,
        alerts: Sequence[Mapping[str, Any]] | None = None,
    ) -> Mapping[str, Any]:
        now = time.time()
        if alerts:
            for alert in alerts:
                kind = str(alert.get("kind") or "external")
                self.register_alert(
                    kind,
                    intensity=float(alert.get("intensity", 1.0)),
                    slowdown=alert.get("slowdown"),
                    duration=float(alert.get("duration", 30.0)),
                    timestamp=float(alert.get("timestamp", now)),
                )
        active_alerts = [alert.to_payload(now) for alert in list(self.alerts) if not alert.expired(now)]
        self.alerts = deque(alert for alert in self.alerts if not alert.expired(now))

        payload = {
            "emotional_state": json_sanitize(emotional_state or {}),
            "novelty": novelty,
            "belief": belief,
            "progress": progress,
            "extrinsic_reward": extrinsic_reward,
            "hedonic_signal": hedonic_signal,
            "fatigue": fatigue,
            "alerts": active_alerts,
            "previous_state": json_sanitize(self.state),
        }
        try:
            response = self.llm_manager.call_dict(
                self.spec_key,
                input_payload=json_sanitize(payload),
            )
        except (LLMUnavailableError, LLMIntegrationError):
            response = None
        if isinstance(response, Mapping):
            self.state = dict(response)
        return dict(self.state)


@dataclass
class ModeManager:
    """Ask the LLM to arbitrate between work and flânerie modes."""

    llm_manager: Any | None = None
    spec_key: str = "phenomenal_mode_manager"
    history: Deque[Mapping[str, Any]] = field(default_factory=lambda: deque(maxlen=200), init=False)

    def __post_init__(self) -> None:
        if self.llm_manager is None:
            self.llm_manager = get_llm_manager()

    # ------------------------------------------------------------------
    def update(self, kernel_state: Mapping[str, Any], *, urgent: bool = False) -> Mapping[str, Any]:
        payload = {
            "kernel_state": json_sanitize(kernel_state),
            "urgent": urgent,
            "history": list(self.history),
        }
        try:
            response = self.llm_manager.call_dict(
                self.spec_key,
                input_payload=json_sanitize(payload),
            )
        except (LLMUnavailableError, LLMIntegrationError):
            return {"mode": kernel_state.get("mode", "travail")}
        if isinstance(response, Mapping):
            snapshot = dict(response)
            self.history.append({"timestamp": time.time(), **snapshot})
            return snapshot
        return {"mode": kernel_state.get("mode", "travail")}
