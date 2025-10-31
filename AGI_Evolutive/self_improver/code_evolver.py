"""LLM-driven code evolution without heuristic learners."""

from __future__ import annotations

import difflib
import json
import logging
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence

from AGI_Evolutive.utils.jsonsafe import json_sanitize
from AGI_Evolutive.utils.llm_service import (
    LLMIntegrationError,
    LLMUnavailableError,
    get_llm_manager,
)


LOGGER = logging.getLogger(__name__)


def _coerce_str(value: Any, *, default: str = "") -> str:
    if isinstance(value, str):
        cleaned = value.strip()
        if cleaned:
            return cleaned
    return default


def _coerce_float(value: Any, *, default: float = 0.5, minimum: float = 0.0, maximum: float = 1.0) -> float:
    try:
        number = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return default
    if number != number:  # NaN
        return default
    return max(minimum, min(maximum, number))


def _coerce_mapping(value: Any) -> Dict[str, Any]:
    if isinstance(value, Mapping):
        return {str(k): v for k, v in value.items()}
    return {}


def _ensure_list(value: Any) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return list(value)
    return []


@dataclass(frozen=True)
class CodeEvolutionTarget:
    """Describe a file/module pair eligible for LLM evolution."""

    identifier: str
    file: Path
    module: str
    summary: str
    source: str

    def relative_path(self, repo_root: Path) -> str:
        try:
            return str(self.file.relative_to(repo_root))
        except ValueError:
            return str(self.file)


@dataclass
class CodePatch:
    """Structured view of an LLM-produced patch."""

    patch_id: str
    target: CodeEvolutionTarget
    original_source: str
    patched_source: str
    summary: str
    assessment: Dict[str, Any]
    evaluation: Dict[str, Any]
    notes: str
    confidence: float
    metadata: Dict[str, Any]
    llm_payload: Dict[str, Any]
    diff_override: Optional[str] = None
    _diff_cache: Optional[str] = field(default=None, init=False, repr=False)

    @classmethod
    def from_llm_payload(
        cls,
        payload: Mapping[str, Any],
        target: CodeEvolutionTarget,
    ) -> Optional["CodePatch"]:
        patched_source = payload.get("patched_source")
        if not isinstance(patched_source, str) or not patched_source.strip():
            return None
        patch_id = _coerce_str(payload.get("id") or payload.get("patch_id"), default=uuid.uuid4().hex)
        summary = _coerce_str(payload.get("summary"), default=target.summary)
        notes = _coerce_str(payload.get("notes"))
        assessment = _coerce_mapping(payload.get("assessment"))
        evaluation = _coerce_mapping(payload.get("evaluation"))
        metadata = _coerce_mapping(payload.get("metadata"))
        confidence = _coerce_float(
            assessment.get("confidence", payload.get("confidence")),
            default=0.5,
        )
        diff_override = payload.get("diff") if isinstance(payload.get("diff"), str) else None
        llm_payload = dict(payload)
        return cls(
            patch_id=patch_id,
            target=target,
            original_source=target.source,
            patched_source=patched_source,
            summary=summary,
            assessment=assessment,
            evaluation=evaluation,
            notes=notes,
            confidence=confidence,
            metadata=metadata,
            llm_payload=llm_payload,
            diff_override=diff_override,
        )

    @property
    def diff(self) -> str:
        if self.diff_override is not None:
            return self.diff_override
        if self._diff_cache is None:
            original_lines = self.original_source.splitlines(keepends=True)
            patched_lines = self.patched_source.splitlines(keepends=True)
            self._diff_cache = "".join(
                difflib.unified_diff(
                    original_lines,
                    patched_lines,
                    fromfile=str(self.target.file),
                    tofile=f"{self.target.file} (patched)",
                )
            )
        return self._diff_cache

    def to_report(self, repo_root: Path) -> Dict[str, Any]:
        expected_metrics = _coerce_mapping(self.evaluation.get("expected_metrics"))
        return {
            "patch_id": self.patch_id,
            "summary": self.summary,
            "file": self.target.relative_path(repo_root),
            "module": self.target.module,
            "diff": self.diff,
            "assessment": dict(self.assessment),
            "evaluation": dict(self.evaluation),
            "expected_metrics": expected_metrics,
            "quality": _coerce_mapping(self.evaluation.get("quality")),
            "canary": _coerce_mapping(self.evaluation.get("canary")),
            "notes": self.notes,
            "confidence": self.confidence,
            "passed": bool(self.assessment.get("should_promote") or self.assessment.get("go")),
            "llm_payload": dict(self.llm_payload),
        }

    def serialise(self, repo_root: Path) -> Dict[str, Any]:
        payload = {
            "patch_id": self.patch_id,
            "file": self.target.relative_path(repo_root),
            "module": self.target.module,
            "patched_source": self.patched_source,
            "summary": self.summary,
            "metadata": dict(self.metadata),
            "assessment": dict(self.assessment),
            "evaluation": dict(self.evaluation),
            "notes": self.notes,
            "confidence": self.confidence,
            "diff": self.diff,
        }
        return payload


class CodeEvolver:
    """Delegate code patch generation and evaluation to a single LLM call."""

    def __init__(
        self,
        repo_root: str,
        sandbox: Any,
        quality: Any,
        arch_factory: Any,
        *,
        llm_manager=None,
    ) -> None:
        self.repo_root = Path(repo_root)
        self.repo_root.mkdir(parents=True, exist_ok=True)
        self.sandbox = sandbox
        self.quality = quality
        self.arch_factory = arch_factory
        self._state_dir = self.repo_root / "data" / "self_improve"
        self._state_dir.mkdir(parents=True, exist_ok=True)
        self._history_path = self._state_dir / "code_evolver_history.jsonl"
        self._targets = self._discover_targets()
        self._targets_by_id = {target.identifier: target for target in self._targets}
        self._last_response: Optional[Mapping[str, Any]] = None
        self._llm_manager = llm_manager

    def _discover_targets(self) -> List[CodeEvolutionTarget]:
        defaults: List[Mapping[str, str]] = [
            {
                "id": "reasoning_abduction_score",
                "file": "AGI_Evolutive/reasoning/abduction.py",
                "module": "AGI_Evolutive.reasoning.abduction",
                "summary": "Ajuster la pondération de la fonction _score dans le module d'abduction.",
            }
        ]
        config_path = self.repo_root / "configs" / "evolution_targets.json"
        config_entries: Iterable[Mapping[str, Any]] = []
        if config_path.exists():
            try:
                with open(config_path, "r", encoding="utf-8") as handle:
                    loaded = json.load(handle)
                    if isinstance(loaded, list):
                        config_entries = [entry for entry in loaded if isinstance(entry, Mapping)]
            except Exception:  # pragma: no cover - defensive against malformed configs
                LOGGER.warning("Impossible de charger evolution_targets.json", exc_info=True)
        merged: Dict[str, Mapping[str, Any]] = {entry["id"]: entry for entry in defaults if "id" in entry}
        for entry in config_entries:
            identifier = _coerce_str(entry.get("id"), default=_coerce_str(entry.get("file")))
            if not identifier:
                continue
            merged[identifier] = {
                "id": identifier,
                "file": _coerce_str(entry.get("file")),
                "module": _coerce_str(entry.get("module")),
                "summary": _coerce_str(entry.get("summary"), default=defaults[0]["summary"]),
            }
        targets: List[CodeEvolutionTarget] = []
        for entry in merged.values():
            file_value = entry.get("file")
            module_value = entry.get("module")
            if not file_value or not module_value:
                continue
            path = self.repo_root / file_value
            if not path.exists():
                alt = self.repo_root / "AGI_Evolutive" / file_value
                if alt.exists():
                    path = alt
                else:
                    continue
            try:
                source = path.read_text(encoding="utf-8")
            except Exception:  # pragma: no cover - defensive file access
                continue
            targets.append(
                CodeEvolutionTarget(
                    identifier=entry.get("id", file_value),
                    file=path,
                    module=module_value,
                    summary=entry.get("summary", ""),
                    source=source,
                )
            )
        if not targets:
            raise RuntimeError("Aucun target valide pour CodeEvolver")
        return targets

    def _build_payload(self, max_candidates: int) -> Mapping[str, Any]:
        return {
            "repo_root": str(self.repo_root),
            "max_candidates": int(max_candidates),
            "targets": [
                {
                    "id": target.identifier,
                    "file": target.relative_path(self.repo_root),
                    "module": target.module,
                    "summary": target.summary,
                    "source": target.source,
                }
                for target in self._targets
            ],
        }

    def _record_history(self, response: Mapping[str, Any]) -> None:
        try:
            with open(self._history_path, "a", encoding="utf-8") as handle:
                handle.write(json.dumps(json_sanitize({"response": response})) + "\n")
        except Exception:  # pragma: no cover - diagnostics only
            LOGGER.debug("Impossible d'enregistrer l'historique du CodeEvolver", exc_info=True)

    def _call_llm(self, max_candidates: int) -> Mapping[str, Any]:
        payload = self._build_payload(max_candidates)
        manager = self._llm_manager or get_llm_manager()
        try:
            response = manager.call_dict(
                "code_evolver",
                input_payload=payload,
                max_retries=2,
            )
        except (LLMUnavailableError, LLMIntegrationError) as exc:
            raise RuntimeError(f"code_evolver LLM call failed: {exc}") from exc

        self._last_response = response
        self._record_history(response)
        return response

    def generate_candidates(self, n: int = 2) -> List[CodePatch]:
        response = self._call_llm(max(1, n))
        patches: List[CodePatch] = []
        for item in _ensure_list(response.get("patches")):
            if not isinstance(item, Mapping):
                continue
            target_id = _coerce_str(item.get("target_id") or item.get("target"))
            target = self._targets_by_id.get(target_id) or next(iter(self._targets_by_id.values()), None)
            if not target:
                continue
            patch = CodePatch.from_llm_payload(item, target)
            if patch:
                patches.append(patch)
        return patches

    def evaluate_patch(
        self,
        patch: CodePatch,
        baseline_metrics: Optional[Mapping[str, Any]] = None,
    ) -> Dict[str, Any]:
        return patch.to_report(self.repo_root)

    def serialise_patch(self, patch: CodePatch) -> Dict[str, Any]:
        return patch.serialise(self.repo_root)

    def promote_patch(self, patch_payload: Mapping[str, Any]) -> None:
        file_value = _coerce_str(patch_payload.get("file"))
        if not file_value:
            raise ValueError("file manquant pour la promotion du patch")
        path = self.repo_root / file_value
        patched_source = _coerce_str(patch_payload.get("patched_source"))
        if not patched_source:
            raise ValueError("patched_source manquant pour la promotion du patch")
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(patched_source)

    @property
    def last_response(self) -> Optional[Mapping[str, Any]]:
        return self._last_response
