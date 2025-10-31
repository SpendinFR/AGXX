
"""LLM-first summarisation orchestrator.

This module used to orchestrate a complex multi-stage heuristic pipeline mixing
adaptive EMAs, Thompson sampling, rolling buckets and manual TTL policies to
promote raw memories into daily/weekly/monthly digests.  In the LLM-first
architecture we collapse the entire behaviour into a single structured call to
an integration managed language model.  The Python side is now responsible for:

* normalising memory items into a compact payload,
* issuing exactly one LLM request per summarisation run,
* validating and persisting the digests returned by the model,
* updating the underlying memory store metadata (e.g. compression lineage).

No fallback heuristics are kept: if the LLM contract cannot be satisfied we
raise a :class:`SummarizationError` so the caller can decide how to recover.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence

from AGI_Evolutive.utils.llm_service import LLMIntegrationError, get_llm_manager


def _normalise_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        text = value
    elif isinstance(value, Mapping):
        for key in ("text", "content", "body", "summary"):
            if key in value:
                candidate = _normalise_text(value.get(key))
                if candidate:
                    return candidate
        text = str(value)
    else:
        text = str(value)
    return text.strip()


def _normalise_string(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, str):
        cleaned = value.strip()
        return cleaned or None
    cleaned = str(value).strip()
    return cleaned or None


def _normalise_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        number = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    if number != number:  # NaN
        return None
    return number


def _normalise_tags(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, str):
        cleaned = value.strip()
        return [cleaned] if cleaned else []
    tags: List[str] = []
    if isinstance(value, Iterable):
        for item in value:
            if item is None:
                continue
            tag = str(item).strip()
            if tag:
                tags.append(tag)
    return tags


@dataclass
class SummarizerConfig:
    """Minimal configuration for :class:`ProgressiveSummarizer`."""

    max_memories: int = 180
    include_kinds: Sequence[str] = ()
    prefer_uncompressed: bool = True


@dataclass
class MemorySnapshot:
    """Normalised memory payload sent to the LLM."""

    id: Optional[str]
    kind: Optional[str]
    text: str
    ts: Optional[float]
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    salience: Optional[float] = None

    @classmethod
    def from_mapping(cls, memory: Mapping[str, Any]) -> Optional["MemorySnapshot"]:
        text = _normalise_text(memory.get("text") or memory)
        if not text:
            return None
        mem_id = memory.get("id") or memory.get("_id") or memory.get("memory_id")
        kind = _normalise_string(memory.get("kind") or memory.get("type"))
        ts = _normalise_float(memory.get("ts"))
        tags = _normalise_tags(memory.get("tags"))
        metadata = memory.get("metadata") if isinstance(memory.get("metadata"), Mapping) else {}
        salience = _normalise_float(memory.get("salience"))
        return cls(
            id=str(mem_id) if mem_id is not None else None,
            kind=kind,
            text=text,
            ts=ts,
            tags=tags,
            metadata={str(k): v for k, v in metadata.items()},
            salience=salience,
        )

    def to_payload(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {"text": self.text}
        if self.id:
            payload["id"] = self.id
        if self.kind:
            payload["kind"] = self.kind
        if self.ts is not None:
            payload["ts"] = self.ts
        if self.tags:
            payload["tags"] = list(self.tags)
        if self.metadata:
            payload["metadata"] = dict(self.metadata)
        if self.salience is not None:
            payload["salience"] = self.salience
        return payload


@dataclass
class DigestDecision:
    """Single digest proposed by the LLM."""

    reference: str
    level: str
    summary: str
    source_ids: List[str] = field(default_factory=list)
    key_points: List[Dict[str, Any]] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    compress_ids: List[str] = field(default_factory=list)

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> Optional["DigestDecision"]:
        reference = _normalise_string(payload.get("reference") or payload.get("id") or payload.get("slug"))
        level = _normalise_string(payload.get("level") or payload.get("kind") or payload.get("digest_level"))
        summary = _normalise_string(payload.get("summary") or payload.get("text"))
        if not (reference and level and summary):
            return None
        key_points: List[Dict[str, Any]] = []
        raw_points = payload.get("key_points") or payload.get("highlights")
        if isinstance(raw_points, Iterable):
            for point in raw_points:
                if isinstance(point, Mapping):
                    key_points.append({str(k): v for k, v in point.items()})
                else:
                    label = _normalise_string(point)
                    if label:
                        key_points.append({"label": label})
        metadata: Dict[str, Any] = {}
        if isinstance(payload.get("metadata"), Mapping):
            metadata = {str(k): v for k, v in payload["metadata"].items()}
        return cls(
            reference=reference,
            level=level,
            summary=summary,
            source_ids=_normalise_tags(payload.get("source_ids") or payload.get("sources")),
            key_points=key_points,
            tags=_normalise_tags(payload.get("tags")),
            metadata=metadata,
            compress_ids=_normalise_tags(payload.get("compress_ids") or payload.get("compressed_sources")),
        )


@dataclass
class SummarizationResult:
    """Structured response returned by :class:`ProgressiveSummarizer`."""

    digests: List[DigestDecision] = field(default_factory=list)
    follow_up: List[str] = field(default_factory=list)
    notes: Optional[str] = None
    raw_response: Mapping[str, Any] = field(default_factory=dict)
    persisted_ids: Dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> "SummarizationResult":
        digests_payload = []
        if isinstance(payload.get("digests"), Iterable):
            digests_payload = payload.get("digests")  # type: ignore[assignment]
        elif isinstance(payload.get("summaries"), Iterable):
            digests_payload = payload.get("summaries")  # type: ignore[assignment]

        digests: List[DigestDecision] = []
        for item in digests_payload or []:
            if isinstance(item, Mapping):
                digest = DigestDecision.from_payload(item)
                if digest:
                    digests.append(digest)

        follow_up: List[str] = []
        raw_follow = payload.get("follow_up") or payload.get("actions")
        if isinstance(raw_follow, Iterable):
            for entry in raw_follow:
                label = _normalise_string(entry)
                if label:
                    follow_up.append(label)

        notes = _normalise_string(payload.get("notes") or payload.get("comment"))
        return cls(digests=digests, follow_up=follow_up, notes=notes, raw_response=dict(payload))


class SummarizationError(RuntimeError):
    """Raised when the LLM summarisation contract cannot be fulfilled."""


class ProgressiveSummarizer:
    """Single-call summariser that persists LLM digests."""

    def __init__(
        self,
        memory_store: Any,
        *,
        concept_store: Optional[Any] = None,
        config: Optional[SummarizerConfig] = None,
    ) -> None:
        self.memory_store = memory_store
        self.concept_store = concept_store
        self.config = config or SummarizerConfig()
        self._llm = get_llm_manager()

    # ------------------------------------------------------------------
    def step(self, now: Optional[float] = None, *, limit: Optional[int] = None) -> SummarizationResult:
        """Run one summarisation pass and persist the returned digests."""

        documents = self._collect_documents(limit)
        if not documents:
            return SummarizationResult(digests=[], raw_response={})

        payload = {
            "now": float(now) if now is not None else self._now(),
            "memories": [document.to_payload() for document in documents],
            "config": {
                "include_kinds": list(self.config.include_kinds),
                "prefer_uncompressed": self.config.prefer_uncompressed,
            },
        }
        try:
            response = self._llm.call_dict("memory_summarizer", payload)
        except LLMIntegrationError as exc:  # pragma: no cover - propagated failure path
            raise SummarizationError(str(exc)) from exc
        if not isinstance(response, Mapping):
            raise SummarizationError("memory_summarizer returned a non-mapping payload")

        result = SummarizationResult.from_payload(response)
        if not result.digests:
            return result

        persisted: Dict[str, str] = {}
        for digest in result.digests:
            digest_id = self._persist_digest(digest)
            if digest_id:
                persisted[digest.reference] = digest_id
                self._mark_compressed(digest, digest_id)
        result.persisted_ids = persisted
        return result

    # ------------------------------------------------------------------
    def _collect_documents(self, limit: Optional[int]) -> List[MemorySnapshot]:
        max_items = int(limit) if limit is not None else int(self.config.max_memories)
        filters: Dict[str, Any] = {"limit": max_items}
        if self.config.include_kinds:
            filters["kind"] = list(self.config.include_kinds)
        if self.config.prefer_uncompressed:
            filters["not_compressed"] = True
        try:
            raw_items = list(self.memory_store.list_items(filters) or [])
        except Exception:
            raw_items = []
        documents: List[MemorySnapshot] = []
        for item in raw_items:
            if isinstance(item, Mapping):
                snapshot = MemorySnapshot.from_mapping(item)
                if snapshot:
                    documents.append(snapshot)
        return documents

    def _persist_digest(self, digest: DigestDecision) -> Optional[str]:
        payload: Dict[str, Any] = {
            "kind": digest.level,
            "text": digest.summary,
            "tags": list(digest.tags),
            "metadata": {
                "llm_reference": digest.reference,
                "key_points": list(digest.key_points),
                **digest.metadata,
            },
            "lineage": list(digest.source_ids),
        }
        try:
            return self.memory_store.add_item(payload)
        except Exception as exc:
            raise SummarizationError(f"failed to persist digest {digest.reference}: {exc}") from exc

    def _mark_compressed(self, digest: DigestDecision, digest_id: str) -> None:
        for source_id in digest.compress_ids or digest.source_ids:
            if not source_id:
                continue
            try:
                self.memory_store.update_item(
                    source_id,
                    {"compressed_into": digest_id, "metadata": {"compressed_by": digest.reference}},
                )
            except Exception:
                continue

    @staticmethod
    def _now() -> float:
        from time import time

        return time()


__all__ = [
    "SummarizerConfig",
    "MemorySnapshot",
    "DigestDecision",
    "SummarizationResult",
    "SummarizationError",
    "ProgressiveSummarizer",
]
