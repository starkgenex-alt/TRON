"""Simulated virtual GPU runtime utilities for TRON."""
from __future__ import annotations

import time
from typing import Any, Dict, List

from .cluster import VirtualGPUCluster, VirtualGPUNode, VirtualGPUProfile


class VirtualGPURuntime:
    """Simulates allocation and task routing onto a virtual GPU cluster."""

    def __init__(self, cluster: VirtualGPUCluster):
        self.cluster = cluster
        self.pending_tasks: List[Dict[str, Any]] = []
        self.completed_tasks: List[Dict[str, Any]] = []

    def submit_task(self, task_name: str, task_payload: Dict[str, Any], required_vram_gb: float) -> Dict[str, Any]:
        profile = self.cluster.aggregated_profile()
        if required_vram_gb > profile.aggregated_vram_gb:
            raise RuntimeError(
                f"Task requires {required_vram_gb} GB, but cluster has only {profile.aggregated_vram_gb} GB"
            )

        task = {
            "task_id": f"task-{int(time.time() * 1000)}",
            "task_name": task_name,
            "payload": task_payload,
            "required_vram_gb": required_vram_gb,
            "submitted_at": time.time(),
            "status": "queued",
            "assigned_nodes": [node.node_id for node in profile.nodes],
            "synthetic_profile": profile,
        }
        self.pending_tasks.append(task)
        return task

    def execute_next(self) -> Dict[str, Any]:
        if not self.pending_tasks:
            raise RuntimeError("No tasks are pending execution")

        task = self.pending_tasks.pop(0)
        task["status"] = "running"
        task["started_at"] = time.time()
        time.sleep(min(0.1, task["required_vram_gb"] * 0.01))

        task["status"] = "completed"
        task["completed_at"] = time.time()
        task["runtime_seconds"] = task["completed_at"] - task["started_at"]
        task["result"] = {
            "status": "ok",
            "profile_name": task["synthetic_profile"].profile_name,
            "node_count": len(task["assigned_nodes"]),
        }
        self.completed_tasks.append(task)
        return task

    def get_summary(self) -> Dict[str, Any]:
        completed = len(self.completed_tasks)
        queued = len(self.pending_tasks)
        profile = self.cluster.aggregated_profile()
        return {
            "cluster_name": self.cluster.cluster_name,
            "synthetic_profile": profile.profile_name,
            "aggregated_vram_gb": profile.aggregated_vram_gb,
            "aggregated_cuda_cores": profile.aggregated_cuda_cores,
            "node_count": profile.node_count,
            "queued_tasks": queued,
            "completed_tasks": completed,
        }
