"""System metrics orchestrator delegating interpretation to the LLM."""

from __future__ import annotations

import subprocess
import time
from dataclasses import dataclass, field
from typing import Any, Mapping, MutableMapping

import psutil

from AGI_Evolutive.utils.jsonsafe import json_sanitize
from AGI_Evolutive.utils.llm_service import (
    LLMIntegrationError,
    LLMUnavailableError,
    get_llm_manager,
)


@dataclass
class SystemMonitor:
    """Collect raw machine metrics and request an LLM commentary."""

    interval: float = 2.0
    spec_key: str = "system_monitor"
    llm_manager: Any | None = None
    last_metrics: Mapping[str, Any] | None = field(default=None, init=False)

    def __post_init__(self) -> None:
        if self.llm_manager is None:
            self.llm_manager = get_llm_manager()

    # ------------------------------------------------------------------
    def poll(self) -> Mapping[str, Any]:
        metrics = self._collect_metrics()
        commentary = self._call_llm(metrics)
        payload: MutableMapping[str, Any] = {"metrics": metrics}
        if commentary:
            payload["llm_analysis"] = commentary
        self.last_metrics = metrics
        return payload

    # ------------------------------------------------------------------
    def _collect_metrics(self) -> Mapping[str, Any]:
        snapshot: MutableMapping[str, Any] = {
            "timestamp": time.time(),
            "cpu": {},
            "memory": {},
            "gpu": {},
            "disks": {},
        }
        try:
            snapshot["cpu"] = {
                "percent": psutil.cpu_percent(interval=0.05),
                "count": psutil.cpu_count(logical=True),
            }
        except Exception:
            snapshot["cpu"] = {}
        try:
            mem = psutil.virtual_memory()
            snapshot["memory"] = {
                "used": mem.used,
                "total": mem.total,
                "percent": mem.percent,
            }
        except Exception:
            snapshot["memory"] = {}
        gpu_info = self._query_gpu()
        if gpu_info:
            snapshot["gpu"] = gpu_info
        disk_info = self._query_disks()
        if disk_info:
            snapshot["disks"] = disk_info
        return snapshot

    # ------------------------------------------------------------------
    def _query_gpu(self) -> Mapping[str, Any]:
        fields = [
            "temperature.gpu",
            "utilization.gpu",
            "memory.used",
            "memory.total",
            "power.draw",
        ]
        cmd = [
            "nvidia-smi",
            f"--query-gpu={','.join(fields)}",
            "--format=csv,noheader,nounits",
        ]
        try:
            output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True, timeout=2)
        except Exception:
            return {}
        pieces = [part.strip() for part in output.strip().split(",")]
        if len(pieces) < len(fields):
            return {}
        payload: MutableMapping[str, Any] = {}
        keys = ["temp_c", "util_pct", "mem_used_mb", "mem_total_mb", "power_w"]
        for key, value in zip(keys, pieces):
            try:
                payload[key] = float(value)
            except ValueError:
                continue
        return payload

    # ------------------------------------------------------------------
    def _query_disks(self) -> Mapping[str, Any]:
        try:
            counters = psutil.disk_io_counters(perdisk=True)
        except Exception:
            return {}
        disks: MutableMapping[str, Any] = {}
        for name, stats in counters.items():
            disks[name] = {
                "read_bytes": stats.read_bytes,
                "write_bytes": stats.write_bytes,
                "read_count": stats.read_count,
                "write_count": stats.write_count,
            }
        return disks

    # ------------------------------------------------------------------
    def _call_llm(self, metrics: Mapping[str, Any]) -> Mapping[str, Any] | None:
        payload = {
            "metrics": metrics,
            "previous": self.last_metrics,
        }
        try:
            response = self.llm_manager.call_dict(
                self.spec_key,
                input_payload=json_sanitize(payload),
            )
        except (LLMUnavailableError, LLMIntegrationError):
            return None
        if isinstance(response, Mapping):
            return dict(response)
        return None
