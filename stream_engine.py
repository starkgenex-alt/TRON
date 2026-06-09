import time
import queue

class StreamEngine:
    def __init__(self):
        # map job_id -> Queue of events
        self._events = {}

    def emit(self, job_id, event_type, data=None):
        q = self._events.setdefault(job_id, queue.Queue())
        q.put({"type": event_type, "data": data or {}, "time": time.time()})

    def stream_generator(self, job_id, timeout=60):
        q = self._events.setdefault(job_id, queue.Queue())
        # yield existing events first
        while True:
            try:
                ev = q.get(timeout=0.5)
                yield f"data: {ev}\n\n"
            except Exception:
                # no new events; break to avoid infinite loop in tests
                break

    def get(self, job_id):
        q = self._events.setdefault(job_id, queue.Queue())
        events = []
        while not q.empty():
            events.append(q.get())
        return events

