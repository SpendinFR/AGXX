"""LLM-first autonomy scheduler.

Ce module supprime la chaîne heuristique historique (régressions logistiques,
EMAs adaptatives, bandits) au profit d'un unique aller-retour LLM qui produit
la micro-étape à exécuter pendant les périodes d'inactivité.  L'autonomie se
résume désormais à :

1. Collecter un instantané léger du contexte (objectif prioritaire, signaux
   disponibles sur l'architecture, propositions éventuelles).
2. Déléguer la décision complète au contrat ``autonomy_core`` via
   :func:`try_call_llm_dict`.
3. Appliquer la réponse structurée (hypothèses, tests, preuve, décision,
   progression) et journaliser le résultat.

Le but est d'assurer que l'intégralité de la stratégie d'autonomie soit
apprise/optimisée côté modèle, sans fallback heuristique.
"""

from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Optional

from AGI_Evolutive.goals.dag_store import GoalDAG
from AGI_Evolutive.reasoning.structures import (
    Evidence,
    Hypothesis,
    Test,
    episode_record,
)
from AGI_Evolutive.runtime.logger import JSONLLogger
from AGI_Evolutive.utils.llm_service import (
    LLMIntegrationError,
    LLMUnavailableError,
    get_llm_manager,
)

LOGGER = logging.getLogger(__name__)


def _coerce_float(
    value: Any,
    *,
    default: float = 0.0,
    minimum: float = 0.0,
    maximum: float = 1.0,
) -> float:
    try:
        number = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        number = default
    if number != number:  # NaN
        number = default
    return max(minimum, min(maximum, number))


def _coerce_optional_mapping(value: Any) -> Optional[Dict[str, Any]]:
    if isinstance(value, Mapping):
        return {str(k): v for k, v in value.items()}
    return None


def _ensure_mapping(value: Any) -> Dict[str, Any]:
    mapping = _coerce_optional_mapping(value)
    return mapping or {}


def _ensure_iterable_of_mappings(value: Any) -> Iterable[Mapping[str, Any]]:
    if value is None:
        return []
    if isinstance(value, Mapping):
        return [value]
    if isinstance(value, Iterable) and not isinstance(value, (str, bytes)):
        return [item for item in value if isinstance(item, Mapping)]
    return []


def _default_hypothesis(goal_id: str) -> Hypothesis:
    return Hypothesis(
        content=f"Micro-étape sur {goal_id}",
        prior=0.5,
    )


def _default_test(goal_id: str) -> Test:
    return Test(
        description=f"Identifier une action incrémentale pour {goal_id}",
        cost_est=0.1,
        expected_information_gain=0.5,
    )


def _coerce_hypotheses(value: Any, goal_id: str) -> List[Hypothesis]:
    hypotheses: List[Hypothesis] = []
    for item in _ensure_iterable_of_mappings(value):
        content = str(item.get("content") or item.get("hypothesis") or "").strip()
        if not content:
            content = f"Hypothèse sur {goal_id}"
        prior = _coerce_float(item.get("prior"), default=0.5)
        hypotheses.append(Hypothesis(content=content, prior=prior))
    if not hypotheses:
        hypotheses.append(_default_hypothesis(goal_id))
    return hypotheses


def _coerce_tests(value: Any, goal_id: str) -> List[Test]:
    tests: List[Test] = []
    for item in _ensure_iterable_of_mappings(value):
        description = str(
            item.get("description")
            or item.get("test")
            or item.get("action")
            or ""
        ).strip()
        if not description:
            description = f"Action exploratoire pour {goal_id}"
        cost_est = _coerce_float(item.get("cost_est"), default=0.15, maximum=10.0)
        info_gain = _coerce_float(
            item.get("expected_information_gain"),
            default=0.5,
        )
        tests.append(
            Test(
                description=description,
                cost_est=cost_est,
                expected_information_gain=info_gain,
            )
        )
    if not tests:
        tests.append(_default_test(goal_id))
    return tests


def _coerce_evidence(value: Any, goal_id: str) -> Evidence:
    mapping = _ensure_mapping(value)
    notes = str(mapping.get("notes") or mapping.get("summary") or "").strip()
    if not notes:
        notes = f"Synthèse LLM sur {goal_id}"
    confidence = _coerce_float(mapping.get("confidence"), default=0.6)
    return Evidence(notes=notes, confidence=confidence)


def _coerce_str(value: Any, *, default: str) -> str:
    if isinstance(value, str):
        cleaned = value.strip()
        if cleaned:
            return cleaned
    return default


def _coerce_confidence(value: Any, *, default: float = 0.6) -> float:
    return _coerce_float(value, default=default, minimum=0.0, maximum=1.0)


@dataclass
class AutonomyLLMOutcome:
    """Normalized view of the autonomy LLM payload."""

    goal_id: str
    hypotheses: List[Hypothesis]
    tests: List[Test]
    evidence: Evidence
    decision: Dict[str, Any]
    progress_step: float
    final_confidence: float
    result_text: str
    metacognition_event: Optional[Dict[str, Any]] = None
    policy_feedback: Optional[Dict[str, Any]] = None
    annotations: Dict[str, Any] = field(default_factory=dict)
    raw: MutableMapping[str, Any] = field(default_factory=dict)

    @classmethod
    def from_payload(
        cls,
        payload: Optional[Mapping[str, Any]],
        *,
        goal_id: str,
    ) -> "AutonomyLLMOutcome":
        payload = payload or {}
        if not isinstance(payload, Mapping):
            payload = {}

        hypotheses = _coerce_hypotheses(payload.get("hypotheses"), goal_id)
        tests = _coerce_tests(payload.get("tests"), goal_id)
        evidence = _coerce_evidence(payload.get("evidence"), goal_id)
        decision = _ensure_mapping(payload.get("decision"))
        if not decision:
            decision = {
                "decision": "noop",
                "reason": "llm_missing_decision",
                "confidence": 0.0,
            }

        progress_step = _coerce_float(
            payload.get("progress_step"),
            default=0.01,
            minimum=0.0,
            maximum=1.0,
        )
        final_confidence = _coerce_confidence(
            payload.get("final_confidence"),
            default=evidence.confidence,
        )
        result_text = _coerce_str(
            payload.get("result_text"),
            default=f"Autonomy update for {goal_id}",
        )

        metacognition_event = _coerce_optional_mapping(
            payload.get("metacognition_event")
        )
        policy_feedback = _coerce_optional_mapping(payload.get("policy_feedback"))
        annotations = _ensure_mapping(payload.get("annotations"))

        raw: MutableMapping[str, Any] = dict(payload)
        return cls(
            goal_id=goal_id,
            hypotheses=hypotheses,
            tests=tests,
            evidence=evidence,
            decision=decision,
            progress_step=progress_step,
            final_confidence=final_confidence,
            result_text=result_text,
            metacognition_event=metacognition_event,
            policy_feedback=policy_feedback,
            annotations=annotations,
            raw=raw,
        )


class AutonomyCore:
    """Idle autonomy scheduler relying exclusively on an LLM contract."""

    def __init__(
        self,
        arch,
        logger: JSONLLogger,
        dag: GoalDAG,
        *,
        llm_manager=None,
    ):
        self.arch = arch
        self.logger = logger
        self.dag = dag
        self.running = True
        self.thread: Optional[threading.Thread] = None
        self.idle_interval = 20  # seconds of inactivity before triggering a tick
        self._last_user_time = time.time()
        self._tick = 0
        self._llm_manager = llm_manager

    def notify_user_activity(self) -> None:
        self._last_user_time = time.time()

    def start(self) -> None:
        if self.thread and self.thread.is_alive():
            return
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()

    def stop(self) -> None:
        self.running = False

    def _loop(self) -> None:
        while self.running:
            try:
                idle_for = time.time() - self._last_user_time
                if idle_for >= self.idle_interval:
                    self.tick(idle_for=idle_for)
                    self._last_user_time = time.time()
                time.sleep(1.0)
            except Exception as exc:  # pragma: no cover - defensive logging
                self.logger.write("autonomy.error", error=str(exc))
                time.sleep(5.0)

    def tick(self, *, idle_for: Optional[float] = None) -> None:
        self._tick += 1
        goal_pick = self._normalize_goal_pick()
        goal_id = goal_pick["id"]

        proposals = self._collect_proposals()
        arch_state = self._collect_architecture_state()

        outcome = self._call_llm(goal_pick, proposals, arch_state, idle_for=idle_for)

        progress_after = self.dag.bump_progress(outcome.progress_step)
        ep = episode_record(
            user_msg="[idle]",
            hypotheses=outcome.hypotheses,
            chosen_index=0,
            tests=outcome.tests,
            evidence=outcome.evidence,
            result_text=outcome.result_text,
            final_confidence=outcome.final_confidence,
        )

        self.logger.write(
            "autonomy.tick",
            goal=goal_id,
            goal_state=goal_pick,
            proposals=proposals,
            arch_state=arch_state,
            episode=ep,
            decision=outcome.decision,
            annotations=outcome.annotations,
            llm_payload=outcome.raw,
            progress_before=goal_pick.get("progress"),
            progress_after=progress_after,
        )

        self._apply_metacognition(outcome)
        self._apply_policy_feedback(outcome)

    # ------------------------------------------------------------------
    # Payload construction helpers

    def _normalize_goal_pick(self) -> Dict[str, Any]:
        try:
            pick = self.dag.choose_next_goal() or {}
        except Exception as exc:  # pragma: no cover - defensive logging
            self.logger.write("autonomy.warn", stage="dag_choose", error=str(exc))
            pick = {}

        goal_id = _coerce_str(pick.get("id"), default="unknown_goal")
        evi = _coerce_float(pick.get("evi"), default=0.0, minimum=0.0, maximum=1.0)
        progress = _coerce_float(
            pick.get("progress"),
            default=0.0,
            minimum=0.0,
            maximum=1.0,
        )
        normalized = {
            "id": goal_id,
            "evi": evi,
            "progress": progress,
        }
        for key in ("label", "description", "priority"):
            if key in pick:
                normalized[key] = pick[key]
        return normalized

    def _collect_proposals(self) -> List[Dict[str, Any]]:
        proposer = getattr(self.arch, "proposer", None)
        if not proposer or not hasattr(proposer, "run_once_now"):
            return []
        try:
            raw = proposer.run_once_now() or []
        except Exception as exc:  # pragma: no cover - best effort
            self.logger.write("autonomy.warn", stage="proposer", error=str(exc))
            return []
        proposals: List[Dict[str, Any]] = []
        if isinstance(raw, Mapping):
            raw = [raw]
        if isinstance(raw, Iterable):
            for item in raw:
                if isinstance(item, Mapping):
                    proposals.append({str(k): v for k, v in item.items()})
        return proposals

    def _collect_architecture_state(self) -> Dict[str, Any]:
        state: Dict[str, Any] = {
            "tick": self._tick,
        }
        kernel_state = getattr(self.arch, "phenomenal_kernel_state", None)
        if isinstance(kernel_state, Mapping):
            state["phenomenal_kernel_state"] = dict(kernel_state)
        planner = getattr(self.arch, "planner", None)
        if planner and hasattr(planner, "status"):
            try:
                state["planner_status"] = planner.status
            except Exception:  # pragma: no cover
                state["planner_status"] = None
        memory = getattr(self.arch, "memory", None)
        if memory and hasattr(memory, "get_recent_memories"):
            try:
                recent = memory.get_recent_memories(n=5)
                if isinstance(recent, list):
                    state["recent_memories"] = [
                        item for item in recent if isinstance(item, Mapping)
                    ][:5]
            except Exception:  # pragma: no cover
                state["recent_memories"] = []
        homeo = getattr(self.arch, "homeostasis", None) or getattr(
            self.arch, "homeo", None
        )
        if homeo and hasattr(homeo, "status_snapshot"):
            try:
                snapshot = homeo.status_snapshot()
                if isinstance(snapshot, Mapping):
                    state["homeostasis"] = dict(snapshot)
            except Exception:  # pragma: no cover
                state["homeostasis"] = None
        return state

    def _call_llm(
        self,
        goal: Mapping[str, Any],
        proposals: List[Mapping[str, Any]],
        arch_state: Mapping[str, Any],
        *,
        idle_for: Optional[float],
    ) -> AutonomyLLMOutcome:
        payload = {
            "goal": dict(goal),
            "proposals": list(proposals),
            "arch_state": dict(arch_state),
        }
        if idle_for is not None:
            payload["idle_seconds"] = float(idle_for)

        manager = self._llm_manager or get_llm_manager()
        try:
            response = manager.call_dict(
                "autonomy_core",
                input_payload=payload,
                max_retries=2,
            )
        except (LLMUnavailableError, LLMIntegrationError) as exc:
            raise RuntimeError(f"autonomy_core LLM call failed: {exc}") from exc

        return AutonomyLLMOutcome.from_payload(response, goal_id=goal.get("id", "?"))

    # ------------------------------------------------------------------
    # Post-processing

    def _apply_metacognition(self, outcome: AutonomyLLMOutcome) -> None:
        if not outcome.metacognition_event:
            return
        metacog = getattr(self.arch, "metacognition", None)
        if not metacog or not hasattr(metacog, "_record_metacognitive_event"):
            return
        event = dict(outcome.metacognition_event)
        try:  # pragma: no cover - depends on runtime integrations
            metacog._record_metacognitive_event(**event)
        except Exception as exc:
            self.logger.write("autonomy.warn", stage="metacognition", error=str(exc))

    def _apply_policy_feedback(self, outcome: AutonomyLLMOutcome) -> None:
        policy = getattr(self.arch, "policy", None)
        if not policy or not hasattr(policy, "register_outcome"):
            return
        feedback = outcome.policy_feedback
        if not feedback:
            feedback = outcome.decision.get("policy_feedback")
            if isinstance(feedback, Mapping):
                feedback = dict(feedback)
        if not isinstance(feedback, Mapping):
            return
        proposal = feedback.get("proposal")
        success = bool(feedback.get("success", False))
        try:  # pragma: no cover - depends on runtime integrations
            policy.register_outcome(proposal, success)
        except Exception as exc:
            self.logger.write("autonomy.warn", stage="policy_feedback", error=str(exc))

