import json
import logging
import os
import threading
import time
from collections import deque
from typing import Optional

from AGI_Evolutive.utils.jsonsafe import json_sanitize
from AGI_Evolutive.utils.llm_service import try_call_llm_dict


LOGGER = logging.getLogger(__name__)


class Telemetry:
    def __init__(self, maxlen=2000):
        self.events = deque(maxlen=maxlen)
        self._jsonl_path = None
        self._console = False
        self._job_manager = None
        self._annotation_lock = threading.Lock()

    def enable_jsonl(self, path="logs/events.jsonl"):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self._jsonl_path = path

    def enable_console(self, on=True):
        self._console = bool(on)

    def bind_job_manager(self, job_manager) -> None:
        """Bind a job manager so annotations can be deferred when urgent."""

        self._job_manager = job_manager

    def log(self, event_type, subsystem, data=None, level="info"):
        e = {
            "ts": time.time(),
            "type": event_type,
            "subsystem": subsystem,
            "level": level,
            "data": data or {}
        }
        annotation = None
        jm = getattr(self, "_job_manager", None)
        defer_annotation = False
        if jm is not None:
            try:
                defer_annotation = bool(jm.has_urgent())
                if not defer_annotation and hasattr(jm, "has_urgent_context"):
                    defer_annotation = bool(jm.has_urgent_context())
            except Exception:
                defer_annotation = False
        if not defer_annotation:
            try:
                annotation = self._llm_annotate(e)
            except Exception as exc:  # pragma: no cover - defensive guard
                LOGGER.debug("LLM annotation failed: %s", exc, exc_info=True)
                annotation = None
        if annotation:
            e["llm_annotation"] = annotation
        self.events.append(e)
        # disque
        if self._jsonl_path:
            try:
                with open(self._jsonl_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(json_sanitize(e), ensure_ascii=False) + "\n")
            except Exception:
                pass
        if defer_annotation:
            self._enqueue_annotation(e)
        # console légère
        if self._console and level in ("info", "warn", "error"):
            ts = time.strftime("%H:%M:%S", time.localtime(e["ts"]))
            print(f"[{ts}] {subsystem}/{level} {event_type} :: {e['data']}")

    def tail(self, n=50):
        return list(self.events)[-max(0, n):]

    def snapshot(self):
        by_sub = {}
        for e in self.events:
            by_sub[e["subsystem"]] = by_sub.get(e["subsystem"], 0) + 1
        return {"events_count": len(self.events), "events_by_subsystem": by_sub}

    def _llm_annotate(self, event: dict) -> Optional[dict]:
        response = try_call_llm_dict(
            "telemetry_annotation",
            input_payload=event,
            logger=LOGGER,
            max_retries=0,
        )
        if not response:
            return None
        summary = response.get("summary")
        severity = response.get("severity")
        if not isinstance(summary, str):
            return None
        if severity is not None and not isinstance(severity, str):
            severity = None
        return {
            "event_id": response.get("event_id", ""),
            "summary": summary,
            "severity": severity,
            "routine": bool(response.get("routine", False)),
            "notes": response.get("notes", ""),
        }

    # ------------------------------------------------------------------
    # Deferred annotation handling
    def _enqueue_annotation(self, event: dict) -> None:
        jm = getattr(self, "_job_manager", None)
        if jm is None:
            return
        try:
            jm.submit(
                kind="telemetry_annotation",
                fn=self._annotation_job,
                args={"event": event},
                queue="background",
                priority=0.35,
                urgent=False,
            )
        except Exception as exc:  # pragma: no cover - defensive guard
            LOGGER.debug("Failed to enqueue telemetry annotation: %s", exc, exc_info=True)

    def _annotation_job(self, ctx, args):
        event = args.get("event") if isinstance(args, dict) else None
        if not isinstance(event, dict):
            return None
        try:
            annotation = self._llm_annotate(event)
        except Exception as exc:  # pragma: no cover - defensive guard
            LOGGER.debug("Deferred telemetry annotation failed: %s", exc, exc_info=True)
            return None
        if annotation:
            self._attach_annotation(event, annotation)
        return annotation

    def _attach_annotation(self, event: dict, annotation: dict) -> None:
        with self._annotation_lock:
            event["llm_annotation"] = annotation
            path = self._jsonl_path
            if not path:
                return
            payload = {
                "ts": time.time(),
                "type": "telemetry_annotation_update",
                "subsystem": event.get("subsystem"),
                "level": event.get("level"),
                "data": {
                    "event_ts": event.get("ts"),
                    "annotation": json_sanitize(annotation),
                },
            }
            try:
                with open(path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(json_sanitize(payload), ensure_ascii=False) + "\n")
            except Exception:
                pass
