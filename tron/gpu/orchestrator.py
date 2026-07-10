"""TRON vGPU orchestration and job specification."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any, Optional

from .cluster import VirtualGPUCluster
from .runtime import VirtualGPURuntime


@dataclass
class VGPUJobSpec:
    job_id: str
    task_type: str
    required_vram_gb: float
    required_cuda_cores: int
    payload: Dict[str, Any]
    priority: int
    requires_vgpu: bool = True
    metadata: Optional[Dict[str, Any]] = None


class VGPUOrchestrator:
    def __init__(self, cluster: VirtualGPUCluster):
        self.cluster = cluster
        self.runtime = VirtualGPURuntime(cluster)

    def create_job(self, spec: VGPUJobSpec) -> Dict[str, Any]:
        profile = self.cluster.aggregated_profile()
        if spec.required_vram_gb > profile.aggregated_vram_gb:
            raise RuntimeError(
                f"VGPU job requires {spec.required_vram_gb} GB but cluster has only {profile.aggregated_vram_gb} GB"
            )

        return self.runtime.submit_task(
            task_name=spec.task_type,
            task_payload={
                "job_id": spec.job_id,
                "payload": spec.payload,
                "metadata": spec.metadata or {},
            },
            required_vram_gb=spec.required_vram_gb,
        )

    def execute_job(self) -> Dict[str, Any]:
        return self.runtime.execute_next()

    def summary(self) -> Dict[str, Any]:
        return self.runtime.get_summary()
