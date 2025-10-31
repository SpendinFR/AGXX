"""Minimal LLM-driven background scheduler."""

from __future__ import annotations

import os
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Deque, Mapping, MutableMapping

from AGI_Evolutive.runtime.logger import JSONLLogger
from AGI_Evolutive.utils.jsonsafe import json_sanitize
from AGI_Evolutive.utils.llm_service import (
    LLMIntegrationError,
    LLMUnavailableError,
    get_llm_manager,
)


@dataclass
class Scheduler:
    """Periodically consult the LLM to decide maintenance actions."""

    arch: Any
    data_dir: str = "data"
    interval: float = 90.0
    spec_key: str = "scheduler"
    llm_manager: Any | None = None
    logger: JSONLLogger | None = None
    history_size: int = 200
    _thread: threading.Thread | None = field(default=None, init=False)
    _running: bool = field(default=False, init=False)
    _decisions: Deque[Mapping[str, Any]] = field(default_factory=deque, init=False)

    def __post_init__(self) -> None:
        if self.llm_manager is None:
            self.llm_manager = get_llm_manager()
        log_path = os.path.join(self.data_dir, "runtime", "scheduler.log.jsonl")
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        self.logger = self.logger or JSONLLogger(path=log_path)
        self._decisions = deque(maxlen=self.history_size)

    # ------------------------------------------------------------------
    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run_loop, name="runtime-scheduler", daemon=True)
        self._thread.start()

    # ------------------------------------------------------------------
    def stop(self, timeout: float | None = None) -> None:
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout)

    # ------------------------------------------------------------------
    def tick(self) -> Mapping[str, Any] | None:
        snapshot = self._build_snapshot()
        decision = self._call_llm(snapshot)
        if decision is None:
            return None
        decision_record = {
            "timestamp": time.time(),
            "decision": decision,
        }
        self._decisions.append(decision_record)
        self.logger.write("scheduler_decision", snapshot=snapshot, decision=decision)
        self._apply(decision)
        return decision

    # ------------------------------------------------------------------
    def history(self) -> list[Mapping[str, Any]]:
        return list(self._decisions)

    # ------------------------------------------------------------------
    def _run_loop(self) -> None:
        while self._running:
            try:
                self.tick()
            except Exception:
                pass
            time.sleep(max(30.0, float(self.interval)))

    # ------------------------------------------------------------------
    def _build_snapshot(self) -> Mapping[str, Any]:
        arch = self.arch
        jobs = getattr(arch, "jobs", None)
        goals = getattr(arch, "goals", None)
        auto_signals = getattr(arch, "auto_signals", None)
        snapshot: MutableMapping[str, Any] = {
            "timestamp": time.time(),
            "mode": getattr(arch, "current_mode", None),
            "phenomenal": json_sanitize(getattr(arch, "phenomenal_kernel_state", {})),
        }
        if jobs is not None:
            snapshot["jobs"] = {
                "budgets": getattr(jobs, "budgets", {}),
                "low_load": bool(getattr(jobs, "is_low_load", lambda: True)()),
            }
        if goals is not None and hasattr(goals, "active_goals"):
            try:
                active = list(getattr(goals, "active_goals")())  # type: ignore[call-arg]
            except Exception:
                active = []
            snapshot["goals"] = [
                {"id": getattr(goal, "id", None), "status": getattr(goal, "status", None)}
                for goal in active[:10]
            ]
        signals = None
        if auto_signals is not None and hasattr(auto_signals, "snapshot"):
            try:
                signals = auto_signals.snapshot()
            except Exception:
                signals = None
        if signals:
            snapshot["signals"] = json_sanitize(signals)
        return snapshot

    # ------------------------------------------------------------------
    def _call_llm(self, snapshot: Mapping[str, Any]) -> Mapping[str, Any] | None:
        try:
            response = self.llm_manager.call_dict(
                self.spec_key,
                input_payload=json_sanitize({
                    "snapshot": snapshot,
                    "history": list(self._decisions),
                }),
            )
        except (LLMUnavailableError, LLMIntegrationError):
            return None
        if isinstance(response, Mapping):
            return dict(response)
        return None

    # ------------------------------------------------------------------
    def _apply(self, decision: Mapping[str, Any]) -> None:
        actions = decision.get("actions")
        if not isinstance(actions, list):
            return
        for action in actions:
            if not isinstance(action, Mapping):
                continue
            target_name = action.get("target")
            method_name = action.get("method")
            args = action.get("args") or {}
            target = self._resolve_target(target_name)
            if target is None or not method_name:
                continue
            method = getattr(target, method_name, None)
            if callable(method):
                try:
                    method(**json_sanitize(args))
                except Exception:
                    continue

    # ------------------------------------------------------------------
    def _resolve_target(self, name: str | None) -> Any | None:
        if not name:
            return None
        if name == "arch":
            return self.arch
        return getattr(self.arch, str(name), None)
