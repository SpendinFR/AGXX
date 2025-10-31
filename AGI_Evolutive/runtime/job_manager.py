"""LLM-backed job manager orchestrating interactive and background work."""

from __future__ import annotations

import collections
import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Deque, Dict, Iterable, Mapping, MutableMapping, Optional

from AGI_Evolutive.utils.jsonsafe import json_sanitize
from AGI_Evolutive.utils.llm_service import (
    LLMIntegrationError,
    LLMUnavailableError,
    get_llm_manager,
)


@dataclass
class JobRecord:
    id: str
    kind: str
    queue: str
    fn: Callable[["JobContext", Mapping[str, Any]], Any]
    args: Mapping[str, Any]
    priority: float
    requested_queue: str
    urgent: bool
    key: str | None
    timeout_s: float | None
    created_ts: float = field(default_factory=time.time)
    started_ts: float = 0.0
    finished_ts: float = 0.0
    status: str = "queued"
    result: Any = None
    error: str | None = None
    llm_notes: Mapping[str, Any] | None = None
    progress: float = 0.0

    def as_payload(self) -> Mapping[str, Any]:
        return {
            "job_id": self.id,
            "kind": self.kind,
            "queue": self.queue,
            "priority": self.priority,
            "urgent": self.urgent,
            "age": time.time() - self.created_ts,
            "requested_queue": self.requested_queue,
            "status": self.status,
        }


class JobContext:
    def __init__(self, manager: "JobManager", job_id: str) -> None:
        self._manager = manager
        self._job_id = job_id

    def update_progress(self, value: float) -> None:
        self._manager._update_progress(self._job_id, max(0.0, min(1.0, float(value))))

    def cancelled(self) -> bool:
        return self._manager._is_cancelled(self._job_id)


class JobManager:
    """Simple LLM-guided priority queue for runtime jobs."""

    def __init__(
        self,
        arch: Any | None,
        data_dir: str = "data",
        *,
        llm_manager: Any | None = None,
        interactive_workers: int = 1,
        background_workers: int = 2,
    ) -> None:
        self.arch = arch
        self.data_dir = data_dir
        self.llm_manager = llm_manager or get_llm_manager()
        self.spec_key = "runtime_job_manager"
        self.idle_sleep = 0.4
        self.budgets: Dict[str, Dict[str, int]] = {
            "interactive": {"max_running": max(1, int(interactive_workers))},
            "background": {"max_running": max(1, int(background_workers))},
        }

        self._lock = threading.RLock()
        self._jobs: Dict[str, JobRecord] = {}
        self._queues: Dict[str, list[str]] = {"interactive": [], "background": []}
        self._key_map: Dict[str, str] = {}
        self._cancelled: set[str] = set()
        self._running_counts: Dict[str, int] = {"interactive": 0, "background": 0}
        self._completions: Deque[Mapping[str, Any]] = collections.deque(maxlen=256)
        self._history: Deque[Mapping[str, Any]] = collections.deque(maxlen=200)
        self._running = True

        self._workers: list[threading.Thread] = []
        for queue in ("interactive", "background"):
            worker = threading.Thread(target=self._worker_loop, args=(queue,), daemon=True)
            worker.start()
            self._workers.append(worker)

    # ------------------------------------------------------------------
    def submit(
        self,
        *,
        kind: str,
        fn: Callable[[JobContext, Mapping[str, Any]], Any],
        args: Optional[Mapping[str, Any]] = None,
        queue: str = "background",
        priority: float = 0.5,
        key: str | None = None,
        timeout_s: float | None = None,
        urgent: bool | None = None,
    ) -> str:
        args = dict(args or {})
        priority = max(0.0, min(1.0, float(priority)))
        requested_queue = "interactive" if queue == "interactive" else "background"
        urgent = bool(urgent) if urgent is not None else False
        assigned_queue = "interactive" if urgent or requested_queue == "interactive" else "background"

        with self._lock:
            if key and key in self._key_map:
                existing_id = self._key_map[key]
                job = self._jobs.get(existing_id)
                if job and job.status in {"queued", "running"}:
                    return existing_id

            job_id = str(uuid.uuid4())
            record = JobRecord(
                id=job_id,
                kind=kind,
                queue=assigned_queue,
                fn=fn,
                args=args,
                priority=priority,
                requested_queue=requested_queue,
                urgent=urgent,
                key=key,
                timeout_s=timeout_s,
            )
            self._jobs[job_id] = record
            self._queues[assigned_queue].append(job_id)
            if key:
                self._key_map[key] = job_id
        return job_id

    # ------------------------------------------------------------------
    def poll_completed(self, limit: int = 16) -> list[Mapping[str, Any]]:
        items: list[Mapping[str, Any]] = []
        with self._lock:
            while self._completions and len(items) < max(1, int(limit)):
                items.append(self._completions.popleft())
        return items

    # ------------------------------------------------------------------
    def drain_to_memory(self, memory: Any | None) -> int:
        drained = 0
        for completion in self.poll_completed(64):
            drained += 1
            if memory is None or not hasattr(memory, "add_memory"):
                continue
            try:
                memory.add_memory(
                    {
                        "kind": "job_completion",
                        "job_id": completion.get("job_id"),
                        "status": completion.get("status"),
                        "result": completion.get("result"),
                        "error": completion.get("error"),
                        "queue": completion.get("queue"),
                        "duration": completion.get("duration"),
                        "llm": completion.get("llm_notes"),
                    }
                )
            except Exception:
                continue
        return drained

    # ------------------------------------------------------------------
    def is_low_load(self) -> bool:
        with self._lock:
            queued = sum(len(ids) for ids in self._queues.values())
            running = sum(self._running_counts.values())
        return queued + running < 2

    # ------------------------------------------------------------------
    def shutdown(self, wait: bool = True) -> None:
        self._running = False
        if wait:
            for worker in self._workers:
                if worker.is_alive():
                    worker.join(timeout=1.0)

    # ------------------------------------------------------------------
    def _worker_loop(self, queue: str) -> None:
        while self._running:
            job = self._select_job(queue)
            if job is None:
                time.sleep(self.idle_sleep)
                continue
            self._execute_job(job)

    # ------------------------------------------------------------------
    def _select_job(self, queue: str) -> JobRecord | None:
        with self._lock:
            budget = self.budgets.get(queue, {}).get("max_running", 1)
            if self._running_counts[queue] >= budget:
                return None
            candidates = [
                self._jobs[jid]
                for jid in list(self._queues[queue])
                if self._jobs.get(jid) and self._jobs[jid].status == "queued"
            ][:10]
        if not candidates:
            return None

        payload = {
            "queue": queue,
            "jobs": [candidate.as_payload() for candidate in candidates],
            "history": list(self._history),
            "budgets": {name: info.get("max_running", 1) for name, info in self.budgets.items()},
        }
        try:
            response = self.llm_manager.call_dict(
                self.spec_key,
                input_payload=json_sanitize(payload),
            )
        except (LLMUnavailableError, LLMIntegrationError):
            return None

        selected_id = self._extract_job_id(response, candidates)
        if selected_id is None:
            self._fail_job(candidates[0], "llm_missing_selection")
            return None

        with self._lock:
            job = self._jobs.get(selected_id)
            if job is None or job.status != "queued":
                return None
            job.status = "running"
            job.started_ts = time.time()
            job.llm_notes = self._extract_job_notes(response, selected_id)
            if selected_id in self._queues[queue]:
                self._queues[queue].remove(selected_id)
            self._running_counts[queue] += 1
        return job

    # ------------------------------------------------------------------
    def _execute_job(self, job: JobRecord) -> None:
        context = JobContext(self, job.id)
        try:
            result = job.fn(context, dict(job.args))
            status = "done"
            error = None
        except Exception as exc:
            result = None
            status = "error"
            error = str(exc)
        finally:
            with self._lock:
                job.status = status
                job.finished_ts = time.time()
                job.result = result
                job.error = error
                job.progress = 1.0 if status == "done" else job.progress
                self._running_counts[job.queue] = max(0, self._running_counts[job.queue] - 1)
                completion = self._completion_payload(job)
                self._completions.append(completion)
                self._history.append({
                    "job_id": job.id,
                    "queue": job.queue,
                    "status": status,
                    "llm": job.llm_notes or {},
                })

    # ------------------------------------------------------------------
    def _completion_payload(self, job: JobRecord) -> Mapping[str, Any]:
        duration = job.finished_ts - job.started_ts if job.finished_ts and job.started_ts else None
        return {
            "job_id": job.id,
            "kind": job.kind,
            "queue": job.queue,
            "status": job.status,
            "result": job.result,
            "error": job.error,
            "duration": duration,
            "llm_notes": job.llm_notes or {},
            "created_ts": job.created_ts,
            "started_ts": job.started_ts,
            "finished_ts": job.finished_ts,
        }

    # ------------------------------------------------------------------
    def _extract_job_id(
        self,
        response: Mapping[str, Any] | None,
        candidates: Iterable[JobRecord],
    ) -> str | None:
        if not isinstance(response, Mapping):
            return None
        prioritized = response.get("prioritized_jobs")
        if isinstance(prioritized, list):
            candidate_ids = {candidate.id for candidate in candidates}
            for item in prioritized:
                if isinstance(item, Mapping):
                    job_id = item.get("job_id")
                    if isinstance(job_id, str) and job_id in candidate_ids:
                        return job_id
        return None

    # ------------------------------------------------------------------
    def _extract_job_notes(
        self,
        response: Mapping[str, Any] | None,
        job_id: str,
    ) -> Mapping[str, Any] | None:
        if not isinstance(response, Mapping):
            return None
        prioritized = response.get("prioritized_jobs")
        if isinstance(prioritized, list):
            for item in prioritized:
                if isinstance(item, Mapping) and item.get("job_id") == job_id:
                    return {k: v for k, v in item.items() if k != "job_id"}
        return None

    # ------------------------------------------------------------------
    def _fail_job(self, job: JobRecord, reason: str) -> None:
        with self._lock:
            job.status = "error"
            job.error = reason
            job.finished_ts = time.time()
            if job.id in self._queues[job.queue]:
                self._queues[job.queue].remove(job.id)
            self._completions.append(self._completion_payload(job))

    # ------------------------------------------------------------------
    def _update_progress(self, job_id: str, progress: float) -> None:
        with self._lock:
            job = self._jobs.get(job_id)
            if job and job.status == "running":
                job.progress = progress

    # ------------------------------------------------------------------
    def _is_cancelled(self, job_id: str) -> bool:
        with self._lock:
            return job_id in self._cancelled

    # ------------------------------------------------------------------
    def cancel(self, job_id: str) -> bool:
        with self._lock:
            job = self._jobs.get(job_id)
            if job and job.status == "queued":
                job.status = "cancelled"
                job.finished_ts = time.time()
                if job_id in self._queues[job.queue]:
                    self._queues[job.queue].remove(job_id)
                self._cancelled.add(job_id)
                self._completions.append(self._completion_payload(job))
                return True
        return False
