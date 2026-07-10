"""Client demo for submitting vGPU jobs to TRON."""
from __future__ import annotations

import uuid
from typing import Any, Dict

import requests


class VGPUClient:
    def __init__(self, master_url: str):
        self.master_url = master_url.rstrip("/")

    def submit_vgpu_job(self, task_type: str, payload: Dict[str, Any], required_vram_gb: float, required_cuda_cores: int, priority: int = 1) -> Dict[str, Any]:
        url = f"{self.master_url}/submit_job"
        body = {
            "task_type": task_type,
            "payload": payload,
            "priority": priority,
            "requires_gpu": True,
            "required_vram_gb": required_vram_gb,
            "required_cuda_cores": required_cuda_cores,
            "metadata": {"job_id": str(uuid.uuid4())},
        }
        response = requests.post(url, json=body, timeout=10)
        response.raise_for_status()
        return response.json()

    def get_workers(self) -> Dict[str, Any]:
        url = f"{self.master_url}/workers"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()

    def get_jobs(self) -> Dict[str, Any]:
        url = f"{self.master_url}/jobs"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()


if __name__ == "__main__":
    client = VGPUClient("http://localhost:9002")
    print("Workers:", client.get_workers())
    print("Submitting sample vGPU job...")
    resp = client.submit_vgpu_job(
        task_type="render_batch",
        payload={"frames": 30, "duration": 2.0},
        required_vram_gb=10.0,
        required_cuda_cores=4096,
    )
    print(resp)
