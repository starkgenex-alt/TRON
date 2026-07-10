import pytest
from tron_ii import MissionPlanner, ArtifactRegistry, ArtifactMetadata, SubstrateManager, Substrate, UtilityEngine, TrainingPhase


def test_mission_planner():
    planner = MissionPlanner()
    plan = planner.create_mission("mission1", "maximize accuracy", 1000.0)
    phase = TrainingPhase(name="phase1", module="encoder", substrate="gpu", resources={"gpu":1}, budget=200.0)
    planner.add_phase("mission1", phase)
    assert plan.mission_name == "mission1"
    assert len(plan.phases) == 1


def test_artifact_registry():
    registry = ArtifactRegistry()
    metadata = ArtifactMetadata(
        artifact_id="a1",
        module="encoder",
        version="v1",
        metrics={"capability_gain": 0.5},
        size_bytes=1024,
        substrates=["gpu"],
        adapter="sb3",
        task_name="test_task",
        training_config={"total_timesteps": 1000, "adapter_type": "sb3", "budget": 1.0},
        created_at="2024-01-01T00:00:00Z",
    )
    registry.register(metadata)
    assert registry.get("a1") is metadata
    assert registry.find_by_module("encoder") == [metadata]


def test_substrate_manager():
    manager = SubstrateManager()
    substrate = Substrate(name="gpu", type="hardware", cost_per_cycle=1.0, capabilities={"compute": 1.0})
    manager.register(substrate)
    assert manager.get("gpu") == substrate
    assert manager.select("gpu") == substrate


def test_utility_engine():
    engine = UtilityEngine()
    assert engine.score({"capability_gain": 5.0}, 2.0) == 2.5
