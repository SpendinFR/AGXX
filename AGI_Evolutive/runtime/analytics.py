"""LLM-driven runtime analytics helper.

This module replaces the historical metric pipeline and rolling averages with a
single orchestrator that batches runtime events and asks the local LLM to
produce a semantic digest.  Callers only need to feed raw events; the
interpreter handles batching, prompt construction, logging and history.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, MutableMapping

from AGI_Evolutive.utils.jsonsafe import json_sanitize
from AGI_Evolutive.utils.llm_service import (
    LLMIntegrationError,
    LLMUnavailableError,
    get_llm_manager,
)


def _ensure_mapping(value: Any) -> MutableMapping[str, Any]:
    if isinstance(value, Mapping):
        return dict(value)
    return {"value": value}


@dataclass
class LLMAnalyticsInterpreter:
    """Batch events and request an LLM interpretation.

    Parameters
    ----------
    log_path:
        JSONL file used to persist each flush (events + LLM analysis).
    batch_size:
        Number of events to accumulate before forcing a flush.
    flush_interval:
        Maximum amount of seconds to wait between flushes even if the batch is
        not full.
    enabled:
        When ``False`` the interpreter still logs the raw events but skips the
        LLM call.
    """

    log_path: str = "runtime/llm_analytics.jsonl"
    batch_size: int = 24
    flush_interval: float = 45.0
    enabled: bool = True
    spec_key: str = "runtime_analytics"
    llm_manager: Any | None = None
    max_history: int = 200
    _pending: list[MutableMapping[str, Any]] = field(default_factory=list, init=False)
    _history: list[Mapping[str, Any]] = field(default_factory=list, init=False)
    last_output: Mapping[str, Any] | None = field(default=None, init=False)
    _last_flush_ts: float = field(default=0.0, init=False)

    def __post_init__(self) -> None:
        if self.llm_manager is None:
            self.llm_manager = get_llm_manager()
        os.makedirs(os.path.dirname(self.log_path) or ".", exist_ok=True)
        self._last_flush_ts = time.time()

    # ------------------------------------------------------------------
    def __call__(self, event: Mapping[str, Any] | None) -> Mapping[str, Any] | None:
        if not event:
            return None
        normalised = _ensure_mapping(event)
        normalised.setdefault("timestamp", time.time())
        self._pending.append(json_sanitize(normalised))

        if len(self._pending) >= max(1, int(self.batch_size)):
            return self.flush()
        if time.time() - self._last_flush_ts >= max(5.0, float(self.flush_interval)):
            return self.flush()
        return None

    # ------------------------------------------------------------------
    def flush(self) -> Mapping[str, Any] | None:
        if not self._pending:
            return self.last_output

        events = [dict(item) for item in self._pending]
        payload = {
            "events": events,
            "history": list(self._history[-20:]),
        }

        analysis: Mapping[str, Any] | None = None
        if self.enabled:
            try:
                response = self.llm_manager.call_dict(
                    self.spec_key,
                    input_payload=json_sanitize(payload),
                )
            except (LLMUnavailableError, LLMIntegrationError):
                response = None
            if isinstance(response, Mapping):
                analysis = dict(response)
        self.last_output = analysis
        self._history.append({
            "timestamp": time.time(),
            "analysis": analysis or {},
        })
        if len(self._history) > self.max_history:
            self._history = self._history[-self.max_history :]

        record = {
            "timestamp": time.time(),
            "events": events,
            "analysis": analysis or {},
        }
        self._append_log(record)
        self._pending.clear()
        self._last_flush_ts = time.time()
        return analysis

    # ------------------------------------------------------------------
    def _append_log(self, record: Mapping[str, Any]) -> None:
        with open(self.log_path, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(json_sanitize(record), ensure_ascii=False) + "\n")

    # ------------------------------------------------------------------
    def drain_history(self) -> list[Mapping[str, Any]]:
        """Return the cached LLM analyses for observability dashboards."""

        return list(self._history)

    # ------------------------------------------------------------------
    def extend(self, events: Iterable[Mapping[str, Any]]) -> None:
        for event in events:
            self(event)
