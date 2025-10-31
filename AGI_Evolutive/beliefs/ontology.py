"""LLM-backed ontology registry for the belief graph."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping, MutableMapping, Optional

from AGI_Evolutive.utils.llm_service import LLMIntegrationError, get_llm_manager


def _ensure_mapping(value: Any) -> MutableMapping[str, Any]:
    if isinstance(value, Mapping):
        return {str(key): val for key, val in value.items()}
    return {}


def _ensure_str_list(value: Any) -> list[str]:
    if isinstance(value, str):
        cleaned = value.strip()
        return [cleaned] if cleaned else []
    if isinstance(value, Iterable):
        result: list[str] = []
        for item in value:
            if isinstance(item, str):
                cleaned = item.strip()
                if cleaned:
                    result.append(cleaned)
        return result
    return []


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


@dataclass(frozen=True)
class EntityType:
    name: str
    parent: Optional[str] = None
    description: Optional[str] = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def is_a(self, other: str, *, registry: Mapping[str, "EntityType"]) -> bool:
        current: Optional[EntityType] = self
        while current is not None:
            if current.name == other:
                return True
            parent = current.parent
            current = registry.get(parent) if parent else None
        return False


@dataclass(frozen=True)
class RelationType:
    name: str
    domain: tuple[str, ...]
    range: tuple[str, ...]
    polarity_sensitive: bool = True
    temporal: bool = False
    stability: str = "anchor"
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class EventType:
    name: str
    roles: Mapping[str, tuple[str, ...]]
    metadata: Mapping[str, Any] = field(default_factory=dict)


class Ontology:
    """Lightweight ontology whose enrichment is delegated to the LLM."""

    def __init__(self, *, llm_manager=None) -> None:
        self.entity_types: dict[str, EntityType] = {}
        self.relation_types: dict[str, RelationType] = {}
        self.event_types: dict[str, EventType] = {}
        self._manager = llm_manager

    # ------------------------------------------------------------------
    def _manager_or_default(self):
        manager = self._manager
        if manager is None:
            manager = get_llm_manager()
        return manager

    def _snapshot(self) -> dict[str, Any]:
        return {
            "entities": [
                {"name": et.name, "parent": et.parent} for et in self.entity_types.values()
            ],
            "relations": [
                {
                    "name": rel.name,
                    "domain": list(rel.domain),
                    "range": list(rel.range),
                    "polarity_sensitive": rel.polarity_sensitive,
                    "temporal": rel.temporal,
                    "stability": rel.stability,
                }
                for rel in self.relation_types.values()
            ],
            "events": [
                {
                    "name": evt.name,
                    "roles": {role: list(options) for role, options in evt.roles.items()},
                }
                for evt in self.event_types.values()
            ],
        }

    def _call_llm(self, request: Mapping[str, Any]) -> Mapping[str, Any]:
        payload = {
            "request": _ensure_mapping(request),
            "snapshot": self._snapshot(),
        }
        manager = self._manager_or_default()
        response = manager.call_dict(
            "ontology_enrichment",
            input_payload=payload,
        )
        if not isinstance(response, Mapping):  # pragma: no cover - defensive guard
            raise LLMIntegrationError(
                "Spec 'ontology_enrichment' did not return a mapping payload",
            )
        return response

    def _register_entity_payload(self, payload: Mapping[str, Any]) -> EntityType:
        name = str(payload.get("name") or "").strip()
        if not name:
            raise LLMIntegrationError("ontology_enrichment returned an entity without name")
        parent = payload.get("parent")
        if parent is not None:
            parent = str(parent).strip() or None
        entity = EntityType(
            name=name,
            parent=parent,
            description=str(payload.get("description") or "").strip() or None,
            metadata=_ensure_mapping(payload.get("metadata")),
        )
        self.entity_types[entity.name] = entity
        return entity

    def _register_relation_payload(self, payload: Mapping[str, Any]) -> RelationType:
        name = str(payload.get("name") or "").strip()
        if not name:
            raise LLMIntegrationError("ontology_enrichment returned a relation without name")
        relation = RelationType(
            name=name,
            domain=tuple(_ensure_str_list(payload.get("domain") or [])) or ("Entity",),
            range=tuple(_ensure_str_list(payload.get("range") or [])) or ("Entity",),
            polarity_sensitive=_coerce_bool(payload.get("polarity_sensitive"), default=True),
            temporal=_coerce_bool(payload.get("temporal"), default=False),
            stability=str(payload.get("stability") or "anchor").strip() or "anchor",
            metadata=_ensure_mapping(payload.get("metadata")),
        )
        self.relation_types[relation.name] = relation
        return relation

    def _register_event_payload(self, payload: Mapping[str, Any]) -> EventType:
        name = str(payload.get("name") or "").strip()
        if not name:
            raise LLMIntegrationError("ontology_enrichment returned an event without name")
        roles_payload = _ensure_mapping(payload.get("roles"))
        roles = {role: tuple(_ensure_str_list(options)) for role, options in roles_payload.items()}
        event = EventType(
            name=name,
            roles=roles,
            metadata=_ensure_mapping(payload.get("metadata")),
        )
        self.event_types[event.name] = event
        return event

    # ------------------------------------------------------------------
    def register_entity(self, name: str, *, parent: Optional[str] = None, metadata: Mapping[str, Any] | None = None) -> EntityType:
        entity = EntityType(name=name, parent=parent, metadata=_ensure_mapping(metadata))
        self.entity_types[name] = entity
        return entity

    def register_relation(
        self,
        name: str,
        *,
        domain: Iterable[str] | None = None,
        range: Iterable[str] | None = None,
        polarity_sensitive: bool = True,
        temporal: bool = False,
        stability: str = "anchor",
        metadata: Mapping[str, Any] | None = None,
    ) -> RelationType:
        relation = RelationType(
            name=name,
            domain=tuple(domain or ("Entity",)),
            range=tuple(range or ("Entity",)),
            polarity_sensitive=polarity_sensitive,
            temporal=temporal,
            stability=stability,
            metadata=_ensure_mapping(metadata),
        )
        self.relation_types[name] = relation
        return relation

    def register_event(
        self,
        name: str,
        *,
        roles: Mapping[str, Iterable[str]] | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> EventType:
        event = EventType(
            name=name,
            roles={role: tuple(values) for role, values in (roles or {}).items()},
            metadata=_ensure_mapping(metadata),
        )
        self.event_types[name] = event
        return event

    # ------------------------------------------------------------------
    def entity(self, name: str) -> Optional[EntityType]:
        return self.entity_types.get(name)

    def relation(self, name: str) -> Optional[RelationType]:
        return self.relation_types.get(name)

    def event(self, name: str) -> Optional[EventType]:
        return self.event_types.get(name)

    # ------------------------------------------------------------------
    def infer_entity_type(self, name: str) -> EntityType:
        entity = self.entity_types.get(name)
        if entity is not None:
            return entity
        response = self._call_llm({"entity": {"name": name}})
        for suggestion in response.get("entities", []):
            suggestion_map = _ensure_mapping(suggestion)
            if str(suggestion_map.get("name") or "").strip() == name:
                return self._register_entity_payload(suggestion_map)
        raise LLMIntegrationError(f"ontology_enrichment did not provide a definition for entity '{name}'")

    def infer_relation_type(self, name: str) -> RelationType:
        relation = self.relation_types.get(name)
        if relation is not None:
            return relation
        response = self._call_llm({"relation": {"name": name}})
        for suggestion in response.get("relations", []):
            suggestion_map = _ensure_mapping(suggestion)
            if str(suggestion_map.get("name") or "").strip() == name:
                return self._register_relation_payload(suggestion_map)
        return self.register_relation(name)

    def infer_event_type(self, name: str) -> EventType:
        event = self.event_types.get(name)
        if event is not None:
            return event
        response = self._call_llm({"event": {"name": name}})
        for suggestion in response.get("events", []):
            suggestion_map = _ensure_mapping(suggestion)
            if str(suggestion_map.get("name") or "").strip() == name:
                return self._register_event_payload(suggestion_map)
        return self.register_event(name)

    # ------------------------------------------------------------------
    def load_from_mapping(self, payload: Mapping[str, Any], *, clear_existing: bool = False) -> None:
        if clear_existing:
            self.entity_types.clear()
            self.relation_types.clear()
            self.event_types.clear()
        for entity_payload in payload.get("entities", []):
            self._register_entity_payload(_ensure_mapping(entity_payload))
        for relation_payload in payload.get("relations", []):
            self._register_relation_payload(_ensure_mapping(relation_payload))
        for event_payload in payload.get("events", []):
            self._register_event_payload(_ensure_mapping(event_payload))

    def load_from_file(self, path: Path | str, *, clear_existing: bool = False) -> None:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        self.load_from_mapping(data, clear_existing=clear_existing)

    # ------------------------------------------------------------------
    @classmethod
    def default(cls) -> "Ontology":
        onto = cls()
        # Entities
        onto.register_entity("Entity")
        onto.register_entity("Agent", parent="Entity")
        onto.register_entity("Person", parent="Agent")
        onto.register_entity("Organization", parent="Agent")
        onto.register_entity("Place", parent="Entity")
        onto.register_entity("Object", parent="Entity")
        onto.register_entity("Resource", parent="Object")
        onto.register_entity("Tool", parent="Resource")
        onto.register_entity("Activity", parent="Entity")
        onto.register_entity("Habit", parent="Activity")
        onto.register_entity("Emotion", parent="Entity")
        onto.register_entity("Goal", parent="Entity")
        onto.register_entity("Intention", parent="Goal")
        onto.register_entity("TemporalSegment", parent="Entity")
        onto.register_entity("Context", parent="Entity")
        onto.register_entity("Knowledge", parent="Entity")
        onto.register_entity("Experience", parent="Entity")
        onto.register_entity("Communication", parent="Activity")

        # Relations
        onto.register_relation("related_to")
        onto.register_relation("likes", domain=["Agent"], range=["Entity"])
        onto.register_relation(
            "does_often",
            domain=["Agent"],
            range=["Activity"],
            temporal=True,
        )
        onto.register_relation("causes")
        onto.register_relation("supports", domain=["Entity"], range=["Goal"], stability="anchor")
        onto.register_relation("opposes", domain=["Entity"], range=["Entity"], stability="episode")
        onto.register_relation(
            "located_in",
            domain=["Entity"],
            range=["Place"],
            stability="anchor",
        )
        onto.register_relation(
            "temporal",
            domain=["Activity", "TemporalSegment"],
            range=["TemporalSegment", "Activity"],
            temporal=True,
            stability="episode",
        )

        # Events
        onto.register_event(
            "interaction",
            roles={
                "agent": ("Agent",),
                "recipient": ("Agent",),
                "medium": ("Communication", "Resource"),
            },
        )
        onto.register_event(
            "routine",
            roles={
                "agent": ("Agent",),
                "activity": ("Activity",),
                "context": ("Context", "Place"),
            },
        )
        onto.register_event(
            "observation",
            roles={
                "observer": ("Agent",),
                "subject": ("Entity",),
                "location": ("Place", "Context"),
            },
        )
        return onto


__all__ = ["EntityType", "RelationType", "EventType", "Ontology"]
