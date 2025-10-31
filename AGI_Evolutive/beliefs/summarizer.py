"""LLM-backed summariser for the belief graph."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, MutableMapping, Optional

from AGI_Evolutive.utils.llm_service import LLMIntegrationError, get_llm_manager


def _ensure_mapping(value: Any) -> MutableMapping[str, Any]:
    if isinstance(value, Mapping):
        return {str(k): v for k, v in value.items()}
    return {}


@dataclass
class BeliefSummary:
    narrative: str
    highlights: list[Mapping[str, Any]]
    coherence_score: float
    notes: str
    raw: Mapping[str, Any]


class BeliefSummarizer:
    """Delegates summarisation to the ``belief_summarizer`` LLM contract."""

    def __init__(self, graph, *, llm_manager=None) -> None:
        self.graph = graph
        self._manager = llm_manager
        self._last_summary: Mapping[str, Any] = {}

    def _manager_or_default(self):
        manager = self._manager
        if manager is None:
            manager = get_llm_manager()
        return manager

    def _snapshot(self, *, limit: int = 40) -> Mapping[str, Any]:
        beliefs = sorted(self.graph.iter_beliefs(), key=lambda b: b.updated_at, reverse=True)[:limit]
        events = sorted(self.graph.events(), key=lambda e: e.updated_at, reverse=True)[: max(1, limit // 3)]
        return {
            "beliefs": [belief.to_dict() for belief in beliefs],
            "events": [event.to_dict() for event in events],
        }

    def summarize(
        self,
        *,
        timeframe: Optional[str] = None,
        focus: Optional[str] = None,
        extra: Mapping[str, Any] | None = None,
    ) -> Mapping[str, Any]:
        payload = {
            "timeframe": timeframe,
            "focus": focus,
            "extra": _ensure_mapping(extra),
            "snapshot": self._snapshot(),
        }
        response = self._manager_or_default().call_dict(
            "belief_summarizer",
            input_payload=payload,
        )
        if not isinstance(response, Mapping):  # pragma: no cover - defensive guard
            raise LLMIntegrationError("Spec 'belief_summarizer' did not return a mapping payload")
        self._last_summary = response
        return response

    def last(self) -> Mapping[str, Any]:
        return self._last_summary


__all__ = ["BeliefSummarizer", "BeliefSummary"]
