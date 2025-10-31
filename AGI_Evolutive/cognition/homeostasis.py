"""LLM-first homeostasis orchestration.

This module intentionally collapses the historical blend of bandits, EMAs and
hand-tuned heuristics into a compact interface backed by a single LLM call.
Each public helper simply forwards a structured payload to the `homeostasis`
specification and merges the returned directive into the persisted state.
"""

from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, Mapping, MutableMapping, Optional

from AGI_Evolutive.utils.jsonsafe import json_sanitize
from AGI_Evolutive.utils.llm_service import try_call_llm_dict

from AGI_Evolutive.core.config import cfg


logger = logging.getLogger(__name__)


def _now() -> float:
    return time.time()


_DEFAULT_DRIVES: Dict[str, float] = {
    "curiosity": 0.6,
    "self_preservation": 0.7,
    "social_bonding": 0.4,
    "competence": 0.5,
    "play": 0.3,
    "restoration": 0.45,
    "task_activation": 0.55,
    "energy": 0.65,
    "respiration": 0.7,
    "thermal_regulation": 0.75,
    "memory_balance": 0.6,
}


@dataclass
class HomeostasisDirective:
    """Structured response produced by the LLM orchestrator."""

    drive_targets: Dict[str, float] = field(default_factory=dict)
    rewards: Dict[str, float] = field(default_factory=dict)
    advisories: Iterable[str] = field(default_factory=tuple)
    actions: Iterable[Mapping[str, Any]] = field(default_factory=tuple)
    telemetry: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_payload(cls, payload: Any) -> "HomeostasisDirective":
        if not isinstance(payload, Mapping):
            return cls()

        drive_targets: Dict[str, float] = {}
        raw_targets = payload.get("drive_targets") or payload.get("drive_updates")
        if isinstance(raw_targets, Mapping):
            for name, value in raw_targets.items():
                try:
                    drive_targets[str(name)] = float(value)
                except (TypeError, ValueError):
                    continue

        rewards: Dict[str, float] = {}
        raw_rewards = payload.get("rewards") or {}
        if isinstance(raw_rewards, Mapping):
            for name, value in raw_rewards.items():
                try:
                    rewards[str(name)] = float(value)
                except (TypeError, ValueError):
                    continue
        reward_signal = payload.get("reward_signal")
        if reward_signal is not None:
            try:
                rewards.setdefault("extrinsic", float(reward_signal))
            except (TypeError, ValueError):
                pass

        advisories = []
        raw_advisories = payload.get("notes") or payload.get("advisories")
        if isinstance(raw_advisories, str):
            text = raw_advisories.strip()
            if text:
                advisories.append(text)
        elif isinstance(raw_advisories, Iterable):
            for entry in raw_advisories:
                if not isinstance(entry, str):
                    continue
                text = entry.strip()
                if text:
                    advisories.append(text)

        actions = []
        for raw_action in payload.get("actions", []):
            if isinstance(raw_action, Mapping):
                actions.append({str(k): raw_action[k] for k in raw_action if isinstance(k, str)})

        telemetry: Dict[str, Any] = {}
        if isinstance(payload.get("telemetry"), Mapping):
            telemetry = {str(k): payload["telemetry"][k] for k in payload["telemetry"] if isinstance(k, str)}

        return cls(
            drive_targets=drive_targets,
            rewards=rewards,
            advisories=tuple(advisories),
            actions=tuple(actions),
            telemetry=telemetry,
        )


class Homeostasis:
    """Facade exposing a single-LLM-call workflow for drive regulation."""

    def __init__(self) -> None:
        self._path = cfg().get("HOMEOSTASIS_PATH")
        self.state: Dict[str, Any] = {
            "drives": dict(_DEFAULT_DRIVES),
            "rewards": {"intrinsic": 0.0, "extrinsic": 0.0, "hedonic": 0.0},
            "meta": {},
            "last_update": _now(),
        }
        self._load()

    # ------------------------------------------------------------------
    # Persistence helpers
    # ------------------------------------------------------------------

    def _load(self) -> None:
        path = self._path
        if not path or not os.path.exists(path):
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("Impossible de charger l'état homeostasis: %s", exc)
            return

        if isinstance(loaded, Mapping):
            drives = loaded.get("drives")
            if isinstance(drives, Mapping):
                self.state["drives"] = {
                    str(name): float(loaded_value)
                    for name, loaded_value in drives.items()
                    if isinstance(name, str) and isinstance(loaded_value, (int, float))
                }
            rewards = loaded.get("rewards")
            if isinstance(rewards, Mapping):
                self.state["rewards"] = {
                    str(name): float(loaded_value)
                    for name, loaded_value in rewards.items()
                    if isinstance(name, str) and isinstance(loaded_value, (int, float))
                }
            for legacy_key in ("intrinsic_reward", "extrinsic_reward", "hedonic_reward"):
                if isinstance(loaded.get(legacy_key), (int, float)):
                    self.state[legacy_key] = float(loaded[legacy_key])
            meta = loaded.get("meta")
            if isinstance(meta, Mapping):
                self.state["meta"] = dict(meta)

    def _save(self) -> None:
        path = self._path
        if not path:
            return
        directory = os.path.dirname(path) or "."
        os.makedirs(directory, exist_ok=True)
        snapshot = dict(self.state)
        snapshot.setdefault("drives", dict(_DEFAULT_DRIVES))
        snapshot.setdefault("rewards", {"intrinsic": 0.0, "extrinsic": 0.0, "hedonic": 0.0})
        with open(path, "w", encoding="utf-8") as f:
            json.dump(json_sanitize(snapshot), f, ensure_ascii=False, indent=2)

    # ------------------------------------------------------------------
    # Core LLM interaction
    # ------------------------------------------------------------------

    def _call_llm(self, reason: str, signals: Optional[Mapping[str, Any]] = None) -> HomeostasisDirective:
        payload = {
            "reason": reason,
            "signals": json_sanitize(signals or {}),
            "state": {
                "drives": dict(self.state.get("drives", {})),
                "rewards": dict(self.state.get("rewards", {})),
                "meta": json_sanitize(self.state.get("meta", {})),
            },
            "timestamp": _now(),
        }
        logger.debug("Homeostasis LLM payload (%s): %s", reason, payload)
        llm_result = try_call_llm_dict(
            "homeostasis",
            input_payload=payload,
            logger=logger,
        )
        directive = HomeostasisDirective.from_payload(llm_result)
        self._apply_directive(directive, reason)
        return directive

    def _apply_directive(self, directive: HomeostasisDirective, reason: str) -> None:
        drives = self.state.setdefault("drives", dict(_DEFAULT_DRIVES))
        for name, value in directive.drive_targets.items():
            try:
                drives[name] = max(0.0, min(1.0, float(value)))
            except (TypeError, ValueError):
                continue

        rewards = self.state.setdefault("rewards", {"intrinsic": 0.0, "extrinsic": 0.0, "hedonic": 0.0})
        for name, value in directive.rewards.items():
            try:
                rewards[name] = float(value)
            except (TypeError, ValueError):
                continue
        # Maintain legacy top-level keys for callers that still rely on them.
        self.state["intrinsic_reward"] = float(rewards.get("intrinsic", self.state.get("intrinsic_reward", 0.0)))
        self.state["extrinsic_reward"] = float(rewards.get("extrinsic", self.state.get("extrinsic_reward", 0.0)))
        self.state["hedonic_reward"] = float(rewards.get("hedonic", self.state.get("hedonic_reward", 0.0)))

        meta = self.state.setdefault("meta", {})
        meta.setdefault("advisories", [])
        if directive.advisories:
            meta["advisories"] = list(directive.advisories)
        meta.setdefault("actions", [])
        if directive.actions:
            meta["actions"] = list(directive.actions)
        meta.setdefault("telemetry", {})
        if directive.telemetry:
            meta["telemetry"] = dict(directive.telemetry)
        meta["last_reason"] = reason
        meta["last_updated_at"] = _now()

        self.state["last_update"] = meta["last_updated_at"]
        self.state["last_directive"] = {
            "drive_targets": directive.drive_targets,
            "rewards": directive.rewards,
            "advisories": list(directive.advisories),
            "actions": list(directive.actions),
            "telemetry": directive.telemetry,
            "reason": reason,
        }
        self._save()

    # ------------------------------------------------------------------
    # Public helpers – all backed by `_call_llm`
    # ------------------------------------------------------------------

    def decay(self) -> None:
        self._call_llm("decay")

    def compute_intrinsic_reward(self, info_gain: float, progress: float) -> float:
        directive = self._call_llm(
            "intrinsic_reward",
            {"info_gain": float(info_gain), "progress": float(progress)},
        )
        if "intrinsic" in directive.rewards:
            return float(directive.rewards["intrinsic"])
        return float(self.state.get("intrinsic_reward", 0.0))

    def compute_extrinsic_reward_from_memories(self, recent_feedback: str) -> float:
        directive = self._call_llm(
            "memory_feedback",
            {"recent_feedback": (recent_feedback or "").strip()},
        )
        if "extrinsic" in directive.rewards:
            return float(directive.rewards["extrinsic"])
        return float(self.state.get("extrinsic_reward", 0.0))

    def adjust_drive(self, drive: str, delta: float, max_step: float = 0.08) -> None:
        self._call_llm(
            "manual_adjust",
            {"drive": str(drive), "delta": float(delta), "max_step": float(max_step)},
        )

    def integrate_system_metrics(self, metrics: MutableMapping[str, Any]) -> Dict[str, float]:
        directive = self._call_llm("system_metrics", {"metrics": json_sanitize(metrics)})
        return dict(directive.drive_targets)

    def register_hedonic_state(
        self,
        pleasure: float,
        mode: str = "travail",
        meta: Optional[Mapping[str, Any]] = None,
    ) -> None:
        self._call_llm(
            "hedonic_state",
            {"pleasure": float(pleasure), "mode": mode, "meta": json_sanitize(meta or {})},
        )

    def register_global_slowdown(self, slowdown: float, meta: Optional[Mapping[str, Any]] = None) -> None:
        self._call_llm(
            "global_slowdown",
            {"slowdown": float(max(0.0, slowdown)), "meta": json_sanitize(meta or {})},
        )

    def update_from_rewards(self, intrinsic: float, extrinsic: float) -> None:
        self._call_llm(
            "reward_update",
            {"intrinsic": float(intrinsic), "extrinsic": float(extrinsic)},
        )

    def process_feedback(self, text: str, channel: Optional[str] = None) -> HomeostasisDirective:
        return self._call_llm(
            "feedback",
            {"text": (text or "").strip(), "channel": channel or "unknown"},
        )

