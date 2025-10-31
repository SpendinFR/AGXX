"""LLM-only autonomous signal registry."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Optional, Sequence

from AGI_Evolutive.utils.llm_service import LLMIntegrationError, get_llm_manager


class AutoSignalError(RuntimeError):
    """Raised when the LLM payload for auto signals is invalid."""


def _coerce_string(value: Any) -> Optional[str]:
    if isinstance(value, str):
        stripped = value.strip()
        if stripped:
            return stripped
    return None


def _coerce_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _coerce_mapping(value: Any) -> Dict[str, Any]:
    if not isinstance(value, Mapping):
        return {}
    return {str(key): val for key, val in value.items()}


def _coerce_string_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, str):
        value = [value]
    items: List[str] = []
    if isinstance(value, Iterable) and not isinstance(value, (bytes, bytearray)):
        for item in value:
            if isinstance(item, str):
                cleaned = item.strip()
                if cleaned:
                    items.append(cleaned)
    return items


def _ensure_metric(definition: MutableMapping[str, Any], *, fallback: str) -> str:
    metric = _coerce_string(definition.get("metric"))
    if metric:
        definition["metric"] = metric
        return metric
    name = _coerce_string(definition.get("name")) or fallback
    definition["metric"] = name
    return name


@dataclass
class AutoSignal:
    """Structured representation of an autonomous signal definition."""

    action_type: str
    name: str
    metric: str
    direction: str
    target: Optional[float]
    weight: Optional[float]
    source: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    last_value: Optional[float] = None
    last_source: Optional[str] = None
    last_updated: float = 0.0

    @classmethod
    def from_payload(
        cls,
        payload: Mapping[str, Any],
        *,
        action_type: str,
    ) -> "AutoSignal":
        if not isinstance(payload, Mapping):
            raise AutoSignalError("Signal payload must be a mapping")
        data: MutableMapping[str, Any] = dict(payload)
        metric = _ensure_metric(data, fallback=f"{action_type}_signal")
        name = _coerce_string(data.get("name")) or metric
        direction = _coerce_string(data.get("direction")) or "above"
        target = _coerce_float(data.get("target"))
        weight = _coerce_float(data.get("weight"))
        source = _coerce_string(data.get("source")) or "auto_evolution"
        metadata = _coerce_mapping(data.get("metadata"))
        return cls(
            action_type=str(action_type),
            name=name,
            metric=metric,
            direction=direction.lower(),
            target=target,
            weight=weight,
            source=source,
            metadata=metadata,
        )

    def to_observation(self) -> Optional[float]:
        return self.last_value


@dataclass
class AutoSignalDerivationRequest:
    """Payload forwarded to the LLM for signal derivation."""

    action_type: str
    description: str
    requirements: Sequence[str] = field(default_factory=tuple)
    hints: Sequence[str] = field(default_factory=tuple)
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def to_payload(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "action_type": self.action_type,
            "description": self.description,
        }
        if self.requirements:
            payload["requirements"] = _coerce_string_list(self.requirements)
        if self.hints:
            payload["hints"] = _coerce_string_list(self.hints)
        if self.metadata:
            payload["metadata"] = _coerce_mapping(self.metadata)
        return payload


@dataclass
class AutoSignalRegistrationRequest:
    """Payload for registering signals with the LLM contract."""

    action_type: str
    signals: Sequence[Mapping[str, Any]]
    evaluation: Optional[Mapping[str, Any]] = None
    blueprint: Optional[Mapping[str, Any]] = None
    description: Optional[str] = None
    requirements: Sequence[str] = field(default_factory=tuple)
    hints: Sequence[str] = field(default_factory=tuple)

    def to_payload(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "action_type": self.action_type,
            "signals": [
                _coerce_mapping(signal)
                for signal in self.signals
                if isinstance(signal, Mapping)
            ],
        }
        if self.evaluation:
            payload["evaluation"] = _coerce_mapping(self.evaluation)
        if self.blueprint:
            payload["blueprint"] = _coerce_mapping(self.blueprint)
        if self.description:
            payload["description"] = self.description
        if self.requirements:
            payload["requirements"] = _coerce_string_list(self.requirements)
        if self.hints:
            payload["hints"] = _coerce_string_list(self.hints)
        return payload


class AutoSignalRegistry:
    """Delegates autonomous signal lifecycle to a single LLM contract."""

    def __init__(self, *, llm_manager=None) -> None:
        self._manager = llm_manager or get_llm_manager()
        self._signals: Dict[str, Dict[str, AutoSignal]] = {}
        self.last_derivation: Optional[Dict[str, Any]] = None
        self.last_registration: Optional[Dict[str, Any]] = None

    # ------------------------------------------------------------------
    def _call_contract(self, spec: str, payload: Mapping[str, Any]) -> Dict[str, Any]:
        try:
            response = self._manager.call_dict(spec, input_payload=dict(payload))
        except LLMIntegrationError as exc:  # pragma: no cover - passthrough
            raise AutoSignalError(str(exc)) from exc
        if not isinstance(response, Mapping):
            raise AutoSignalError("LLM did not return a mapping payload")
        return {str(key): value for key, value in response.items()}

    # ------------------------------------------------------------------
    def derive(
        self,
        action_type: str,
        description: str,
        *,
        requirements: Optional[Sequence[str]] = None,
        hints: Optional[Sequence[str]] = None,
        metadata: Optional[Mapping[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        request = AutoSignalDerivationRequest(
            action_type=str(action_type),
            description=description,
            requirements=requirements or (),
            hints=hints or (),
            metadata=metadata or {},
        )
        payload = self._call_contract("auto_signal_derivation", request.to_payload())
        self.last_derivation = payload
        candidates = payload.get("signals")
        if not isinstance(candidates, Iterable) or isinstance(candidates, (str, bytes, bytearray)):
            raise AutoSignalError("LLM derivation payload missing 'signals'")
        result: List[Dict[str, Any]] = []
        for candidate in candidates:
            if isinstance(candidate, Mapping):
                result.append({str(key): value for key, value in candidate.items()})
        return result

    # ------------------------------------------------------------------
    def register(
        self,
        action_type: str,
        signals: Sequence[Mapping[str, Any]] | None,
        *,
        evaluation: Optional[Mapping[str, Any]] = None,
        blueprint: Optional[Mapping[str, Any]] = None,
        description: Optional[str] = None,
        requirements: Optional[Sequence[str]] = None,
        hints: Optional[Sequence[str]] = None,
    ) -> List[AutoSignal]:
        catalogue = self._signals.setdefault(str(action_type), {})
        request = AutoSignalRegistrationRequest(
            action_type=str(action_type),
            signals=signals or (),
            evaluation=evaluation,
            blueprint=blueprint,
            description=description,
            requirements=requirements or (),
            hints=hints or (),
        )
        payload = self._call_contract("auto_signal_registration", request.to_payload())
        self.last_registration = payload
        returned = payload.get("signals")
        if not isinstance(returned, Iterable) or isinstance(returned, (str, bytes, bytearray)):
            raise AutoSignalError("LLM registration payload missing 'signals'")
        registered: List[AutoSignal] = []
        for entry in returned:
            if not isinstance(entry, Mapping):
                continue
            signal = AutoSignal.from_payload(entry, action_type=str(action_type))
            value = _coerce_float(entry.get("last_value"))
            if value is not None:
                signal.last_value = value
                signal.last_source = _coerce_string(entry.get("last_source")) or "llm"
                signal.last_updated = float(entry.get("last_updated", time.time()) or time.time())
            catalogue[signal.metric] = signal
            registered.append(signal)
        return registered

    # ------------------------------------------------------------------
    def record(
        self,
        action_type: str,
        metric: str,
        value: Any,
        *,
        source: Optional[str] = None,
        timestamp: Optional[float] = None,
    ) -> Optional[AutoSignal]:
        if not action_type or not metric:
            return None
        catalogue = self._signals.setdefault(str(action_type), {})
        entry = catalogue.get(metric)
        if entry is None:
            entry = AutoSignal(
                action_type=str(action_type),
                name=metric,
                metric=metric,
                direction="above",
                target=None,
                weight=None,
                source=source or "observation",
            )
            catalogue[metric] = entry
        entry.last_value = _coerce_float(value)
        entry.last_source = source or entry.last_source
        entry.last_updated = timestamp or time.time()
        return entry

    # ------------------------------------------------------------------
    def bulk_record(
        self,
        action_type: str,
        metrics: Mapping[str, Any],
        *,
        source: Optional[str] = None,
        timestamp: Optional[float] = None,
    ) -> List[AutoSignal]:
        observations: List[AutoSignal] = []
        for metric, value in metrics.items():
            metric_name = _coerce_string(metric)
            if not metric_name:
                continue
            entry = self.record(
                action_type,
                metric_name,
                value,
                source=source,
                timestamp=timestamp,
            )
            if entry is not None:
                observations.append(entry)
        return observations

    # ------------------------------------------------------------------
    def get_signals(self, action_type: str) -> List[AutoSignal]:
        catalogue = self._signals.get(str(action_type))
        if not catalogue:
            return []
        return list(catalogue.values())

    # ------------------------------------------------------------------
    def get_observations(self, action_type: str) -> Dict[str, float]:
        observations: Dict[str, float] = {}
        for signal in self.get_signals(action_type):
            value = signal.to_observation()
            if value is not None:
                observations[signal.metric] = value
        return observations

    # ------------------------------------------------------------------
    def actions(self) -> Iterable[str]:
        return list(self._signals.keys())


def extract_keywords(*chunks: str, llm_manager=None) -> List[str]:
    """Delegate keyword extraction to the LLM."""

    joined = "\n".join(chunk for chunk in chunks if chunk)
    if not joined:
        return []
    manager = llm_manager or get_llm_manager()
    try:
        response = manager.call_dict(
            "auto_signal_keywords",
            input_payload={"text": joined},
        )
    except LLMIntegrationError as exc:  # pragma: no cover - passthrough
        raise AutoSignalError(str(exc)) from exc
    if not isinstance(response, Mapping):
        raise AutoSignalError("LLM keyword payload must be a mapping")
    return _coerce_string_list(response.get("keywords"))


def derive_signals_for_description(
    action_type: str,
    description: str,
    *,
    requirements: Optional[Sequence[str]] = None,
    hints: Optional[Sequence[str]] = None,
    metadata: Optional[Mapping[str, Any]] = None,
    llm_manager=None,
) -> List[Dict[str, Any]]:
    """Helper that mirrors :meth:`AutoSignalRegistry.derive` without state."""

    registry = AutoSignalRegistry(llm_manager=llm_manager)
    return registry.derive(
        action_type,
        description,
        requirements=requirements,
        hints=hints,
        metadata=metadata,
    )


__all__ = [
    "AutoSignal",
    "AutoSignalError",
    "AutoSignalRegistry",
    "derive_signals_for_description",
    "extract_keywords",
]
