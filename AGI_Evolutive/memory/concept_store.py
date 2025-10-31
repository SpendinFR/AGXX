"""Minimal concept store to accompany the LLM-first extractor.

The previous implementation exposed a complex online-learning system (linear
models with forgetting, Thompson sampling for half-life selection, adaptive
salience boosts, etc.).  With the refactor every concept update already comes
from the LLM in a structured payload, so the store only needs to keep an
append-only registry of concepts and relations while providing a few helpers
for the rest of the runtime.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Sequence, TYPE_CHECKING

if TYPE_CHECKING:
    from .concept_extractor import (
        ConceptExtractionResult,
        ExtractedConcept,
        ExtractedRelation,
        MemoryDocument,
    )


def _normalise_label(label: str) -> str:
    return label.strip().lower()


@dataclass
class Concept:
    id: str
    label: str
    salience: float = 0.0
    confidence: float = 0.0
    support: float = 0.0
    last_seen: float = field(default_factory=time.time)
    examples: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def update_from_llm(self, concept: ExtractedConcept) -> None:
        if concept.salience is not None:
            self.salience = float(concept.salience)
        if concept.confidence is not None:
            self.confidence = float(concept.confidence)
        self.support += 1.0
        self.last_seen = time.time()
        if concept.evidence:
            if concept.evidence not in self.examples:
                self.examples.append(concept.evidence)
        if concept.metadata:
            self.metadata.update({str(k): v for k, v in concept.metadata.items()})


@dataclass
class Relation:
    id: str
    src: str
    dst: str
    rtype: str
    confidence: float = 0.0
    weight: float = 0.0
    last_seen: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def update_from_llm(self, relation: ExtractedRelation) -> None:
        self.last_seen = time.time()
        if relation.confidence is not None:
            self.confidence = float(relation.confidence)
        self.weight += 1.0
        if relation.metadata:
            self.metadata.update({str(k): v for k, v in relation.metadata.items()})


class ConceptStore:
    """Keeps the latest concept graph derived from LLM outputs."""

    def __init__(self) -> None:
        self._concepts: Dict[str, Concept] = {}
        self._relations: Dict[str, Relation] = {}
        self._label_index: Dict[str, str] = {}

    # ------------------------------------------------------------------
    def apply_extraction(
        self,
        extraction: "ConceptExtractionResult",
        documents: Sequence["MemoryDocument"],
    ) -> None:
        doc_ids = {doc.id for doc in documents if doc.id}
        for concept in extraction.concepts:
            self._upsert_concept(concept, doc_ids)
        for relation in extraction.relations:
            self._upsert_relation(relation)

    # ------------------------------------------------------------------
    def _upsert_concept(self, concept: "ExtractedConcept", doc_ids: Iterable[str]) -> Concept:
        key = _normalise_label(concept.label)
        concept_id = self._label_index.get(key)
        if concept_id is None:
            concept_id = uuid.uuid4().hex
            self._label_index[key] = concept_id
            instance = Concept(
                id=concept_id,
                label=concept.label,
                salience=float(concept.salience or concept.confidence or 1.0),
                confidence=float(concept.confidence or 0.0),
                support=1.0,
            )
            if concept.evidence:
                instance.examples.append(concept.evidence)
            if concept.metadata:
                instance.metadata.update({str(k): v for k, v in concept.metadata.items()})
            self._concepts[concept_id] = instance
        else:
            instance = self._concepts[concept_id]
            instance.label = concept.label
            instance.update_from_llm(concept)
        if concept.source_ids:
            self._update_source_ids(instance, concept.source_ids)
        elif doc_ids:
            self._update_source_ids(instance, doc_ids)
        return instance

    def _resolve_concept_id(self, value: str) -> Optional[str]:
        if value in self._concepts:
            return value
        key = _normalise_label(value)
        return self._label_index.get(key)

    def _upsert_relation(self, relation: "ExtractedRelation") -> Relation:
        src_id = self._resolve_concept_id(relation.subject) or self._register_placeholder(relation.subject)
        dst_id = self._resolve_concept_id(relation.object) or self._register_placeholder(relation.object)
        key = f"{src_id}:{relation.verb}:{dst_id}"
        instance = self._relations.get(key)
        if instance is None:
            instance = Relation(
                id=uuid.uuid4().hex,
                src=src_id,
                dst=dst_id,
                rtype=relation.verb,
                confidence=float(relation.confidence or 0.0),
                weight=1.0,
            )
            if relation.metadata:
                instance.metadata.update({str(k): v for k, v in relation.metadata.items()})
            if relation.evidence:
                instance.metadata.setdefault("evidence", []).append(relation.evidence)
            self._relations[key] = instance
        else:
            instance.update_from_llm(relation)
            if relation.evidence:
                instance.metadata.setdefault("evidence", []).append(relation.evidence)
        return instance

    def _register_placeholder(self, label: str) -> str:
        key = _normalise_label(label)
        concept_id = self._label_index.get(key)
        if concept_id is None:
            concept_id = uuid.uuid4().hex
            self._label_index[key] = concept_id
            self._concepts[concept_id] = Concept(id=concept_id, label=label)
        return concept_id

    # ------------------------------------------------------------------
    def get_top_concepts(self, k: int = 10) -> List[Concept]:
        concepts = sorted(
            self._concepts.values(),
            key=lambda item: (item.salience, item.support, item.last_seen),
            reverse=True,
        )
        return concepts[:k]

    def find_by_label_prefix(self, prefix: str, k: int = 5) -> List[Concept]:
        prefix_key = prefix.lower()
        results: List[Concept] = []
        for concept in self._concepts.values():
            if concept.label.lower().startswith(prefix_key):
                results.append(concept)
                if len(results) >= k:
                    break
        return results

    def neighbors(self, concept_id: str, rtype: Optional[str] = None, k: int = 5) -> List[Relation]:
        neighbours: List[Relation] = []
        for relation in self._relations.values():
            if relation.src == concept_id or relation.dst == concept_id:
                if rtype is None or relation.rtype == rtype:
                    neighbours.append(relation)
        neighbours.sort(key=lambda rel: (rel.weight, rel.last_seen), reverse=True)
        return neighbours[:k]

    # ------------------------------------------------------------------
    def _update_source_ids(self, concept: Concept, identifiers: Iterable[str]) -> None:
        bucket: List[str] = []
        existing = concept.metadata.get("source_ids")
        if isinstance(existing, Iterable) and not isinstance(existing, (str, bytes)):
            bucket.extend(str(item) for item in existing)
        ids = set(bucket)
        for identifier in identifiers:
            ids.add(str(identifier))
        concept.metadata["source_ids"] = sorted(ids)

    # ------------------------------------------------------------------
    def concepts(self) -> List[Concept]:
        return list(self._concepts.values())

    def relations(self) -> List[Relation]:
        return list(self._relations.values())

    def save(self) -> None:
        """Kept for compatibility; persistence is no longer handled here."""
        return None


__all__ = ["ConceptStore", "Concept", "Relation"]
