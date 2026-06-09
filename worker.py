import os
import time
import uuid
import requests
import traceback

from tron.serializer import deserialize

TRON_URL = os.environ.get("TRON_URL", "http://127.0.0.1:9000")
WORKER_NAME = os.environ.get("TRON_WORKER_NAME", f"worker-{uuid.uuid4().hex[:8]}")


def register_worker():
    payload = {
        "name": WORKER_NAME,
        "gpu": False,
        "memory_gb": 2,
    }
    try:
        resp = requests.post(f"{TRON_URL}/register_worker", json=payload, timeout=10)
        resp.raise_for_status()
        print(f"[WORKER] Registered {WORKER_NAME} with TRON server")
    except Exception as exc:
        print(f"[WORKER] Failed to register worker: {exc}")
        raise


def heartbeat():
    try:
        requests.post(f"{TRON_URL}/heartbeat/{WORKER_NAME}", timeout=5)
    except Exception:
        pass


def fetch_next_job():
    try:
        resp = requests.get(f"{TRON_URL}/next_job/{WORKER_NAME}", timeout=10)
        resp.raise_for_status()
        data = resp.json()
        return data.get("job")
    except Exception as exc:
        print(f"[WORKER] next_job failed: {exc}")
        return None


def report_complete(job_id, result):
    try:
        resp = requests.post(f"{TRON_URL}/complete/{job_id}", json={"result": result}, timeout=10)
        resp.raise_for_status()
        print(f"[WORKER] Completed job {job_id}")
    except Exception as exc:
        print(f"[WORKER] Failed to report completion for {job_id}: {exc}")


def execute_job(job):
    try:
        function_blob = job.get("function")
        if function_blob is None:
            raise ValueError("Missing serialized function payload")

        func, args, kwargs = deserialize(function_blob)
        print(f"[WORKER] Executing job {job['id']} func={func.__name__}")
        result = func(*args, **kwargs)
        return result
    except Exception as exc:
        traceback.print_exc()
        return {"status": "error", "error": str(exc)}


def main():
    register_worker()
    print(f"[WORKER] Starting polling loop for jobs on {TRON_URL}")
    while True:
        try:
            job = fetch_next_job()
            if job:
                job_id = job.get("id")
                result = execute_job(job)
                report_complete(job_id, result)
            else:
                heartbeat()
                time.sleep(1)
        except KeyboardInterrupt:
            print("[WORKER] Shutting down")
            break
        except Exception as exc:
            print(f"[WORKER] Polling error: {exc}")
            time.sleep(2)


if __name__ == "__main__":
    main()
