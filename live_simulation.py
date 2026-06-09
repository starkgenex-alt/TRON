import time
import tron

# Force the SDK to use the local runtime server explicitly
tron.set_config_url("http://127.0.0.1:9000")

@tron.remote(remote_only=True, memory_gb=4, priority=10)
def design_ai_accelerator(model_size: int, target_power_w: int):
    # Simulate a difficult design generation task for an AI chip
    complexity = model_size * target_power_w
    detail = "".join([f"A{(i % 26)}" for i in range(min(complexity, 3000))])
    time.sleep(1)
    blueprint = {
        "type": "AI accelerator",
        "model_size": model_size,
        "target_power_w": target_power_w,
        "complexity_score": complexity,
        "layout_hash": hash(detail) % 10_000,
    }
    return {"result": blueprint}

@tron.remote(remote_only=True, memory_gb=4)
def simulate_thermal(blueprint: dict):
    # Simulate the thermal profile of the proposed chip
    thermal_nodes = [((blueprint["layout_hash"] + i) % 100) / 100 for i in range(10)]
    peak_temp = 60 + sum(thermal_nodes) * 20
    time.sleep(1)
    return {"result": {"peak_temp_c": round(peak_temp, 2), "distribution": thermal_nodes}}

@tron.remote(remote_only=True, memory_gb=3)
def estimate_manufacturing_cost(blueprint: dict):
    base_cost = 150_000
    multiplier = blueprint["complexity_score"] / 1000
    total_cost = base_cost * (1 + multiplier * 0.08)
    time.sleep(1)
    return {"result": {"estimated_cost_usd": round(total_cost, 2), "process_node": "5nm"}}

@tron.remote(remote_only=True, memory_gb=2)
def validate_training_pipeline(blueprint: dict, dataset_size_tb: float):
    # Simulate an AI infrastructure validation step
    efficiency = 0.72 + ((blueprint["layout_hash"] % 30) / 100) + (dataset_size_tb * 0.01)
    throughput = 200 + dataset_size_tb * 15
    time.sleep(1)
    return {"result": {"efficiency": round(min(efficiency, 0.97), 4), "throughput_tflops": round(throughput, 2)}}

@tron.remote(remote_only=True, memory_gb=2)
def summarize_project(design_info: dict, thermal_info: dict, cost_info: dict, validation_info: dict):
    summary = {
        "design": design_info,
        "thermal": thermal_info,
        "cost": cost_info,
        "validation": validation_info,
        "risk_level": "medium" if thermal_info["peak_temp_c"] < 85 else "high",
    }
    return {"result": summary}


def main():
    print("[SIM] Starting AI infrastructure simulation")

    design_future = design_ai_accelerator(512, 75)
    thermal_future = simulate_thermal(design_future.get())
    cost_future = estimate_manufacturing_cost(design_future.get())
    validation_future = validate_training_pipeline(design_future.get(), dataset_size_tb=4.5)

    print("[SIM] Waiting for all distributed tasks to complete...")
    design = design_future.get()
    thermal = thermal_future.get()
    cost = cost_future.get()
    validation = validation_future.get()

    summary_future = summarize_project(design, thermal, cost, validation)
    summary = summary_future.get()

    print("\n[SIM] FINAL SUMMARY")
    for key, value in summary.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
