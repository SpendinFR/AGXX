"""LLM-backed JSONL logger."""

from __future__ import annotations

import json
import os
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Mapping, MutableMapping

from AGI_Evolutive.utils.jsonsafe import json_sanitize
from AGI_Evolutive.utils.llm_service import (
    LLMIntegrationError,
    LLMUnavailableError,
    get_llm_manager,
)


@dataclass
class JSONLLogger:
    """Thread-safe JSONL logger that enriches events via the LLM."""

    path: str = "runtime/agent_events.jsonl"
    spec_key: str = "jsonl_logger"
    llm_manager: Any | None = None
    metadata_provider: Callable[[str, Mapping[str, Any]], Mapping[str, Any]] | None = None
    extra_tags: Mapping[str, Any] | None = None
    _lock: threading.Lock = field(default_factory=threading.Lock, init=False)

    def __post_init__(self) -> None:
        if self.llm_manager is None:
            self.llm_manager = get_llm_manager()
        os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)

    # ------------------------------------------------------------------
    def write(self, event_type: str, **fields: Any) -> Mapping[str, Any]:
        metadata = self._resolve_metadata(event_type, fields)
        payload = {
            "event_type": event_type,
            "fields": json_sanitize(fields),
            "metadata": json_sanitize(metadata),
            "tags": dict(self.extra_tags or {}),
        }
        llm_insight = self._call_llm(payload)
        record: MutableMapping[str, Any] = {
            "timestamp": time.time(),
            "type": event_type,
            **json_sanitize(fields),
        }
        if metadata:
            record["metadata"] = metadata
        if llm_insight:
            record["llm_analysis"] = llm_insight
        self._append(record)
        return record

    # ------------------------------------------------------------------
    def snapshot(
        self,
        name: str,
        payload: Mapping[str, Any] | None = None,
        *,
        persistence: Any | None = None,
    ) -> str:
        """Persist a snapshot on disk and annotate it via the LLM."""

        if payload is None and persistence is not None and hasattr(persistence, "make_snapshot"):
            try:
                payload = persistence.make_snapshot() or {}
            except Exception:
                payload = {}
        payload = payload or {}
        directory = os.path.join(os.path.dirname(self.path) or ".", "snapshots")
        os.makedirs(directory, exist_ok=True)
        filename = os.path.join(directory, f"{int(time.time())}_{name}.json")
        with open(filename, "w", encoding="utf-8") as handle:
            json.dump(json_sanitize(payload), handle, ensure_ascii=False, indent=2)
        self.write("snapshot", name=name, path=filename, payload=json_sanitize(payload))
        return filename

    # ------------------------------------------------------------------
    def rotate(self, keep_last: int = 5) -> None:
        if keep_last < 0:
            raise ValueError("keep_last must be >= 0")
        directory = os.path.dirname(self.path) or "."
        basename = os.path.basename(self.path)
        timestamp = int(time.time())
        rotated = os.path.join(directory, f"{basename}.{timestamp}")
        with self._lock:
            if not os.path.exists(self.path):
                return
            os.replace(self.path, rotated)
            open(self.path, "a", encoding="utf-8").close()
            if keep_last == 0:
                return
            archives = [
                (os.path.getmtime(os.path.join(directory, name)), os.path.join(directory, name))
                for name in os.listdir(directory)
                if name.startswith(f"{basename}.")
            ]
            archives.sort(reverse=True)
            for _, path in archives[keep_last:]:
                try:
                    os.remove(path)
                except OSError:
                    continue

    # ------------------------------------------------------------------
    def _resolve_metadata(
        self,
        event_type: str,
        fields: Mapping[str, Any],
    ) -> Mapping[str, Any]:
        if self.metadata_provider is None:
            return {}
        try:
            return dict(self.metadata_provider(event_type, dict(fields)))
        except Exception:
            return {}

    # ------------------------------------------------------------------
    def _call_llm(self, payload: Mapping[str, Any]) -> Mapping[str, Any] | None:
        try:
            response = self.llm_manager.call_dict(self.spec_key, input_payload=payload)
        except (LLMUnavailableError, LLMIntegrationError):
            return None
        if isinstance(response, Mapping):
            return dict(response)
        return None

    # ------------------------------------------------------------------
    def _append(self, record: Mapping[str, Any]) -> None:
        with self._lock:
            with open(self.path, "a", encoding="utf-8") as handle:
                handle.write(json.dumps(json_sanitize(record), ensure_ascii=False) + "\n")
