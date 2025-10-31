"""Runtime dashboard helpers that summarise logs via the LLM."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Mapping

from AGI_Evolutive.utils.jsonsafe import json_sanitize
from AGI_Evolutive.utils.llm_service import (
    LLMIntegrationError,
    LLMUnavailableError,
    get_llm_manager,
)


@dataclass
class RuntimeDashReporter:
    llm_manager: Any | None = None
    spec_key: str = "runtime_dash"
    logs_dir: str = "logs"

    def __post_init__(self) -> None:
        if self.llm_manager is None:
            self.llm_manager = get_llm_manager()

    # ------------------------------------------------------------------
    def build_report(self, *, since: datetime | None = None) -> Mapping[str, Any]:
        records = {
            "reasoning": self._read_jsonl("reasoning.jsonl", since),
            "experiments": self._read_jsonl("experiments.jsonl", since),
            "metacog": self._read_jsonl("metacog.log", since),
            "goals": self._read_json("goals_dag.json"),
        }
        payload = {
            "logs": json_sanitize(records),
            "since": since.isoformat() if since else None,
        }
        try:
            response = self.llm_manager.call_dict(self.spec_key, input_payload=payload)
        except (LLMUnavailableError, LLMIntegrationError):
            response = None
        report: dict[str, Any] = {"logs": records}
        if isinstance(response, Mapping):
            report["analysis"] = dict(response)
        return report

    # ------------------------------------------------------------------
    def _read_jsonl(self, name: str, since: datetime | None) -> list[Mapping[str, Any]]:
        path = os.path.join(self.logs_dir, name)
        if not os.path.exists(path):
            return []
        items: list[Mapping[str, Any]] = []
        with open(path, "r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if since and not self._is_recent(record, since):
                    continue
                if isinstance(record, Mapping):
                    items.append(record)
        return items

    # ------------------------------------------------------------------
    def _read_json(self, name: str) -> Mapping[str, Any]:
        path = os.path.join(self.logs_dir, name)
        if not os.path.exists(path):
            return {}
        try:
            with open(path, "r", encoding="utf-8") as handle:
                data = json.load(handle)
        except json.JSONDecodeError:
            return {}
        if isinstance(data, Mapping):
            return data
        return {}

    # ------------------------------------------------------------------
    def _is_recent(self, record: Mapping[str, Any], since: datetime) -> bool:
        for key in ("timestamp", "time", "created_at"):
            value = record.get(key)
            if isinstance(value, (int, float)):
                try:
                    ts = datetime.fromtimestamp(float(value))
                except (OverflowError, ValueError):
                    continue
                return ts >= since
            if isinstance(value, str):
                for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
                    try:
                        ts = datetime.strptime(value[: len(fmt)], fmt)
                    except ValueError:
                        continue
                    return ts >= since
        return True
