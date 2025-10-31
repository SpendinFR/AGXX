"""LLM-driven adaptation helpers for belief confidence adjustments.

This module replaces the historical adaptive heuristics (decay trackers,
bandits, EMA tuners) with a very small façade around the shared LLM
manager.  The only responsibility left in Python land is to craft a
structured payload and to normalise the returned adjustment so the rest
of the codebase can persist it as-is.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, MutableMapping

from AGI_Evolutive.utils.llm_service import (
    LLMIntegrationError,
    get_llm_manager,
)


def _coerce_float(value: Any, *, default: float = 0.0) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        number = default
    if number != number:  # NaN guard
        number = default
    return number


def _ensure_mapping(value: Any) -> MutableMapping[str, Any]:
    if isinstance(value, Mapping):
        return {str(key): val for key, val in value.items()}
    return {}


@dataclass(frozen=True)
class BeliefAdjustment:
    """Structured result returned by the ``belief_adaptation`` spec."""

    belief_id: str
    delta: float
    confidence: float
    justification: str
    notes: str
    metadata: Mapping[str, Any] = field(default_factory=dict)
    raw: Mapping[str, Any] = field(default_factory=dict)

    @classmethod
    def from_payload(
        cls,
        payload: Mapping[str, Any],
        *,
        belief_id: str,
        fallback_delta: float = 0.0,
    ) -> "BeliefAdjustment":
        mapping = _ensure_mapping(payload)
        delta = _coerce_float(mapping.get("delta"), default=fallback_delta)
        confidence = max(0.0, min(1.0, _coerce_float(mapping.get("confidence"), default=0.5)))
        justification = str(mapping.get("justification") or "").strip() or "Ajustement proposé par le LLM."
        notes = str(mapping.get("notes") or "").strip()
        metadata = _ensure_mapping(mapping.get("metadata"))
        return cls(
            belief_id=belief_id,
            delta=delta,
            confidence=confidence,
            justification=justification,
            notes=notes,
            metadata=metadata,
            raw=mapping,
        )


class BeliefAdaptationEngine:
    """Minimal façade that forwards belief adjustments to the LLM."""

    def __init__(self, *, llm_manager=None) -> None:
        self._manager = llm_manager

    def _manager_or_default(self):
        manager = self._manager
        if manager is None:
            manager = get_llm_manager()
        return manager

    def suggest_adjustment(
        self,
        belief_id: str,
        *,
        belief_snapshot: Mapping[str, Any] | None = None,
        statistics: Mapping[str, Any] | None = None,
        suggested_delta: float | None = None,
        extra: Mapping[str, Any] | None = None,
    ) -> BeliefAdjustment:
        """Return the LLM recommendation for adjusting ``belief_id``.

        ``belief_snapshot`` and ``statistics`` are both optional; when
        omitted, empty mappings are forwarded.  ``suggested_delta`` can be
        used by callers that wish to provide a hint to the LLM (for
        instance the previously applied heuristic delta).
        """

        payload: dict[str, Any] = {
            "belief_id": belief_id,
            "belief": _ensure_mapping(belief_snapshot),
            "statistics": _ensure_mapping(statistics),
        }
        if suggested_delta is not None:
            payload["suggested_delta"] = float(suggested_delta)
        extra_payload = _ensure_mapping(extra)
        if extra_payload:
            payload["extra"] = extra_payload

        manager = self._manager_or_default()
        response = manager.call_dict(
            "belief_adaptation",
            input_payload=payload,
        )
        if not isinstance(response, Mapping):  # pragma: no cover - defensive guard
            raise LLMIntegrationError(
                "Spec 'belief_adaptation' did not return a mapping payload",
            )

        return BeliefAdjustment.from_payload(
            response,
            belief_id=belief_id,
            fallback_delta=suggested_delta or 0.0,
        )


__all__ = [
    "BeliefAdaptationEngine",
    "BeliefAdjustment",
]
