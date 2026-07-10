"""Worker daemon for the TRON virtual GPU scheduler."""
from __future__ import annotations

import argparse
import os
import sys
import time
import threading
from typing import Any, Dict, Optional

import requests

DEFAULT_MASTER_URL = "http://localhost:9002"
HEARTBEAT_INTERVAL = 10.0
JOB_POLL_INTERVAL = 5.0


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="TRON vGPU worker daemon")
    parser.add_argument("--master-url", default=os.environ.get("TRON_MASTER_URL", DEFAULT_MASTER_URL), help="vGPU master scheduler URL")
    parser.add_argument("--name", default=os.environ.get("TRON_WORKER_NAME", "vgpu-worker"), help="Worker name")
    parser.add_argument("--gpu-name", default=os.environ.get("TRON_GPU_NAME", "RTX 3050"), help="GPU model name")
    parser.add_argument("--vram-gb", type=float, default=float(os.environ.get("TRON_VRAM_GB", "4.0")), help="Available GPU VRAM in GB")
    parser.add_argument("--cuda-cores", type=int, default=int(os.environ.get("TRON_CUDA_CORES", "2048")), help="Physical CUDA core count")
    parser.add_argument("--network-bandwidth-gbps", type=float, default=float(os.environ.get("TRON_NETWORK_BANDWIDTH_GBPS", "1.0")), help="Network bandwidth in Gbps")
    parser.add_argument("--memory-gb", type=float, default=float(os.environ.get("TRON_MEMORY_GB", "8.0")), help="System memory available")
    parser.add_argument("--location", default=os.environ.get("TRON_WORKER_LOCATION", "unknown"), help="Worker location or tag")
    parser.add_argument("--auth-token", default=os.environ.get("TRON_WORKER_AUTH_TOKEN"), help="Pre-existing auth token")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    return parser.parse_args(argv)


def build_headers(auth_token: str) -> Dict[str, str]:
    return {"X-TRON-AUTH": auth_token}


def register_worker(master_url: str, name: str, capabilities: Dict[str, Any], gpu_name: str, vram_gb: float, cuda_cores: int, network_bandwidth_gbps: float, location: str, auth_token: Optional[str]) -> str:
    url = f"{master_url.rstrip('/')}/register"
    payload = {
        "name": name,
        "capabilities": capabilities,
        "gpu_name": gpu_name,
        "vram_gb": vram_gb,
        "cuda_cores": cuda_cores,
        "network_bandwidth_gbps": network_bandwidth_gbps,
        "location": location,
        "metadata": {"platform": sys.platform},
    }
    response = requests.post(url, json=payload, timeout=10)
    response.raise_for_status()
    data = response.json()
    if auth_token and data.get("auth_token") != auth_token:
        return data["auth_token"]
    return data["auth_token"]


def send_heartbeat(master_url: str, auth_token: str, worker_name: str, active_job_id: Optional[str]) -> None:
    url = f"{master_url.rstrip('/')}/heartbeat"
    payload = {"worker_name": worker_name, "active_job_id": active_job_id}
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


def complete_job(master_url: str, auth_token: str, worker_name: str, job_id: str, result: Dict[str, Any], success: bool, runtime_seconds: float, shard_id: Optional[str] = None) -> None:
    url = f"{master_url.rstrip('/')}/complete_job"
    headers = build_headers(auth_token)
    payload = {
        "job_id": job_id,
        "worker_name": worker_name,
        "result": result,
        "success": success,
        "runtime_seconds": runtime_seconds,
    }
    if shard_id:
        payload["shard_id"] = shard_id
    try:
        requests.post(url, json=payload, headers=headers, timeout=10)
    except Exception:
        pass


def run_task(task_payload: Dict[str, Any], verbose: bool = False) -> Dict[str, Any]:
    start = time.time()
    if verbose:
        print(f"[vgpu-worker] executing payload: {task_payload}")
    duration = float(task_payload.get("duration", 1.0))
    time.sleep(duration)
    result: Dict[str, Any] = {"status": "ok"}

    task_kind = str(task_payload.get("task_kind", ""))
    if task_kind == "openai_chat":
        prompt = task_payload.get("prompt") or ""
        result["content"] = f"TRON distributed reply for: {prompt[:512]}"
    elif task_kind == "agent_run":
        agent_id = task_payload.get("agent_id", "unknown")
        prompt = task_payload.get("prompt", "")
        result["message"] = f"Agent {agent_id} processed prompt: {prompt[:256]}"
    else:
        result["payload"] = task_payload

    result["runtime_seconds"] = time.time() - start
    return result


def worker_loop(master_url: str, auth_token: str, worker_name: str, verbose: bool) -> None:
    active_job_id: Optional[str] = None
    active_shard_id: Optional[str] = None
    active_assigned_nodes: Optional[list] = None
    last_heartbeat = 0.0
    while True:
        now = time.time()
        if now - last_heartbeat >= HEARTBEAT_INTERVAL:
            send_heartbeat(master_url, auth_token, worker_name, active_job_id)
            last_heartbeat = now

        if active_job_id is None:
            job = fetch_next_job(master_url, auth_token)
            if job:
                active_job_id = job["job_id"]
                active_shard_id = job.get("shard_id")
                active_assigned_nodes = job.get("assigned_nodes", [])
                if verbose:
                    shard_str = f" (shard={active_shard_id})" if active_shard_id else ""
                    nodes_str = f" on nodes {active_assigned_nodes}" if active_assigned_nodes else ""
                    print(f"[vgpu-worker] picked up job {active_job_id}{shard_str}{nodes_str}")
                start_time = time.time()
                try:
                    result = run_task(job["payload"], verbose=verbose)
                    runtime = time.time() - start_time
                    complete_job(master_url, auth_token, worker_name, active_job_id, result, True, runtime, shard_id=active_shard_id)
                    if verbose:
                        print(f"[vgpu-worker] completed job {active_job_id} (shard {active_shard_id}) in {runtime:.3f}s")
                except Exception as exc:
                    runtime = time.time() - start_time
                    complete_job(master_url, auth_token, worker_name, active_job_id, {"error": str(exc)}, False, runtime, shard_id=active_shard_id)
                    if verbose:
                        print(f"[vgpu-worker] failed job {active_job_id} (shard {active_shard_id}): {exc}")
                active_job_id = None
                active_shard_id = None
                active_assigned_nodes = None
        time.sleep(JOB_POLL_INTERVAL)


def main(argv: Optional[list[str]] = None) -> int:
    args = parse_args(argv)
    capabilities = {"gpu": True, "memory_gb": args.memory_gb}
    auth_token = args.auth_token
    if not auth_token:
        auth_token = register_worker(
            args.master_url,
            args.name,
            capabilities,
            args.gpu_name,
            args.vram_gb,
            args.cuda_cores,
            args.network_bandwidth_gbps,
            args.location,
            auth_token,
        )
        print(f"Registered worker {args.name} with token {auth_token}")

    print(f"Connecting to TRON vGPU master at {args.master_url}")
    thread = threading.Thread(target=worker_loop, args=(args.master_url, auth_token, args.name, args.verbose), daemon=True)
    thread.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down vGPU worker daemon")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
