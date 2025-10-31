"""LLM-first belief graph orchestration."""

from __future__ import annotations

import json
import os
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Iterable, Iterator, Mapping, MutableMapping, Optional, Sequence

from AGI_Evolutive.utils.jsonsafe import json_sanitize
from AGI_Evolutive.utils.llm_service import LLMIntegrationError, get_llm_manager

from .entity_linker import EntityLinker
from .ontology import Ontology


def _ensure_mapping(value: Any) -> MutableMapping[str, Any]:
    if isinstance(value, Mapping):
        return {str(key): val for key, val in value.items()}
    return {}


def _ensure_iterable_of_mappings(value: Any) -> Iterator[Mapping[str, Any]]:
    if isinstance(value, Mapping):
        yield value
        return
    if isinstance(value, Iterable) and not isinstance(value, (str, bytes)):
        for item in value:
            if isinstance(item, Mapping):
                yield item


def _ensure_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, Iterable) and not isinstance(value, (str, bytes)):
        return list(value)
    return [value]


def _coerce_float(value: Any, *, default: float = 0.0) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        number = default
    if number != number:  # NaN guard
        number = default
    return number


def _coerce_int(value: Any, *, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _coerce_bool(value: Any, *, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "1", "yes", "oui"}:
            return True
        if lowered in {"false", "0", "no", "non"}:
            return False
    return default


def _coerce_str(value: Any, *, default: str = "") -> str:
    if isinstance(value, str):
        cleaned = value.strip()
        if cleaned:
            return cleaned
    if value is None:
        return default
    return str(value)


def _timestamp(value: Any | None) -> float:
    if value is None:
        return time.time()
    try:
        return float(value)
    except (TypeError, ValueError):
        return time.time()


@dataclass
class Evidence:
    id: str
    kind: str
    source: str
    snippet: str
    weight: float = 0.5
    timestamp: float = field(default_factory=lambda: time.time())
    metadata: Mapping[str, Any] = field(default_factory=dict)
    raw: Mapping[str, Any] = field(default_factory=dict)

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "Evidence":
        mapping = _ensure_mapping(payload)
        return cls(
            id=_coerce_str(mapping.get("id"), default=str(uuid.uuid4())),
            kind=_coerce_str(mapping.get("kind"), default="observation"),
            source=_coerce_str(mapping.get("source"), default="system"),
            snippet=_coerce_str(mapping.get("snippet"), default=""),
            weight=max(0.0, min(1.0, _coerce_float(mapping.get("weight"), default=0.5))),
            timestamp=_timestamp(mapping.get("timestamp")),
            metadata=_ensure_mapping(mapping.get("metadata")),
            raw=mapping,
        )

    @classmethod
    def new(cls, kind: str, source: str, snippet: str, *, weight: float = 0.5) -> "Evidence":
        return cls(
            id=str(uuid.uuid4()),
            kind=kind,
            source=source,
            snippet=snippet,
            weight=max(0.0, min(1.0, float(weight))),
            timestamp=time.time(),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "kind": self.kind,
            "source": self.source,
            "snippet": self.snippet,
            "weight": self.weight,
            "timestamp": self.timestamp,
            "metadata": dict(self.metadata),
        }


@dataclass
class TemporalSegment:
    start: float
    end: Optional[float] = None
    recurrence: Mapping[str, Any] = field(default_factory=dict)

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "TemporalSegment":
        mapping = _ensure_mapping(payload)
        return cls(
            start=_timestamp(mapping.get("start")),
            end=mapping.get("end"),
            recurrence=_ensure_mapping(mapping.get("recurrence")),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "start": self.start,
            "end": self.end,
            "recurrence": dict(self.recurrence),
        }


@dataclass
class Belief:
    id: str
    subject: str
    relation: str
    value: str
    confidence: float = 0.5
    polarity: int = 1
    created_by: str = "system"
    subject_type: str = "Entity"
    relation_type: str = "related_to"
    value_type: str = "Entity"
    subject_label: Optional[str] = None
    value_label: Optional[str] = None
    valid_from: float = field(default_factory=lambda: time.time())
    valid_to: Optional[float] = None
    updated_at: float = field(default_factory=lambda: time.time())
    stability: str = "anchor"
    justifications: list[Evidence] = field(default_factory=list)
    temporal_segments: list[TemporalSegment] = field(default_factory=list)
    annotations: Mapping[str, Any] = field(default_factory=dict)
    raw: Mapping[str, Any] = field(default_factory=dict)

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "Belief":
        mapping = _ensure_mapping(payload)
        evidences = [Evidence.from_mapping(item) for item in _ensure_iterable_of_mappings(mapping.get("justifications"))]
        segments = [TemporalSegment.from_mapping(item) for item in _ensure_iterable_of_mappings(mapping.get("temporal_segments"))]
        return cls(
            id=_coerce_str(mapping.get("id"), default=str(uuid.uuid4())),
            subject=_coerce_str(mapping.get("subject")),
            relation=_coerce_str(mapping.get("relation")),
            value=_coerce_str(mapping.get("value")),
            confidence=max(0.0, min(1.0, _coerce_float(mapping.get("confidence"), default=0.5))),
            polarity=1 if _coerce_int(mapping.get("polarity"), default=1) >= 0 else -1,
            created_by=_coerce_str(mapping.get("created_by"), default="system"),
            subject_type=_coerce_str(mapping.get("subject_type"), default="Entity"),
            relation_type=_coerce_str(mapping.get("relation_type"), default="related_to"),
            value_type=_coerce_str(mapping.get("value_type"), default="Entity"),
            subject_label=mapping.get("subject_label"),
            value_label=mapping.get("value_label"),
            valid_from=_timestamp(mapping.get("valid_from")),
            valid_to=mapping.get("valid_to"),
            updated_at=_timestamp(mapping.get("updated_at")),
            stability=_coerce_str(mapping.get("stability"), default="anchor"),
            justifications=evidences,
            temporal_segments=segments,
            annotations=_ensure_mapping(mapping.get("annotations")),
            raw=mapping,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": "belief",
            "id": self.id,
            "subject": self.subject,
            "relation": self.relation,
            "value": self.value,
            "confidence": self.confidence,
            "polarity": self.polarity,
            "created_by": self.created_by,
            "subject_type": self.subject_type,
            "relation_type": self.relation_type,
            "value_type": self.value_type,
            "subject_label": self.subject_label,
            "value_label": self.value_label,
            "valid_from": self.valid_from,
            "valid_to": self.valid_to,
            "updated_at": self.updated_at,
            "stability": self.stability,
            "justifications": [e.to_dict() for e in self.justifications],
            "temporal_segments": [segment.to_dict() for segment in self.temporal_segments],
            "annotations": dict(self.annotations),
        }


@dataclass
class Event:
    id: str
    event_type: str
    roles: Mapping[str, str]
    occurred_at: float
    location: Optional[str] = None
    confidence: float = 0.5
    justifications: list[Evidence] = field(default_factory=list)
    updated_at: float = field(default_factory=lambda: time.time())
    annotations: Mapping[str, Any] = field(default_factory=dict)
    raw: Mapping[str, Any] = field(default_factory=dict)

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "Event":
        mapping = _ensure_mapping(payload)
        evidences = [Evidence.from_mapping(item) for item in _ensure_iterable_of_mappings(mapping.get("justifications"))]
        return cls(
            id=_coerce_str(mapping.get("id"), default=str(uuid.uuid4())),
            event_type=_coerce_str(mapping.get("event_type"), default="event"),
            roles={_coerce_str(key): _coerce_str(val) for key, val in _ensure_mapping(mapping.get("roles")).items()},
            occurred_at=_timestamp(mapping.get("occurred_at")),
            location=mapping.get("location"),
            confidence=max(0.0, min(1.0, _coerce_float(mapping.get("confidence"), default=0.5))),
            justifications=evidences,
            updated_at=_timestamp(mapping.get("updated_at")),
            annotations=_ensure_mapping(mapping.get("annotations")),
            raw=mapping,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": "event",
            "id": self.id,
            "event_type": self.event_type,
            "roles": dict(self.roles),
            "occurred_at": self.occurred_at,
            "location": self.location,
            "confidence": self.confidence,
            "updated_at": self.updated_at,
            "justifications": [e.to_dict() for e in self.justifications],
            "annotations": dict(self.annotations),
        }


class BeliefGraph:
    """Storage façade that delegates reasoning and evolution to the LLM."""

    def __init__(
        self,
        path: str = "data/beliefs.jsonl",
        *,
        ontology: Optional[Ontology] = None,
        entity_linker: Optional[EntityLinker] = None,
        llm_manager=None,
    ) -> None:
        self.path = path
        os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
        self.ontology = ontology or Ontology.default()
        self.entity_linker = entity_linker or EntityLinker(llm_manager=llm_manager)
        self._manager = llm_manager
        self._beliefs: dict[str, Belief] = {}
        self._events: dict[str, Event] = {}
        self._last_summary: dict[str, Any] = {}
        self._last_summary_ts: float = 0.0
        self._load()
        from .summarizer import BeliefSummarizer

        self.summarizer = BeliefSummarizer(self, llm_manager=llm_manager)

    # ------------------------------------------------------------------
    def set_entity_linker(self, linker: EntityLinker) -> None:
        self.entity_linker = linker

    def _manager_or_default(self):
        manager = self._manager
        if manager is None:
            manager = get_llm_manager()
        return manager

    def _load(self) -> None:
        self._beliefs.clear()
        self._events.clear()
        if not os.path.exists(self.path):
            return
        with open(self.path, "r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    payload = json.loads(line)
                except json.JSONDecodeError:
                    continue
                kind = payload.get("kind")
                if kind == "event":
                    event = Event.from_mapping(payload)
                    self._events[event.id] = event
                else:
                    belief = Belief.from_mapping(payload)
                    self._beliefs[belief.id] = belief

    def flush(self) -> None:
        with open(self.path, "w", encoding="utf-8") as handle:
            for belief in self._beliefs.values():
                handle.write(json.dumps(json_sanitize(belief.to_dict()), ensure_ascii=False) + "\n")
            for event in self._events.values():
                handle.write(json.dumps(json_sanitize(event.to_dict()), ensure_ascii=False) + "\n")

    # ------------------------------------------------------------------
    def _snapshot(self, *, limit: int = 64) -> dict[str, Any]:
        beliefs = sorted(self._beliefs.values(), key=lambda b: b.updated_at, reverse=True)[:limit]
        events = sorted(self._events.values(), key=lambda e: e.updated_at, reverse=True)[: max(1, limit // 2)]
        return {
            "beliefs": [belief.to_dict() for belief in beliefs],
            "events": [event.to_dict() for event in events],
        }

    def _call_llm(self, operation: str, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        manager = self._manager_or_default()
        request = {
            "operation": operation,
            "payload": _ensure_mapping(payload),
            "snapshot": self._snapshot(),
        }
        response = manager.call_dict(
            "belief_graph_orchestrator",
            input_payload=request,
        )
        if not isinstance(response, Mapping):  # pragma: no cover - defensive guard
            raise LLMIntegrationError("Spec 'belief_graph_orchestrator' did not return a mapping payload")
        return response

    def _apply_updates(self, response: Mapping[str, Any]) -> None:
        updates = _ensure_mapping(response.get("updates"))
        for belief_payload in _ensure_iterable_of_mappings(updates.get("beliefs")):
            belief = Belief.from_mapping(belief_payload)
            self._beliefs[belief.id] = belief
        for belief_id in _ensure_list(updates.get("remove_beliefs")):
            self._beliefs.pop(_coerce_str(belief_id), None)
        for event_payload in _ensure_iterable_of_mappings(updates.get("events")):
            event = Event.from_mapping(event_payload)
            self._events[event.id] = event
        for event_id in _ensure_list(updates.get("remove_events")):
            self._events.pop(_coerce_str(event_id), None)
        if _coerce_bool(updates.get("flush"), default=False):
            self.flush()

    # ------------------------------------------------------------------
    def iter_beliefs(self) -> Sequence[Belief]:
        return tuple(self._beliefs.values())

    def all(self, *, active_only: bool = True) -> list[Belief]:
        now = time.time()
        beliefs = list(self._beliefs.values())
        if not active_only:
            return beliefs
        filtered: list[Belief] = []
        for belief in beliefs:
            if belief.valid_to and belief.valid_to < now:
                continue
            filtered.append(belief)
        return filtered

    def events(self) -> list[Event]:
        return list(self._events.values())

    # ------------------------------------------------------------------
    def update(
        self,
        subject: str,
        relation: str,
        value: str,
        *,
        confidence: float = 0.6,
        polarity: int = 1,
        evidence: Evidence | Mapping[str, Any] | None = None,
        metadata: Mapping[str, Any] | None = None,
        extra: Mapping[str, Any] | None = None,
    ) -> Belief:
        payload: dict[str, Any] = {
            "subject": subject,
            "relation": relation,
            "value": value,
            "confidence": confidence,
            "polarity": polarity,
            "metadata": _ensure_mapping(metadata),
            "extra": _ensure_mapping(extra),
        }
        if evidence is not None:
            payload["evidence"] = (
                evidence.to_dict() if isinstance(evidence, Evidence) else _ensure_mapping(evidence)
            )
        response = self._call_llm("upsert_belief", payload)
        self._apply_updates(response)
        result = _ensure_mapping(response.get("result"))
        belief_id = _coerce_str(result.get("belief_id"))
        if not belief_id:
            # fallback to the first updated belief when the LLM returns only the object
            beliefs = [Belief.from_mapping(item) for item in _ensure_iterable_of_mappings(result.get("belief"))]
            if beliefs:
                belief_id = beliefs[0].id
        belief = self._beliefs.get(belief_id)
        if belief is None:
            raise LLMIntegrationError("belief_graph_orchestrator did not provide a belief identifier")
        return belief

    def add_fact(
        self,
        *,
        subject: str,
        predicate: str,
        obj: str,
        confidence: float = 0.6,
        polarity: int = 1,
        evidence: Evidence | Mapping[str, Any] | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> Belief:
        return self.update(
            subject,
            predicate,
            obj,
            confidence=confidence,
            polarity=polarity,
            evidence=evidence,
            metadata=metadata,
        )

    def add_evidence(
        self,
        *,
        belief_id: Optional[str] = None,
        subject: Optional[str] = None,
        relation: Optional[str] = None,
        predicate: Optional[str] = None,
        value: Optional[str] = None,
        obj: Optional[str] = None,
        evidence: Evidence | Mapping[str, Any] | None = None,
        weight: float | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> Optional[Belief]:
        relation = relation or predicate
        value = value or obj
        payload: dict[str, Any] = {
            "belief_id": belief_id,
            "subject": subject,
            "relation": relation,
            "value": value,
            "metadata": _ensure_mapping(metadata),
        }
        if evidence is not None:
            payload["evidence"] = (
                evidence.to_dict() if isinstance(evidence, Evidence) else _ensure_mapping(evidence)
            )
        if weight is not None:
            payload["weight"] = weight
        response = self._call_llm("add_evidence", payload)
        self._apply_updates(response)
        result = _ensure_mapping(response.get("result"))
        belief_id = _coerce_str(result.get("belief_id")) or _coerce_str(payload.get("belief_id"))
        return self._beliefs.get(belief_id) if belief_id else None

    def record_feedback(self, belief_id: str, *, success: Optional[bool], weight: float = 1.0) -> None:
        payload = {
            "belief_id": belief_id,
            "success": success,
            "weight": weight,
        }
        response = self._call_llm("record_feedback", payload)
        self._apply_updates(response)

    def retire(self, belief_id: str) -> None:
        response = self._call_llm("retire", {"belief_id": belief_id})
        self._apply_updates(response)

    def reactivate(self, belief_id: str) -> None:
        response = self._call_llm("reactivate", {"belief_id": belief_id})
        self._apply_updates(response)

    def add_event(
        self,
        event_type: str,
        *,
        roles: Mapping[str, str],
        occurred_at: Optional[float] = None,
        location: Optional[str] = None,
        confidence: float = 0.5,
        metadata: Mapping[str, Any] | None = None,
    ) -> Event:
        payload = {
            "event_type": event_type,
            "roles": dict(roles),
            "occurred_at": occurred_at,
            "location": location,
            "confidence": confidence,
            "metadata": _ensure_mapping(metadata),
        }
        response = self._call_llm("add_event", payload)
        self._apply_updates(response)
        result = _ensure_mapping(response.get("result"))
        event_id = _coerce_str(result.get("event_id"))
        if not event_id:
            raise LLMIntegrationError("belief_graph_orchestrator did not provide an event identifier")
        event = self._events.get(event_id)
        if event is None:
            raise LLMIntegrationError("Event not found after LLM update")
        return event

    def find_contradictions(self, *, min_confidence: float = 0.6) -> list[tuple[Belief, Belief]]:
        response = self._call_llm("find_contradictions", {"min_confidence": min_confidence})
        self._apply_updates(response)
        pairs: list[tuple[Belief, Belief]] = []
        for entry in _ensure_iterable_of_mappings(response.get("pairs")):
            first = self._beliefs.get(_coerce_str(entry.get("positive")))
            second = self._beliefs.get(_coerce_str(entry.get("negative")))
            if first and second:
                pairs.append((first, second))
        return pairs

    def query(
        self,
        *,
        subject: Optional[str] = None,
        relation: Optional[str] = None,
        value: Optional[str] = None,
        min_confidence: float | None = None,
        active_only: bool = True,
        extra: Mapping[str, Any] | None = None,
    ) -> list[Belief]:
        payload = {
            "subject": subject,
            "relation": relation,
            "value": value,
            "min_confidence": min_confidence,
            "active_only": active_only,
            "extra": _ensure_mapping(extra),
        }
        response = self._call_llm("query_beliefs", payload)
        self._apply_updates(response)
        results: list[Belief] = []
        for belief_payload in _ensure_iterable_of_mappings(response.get("beliefs")):
            belief = Belief.from_mapping(belief_payload)
            self._beliefs[belief.id] = belief
            results.append(belief)
        return results

    # ------------------------------------------------------------------
    def latest_summary(self, *, force: bool = False) -> Mapping[str, Any]:
        if not force and self._last_summary and (time.time() - self._last_summary_ts) < 60:
            return self._last_summary
        summary = self.summarizer.summarize()
        self._last_summary = summary
        self._last_summary_ts = time.time()
        return summary


__all__ = [
    "Belief",
    "BeliefGraph",
    "Evidence",
    "Event",
    "TemporalSegment",
]
