"""LLM-first retrieval pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Optional, Sequence

from AGI_Evolutive.utils.llm_service import LLMIntegrationError, get_llm_manager


class RAGPipelineError(RuntimeError):
    """Raised when the retrieval pipeline contract cannot be honoured."""


def _coerce_string(value: Any) -> Optional[str]:
    if isinstance(value, str):
        stripped = value.strip()
        if stripped:
            return stripped
    return None


def _coerce_mapping(value: Any) -> Dict[str, Any]:
    if isinstance(value, Mapping):
        return {str(key): val for key, val in value.items()}
    return {}


def _coerce_string_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, str):
        value = [value]
    result: List[str] = []
    if isinstance(value, Iterable) and not isinstance(value, (bytes, bytearray)):
        for item in value:
            if isinstance(item, str):
                cleaned = item.strip()
                if cleaned:
                    result.append(cleaned)
    return result


def _ensure_documents(documents: Iterable["RAGDocument"], *, limit: Optional[int]) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    for idx, doc in enumerate(documents):
        if limit is not None and idx >= limit:
            break
        items.append(doc.to_payload())
    return items


@dataclass
class RAGDocument:
    """Document registered in the in-memory store."""

    doc_id: str
    content: str
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def to_payload(self) -> Dict[str, Any]:
        payload = {
            "doc_id": self.doc_id,
            "content": self.content,
            "metadata": _coerce_mapping(self.metadata),
        }
        return payload


@dataclass
class RAGRequest:
    """Structured payload forwarded to the answer generation spec."""

    question: str
    plan: Optional[Mapping[str, Any]] = None
    documents: Sequence[RAGDocument] = field(default_factory=tuple)
    history: Sequence[Mapping[str, Any]] = field(default_factory=tuple)
    memory: Optional[Mapping[str, Any]] = None
    config: Optional[Mapping[str, Any]] = None
    metadata: Optional[Mapping[str, Any]] = None

    def build_payload(self, *, document_limit: Optional[int] = None) -> Dict[str, Any]:
        payload: Dict[str, Any] = {"question": self.question}
        if self.plan:
            payload["plan"] = _coerce_mapping(self.plan)
        if self.history:
            payload["history"] = [
                _coerce_mapping(item) for item in self.history if isinstance(item, Mapping)
            ]
        if self.memory:
            payload["memory"] = _coerce_mapping(self.memory)
        if self.config:
            payload["config"] = _coerce_mapping(self.config)
        if self.metadata:
            payload["metadata"] = _coerce_mapping(self.metadata)
        payload["documents"] = _ensure_documents(self.documents, limit=document_limit)
        return payload


@dataclass
class RAGAnswer:
    """Normalised representation of the LLM response."""

    status: str
    answer: Optional[str]
    citations: List[Dict[str, Any]]
    diagnostics: Dict[str, Any]
    notes: List[str]
    meta: Dict[str, Any]
    raw: MutableMapping[str, Any]

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> "RAGAnswer":
        if not isinstance(payload, Mapping):
            raise RAGPipelineError("LLM payload must be a mapping")

        status = _coerce_string(payload.get("status")) or "ok"
        answer = _coerce_string(payload.get("answer"))
        citations_raw = payload.get("citations") or []
        citations: List[Dict[str, Any]] = []
        if isinstance(citations_raw, Iterable) and not isinstance(citations_raw, (bytes, bytearray, str)):
            for item in citations_raw:
                if isinstance(item, Mapping):
                    citations.append({str(key): val for key, val in item.items()})
        diagnostics = _coerce_mapping(payload.get("diagnostics"))
        notes = _coerce_string_list(payload.get("notes"))
        meta = _coerce_mapping(payload.get("meta"))
        raw: MutableMapping[str, Any] = dict(payload)
        if citations and "citations" not in raw:
            raw["citations"] = [dict(item) for item in citations]
        return cls(
            status=status,
            answer=answer,
            citations=citations,
            diagnostics=diagnostics,
            notes=notes,
            meta=meta,
            raw=raw,
        )

    def to_dict(self) -> Dict[str, Any]:
        data = {
            "status": self.status,
            "answer": self.answer,
            "citations": [dict(item) for item in self.citations],
            "diagnostics": dict(self.diagnostics),
            "notes": list(self.notes),
            "meta": dict(self.meta),
            "raw": dict(self.raw),
        }
        return data


class RAGPipeline:
    """Facade delegating answer composition to a single LLM call."""

    def __init__(self, cfg: Mapping[str, Any], *, llm_manager=None) -> None:
        self.cfg = _coerce_mapping(cfg)
        self._manager = llm_manager or get_llm_manager()
        self._documents: Dict[str, RAGDocument] = {}
        self.last_request: Optional[RAGRequest] = None
        self.last_answer: Optional[RAGAnswer] = None

    def add_document(self, doc_id: str, content: str, meta: Optional[Mapping[str, Any]] = None) -> None:
        document = RAGDocument(doc_id=doc_id, content=content, metadata=meta or {})
        self._documents[doc_id] = document

    def list_documents(self) -> List[RAGDocument]:
        return list(self._documents.values())

    def ask(
        self,
        question: str,
        *,
        plan: Optional[Mapping[str, Any]] = None,
        history: Sequence[Mapping[str, Any]] = (),
        memory: Optional[Mapping[str, Any]] = None,
        metadata: Optional[Mapping[str, Any]] = None,
    ) -> Dict[str, Any]:
        request = RAGRequest(
            question=question,
            plan=plan,
            documents=self.list_documents(),
            history=history,
            memory=memory,
            config=self.cfg,
            metadata=metadata,
        )
        self.last_request = request
        payload = request.build_payload(
            document_limit=int(self.cfg.get("compose", {}).get("max_documents", 12))
            if isinstance(self.cfg.get("compose"), Mapping)
            else None
        )
        try:
            response = self._manager.call_dict(
                "retrieval_answer",
                input_payload=payload,
            )
        except LLMIntegrationError as exc:  # pragma: no cover - passthrough
            raise RAGPipelineError(str(exc)) from exc
        answer = RAGAnswer.from_payload(response)
        self.last_answer = answer
        return answer.to_dict()


__all__ = [
    "RAGPipeline",
    "RAGPipelineError",
    "RAGDocument",
    "RAGRequest",
    "RAGAnswer",
]
