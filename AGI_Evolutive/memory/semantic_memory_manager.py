
"""LLM-first semantic memory maintenance orchestrator."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Mapping, Optional

from .concept_extractor import ConceptExtractor
from .summarizer import MemorySnapshot, ProgressiveSummarizer, SummarizationResult
from AGI_Evolutive.utils.llm_service import LLMIntegrationError, get_llm_manager


def _normalise_snapshot(memories: Iterable[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    payload: List[Dict[str, Any]] = []
    for memory in memories:
        if isinstance(memory, Mapping):
            snapshot = MemorySnapshot.from_mapping(memory)
            if snapshot:
                payload.append(snapshot.to_payload())
    return payload


@dataclass
class MaintenancePlan:
    """Plan renvoyé par le LLM pour orchestrer la maintenance."""

    run_concepts: bool = False
    run_summaries: bool = False
    concept_batch: Optional[int] = None
    summary_limit: Optional[int] = None
    rationale: Optional[str] = None
    follow_up: List[str] = field(default_factory=list)

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> "MaintenancePlan":
        run_concepts = bool(payload.get("run_concepts") or payload.get("concepts"))
        run_summaries = bool(payload.get("run_summaries") or payload.get("summaries"))
        concept_batch = payload.get("concept_batch") or payload.get("concept_limit")
        summary_limit = payload.get("summary_limit") or payload.get("summary_batch")
        follow_up: List[str] = []
        if isinstance(payload.get("follow_up"), Iterable):
            for entry in payload["follow_up"]:  # type: ignore[index]
                label = str(entry).strip()
                if label:
                    follow_up.append(label)
        rationale = str(payload.get("rationale") or payload.get("notes") or "") or None
        return cls(
            run_concepts=run_concepts,
            run_summaries=run_summaries,
            concept_batch=int(concept_batch) if concept_batch else None,
            summary_limit=int(summary_limit) if summary_limit else None,
            rationale=rationale,
            follow_up=follow_up,
        )


@dataclass
class MaintenanceOutcome:
    """Resultats produits par un cycle de maintenance."""

    plan: MaintenancePlan
    concept_notes: Optional[Mapping[str, Any]] = None
    summary_result: Optional[SummarizationResult] = None


class SemanticMemoryManager:
    """Collapse concept extraction and summarisation under one LLM plan."""

    def __init__(
        self,
        *,
        memory_store: Any,
        concept_extractor: Optional[ConceptExtractor] = None,
        summarizer: Optional[ProgressiveSummarizer] = None,
    ) -> None:
        self.memory = memory_store
        self.concept_extractor = concept_extractor or ConceptExtractor(memory_store)
        self.summarizer = summarizer or ProgressiveSummarizer(memory_store)
        self._llm = get_llm_manager()

    # ------------------------------------------------------------------
    def run_once(self, *, now: Optional[float] = None) -> MaintenanceOutcome:
        """Execute a maintenance cycle following a single LLM plan."""

        snapshot = self._describe_context(now)
        try:
            response = self._llm.call_dict("semantic_memory_maintenance", snapshot)
        except LLMIntegrationError as exc:  # pragma: no cover
            raise RuntimeError(f"semantic_memory_maintenance failed: {exc}") from exc
        if not isinstance(response, Mapping):
            raise RuntimeError("semantic_memory_maintenance returned an invalid payload")

        plan = MaintenancePlan.from_payload(response)
        outcome = MaintenanceOutcome(plan=plan)

        if plan.run_concepts:
            batch = plan.concept_batch or 300
            self.concept_extractor.run_once(max_batch=batch)
            outcome.concept_notes = self.concept_extractor.last_llm_feedback

        if plan.run_summaries:
            outcome.summary_result = self.summarizer.step(now=now, limit=plan.summary_limit)

        return outcome

    # ------------------------------------------------------------------
    def step(self, now: Optional[float] = None) -> MaintenanceOutcome:
        """Backward-compatible alias used by legacy callers."""

        return self.run_once(now=now)

    def on_new_items(self, urgency: float = 0.5) -> MaintenanceOutcome:
        """Trigger an immediate maintenance run when new memories arrive."""

        _ = urgency  # The LLM plan already decides priority; value kept for signature compatibility.
        return self.run_once()

    # ------------------------------------------------------------------
    def _describe_context(self, now: Optional[float]) -> Dict[str, Any]:
        recent = self._recent_memories(limit=50)
        uncompressed = self._recent_memories(limit=50, not_compressed=True)
        return {
            "now": float(now) if now is not None else self._now(),
            "memory_stats": {
                "total": self._total_memories(),
                "recent_count": len(recent),
                "recent_uncompressed": len(uncompressed),
            },
            "recent_memories": recent,
            "concept_backlog": self.concept_extractor.pending_backlog(max_batch=200) if self.concept_extractor else 0,
        }

    def _recent_memories(self, *, limit: int, not_compressed: bool = False) -> List[Dict[str, Any]]:
        filters: Dict[str, Any] = {"limit": limit}
        if not_compressed:
            filters["not_compressed"] = True
        try:
            items = self.memory.list_items(filters)
        except Exception:
            items = []
        return _normalise_snapshot(items or [])

    def _total_memories(self) -> int:
        try:
            state = getattr(self.memory, "state", {})
            memories = state.get("memories", [])
            return len(memories)
        except Exception:
            return 0

    @staticmethod
    def _now() -> float:
        from time import time

        return time()


__all__ = ["SemanticMemoryManager", "MaintenancePlan", "MaintenanceOutcome"]
