"""Management utilities for TRON virtual GPU clustering."""
from __future__ import annotations

from typing import Dict, Any

from .cluster import VirtualGPUCluster, VirtualGPUNode


def build_cluster_from_workers(workers: Dict[str, Dict[str, Any]], cluster_name: str = "tron-vgpu-cluster") -> VirtualGPUCluster:
    cluster = VirtualGPUCluster(cluster_name=cluster_name)
    for worker_name, worker_info in workers.items():
        gpu_name = worker_info.get("gpu_name")
        if not gpu_name:
            continue

        cluster.register_node(
            node_id=worker_name,
            gpu_name=gpu_name,
            vram_gb=float(worker_info.get("vram_gb", 0.0)),
            cuda_cores=int(worker_info.get("cuda_cores", 0)),
            network_bandwidth_gbps=float(worker_info.get("network_bandwidth_gbps", 0.0)),
        )
    return cluster
