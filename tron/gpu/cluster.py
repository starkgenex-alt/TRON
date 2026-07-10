"""Aggregated virtual GPU cluster support for TRON."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class VirtualGPUNode:
    node_id: str
    gpu_name: str
    vram_gb: float
    cuda_cores: int
    network_bandwidth_gbps: float
    active: bool = True


@dataclass
class VirtualGPUProfile:
    profile_name: str
    aggregated_vram_gb: float
    aggregated_cuda_cores: int
    node_count: int
    nodes: List[VirtualGPUNode]
    status: str
    metadata: Dict[str, object]


class VirtualGPUCluster:
    """Represents a pool of physical GPUs aggregated into a virtual GPU offer."""

    def __init__(self, cluster_name: str):
        self.cluster_name = cluster_name
        self.nodes: Dict[str, VirtualGPUNode] = {}

    def register_node(
        self,
        node_id: str,
        gpu_name: str,
        vram_gb: float,
        cuda_cores: int,
        network_bandwidth_gbps: float,
    ) -> VirtualGPUNode:
        node = VirtualGPUNode(
            node_id=node_id,
            gpu_name=gpu_name,
            vram_gb=vram_gb,
            cuda_cores=cuda_cores,
            network_bandwidth_gbps=network_bandwidth_gbps,
        )
        self.nodes[node_id] = node
        return node

    def unregister_node(self, node_id: str) -> None:
        if node_id in self.nodes:
            self.nodes[node_id].active = False

    def active_nodes(self) -> List[VirtualGPUNode]:
        return [node for node in self.nodes.values() if node.active]

    def aggregated_profile(self, profile_name: Optional[str] = None) -> VirtualGPUProfile:
        active = self.active_nodes()
        total_vram = sum(node.vram_gb for node in active)
        total_cores = sum(node.cuda_cores for node in active)
        metadata = {
            "physical_nodes": [node.node_id for node in active],
            "physical_gpus": [node.gpu_name for node in active],
            "total_network_gbps": sum(node.network_bandwidth_gbps for node in active),
        }

        if total_vram >= 80:
            name = "NVIDIA A100-Virtual Enterprise"
        elif total_vram >= 40:
            name = "NVIDIA H100-Virtual Enterprise"
        elif total_vram >= 24:
            name = "NVIDIA RTX 4090-Virtual Instance"
        else:
            name = "TRON Synthetic vGPU"

        return VirtualGPUProfile(
            profile_name=profile_name or name,
            aggregated_vram_gb=round(total_vram, 2),
            aggregated_cuda_cores=total_cores,
            node_count=len(active),
            nodes=active,
            status="READY" if active else "DEGRADED",
            metadata=metadata,
        )
