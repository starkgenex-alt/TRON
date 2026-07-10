"""Lightweight TRON worker daemon for remote nodes in DePIN."""
from __future__ import annotations

import argparse
import os
import sys
import time
import json
import threading
from pathlib import Path
from typing import Any, Dict, Optional

import requests

DEFAULT_MASTER_URL = "http://localhost:9000"
HEARTBEAT_INTERVAL = 10.0
JOB_POLL_INTERVAL = 5.0


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="TRON worker daemon for DePIN")
    parser.add_argument("--master-url", default=os.environ.get("TRON_MASTER_URL", DEFAULT_MASTER_URL), help="Master scheduler URL")
    parser.add_argument("--name", default=os.environ.get("TRON_WORKER_NAME", "tron-worker"), help="Worker name")
    parser.add_argument("--gpu", action="store_true", help="Expose GPU capability")
    parser.add_argument("--memory-gb", type=float, default=8.0, help="Available memory in GB")
    parser.add_argument("--location", default="unknown", help="Worker location or tag")
    parser.add_argument("--auth-token", default=os.environ.get("TRON_WORKER_AUTH_TOKEN"), help="Pre-existing auth token")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    return parser.parse_args(argv)


def build_headers(auth_token: str) -> Dict[str, str]:
    return {"X-TRON-AUTH": auth_token}


def register_worker(master_url: str, name: str, capabilities: Dict[str, Any], location: str, auth_token: Optional[str]) -> str:
    url = f"{master_url.rstrip('/')}/register"
    payload = {
        "name": name,
        "capabilities": capabilities,
        "location": location,
        "metadata": {"platform": sys.platform},
    }
    response = requests.post(url, json=payload, timeout=10)
    response.raise_for_status()
    data = response.json()
    if auth_token and data.get("auth_token") != auth_token:
        # If auth token was passed in, accept the registered auth token for simplicity.
        return data["auth_token"]
    return data["auth_token"]


def send_heartbeat(master_url: str, auth_token: str, active_job_id: Optional[str]) -> None:
    url = f"{master_url.rstrip('/')}/heartbeat"
    payload = {"worker_name": None, "active_job_id": active_job_id}
    headers = build_headers(auth_token)
    try:
        requests.post(url, json=payload, headers=headers, timeout=10)
    except Exception:
        pass


def fetch_next_job(master_url: str, auth_token: str) -> Optional[Dict[str, Any]]:
    url = f"{master_url.rstrip('/')}/next_job"
    headers = build_headers(auth_token)
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get("job")
    except Exception:
        return None


def complete_job(master_url: str, auth_token: str, job_id: str, result: Dict[str, Any], success: bool, runtime_seconds: float) -> None:
    url = f"{master_url.rstrip('/')}/complete_job"
    headers = build_headers(auth_token)
    payload = {
        "job_id": job_id,
        "worker_name": None,
        "result": result,
        "success": success,
        "runtime_seconds": runtime_seconds,
    }
    try:
        requests.post(url, json=payload, headers=headers, timeout=10)
    except Exception:
        pass


def run_task(task_payload: Dict[str, Any], verbose: bool = False) -> Dict[str, Any]:
    start = time.time()
    if verbose:
        print(f"[worker] executing payload: {task_payload}")
    # Task execution is intentionally simple so this daemon can execute arbitrary small workloads.
    result = {"status": "ok", "payload": task_payload}
    time.sleep(task_payload.get("duration", 1))
    result["runtime_seconds"] = time.time() - start
    return result


def worker_loop(master_url: str, auth_token: str, verbose: bool) -> None:
    active_job_id: Optional[str] = None
    last_heartbeat = 0.0
    while True:
        now = time.time()
        if now - last_heartbeat >= HEARTBEAT_INTERVAL:
            send_heartbeat(master_url, auth_token, active_job_id)
            last_heartbeat = now

        if active_job_id is None:
            job = fetch_next_job(master_url, auth_token)
            if job:
                active_job_id = job["job_id"]
                if verbose:
                    print(f"[worker] picked up job {active_job_id}")
                start_time = time.time()
                try:
                    result = run_task(job["payload"], verbose=verbose)
                    runtime = time.time() - start_time
                    complete_job(master_url, auth_token, active_job_id, result, True, runtime)
                    if verbose:
                        print(f"[worker] completed job {active_job_id} in {runtime:.3f}s")
                except Exception as exc:
                    runtime = time.time() - start_time
                    complete_job(master_url, auth_token, active_job_id, {"error": str(exc)}, False, runtime)
                    if verbose:
                        print(f"[worker] failed job {active_job_id}: {exc}")
                active_job_id = None
        time.sleep(JOB_POLL_INTERVAL)


def main(argv: Optional[list[str]] = None) -> int:
    args = parse_args(argv)
    capabilities = {"gpu": args.gpu, "memory_gb": args.memory_gb}
    auth_token = args.auth_token
    if not auth_token:
        auth_token = register_worker(args.master_url, args.name, capabilities, args.location, auth_token)
        print(f"Registered worker {args.name} with token {auth_token}")

    print(f"Connecting to TRON master at {args.master_url}")
    thread = threading.Thread(target=worker_loop, args=(args.master_url, auth_token, args.verbose), daemon=True)
    thread.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down worker daemon")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
