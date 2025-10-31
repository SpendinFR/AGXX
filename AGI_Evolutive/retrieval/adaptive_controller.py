"""LLM-first retrieval orchestration controller."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Optional, Sequence

from AGI_Evolutive.utils.llm_service import LLMIntegrationError, get_llm_manager


class RAGOrchestrationError(RuntimeError):
    """Raised when the retrieval orchestration payload is invalid."""


def _coerce_string(value: Any) -> Optional[str]:
    if isinstance(value, str):
        stripped = value.strip()
        if stripped:
            return stripped
    return None


def _coerce_string_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, str):
        value = [value]
    result: List[str] = []
    if isinstance(value, Iterable) and not isinstance(value, (bytes, bytearray)):
        for item in value:
            if isinstance(item, str):
                cleaned = item.strip()
                if cleaned:
                    result.append(cleaned)
    return result


def _coerce_mapping(value: Any) -> Dict[str, Any]:
    if not isinstance(value, Mapping):
        return {}
    return {str(key): val for key, val in value.items()}


def _coerce_actions(value: Any) -> List[Dict[str, Any]]:
    if not isinstance(value, Iterable) or isinstance(value, (bytes, bytearray, str)):
        return []
    actions: List[Dict[str, Any]] = []
    for item in value:
        if isinstance(item, Mapping):
            actions.append({str(key): val for key, val in item.items()})
    return actions


def _merge_nested(base: Mapping[str, Any], overrides: Mapping[str, Any]) -> Dict[str, Any]:
    merged: Dict[str, Any] = {str(key): val for key, val in base.items()}
    for key, value in overrides.items():
        key_str = str(key)
        if isinstance(value, Mapping) and isinstance(merged.get(key_str), Mapping):
            merged[key_str] = _merge_nested(merged[key_str], value)  # type: ignore[arg-type]
        else:
            merged[key_str] = value
    return merged


@dataclass
class RAGPlanRequest:
    """Structured payload forwarded to the orchestration LLM."""

    question: str
    config: Mapping[str, Any]
    history: Sequence[Mapping[str, Any]] = field(default_factory=tuple)
    memory: Optional[Mapping[str, Any]] = None
    diagnostics: Optional[Mapping[str, Any]] = None
    metadata: Optional[Mapping[str, Any]] = None
    mode: str = "plan"

    def build_payload(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "mode": self.mode,
            "question": self.question,
            "config": _coerce_mapping(self.config),
        }
        if self.history:
            payload["history"] = [
                _coerce_mapping(item) for item in self.history if isinstance(item, Mapping)
            ]
        if self.memory:
            payload["memory"] = _coerce_mapping(self.memory)
        if self.diagnostics:
            payload["diagnostics"] = _coerce_mapping(self.diagnostics)
        if self.metadata:
            payload["metadata"] = _coerce_mapping(self.metadata)
        return payload


@dataclass
class RAGPlan:
    """Normalised representation of the LLM plan response."""

    question: str
    plan_id: Optional[str]
    expansions: List[str]
    overrides: Dict[str, Any]
    actions: List[Dict[str, Any]]
    decision: Optional[str]
    notes: List[str]
    meta: Dict[str, Any]
    raw: MutableMapping[str, Any]

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any], *, question: str) -> "RAGPlan":
        if not isinstance(payload, Mapping):
            raise RAGOrchestrationError("LLM payload must be a mapping")

        plan_id = _coerce_string(payload.get("plan_id"))
        expansions = _coerce_string_list(
            payload.get("expansions") or payload.get("queries") or payload.get("supplemental_queries")
        )
        overrides = _coerce_mapping(payload.get("overrides"))
        actions = _coerce_actions(payload.get("actions"))
        decision = _coerce_string(payload.get("decision"))
        notes = _coerce_string_list(payload.get("notes"))
        meta = _coerce_mapping(payload.get("meta"))

        raw: MutableMapping[str, Any] = dict(payload)
        if expansions and "expansions" not in raw:
            raw["expansions"] = list(expansions)
        if overrides and "overrides" not in raw:
            raw["overrides"] = dict(overrides)

        return cls(
            question=question,
            plan_id=plan_id,
            expansions=expansions,
            overrides=overrides,
            actions=actions,
            decision=decision,
            notes=notes,
            meta=meta,
            raw=raw,
        )

    def merged_config(self, base_config: Mapping[str, Any]) -> Dict[str, Any]:
        if not self.overrides:
            return {str(key): val for key, val in base_config.items()}
        return _merge_nested(base_config, self.overrides)

    def to_context(self) -> Dict[str, Any]:
        context: Dict[str, Any] = {
            "question": self.question,
            "plan": {
                "plan_id": self.plan_id,
                "expansions": list(self.expansions),
                "decision": self.decision,
                "actions": [dict(action) for action in self.actions],
            },
            "overrides": dict(self.overrides),
            "notes": list(self.notes),
            "meta": dict(self.meta),
            "raw": dict(self.raw),
        }
        return context

    def to_dict(self) -> Dict[str, Any]:
        return self.to_context()


class RAGAdaptiveController:
    """Thin façade delegating the full retrieval orchestration to the LLM."""

    def __init__(self, base_config: Mapping[str, Any], *, llm_manager=None) -> None:
        self.base_config: Dict[str, Any] = _coerce_mapping(base_config)
        self._manager = llm_manager or get_llm_manager()
        self.last_request: Optional[RAGPlanRequest] = None
        self.last_plan: Optional[RAGPlan] = None
        self.last_feedback: Optional[Dict[str, Any]] = None
        self.last_activation: Optional[float] = None

    def _call_orchestrator(self, payload: Mapping[str, Any]) -> Dict[str, Any]:
        try:
            response = self._manager.call_dict(
                "retrieval_orchestrator",
                input_payload=dict(payload),
            )
        except LLMIntegrationError as exc:  # pragma: no cover - passthrough
            raise RAGOrchestrationError(str(exc)) from exc
        if not isinstance(response, Mapping):
            raise RAGOrchestrationError("LLM returned no payload")
        return {str(key): value for key, value in response.items()}

    def prepare_query(
        self,
        question: str,
        *,
        history: Sequence[Mapping[str, Any]] = (),
        memory: Optional[Mapping[str, Any]] = None,
        diagnostics: Optional[Mapping[str, Any]] = None,
        metadata: Optional[Mapping[str, Any]] = None,
    ) -> Dict[str, Any]:
        request = RAGPlanRequest(
            question=question,
            config=self.base_config,
            history=history,
            memory=memory,
            diagnostics=diagnostics,
            metadata=metadata,
        )
        self.last_request = request
        payload = request.build_payload()
        response = self._call_orchestrator(payload)
        plan = RAGPlan.from_payload(response, question=question)
        self.last_plan = plan
        merged = plan.merged_config(self.base_config)
        self.base_config = merged
        return plan.to_context()

    def observe_outcome(
        self,
        context: Mapping[str, Any],
        rag_output: Mapping[str, Any],
    ) -> Optional[Dict[str, Any]]:
        payload = {
            "mode": "feedback",
            "plan": dict(context),
            "rag_output": _coerce_mapping(rag_output),
        }
        response = self._call_orchestrator(payload)
        self.last_feedback = response
        return response

    def apply_feedback(self, reward: float, metadata: Optional[Mapping[str, Any]] = None) -> Optional[Dict[str, Any]]:
        payload = {
            "mode": "reward",
            "reward": float(reward),
        }
        if metadata:
            payload["metadata"] = _coerce_mapping(metadata)
        response = self._call_orchestrator(payload)
        self.last_feedback = response
        return response

    def current_config(self) -> Dict[str, Any]:
        return dict(self.base_config)

    def update_global_activation(
        self,
        signal: float,
        *,
        reinforce: Optional[float] = None,
        metadata: Optional[Mapping[str, Any]] = None,
    ) -> float:
        payload: Dict[str, Any] = {
            "mode": "activation",
            "signal": float(signal),
        }
        if reinforce is not None:
            payload["reinforce"] = float(reinforce)
        if metadata:
            payload["metadata"] = _coerce_mapping(metadata)
        response = self._call_orchestrator(payload)
        value = response.get("activation")
        try:
            activation = float(value)
        except (TypeError, ValueError):
            activation = float(signal)
        activation = max(0.0, min(1.0, activation))
        self.last_activation = activation
        return activation


__all__ = [
    "RAGAdaptiveController",
    "RAGPlan",
    "RAGPlanRequest",
    "RAGOrchestrationError",
]
