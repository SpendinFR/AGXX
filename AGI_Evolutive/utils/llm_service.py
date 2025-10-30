"""Service layer to orchestrate repository-wide LLM integrations."""
from __future__ import annotations

import logging
import os
import threading
import time
from collections import deque
from dataclasses import dataclass
from typing import Any, Mapping, MutableMapping, Optional, Sequence

try:  # pragma: no cover - platform guard
    import ctypes
except Exception:  # pragma: no cover - environment without ctypes support
    ctypes = None

from itertools import islice

from .llm_client import LLMCallError, LLMResult, OllamaLLMClient, OllamaModelConfig
from .llm_specs import LLMIntegrationSpec, get_spec


_module_logger = logging.getLogger(__name__)


def _env_flag(name: str, *, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    normalized = value.strip().lower()
    if normalized in {"", "0", "false", "no", "off"}:
        return False
    if normalized in {"1", "true", "yes", "on"}:
        return True
    return default




def _llm_env_enabled() -> bool:
    """Resolve the current LLM availability from the environment."""

    return _env_flag("AGI_ENABLE_LLM") and not _env_flag("AGI_DISABLE_LLM")


_DEFAULT_ENABLED = _llm_env_enabled()


class LLMIntegrationError(RuntimeError):
    """Raised when the structured LLM integration fails."""


class LLMUnavailableError(LLMIntegrationError):
    """Raised when LLM integration is disabled or unavailable."""


class LLMPreempted(LLMIntegrationError):
    """Raised internally when a background LLM call is interrupted."""


@dataclass
class LLMInvocation:
    """Encapsulate the result of one integration call."""

    spec: LLMIntegrationSpec
    result: LLMResult


@dataclass(frozen=True)
class LLMCallRecord:
    """Trace the outcome of an integration attempt for diagnostics."""

    spec_key: str
    status: str
    timestamp: float
    message: Optional[str] = None


_ACTIVITY_LOG: deque[LLMCallRecord] = deque(maxlen=200)


_JOB_MANAGER_BINDING_LOCK = threading.Lock()
_JOB_MANAGER_BINDING: Optional[Any] = None
_ACTIVE_LLM_CALLS_LOCK = threading.Lock()
_ACTIVE_LLM_CALLS: dict[int, dict[str, Any]] = {}


def _record_activity(spec_key: str, status: str, message: Optional[str] = None) -> None:
    try:
        _ACTIVITY_LOG.appendleft(
            LLMCallRecord(
                spec_key=spec_key,
                status=status,
                timestamp=time.time(),
                message=message.strip() if isinstance(message, str) else message,
            )
        )
    except Exception:  # pragma: no cover - defensive guard for diagnostics
        pass


def bind_job_manager(job_manager: Optional[Any]) -> None:
    """Expose the shared job manager so LLM calls can respect urgent contexts."""

    with _JOB_MANAGER_BINDING_LOCK:
        global _JOB_MANAGER_BINDING
        _JOB_MANAGER_BINDING = job_manager


def _get_bound_job_manager() -> Optional[Any]:
    with _JOB_MANAGER_BINDING_LOCK:
        return _JOB_MANAGER_BINDING


def _register_active_llm_call(spec_key: str, *, urgent: bool) -> None:
    ident = threading.get_ident()
    with _ACTIVE_LLM_CALLS_LOCK:
        _ACTIVE_LLM_CALLS[ident] = {"spec": spec_key, "urgent": urgent}


def _unregister_active_llm_call() -> None:
    ident = threading.get_ident()
    with _ACTIVE_LLM_CALLS_LOCK:
        _ACTIVE_LLM_CALLS.pop(ident, None)


def _raise_async_exception(thread_id: int, exc_type: type[BaseException]) -> bool:
    if ctypes is None or thread_id is None:
        return False
    try:
        result = ctypes.pythonapi.PyThreadState_SetAsyncExc(
            ctypes.c_long(thread_id), ctypes.py_object(exc_type)
        )
    except Exception:
        return False
    if result == 0:
        return False
    if result > 1:
        try:
            ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(thread_id), None)
        except Exception:
            pass
        return False
    return True


def preempt_background_llm_calls() -> int:
    """Interrupt non-urgent LLM calls in progress.

    Returns the number of threads that received a preemption signal.
    """

    with _ACTIVE_LLM_CALLS_LOCK:
        targets = [
            (ident, data)
            for ident, data in _ACTIVE_LLM_CALLS.items()
            if not data.get("urgent")
        ]
    preempted = 0
    for ident, _ in targets:
        if _raise_async_exception(ident, LLMPreempted):
            preempted += 1
    return preempted


def get_recent_llm_activity(limit: int = 20) -> Sequence[LLMCallRecord]:
    """Return the most recent integration attempts for observability."""

    if limit is None or limit <= 0:
        limit = len(_ACTIVITY_LOG)
    return tuple(islice(_ACTIVITY_LOG, 0, limit))


class LLMIntegrationManager:
    """Coordinates prompt construction and model selection for integrations."""

    def __init__(
        self,
        *,
        client: Optional[OllamaLLMClient] = None,
        model_configs: Optional[Mapping[str, OllamaModelConfig]] = None,
        enabled: Optional[bool] = None,
    ) -> None:
        self._client = client or OllamaLLMClient()
        self._enabled = _llm_env_enabled() if enabled is None else bool(enabled)
        self._model_configs: MutableMapping[str, OllamaModelConfig] = dict(model_configs or {})
        self._lock = threading.Lock()

    @property
    def enabled(self) -> bool:
        return self._enabled

    def set_enabled(self, value: bool) -> None:
        self._enabled = bool(value)

    def call_json(
        self,
        spec_key: str,
        *,
        input_payload: Any | None = None,
        extra_instructions: Optional[Sequence[str]] = None,
        max_retries: int = 1,
    ) -> LLMInvocation:
        if not self._enabled:
            raise LLMUnavailableError("LLM integration is disabled")

        spec = get_spec(spec_key)
        instructions: list[str] = list(spec.extra_instructions)
        if extra_instructions:
            instructions.extend(instr.strip() for instr in extra_instructions if instr and instr.strip())
        instructions.append("Si tu n'es pas certain, explique l'incertitude dans le champ 'notes'.")

        try:
            result = self._client.generate_json(
                self._resolve_model(spec.preferred_model),
                spec.prompt_goal,
                input_data=input_payload,
                extra_instructions=instructions,
                example_output=spec.example_output,
                max_retries=max_retries,
            )
        except LLMCallError as exc:  # pragma: no cover - delegated to integration error
            raise LLMIntegrationError(f"LLM call failed for spec '{spec_key}': {exc}") from exc

        return LLMInvocation(spec=spec, result=result)

    def call_dict(
        self,
        spec_key: str,
        *,
        input_payload: Any | None = None,
        extra_instructions: Optional[Sequence[str]] = None,
        max_retries: int = 1,
    ) -> Mapping[str, Any]:
        invocation = self.call_json(
            spec_key,
            input_payload=input_payload,
            extra_instructions=extra_instructions,
            max_retries=max_retries,
        )
        parsed = invocation.result.parsed
        if not isinstance(parsed, Mapping):
            raise LLMIntegrationError(
                f"Spec '{spec_key}' returned a non-mapping payload: {type(parsed).__name__}"
            )
        return parsed

    def _resolve_model(self, model_name: str) -> OllamaModelConfig:
        with self._lock:
            if model_name not in self._model_configs:
                self._model_configs[model_name] = OllamaModelConfig(name=model_name)
            return self._model_configs[model_name]


_default_manager: Optional[LLMIntegrationManager] = None
_default_lock = threading.Lock()


def get_llm_manager() -> LLMIntegrationManager:
    global _default_manager
    with _default_lock:
        if _default_manager is None:
            _default_manager = LLMIntegrationManager()
        return _default_manager


def set_llm_manager(manager: Optional[LLMIntegrationManager]) -> None:
    global _default_manager
    with _default_lock:
        _default_manager = manager


def is_llm_enabled() -> bool:
    manager = _default_manager
    if manager is not None:
        return manager.enabled
    return _llm_env_enabled()


def try_call_llm_dict(
    spec_key: str,
    *,
    input_payload: Any | None = None,
    extra_instructions: Optional[Sequence[str]] = None,
    logger: Optional[Any] = None,
    max_retries: int = 1,
) -> Optional[Mapping[str, Any]]:
    """Attempt to call the shared LLM and return a mapping payload.

    The helper centralises the common guard/exception handling logic used by the
    individual modules so they can focus on crafting the structured payload
    without duplicating availability checks.  When the LLM is disabled or the
    integration fails, ``None`` is returned to signal the caller to fall back to
    heuristics.
    """

    log = logger or _module_logger
    thread = threading.current_thread()
    thread_name = thread.name or "Thread"
    thread_identifier = f"{thread_name}#{thread.ident}" if thread.ident is not None else thread_name

    job_manager = _get_bound_job_manager()
    wait_after_call = False
    thread_is_urgent = False
    if job_manager is not None:
        try:
            thread_is_urgent = bool(job_manager.current_thread_is_urgent())
        except Exception:
            thread_is_urgent = False
        if not thread_is_urgent:
            wait_after_call = True
            wait_deadline = time.perf_counter() + 60.0
            notified = False
            while True:
                try:
                    cleared = job_manager.wait_for_urgent_clear(timeout=0.1)
                except Exception:
                    break
                if cleared:
                    break
                if not notified:
                    try:
                        log.debug(
                            "LLM spec '%s' en pause : travail urgent en cours – thread %s",
                            spec_key,
                            thread_identifier,
                        )
                    except Exception:
                        pass
                    notified = True
                if time.perf_counter() >= wait_deadline:
                    break

    if not is_llm_enabled():
        _record_activity(spec_key, "disabled", "LLM integration désactivée")
        try:
            log.info(
                "LLM spec '%s' ignorée : LLM désactivé – thread %s",
                spec_key,
                thread_identifier,
            )
        except Exception:  # pragma: no cover - defensive logging guard
            pass
        return None

    total_start = time.perf_counter()
    _register_active_llm_call(spec_key, urgent=thread_is_urgent)
    try:
        manager = get_llm_manager()
        call_start = time.perf_counter()
        payload = manager.call_dict(
            spec_key,
            input_payload=input_payload,
            extra_instructions=extra_instructions,
            max_retries=max_retries,
        )
        call_elapsed = time.perf_counter() - call_start
        total_elapsed = time.perf_counter() - total_start
        waited_for_clear = False
        if wait_after_call and job_manager is not None and not thread_is_urgent:
            try:
                waited_for_clear = job_manager.wait_for_urgent_clear(timeout=60.0)
            except Exception:
                waited_for_clear = False
        _record_activity(spec_key, "success", None)
        try:
            if waited_for_clear:
                log.debug(
                    "LLM spec '%s' reprise après fenêtre urgente – thread %s",
                    spec_key,
                    thread_identifier,
                )
            log.info(
                "LLM spec '%s' terminée avec succès en %.2fs (appel %.2fs) – thread %s",
                spec_key,
                total_elapsed,
                call_elapsed,
                thread_identifier,
            )
        except Exception:  # pragma: no cover - defensive logging guard
            pass
        return payload
    except (LLMUnavailableError, LLMIntegrationError) as exc:
        total_elapsed = time.perf_counter() - total_start
        _record_activity(spec_key, "error", str(exc))
        try:
            log.warning(
                "LLM spec '%s' en échec après %.2fs : %s – thread %s",
                spec_key,
                total_elapsed,
                exc,
                thread_identifier,
                exc_info=True,
            )
        except Exception:  # pragma: no cover - defensive logging guard
            pass
        return None
    except LLMPreempted:
        _record_activity(spec_key, "cancelled", "preempted by urgent context")
        try:
            log.info(
                "LLM spec '%s' annulée : préemption urgente – thread %s",
                spec_key,
                thread_identifier,
            )
        except Exception:
            pass
        raise
    except Exception as exc:  # pragma: no cover - unexpected failure safety net
        total_elapsed = time.perf_counter() - total_start
        _record_activity(spec_key, "error", str(exc))
        try:
            log.error(
                "Erreur inattendue lors de la spec LLM '%s' après %.2fs : %s – thread %s",
                spec_key,
                total_elapsed,
                exc,
                thread_identifier,
                exc_info=True,
            )
        except Exception:
            pass
        return None
    finally:
        _unregister_active_llm_call()


__all__ = [
    "LLMIntegrationError",
    "LLMIntegrationManager",
    "LLMInvocation",
    "LLMCallRecord",
    "LLMUnavailableError",
    "LLMPreempted",
    "bind_job_manager",
    "get_llm_manager",
    "get_recent_llm_activity",
    "is_llm_enabled",
    "preempt_background_llm_calls",
    "set_llm_manager",
    "try_call_llm_dict",
]
