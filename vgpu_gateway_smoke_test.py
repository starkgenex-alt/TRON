"""Smoke test for TRON vGPU gateway, scheduler, and worker end-to-end flow."""
from __future__ import annotations

import signal
import socket
import subprocess
import sys
import time
import uuid
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent
SCHEDULER_URL = "http://127.0.0.1:9002"
BRIDGE_URL = "http://127.0.0.1:9003"
WORKER_NAME = f"smoke-test-worker-{uuid.uuid4().hex[:8]}"


def wait_for_port(host: str, port: int, timeout: float = 20.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection((host, port), timeout=2.0):
                return True
        except OSError:
            time.sleep(0.25)
    return False


def wait_for_http(url: str, timeout: float = 20.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                return True
        except requests.RequestException:
            pass
        time.sleep(0.25)
    return False


def launch_process(command: list[str], cwd: Path) -> subprocess.Popen[str]:
    return subprocess.Popen(
        command,
        cwd=str(cwd),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )


def terminate_process(proc: subprocess.Popen[str]) -> None:
    if proc.poll() is not None:
        return
    try:
        proc.send_signal(signal.SIGINT)
        proc.wait(timeout=5)
    except Exception:
        proc.kill()
        proc.wait(timeout=5)


def wait_for_worker_registration(worker_name: str, timeout: float = 20.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            response = requests.get(f"{SCHEDULER_URL}/workers", timeout=5)
            response.raise_for_status()
            workers = response.json().get("workers", {})
            if worker_name in workers:
                return True
        except requests.RequestException:
            pass
        time.sleep(0.25)
    return False


def main() -> int:
    scheduler_cmd = [sys.executable, "-m", "vgpu.scheduler"]
    bridge_cmd = [sys.executable, "-m", "vgpu.openai_bridge"]
    worker_cmd = [
        sys.executable,
        "-m",
        "vgpu.worker",
        "--name",
        WORKER_NAME,
        "--master-url",
        SCHEDULER_URL,
        "--verbose",
    ]

    processes: list[subprocess.Popen[str]] = []
    try:
        if wait_for_port("127.0.0.1", 9002, timeout=2.0) and wait_for_http(f"{SCHEDULER_URL}/health", timeout=5.0):
            print("Using existing scheduler on port 9002")
            scheduler_proc = None
        else:
            print("Starting scheduler...")
            scheduler_proc = launch_process(scheduler_cmd, ROOT)
            processes.append(scheduler_proc)
            if not wait_for_port("127.0.0.1", 9002, timeout=20.0):
                raise RuntimeError("Scheduler did not open port 9002")
            if not wait_for_http(f"{SCHEDULER_URL}/health", timeout=20.0):
                raise RuntimeError("Scheduler health endpoint did not respond")

        if wait_for_port("127.0.0.1", 9003, timeout=2.0) and wait_for_http(f"{BRIDGE_URL}/health", timeout=5.0):
            print("Using existing gateway on port 9003")
            bridge_proc = None
        else:
            print("Starting OpenAI gateway...")
            bridge_proc = launch_process(bridge_cmd, ROOT)
            processes.append(bridge_proc)
            if not wait_for_port("127.0.0.1", 9003, timeout=20.0):
                raise RuntimeError("Gateway did not open port 9003")
            if not wait_for_http(f"{BRIDGE_URL}/health", timeout=20.0):
                raise RuntimeError("Gateway health endpoint did not respond")

        print("Starting worker...")
        worker_proc = launch_process(worker_cmd, ROOT)
        processes.append(worker_proc)
        if not wait_for_worker_registration(WORKER_NAME, timeout=20.0):
            raise RuntimeError(f"Worker {WORKER_NAME} did not register with scheduler")

        print("Submitting OpenAI-style request through gateway...")
        response = requests.post(
            f"{BRIDGE_URL}/v1/chat/completions",
            json={
                "model": "tron-gateway",
                "messages": [{"role": "user", "content": "Smoke test for TRON gateway"}],
                "temperature": 0.5,
                "max_tokens": 32,
            },
            timeout=60,
        )
        response.raise_for_status()
        print("Gateway response:")
        print(response.json())

        return 0
    except Exception as exc:
        print(f"Smoke test failed: {exc}")
        return 1
    finally:
        print("Shutting down processes...")
        for proc in reversed(processes):
            terminate_process(proc)


if __name__ == "__main__":
    raise SystemExit(main())
