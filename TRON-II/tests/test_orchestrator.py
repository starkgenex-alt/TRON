"""Unit tests for the training orchestrator."""

import pytest

from tron_ii import ArtifactMetadata
from tron_ii.hybrid import DummyHybridAdapter, HybridAdapter, HybridIntegrator
from tron_ii.module import CapabilityModule
from tron_ii.orchestrator import TrainingConfig, TrainingOrchestrator


def test_orchestrator_initialization():
    """Verify orchestrator initializes correctly."""
    orch = TrainingOrchestrator()
    assert orch.manager is not None
    assert "sb3" in orch.adapters
    assert len(orch.training_log) == 0


def test_orchestrator_invalid_adapter():
    """Test orchestrator rejects unknown adapters."""
    orch = TrainingOrchestrator()
    config = TrainingConfig(task_name="test", adapter_type="unknown_adapter")

    # Should fail gracefully when adapter not found
    success = orch.run_training(config, None, None)
    assert not success
    assert len(orch.training_log) == 1
    assert orch.training_log[0]["status"] == "failed"


def test_orchestrator_summary():
    """Verify orchestrator summary reflects training outcomes."""
    orch = TrainingOrchestrator()
    config_fail = TrainingConfig(task_name="fail_test", adapter_type="unknown")
    orch.run_training(config_fail, None, None)

    summary = orch.get_training_summary()
    assert summary["total_runs"] == 1
    assert summary["failed"] == 1
    assert summary["successful"] == 0


def test_orchestrator_last_plan_is_recorded():
    orch = TrainingOrchestrator()
    module = CapabilityModule(
        module_id="policy",
        name="policy",
        description="test module",
        preferred_substrate="cpu",
        complexity=1.0,
        task_type="reinforcement",
        dataset_size=1,
        metrics={"capability_gain": 1.0},
    )
    config = TrainingConfig(task_name="plan_test", adapter_type="auto", modules=[module])

    orch.run_training(config, None, None)
    assert orch.get_last_plan() is not None
    assert orch.get_last_plan().mission_name == "plan_test"


def test_orchestrator_uses_adapter_estimates_to_select_best():
    class StubAdapter(HybridAdapter):
        def __init__(self, name):
            super().__init__(name)

        def train(self, dataset, config):
            return {"capability_gain": 1.0, "cost": 0.1}

        def evaluate(self, model, dataset):
            return {"capability_gain": 1.0}

    orch = TrainingOrchestrator()
    orch.integrator = HybridIntegrator([StubAdapter("sb3"), StubAdapter("ray")])
    orch.adapters = {adapter.name: adapter for adapter in orch.integrator.adapters}

    module = CapabilityModule(
        module_id="policy",
        name="policy",
        description="CPU task",
        preferred_substrate="cpu",
        complexity=1.0,
        task_type="reinforcement",
        dataset_size=1,
        metrics={"capability_gain": 1.0},
    )
    config = TrainingConfig(
        task_name="estimate_adapter",
        adapter_type="auto",
        modules=[module],
        adapter_estimates={
            "sb3": {"capability_gain": 0.5, "cost": 1.0},
            "ray": {"capability_gain": 0.9, "cost": 0.1},
        },
    )

    success = orch.run_training(config, None, None)
    assert success
    assert orch.training_log[-1]["adapter"] == "ray"


def test_orchestrator_mission_aware_adapter_selection():
    class StubAdapter(HybridAdapter):
        def __init__(self, name):
            super().__init__(name)

        def train(self, dataset, config):
            return {"capability_gain": 1.0, "cost": 0.1}

        def evaluate(self, model, dataset):
            return {"capability_gain": 1.0}

    orch = TrainingOrchestrator()
    orch.integrator = HybridIntegrator([StubAdapter("sb3"), StubAdapter("ray")])
    orch.adapters = {adapter.name: adapter for adapter in orch.integrator.adapters}

    module = CapabilityModule(
        module_id="policy",
        name="policy",
        description="GPU task",
        preferred_substrate="gpu",
        complexity=1.0,
        task_type="reinforcement",
        dataset_size=1,
        metrics={"capability_gain": 1.0},
    )
    config = TrainingConfig(task_name="mission_adapter", adapter_type="auto", modules=[module])

    success = orch.run_training(config, None, None)
    assert success
    assert orch.training_log[-1]["adapter"] == "ray"


def test_orchestrator_reuses_artifacts_when_available():
    module = CapabilityModule(
        module_id="policy",
        name="policy",
        description="reusable module",
        preferred_substrate="cpu",
        complexity=1.0,
        task_type="reinforcement",
        dataset_size=1,
        metrics={"capability_gain": 0.1},
    )

    orch = TrainingOrchestrator()
    orch.integrator = HybridIntegrator([DummyHybridAdapter()])
    orch.adapters = {adapter.name: adapter for adapter in orch.integrator.adapters}
    orch.manager.registry.register(
        ArtifactMetadata(
            artifact_id="artifact1",
            module="policy",
            version="v1",
            metrics={"capability_gain": 2.0},
            size_bytes=1,
            substrates=["cpu"],
            adapter="dummy",
            task_name="reuse_test",
            training_config={"total_timesteps": 100, "adapter_type": "dummy", "budget": 1.0},
            created_at="2024-01-01T00:00:00Z",
        )
    )

    config = TrainingConfig(task_name="reuse_test", adapter_type="auto", modules=[module])
    success = orch.run_training(config, None, None)

    assert success
    assert orch.training_log[-1]["status"] == "reused"
    assert orch.training_log[-1]["adapter"] == "reuse"
    assert orch.training_log[-1]["artifact_ids"] == ["artifact1"]


def test_orchestrator_registers_artifacts_after_training():
    module = CapabilityModule(
        module_id="policy",
        name="policy",
        description="artifact registration test",
        preferred_substrate="cpu",
        complexity=1.0,
        task_type="reinforcement",
        dataset_size=1,
        metrics={"capability_gain": 1.0},
    )

    orch = TrainingOrchestrator()
    orch.integrator = HybridIntegrator([DummyHybridAdapter()])
    orch.adapters = {adapter.name: adapter for adapter in orch.integrator.adapters}

    config = TrainingConfig(task_name="artifact_test", adapter_type="auto", modules=[module])
    success = orch.run_training(config, None, None)

    assert success
    registered = orch.manager.registry.find_by_module("policy")
    assert len(registered) == 1
    assert registered[0].artifact_id == "artifact_test-policy-dummy"
    assert registered[0].metrics["capability_gain"] == 1.0


def test_orchestrator_auto_adapter_selection():
    orch = TrainingOrchestrator()
    orch.integrator = HybridIntegrator([DummyHybridAdapter()])
    orch.adapters = {adapter.name: adapter for adapter in orch.integrator.adapters}

    config = TrainingConfig(task_name="auto_selection", adapter_type="auto")
    success = orch.run_training(config, None, None)

    assert success
    assert orch.training_log[-1]["adapter"] == "dummy"
