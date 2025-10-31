"""LLM-backed perception facade."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping, MutableMapping

import numpy as np

from AGI_Evolutive.utils.jsonsafe import json_sanitize
from AGI_Evolutive.utils.llm_service import (
    LLMIntegrationError,
    LLMUnavailableError,
    get_llm_manager,
)


class Modality(str, Enum):
    VISUAL = "visual"
    AUDITORY = "auditory"
    TEXT = "text"
    SENSOR = "sensor"


@dataclass
class PerceptualScene:
    objects: list[Mapping[str, Any]]
    salience_map: Mapping[str, Any]
    background: MutableMapping[str, Any] = field(default_factory=dict)


@dataclass
class PerceptionSystem:
    cognitive_architecture: Any | None = None
    memory: Any | None = None
    llm_manager: Any | None = None
    spec_key: str = "perception_module"
    perceptual_parameters: MutableMapping[str, float] = field(default_factory=lambda: {
        "sensitivity_threshold": 0.1,
        "discrimination_threshold": 0.05,
        "integration_window": 0.1,
        "object_persistence": 2.0,
        "change_blindness_threshold": 0.3,
    })
    _history: list[Mapping[str, Any]] = field(default_factory=list, init=False)
    _last_llm_summary: Mapping[str, Any] | None = field(default=None, init=False)

    def __post_init__(self) -> None:
        if self.llm_manager is None:
            self.llm_manager = get_llm_manager()

    # ------------------------------------------------------------------
    def process_sensory_input(self, sensory_data: Mapping[Modality, Any]) -> PerceptualScene:
        metrics = self._summarise_inputs(sensory_data)
        payload = {
            "metrics": metrics,
            "parameters": dict(self.perceptual_parameters),
            "history": self._history[-20:],
            "arch": self._arch_snapshot(),
        }
        try:
            response = self.llm_manager.call_dict(self.spec_key, input_payload=json_sanitize(payload))
        except (LLMUnavailableError, LLMIntegrationError):
            response = None

        background: MutableMapping[str, Any] = {}
        if isinstance(response, Mapping):
            llm_analysis = dict(response)
            background["llm_analysis"] = llm_analysis
            self._last_llm_summary = llm_analysis
            recommended = llm_analysis.get("recommended_settings") or {}
            for key, value in recommended.items():
                try:
                    self.perceptual_parameters[str(key)] = float(value)
                except (TypeError, ValueError):
                    continue
            self._history.append({"metrics": metrics, "analysis": llm_analysis})
        else:
            self._last_llm_summary = None

        scene = PerceptualScene(objects=metrics.get("objects", []), salience_map=metrics.get("salience", {}), background=background)
        return scene

    # ------------------------------------------------------------------
    def _summarise_inputs(self, sensory_data: Mapping[Modality, Any]) -> MutableMapping[str, Any]:
        summary: MutableMapping[str, Any] = {"modalities": {}}
        objects: list[Mapping[str, Any]] = []
        for modality, value in sensory_data.items():
            modality_key = modality.value if isinstance(modality, Modality) else str(modality)
            if isinstance(value, np.ndarray):
                summary["modalities"][modality_key] = {
                    "shape": list(value.shape),
                    "mean": float(np.mean(value)),
                    "std": float(np.std(value)),
                }
            else:
                summary["modalities"][modality_key] = {"type": type(value).__name__}
            objects.append({"modality": modality_key, "summary": summary["modalities"][modality_key]})
        summary["objects"] = objects
        summary["salience"] = {obj["modality"]: obj.get("summary", {}) for obj in objects}
        return summary

    # ------------------------------------------------------------------
    def _arch_snapshot(self) -> Mapping[str, Any]:
        arch = self.cognitive_architecture
        if arch is None:
            return {}
        snapshot: MutableMapping[str, Any] = {}
        for attr in ("current_mode", "phenomenal_kernel_state", "global_slowdown"):
            value = getattr(arch, attr, None)
            if value is not None:
                snapshot[attr] = json_sanitize(value)
        return snapshot


__all__ = ["PerceptionSystem", "PerceptualScene", "Modality", "np"]
