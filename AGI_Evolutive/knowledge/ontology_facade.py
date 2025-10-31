"""Knowledge-layer façade around the belief ontology/linker."""

from __future__ import annotations

from typing import Any, Mapping, Optional

from AGI_Evolutive.beliefs.entity_linker import EntityLinker as _BeliefEntityLinker
from AGI_Evolutive.beliefs.graph import BeliefGraph
from AGI_Evolutive.beliefs.ontology import Ontology as _BeliefOntology
from AGI_Evolutive.utils.llm_service import LLMIntegrationError, get_llm_manager


class Ontology(_BeliefOntology):
    """Clone the default belief ontology for knowledge experiments."""

    def __init__(self, source: Optional[_BeliefOntology] = None, *, llm_manager=None) -> None:
        super().__init__(llm_manager=llm_manager)
        if source is None:
            source = _BeliefOntology.default()
        self.entity_types = dict(source.entity_types)
        self.relation_types = dict(source.relation_types)
        self.event_types = dict(source.event_types)


class EntityLinker(_BeliefEntityLinker):
    """Augments the belief entity linker with knowledge-specific context."""

    def __init__(
        self,
        ontology: Optional[Ontology] = None,
        beliefs: Optional[BeliefGraph] = None,
        *,
        llm_manager=None,
    ) -> None:
        super().__init__(llm_manager=llm_manager)
        self.ontology = ontology or Ontology(llm_manager=llm_manager)
        self.beliefs = beliefs
        self._manager = llm_manager

    def _manager_or_default(self):
        manager = self._manager
        if manager is None:
            manager = get_llm_manager()
        return manager

    def link(
        self,
        text: str,
        *,
        hint_type: Optional[str] = None,
        context: Mapping[str, Any] | None = None,
    ) -> Mapping[str, Any]:
        canonical, resolved_type = self.resolve(
            text,
            entity_type=hint_type,
            context=context,
        )
        payload = {
            "text": text,
            "canonical": canonical,
            "resolved_type": resolved_type,
            "known_types": sorted(self.ontology.entity_types.keys()),
            "context": context or {},
        }
        try:
            classification = self._manager_or_default().call_dict(
                "knowledge_entity_typing",
                input_payload=payload,
            )
        except LLMIntegrationError:
            classification = {}
        result_type = classification.get("type") or resolved_type
        return {
            "text": text,
            "canonical": canonical,
            "type": result_type,
            "confidence": classification.get("confidence"),
            "notes": classification.get("notes"),
        }


__all__ = ["EntityLinker", "Ontology"]
