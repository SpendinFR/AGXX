"""LLM-first concept extraction orchestrator.

This module used to orchestrate a large amount of heuristic logic (n-gram
statistics, adaptive bandits, incremental TF/IDF, Thompson sampling, manual
relation mining, etc.) to recover salient concepts from the episodic memory.
With the LLM-first refactor the entire pipeline is collapsed into a single call
that produces concepts, relations and annotations in one shot.  The local code
is now responsible for:

* normalising memories into a compact payload suitable for the LLM,
* calling the integration layer once,
* validating and normalising the response,
* updating the optional concept store.

No heuristic fallback or multi-stage scoring remains – if the LLM cannot answer
we surface a `ConceptExtractionError` so the caller can decide what to do.
"""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Optional, Sequence, Tuple

from AGI_Evolutive.utils.llm_service import LLMIntegrationError, get_llm_manager

from .concept_store import ConceptStore


class ConceptExtractionError(RuntimeError):
    """Raised when the LLM concept extraction fails."""


def _normalise_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        text = value
    elif isinstance(value, Mapping):
        for key in ("text", "content", "summary", "message", "body"):
            if key in value:
                candidate = _normalise_text(value.get(key))
                if candidate:
                    return candidate
        text = str(value)
    else:
        text = str(value)
    normalised = unicodedata.normalize("NFKC", text)
    return normalised.strip()


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


def _normalise_tag_list(value: Any) -> List[str]:
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
class MemoryDocument:
    """Normalised view over a memory item sent to the LLM."""

    id: Optional[str]
    text: str
    kind: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    salience: Optional[float] = None

    @classmethod
    def from_mapping(cls, memory: Mapping[str, Any]) -> Optional["MemoryDocument"]:
        text = _normalise_text(memory.get("text") or memory.get("content") or memory)
        if not text:
            return None
        mem_id = memory.get("id") or memory.get("_id") or memory.get("memory_id")
        kind = _normalise_string(memory.get("kind") or memory.get("type"))
        tags = _normalise_tag_list(memory.get("tags") or memory.get("labels"))
        metadata = memory.get("metadata")
        if not isinstance(metadata, Mapping):
            metadata = {}
        salience = _normalise_float(memory.get("salience"))
        return cls(
            id=str(mem_id) if mem_id is not None else None,
            text=text,
            kind=kind,
            tags=tags,
            metadata={str(key): value for key, value in metadata.items()},
            salience=salience,
        )

    def to_payload(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {"text": self.text}
        if self.id:
            payload["id"] = self.id
        if self.kind:
            payload["kind"] = self.kind
        if self.tags:
            payload["tags"] = list(self.tags)
        if self.metadata:
            payload["metadata"] = dict(self.metadata)
        if self.salience is not None:
            payload["salience"] = self.salience
        return payload


@dataclass
class ExtractedConcept:
    label: str
    salience: Optional[float] = None
    confidence: Optional[float] = None
    evidence: Optional[str] = None
    source_ids: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> Optional["ExtractedConcept"]:
        label = _normalise_string(payload.get("label") or payload.get("term") or payload.get("concept"))
        if not label:
            return None
        salience = _normalise_float(payload.get("salience") or payload.get("score"))
        confidence = _normalise_float(payload.get("confidence"))
        evidence = _normalise_string(payload.get("evidence") or payload.get("excerpt"))
        raw_sources = payload.get("source_ids") or payload.get("sources")
        source_ids = _normalise_tag_list(raw_sources)
        metadata: Dict[str, Any] = {}
        if isinstance(payload.get("metadata"), Mapping):
            metadata = {str(k): v for k, v in payload["metadata"].items()}
        return cls(
            label=label,
            salience=salience,
            confidence=confidence,
            evidence=evidence,
            source_ids=source_ids,
            metadata=metadata,
        )


@dataclass
class ExtractedRelation:
    subject: str
    verb: str
    object: str
    confidence: Optional[float] = None
    evidence: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> Optional["ExtractedRelation"]:
        subject = _normalise_string(payload.get("subject") or payload.get("source"))
        obj = _normalise_string(payload.get("object") or payload.get("target"))
        verb = _normalise_string(payload.get("verb") or payload.get("relation") or payload.get("type"))
        if not (subject and obj and verb):
            return None
        confidence = _normalise_float(payload.get("confidence"))
        evidence = _normalise_string(payload.get("evidence"))
        metadata: Dict[str, Any] = {}
        if isinstance(payload.get("metadata"), Mapping):
            metadata = {str(k): v for k, v in payload["metadata"].items()}
        return cls(
            subject=subject,
            verb=verb,
            object=obj,
            confidence=confidence,
            evidence=evidence,
            metadata=metadata,
        )


@dataclass
class ConceptExtractionResult:
    concepts: List[ExtractedConcept]
    relations: List[ExtractedRelation]
    highlights: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)
    meta: Dict[str, Any] = field(default_factory=dict)
    raw: MutableMapping[str, Any] = field(default_factory=dict)

    @classmethod
    def empty(cls) -> "ConceptExtractionResult":
        return cls(concepts=[], relations=[], highlights=[], notes=[], meta={}, raw={})

    @classmethod
    def from_payload(
        cls,
        payload: Mapping[str, Any],
    ) -> "ConceptExtractionResult":
        if not isinstance(payload, Mapping):
            raise ConceptExtractionError("LLM payload must be a mapping")
        raw: MutableMapping[str, Any] = dict(payload)

        concepts: List[ExtractedConcept] = []
        for entry in payload.get("concepts") or []:
            if isinstance(entry, Mapping):
                concept = ExtractedConcept.from_payload(entry)
                if concept:
                    concepts.append(concept)

        relations: List[ExtractedRelation] = []
        for entry in payload.get("relations") or []:
            if isinstance(entry, Mapping):
                relation = ExtractedRelation.from_payload(entry)
                if relation:
                    relations.append(relation)

        highlights = [_normalise_string(item) or "" for item in payload.get("highlights") or [] if _normalise_string(item)]
        notes = [_normalise_string(item) or "" for item in payload.get("notes") or [] if _normalise_string(item)]
        meta = {str(k): v for k, v in payload.get("meta", {}).items()} if isinstance(payload.get("meta"), Mapping) else {}

        return cls(
            concepts=concepts,
            relations=relations,
            highlights=highlights,
            notes=notes,
            meta=meta,
            raw=raw,
        )

    def ranked_concepts(self) -> List[Tuple[str, float]]:
        ranking: List[Tuple[str, float]] = []
        for concept in self.concepts:
            base = concept.salience
            if base is None:
                base = concept.confidence
            if base is None:
                base = 1.0
            ranking.append((concept.label, float(base)))
        return ranking

    def to_rank_dicts(self) -> List[Dict[str, Any]]:
        output: List[Dict[str, Any]] = []
        for label, score in self.ranked_concepts():
            entry: Dict[str, Any] = {"concept": label, "score": score}
            output.append(entry)
        return output


class ConceptExtractor:
    """LLM-first concept extraction helper."""

    def __init__(self, memory_store: Optional[Any]) -> None:
        self.memory = memory_store
        self.store: Optional[ConceptStore] = None
        self._last_result: ConceptExtractionResult = ConceptExtractionResult.empty()
        self._score_history: List[float] = []

    # ------------------------------------------------------------------
    def bind(self, memory: Any = None, **unused: Any) -> None:
        if memory is not None:
            self.memory = memory

    # ------------------------------------------------------------------
    def step(self, memory: Any = None, max_batch: int = 300) -> None:
        docs = self._collect_recent(limit=max_batch, override_memory=memory)
        self._apply_documents(docs)

    def run_once(self, max_batch: int = 400) -> None:
        docs = self._collect_recent(limit=max_batch)
        self._apply_documents(docs)

    def extract_from_recent(self, n: int = 200) -> List[Dict[str, Any]]:
        docs = self._collect_recent(limit=n)
        result = self._apply_documents(docs)
        return result.to_rank_dicts()

    def process_memories(self, memories: Iterable[Mapping[str, Any]]) -> List[Tuple[str, float]]:
        docs: List[MemoryDocument] = []
        for memory in memories:
            if isinstance(memory, Mapping):
                doc = MemoryDocument.from_mapping(memory)
                if doc:
                    docs.append(doc)
        result = self._apply_documents(docs)
        return result.ranked_concepts()

    # ------------------------------------------------------------------
    def pending_backlog(self, memory: Any = None, max_batch: int = 400) -> int:
        docs = self._collect_recent(limit=max_batch, override_memory=memory)
        return len(docs)

    @property
    def last_batch_score(self) -> float:
        return self._score_history[-1] if self._score_history else 0.0

    @property
    def last_llm_feedback(self) -> Optional[Mapping[str, Any]]:
        return self._last_result.meta or None

    def quality_signal(self, window: int = 5) -> float:
        if not self._score_history:
            return 0.0
        window = max(1, min(window, len(self._score_history)))
        recent = self._score_history[-window:]
        maximum = max(self._score_history)
        if maximum <= 0.0:
            return 0.0
        return sum(recent) / (window * maximum)

    # ------------------------------------------------------------------
    def _collect_recent(
        self,
        *,
        limit: int,
        override_memory: Any = None,
    ) -> List[MemoryDocument]:
        source = override_memory if override_memory is not None else self.memory
        if source is None:
            return []

        documents: List[MemoryDocument] = []
        try:
            if hasattr(source, "get_recent_memories"):
                raw = source.get_recent_memories(n=limit)  # type: ignore[call-arg]
                for item in raw or []:
                    doc = MemoryDocument.from_mapping(item)
                    if doc:
                        documents.append(doc)
                        if len(documents) >= limit:
                            return documents
        except Exception:
            pass

        if documents:
            return documents

        try:
            if hasattr(source, "iter_memories"):
                for item in source.iter_memories():
                    doc = MemoryDocument.from_mapping(item)
                    if doc:
                        documents.append(doc)
                        if len(documents) >= limit:
                            break
        except Exception:
            return documents

        return documents[:limit]

    def _apply_documents(self, documents: Sequence[MemoryDocument]) -> ConceptExtractionResult:
        if not documents:
            self._last_result = ConceptExtractionResult.empty()
            return self._last_result

        payload = {"memories": [doc.to_payload() for doc in documents]}
        try:
            response = get_llm_manager().call_dict("concept_extraction", input_payload=payload)
        except LLMIntegrationError as exc:  # pragma: no cover - defensive guard
            raise ConceptExtractionError("concept_extraction call failed") from exc

        result = ConceptExtractionResult.from_payload(response)
        self._last_result = result
        if self.store is not None:
            self.store.apply_extraction(result, documents)
        self._register_score(result)
        return result

    def _register_score(self, result: ConceptExtractionResult) -> None:
        ranking = result.ranked_concepts()
        if not ranking:
            score = 0.0
        else:
            score = sum(score for _, score in ranking) / len(ranking)
        self._score_history.append(score)
        if len(self._score_history) > 50:
            del self._score_history[:-50]


__all__ = [
    "ConceptExtractionError",
    "ConceptExtractor",
    "ConceptExtractionResult",
    "ExtractedConcept",
    "ExtractedRelation",
    "MemoryDocument",
]
