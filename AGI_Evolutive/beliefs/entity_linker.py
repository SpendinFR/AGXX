"""LLM-backed entity resolution for the belief graph."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, MutableMapping, Optional

from AGI_Evolutive.utils.llm_service import LLMIntegrationError, get_llm_manager


def _ensure_mapping(value: Any) -> MutableMapping[str, Any]:
    if isinstance(value, Mapping):
        return {str(k): v for k, v in value.items()}
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


def _coerce_float(value: Any, *, default: float = 0.5) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        number = default
    if number != number:  # NaN
        number = default
    return number


@dataclass
class EntityEntry:
    """Snapshot of a canonical entity returned by the LLM."""

    canonical_id: str
    name: str
    entity_type: str
    confidence: float = 0.5
    justification: Optional[str] = None
    aliases: set[str] = field(default_factory=set)
    metadata: Mapping[str, Any] = field(default_factory=dict)
    raw: Mapping[str, Any] = field(default_factory=dict)

    @classmethod
    def from_payload(
        cls,
        payload: Mapping[str, Any],
        *,
        fallback_id: str,
        fallback_name: str,
        fallback_type: Optional[str],
    ) -> "EntityEntry":
        mapping = _ensure_mapping(payload)
        canonical = str(mapping.get("canonical_id") or fallback_id).strip() or fallback_id
        name = str(mapping.get("name") or fallback_name).strip() or fallback_name
        entity_type = str(mapping.get("entity_type") or fallback_type or "Entity").strip() or "Entity"
        confidence = max(0.0, min(1.0, _coerce_float(mapping.get("confidence"), default=0.5)))
        justification = mapping.get("justification")
        if justification is not None:
            justification = str(justification).strip() or None
        metadata = _ensure_mapping(mapping.get("metadata"))
        aliases = set(_ensure_str_list(mapping.get("aliases")))
        if fallback_name:
            aliases.add(fallback_name)
        return cls(
            canonical_id=canonical,
            name=name,
            entity_type=entity_type,
            confidence=confidence,
            justification=justification,
            aliases=aliases,
            metadata=metadata,
            raw=mapping,
        )


class EntityLinker:
    """Minimal alias table that fully delegates resolution to the LLM."""

    def __init__(self, *, llm_manager=None) -> None:
        self._manager = llm_manager
        self._entities: dict[str, EntityEntry] = {}
        self._aliases: dict[str, str] = {}

    def _manager_or_default(self):
        manager = self._manager
        if manager is None:
            manager = get_llm_manager()
        return manager

    def _normalize(self, value: str) -> str:
        return value.strip().lower()

    def _snapshot(self, *, limit: int = 50) -> list[dict[str, Any]]:
        entries: list[dict[str, Any]] = []
        for entry in list(self._entities.values())[:limit]:
            entries.append(
                {
                    "canonical_id": entry.canonical_id,
                    "name": entry.name,
                    "entity_type": entry.entity_type,
                    "aliases": sorted(entry.aliases),
                    "confidence": entry.confidence,
                }
            )
        return entries

    def _call_llm(self, action: str, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        request = {
            "action": action,
            "payload": _ensure_mapping(payload),
            "known_entities": self._snapshot(),
        }
        manager = self._manager_or_default()
        response = manager.call_dict(
            "entity_linker",
            input_payload=request,
        )
        if not isinstance(response, Mapping):  # pragma: no cover - defensive guard
            raise LLMIntegrationError(
                "Spec 'entity_linker' did not return a mapping payload",
            )
        return response

    def _store_entry(self, entry: EntityEntry, *, aliases: Iterable[str] = ()) -> EntityEntry:
        self._entities[entry.canonical_id] = entry
        for alias in set(entry.aliases).union(set(_ensure_str_list(aliases))):
            norm = self._normalize(alias)
            if norm:
                self._aliases[norm] = entry.canonical_id
        norm_name = self._normalize(entry.name)
        if norm_name:
            self._aliases[norm_name] = entry.canonical_id
        return entry

    # ------------------------------------------------------------------
    def resolve_entry(
        self,
        name: str,
        *,
        entity_type: Optional[str] = None,
        context: Mapping[str, Any] | None = None,
        extra: Mapping[str, Any] | None = None,
    ) -> EntityEntry:
        context_payload = _ensure_mapping(context)
        if not context_payload and isinstance(context, str):
            context_payload = {"text": context}
        payload: dict[str, Any] = {
            "mention": name,
            "hint_type": entity_type,
            "context": context_payload,
        }
        extra_payload = _ensure_mapping(extra)
        if extra_payload:
            payload["extra"] = extra_payload

        response = self._call_llm("resolve", payload)
        entity_payload = response.get("entity")
        entry = EntityEntry.from_payload(
            entity_payload or {},
            fallback_id=self._normalize(name) or name,
            fallback_name=name,
            fallback_type=entity_type,
        )
        aliases = response.get("aliases")
        if isinstance(aliases, str):
            aliases = [aliases]
        elif not isinstance(aliases, Iterable):
            aliases = []
        self._store_entry(entry, aliases=aliases)
        return entry

    def resolve(
        self,
        name: str,
        *,
        entity_type: Optional[str] = None,
        context: Mapping[str, Any] | None = None,
        extra: Mapping[str, Any] | None = None,
    ) -> tuple[str, str]:
        entry = self.resolve_entry(
            name,
            entity_type=entity_type,
            context=context,
            extra=extra,
        )
        return entry.canonical_id, entry.entity_type

    def register(
        self,
        name: str,
        entity_type: str,
        *,
        context: Mapping[str, Any] | None = None,
        extra: Mapping[str, Any] | None = None,
    ) -> str:
        entry = self.resolve_entry(
            name,
            entity_type=entity_type,
            context=context,
            extra=extra,
        )
        return entry.canonical_id

    def alias(self, alias: str, canonical_id: str) -> None:
        entry = self._entities.get(canonical_id)
        if not entry:
            return
        entry.aliases.add(alias)
        self._aliases[self._normalize(alias)] = canonical_id

    def merge(self, preferred: str, duplicate: str) -> None:
        payload = {"preferred": preferred, "duplicate": duplicate}
        response = self._call_llm("merge", payload)
        canonical = str(response.get("canonical_id") or preferred).strip() or preferred
        merged_aliases = _ensure_str_list(response.get("aliases"))
        entry = self._entities.get(canonical)
        if entry is None:
            entry = EntityEntry.from_payload(
                response.get("entity") or {},
                fallback_id=canonical,
                fallback_name=canonical,
                fallback_type=None,
            )
        entry.aliases.update(merged_aliases)
        self._store_entry(entry)
        self._aliases[self._normalize(duplicate)] = canonical

    # ------------------------------------------------------------------
    def get(self, canonical_id: str) -> Optional[EntityEntry]:
        return self._entities.get(canonical_id)

    def known_entities(self) -> Mapping[str, EntityEntry]:
        return dict(self._entities)

    def canonical_form(self, name: str) -> str:
        norm = self._normalize(name)
        return self._aliases.get(norm, norm)


__all__ = ["EntityEntry", "EntityLinker"]
