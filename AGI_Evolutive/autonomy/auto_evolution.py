"""LLM-only auto evolution orchestrator."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Optional, Sequence

from AGI_Evolutive.autonomy.auto_signals import AutoSignalRegistry
from AGI_Evolutive.utils.llm_service import LLMIntegrationError, get_llm_manager


class AutoEvolutionError(RuntimeError):
    """Raised when the auto evolution LLM payload is invalid."""


def _coerce_mapping(value: Any) -> Dict[str, Any]:
    if not isinstance(value, Mapping):
        return {}
    return {str(key): val for key, val in value.items()}


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


def _coerce_sequence(value: Any) -> List[Dict[str, Any]]:
    if value is None:
        return []
    if isinstance(value, Mapping):
        value = [value]
    if not isinstance(value, Iterable) or isinstance(value, (bytes, bytearray)):
        return []
    results: List[Dict[str, Any]] = []
    for item in value:
        if isinstance(item, Mapping):
            results.append({str(key): val for key, val in item.items()})
    return results


@dataclass
class AutoEvolutionRequest:
    """Payload forwarded to the `auto_evolution` contract."""

    memory_snapshot: Mapping[str, Any] = field(default_factory=dict)
    recent_insights: Sequence[Mapping[str, Any]] = field(default_factory=tuple)
    active_modules: Sequence[Mapping[str, Any]] = field(default_factory=tuple)
    signals: Sequence[Mapping[str, Any]] = field(default_factory=tuple)
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def to_payload(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "memory": _coerce_mapping(self.memory_snapshot),
        }
        insights = _coerce_sequence(self.recent_insights)
        if insights:
            payload["recent_insights"] = insights
        modules = _coerce_sequence(self.active_modules)
        if modules:
            payload["modules"] = modules
        signal_defs = _coerce_sequence(self.signals)
        if signal_defs:
            payload["signals"] = signal_defs
        metadata = _coerce_mapping(self.metadata)
        if metadata:
            payload["metadata"] = metadata
        return payload


@dataclass
class AutoEvolutionOutcome:
    """Normalised LLM response for auto evolution."""

    accepted: bool
    intention: Dict[str, Any]
    evaluation: Dict[str, Any]
    signals: List[Dict[str, Any]]
    follow_up: List[str]
    metadata: Dict[str, Any]
    raw: Dict[str, Any]

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> "AutoEvolutionOutcome":
        if not isinstance(payload, Mapping):
            raise AutoEvolutionError("Auto evolution payload must be a mapping")
        data: MutableMapping[str, Any] = dict(payload)
        accepted = bool(payload.get("accepted", True))
        intention = _coerce_mapping(payload.get("intention"))
        evaluation = _coerce_mapping(payload.get("evaluation"))
        signals = _coerce_sequence(payload.get("signals"))
        follow_up_raw = payload.get("follow_up")
        follow_up: List[str] = []
        if isinstance(follow_up_raw, str):
            candidate = _coerce_string(follow_up_raw)
            if candidate:
                follow_up.append(candidate)
        elif isinstance(follow_up_raw, Iterable) and not isinstance(
            follow_up_raw, (bytes, bytearray)
        ):
            for item in follow_up_raw:
                candidate = _coerce_string(item)
                if candidate:
                    follow_up.append(candidate)
        metadata = _coerce_mapping(payload.get("metadata"))
        raw = {str(key): val for key, val in data.items()}
        return cls(
            accepted=accepted,
            intention=intention,
            evaluation=evaluation,
            signals=signals,
            follow_up=follow_up,
            metadata=metadata,
            raw=raw,
        )


class AutoEvolutionCoordinator:
    """Thin façade delegating the auto evolution workflow to the LLM."""

    def __init__(
        self,
        *,
        memory: Optional[Any] = None,
        metacog: Optional[Any] = None,
        skill_sandbox: Optional[Any] = None,
        evolution_manager: Optional[Any] = None,
        mechanism_store: Optional[Any] = None,
        self_improver: Optional[Any] = None,
        goals: Optional[Any] = None,
        emotions: Optional[Any] = None,
        interval: float = 60.0,
        modules: Optional[Sequence[Any]] = None,
        signal_registry: Optional[AutoSignalRegistry] = None,
        llm_manager=None,
    ) -> None:
        self.memory = memory
        self.metacog = metacog
        self.skill_sandbox = skill_sandbox
        self.evolution_manager = evolution_manager
        self.mechanism_store = mechanism_store
        self.self_improver = self_improver
        self.goals = goals
        self.emotions = emotions
        self.interval = float(interval)
        self.modules = list(modules or [])
        self.signal_registry = signal_registry
        self._manager = llm_manager or get_llm_manager()
        self._installed = False
        self.last_request: Optional[AutoEvolutionRequest] = None
        self.last_outcome: Optional[AutoEvolutionOutcome] = None

    # ------------------------------------------------------------------
    def install(self) -> None:
        self._installed = True

    def shutdown(self) -> None:
        self._installed = False

    # ------------------------------------------------------------------
    def _call_contract(self, payload: Mapping[str, Any]) -> Dict[str, Any]:
        try:
            response = self._manager.call_dict(
                "auto_evolution",
                input_payload=dict(payload),
            )
        except LLMIntegrationError as exc:  # pragma: no cover - passthrough
            raise AutoEvolutionError(str(exc)) from exc
        if not isinstance(response, Mapping):
            raise AutoEvolutionError("LLM did not return a mapping payload")
        return {str(key): value for key, value in response.items()}

    # ------------------------------------------------------------------
    def _default_modules(self) -> List[Dict[str, Any]]:
        modules: List[Dict[str, Any]] = []
        for module in self.modules:
            label = type(module).__name__
            modules.append({"name": label})
        return modules

    def _default_memory_snapshot(self) -> Dict[str, Any]:
        memory = self.memory
        if memory is None:
            return {"status": "unavailable"}
        snapshot_getter = getattr(memory, "describe_for_auto_evolution", None)
        if callable(snapshot_getter):  # pragma: no cover - optional
            try:
                snapshot = snapshot_getter()
                if isinstance(snapshot, Mapping):
                    return {str(key): val for key, val in snapshot.items()}
            except Exception:
                return {"status": "error"}
        return {"status": "available"}

    # ------------------------------------------------------------------
    def tick(
        self,
        *,
        memory_snapshot: Optional[Mapping[str, Any]] = None,
        recent_insights: Optional[Sequence[Mapping[str, Any]]] = None,
        active_modules: Optional[Sequence[Mapping[str, Any]]] = None,
        signals: Optional[Sequence[Mapping[str, Any]]] = None,
        metadata: Optional[Mapping[str, Any]] = None,
    ) -> AutoEvolutionOutcome:
        if not self._installed:
            self.install()
        request = AutoEvolutionRequest(
            memory_snapshot=memory_snapshot or self._default_memory_snapshot(),
            recent_insights=recent_insights or (),
            active_modules=active_modules or self._default_modules(),
            signals=signals or (),
            metadata=metadata or {},
        )
        payload = request.to_payload()
        self.last_request = request
        response = self._call_contract(payload)
        outcome = AutoEvolutionOutcome.from_payload(response)
        self.last_outcome = outcome
        if self.signal_registry and outcome.signals:
            action_type = _coerce_string(outcome.intention.get("action_type")) or "auto"
            description = _coerce_string(outcome.intention.get("description"))
            self.signal_registry.register(
                action_type,
                outcome.signals,
                evaluation=outcome.evaluation,
                description=description,
            )
        return outcome


__all__ = ["AutoEvolutionCoordinator", "AutoEvolutionError", "AutoEvolutionOutcome", "AutoEvolutionRequest"]
