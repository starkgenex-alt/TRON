"""Unit tests for TRON-II training policy and substrate recommendation."""

from tron_ii.manager import TrainingManager
from tron_ii.orchestrator import TrainingOrchestrator
from tron_ii.policy import TrainingPolicy
from tron_ii.module import CapabilityModule


def test_training_policy_decides_adapter_with_gpu_preference():
    policy = TrainingPolicy()
    estimates = {
        "sb3": {"capability_gain": 1.0, "cost": 1.5},
        "ray": {"capability_gain": 0.9, "cost": 0.8},
        "transformers": {"capability_gain": 0.8, "cost": 2.0},
    }

    selected = policy.decide_adapter(
        estimates=estimates,
        preferred_substrate="gpu",
        available=["sb3", "ray", "transformers"],
    )

    assert selected == "ray"


def test_training_policy_respects_requested_adapter():
    policy = TrainingPolicy()
    estimates = {
        "sb3": {"capability_gain": 1.0, "cost": 1.0},
        "ray": {"capability_gain": 0.9, "cost": 0.8},
    }

    selected = policy.decide_adapter(
        estimates=estimates,
        preferred_substrate="cpu",
        available=["sb3", "ray"],
        requested="sb3",
    )

    assert selected == "sb3"


def test_training_manager_recommends_preferred_substrate():
    policy = TrainingPolicy()
    orchestrator = TrainingOrchestrator(policy=policy)
    manager = orchestrator.manager
    module = CapabilityModule(
        module_id="m3",
        name="policy",
        description="test module",
        preferred_substrate="gpu",
        complexity=1.0,
        task_type="reinforcement",
        dataset_size=1,
        metrics={"capability_gain": 1.0},
    )

    selected = manager.recommend_substrate(module)

    assert selected == "gpu"


def test_training_manager_falls_back_to_available_substrate():
    policy = TrainingPolicy()
    orchestrator = TrainingOrchestrator(policy=policy)
    manager = orchestrator.manager
    module = CapabilityModule(
        module_id="m4",
        name="policy",
        description="test module",
        preferred_substrate="tpu",
        complexity=1.0,
        task_type="reinforcement",
        dataset_size=1,
        metrics={"capability_gain": 1.0},
    )

    selected = manager.recommend_substrate(module)

    assert selected in {"cpu", "gpu"}
