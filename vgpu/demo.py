"""Demo for TRON virtual GPU aggregation."""
from __future__ import annotations

import time

from .cluster import VirtualGPUCluster
from .runtime import VirtualGPURuntime


def main() -> None:
    cluster = VirtualGPUCluster(cluster_name="tron-vgpu-cluster")
    cluster.register_node("node-1", "RTX 3050", vram_gb=4.0, cuda_cores=2048, network_bandwidth_gbps=1.0)
    cluster.register_node("node-2", "RTX 3060", vram_gb=6.0, cuda_cores=3584, network_bandwidth_gbps=1.0)
    cluster.register_node("node-3", "RTX 4060", vram_gb=8.0, cuda_cores=3072, network_bandwidth_gbps=1.0)

    runtime = VirtualGPURuntime(cluster)
    task = runtime.submit_task(
        task_name="render_batch",
        task_payload={"frames": 120, "complexity": "high"},
        required_vram_gb=12.0,
    )

    print("Registered virtual GPU cluster:")
    print(runtime.get_summary())
    print("\nSubmitting task:")
    print(task)

    print("\nExecuting task on synthetic vGPU...")
    completed = runtime.execute_next()
    print("Task completed:")
    print(completed)
    print("\nCluster summary after execution:")
    print(runtime.get_summary())


if __name__ == "__main__":
    main()
