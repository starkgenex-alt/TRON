from pathlib import Path

from tron_ii.orchestrator import TrainingConfig, TrainingOrchestrator
from tron_ii.module import CapabilityModule
from tron_ii.hybrid import DummyHybridAdapter, HybridIntegrator
from tron_ii.registry import ArtifactRegistry


def test_artifact_registry_persists_after_training(tmp_path):
    # Use a temporary storage path for registry persistence
    storage = tmp_path / "test_tron_artifacts.json"

    orch = TrainingOrchestrator()
    # replace integrator with a dummy adapter that simulates training
    orch.integrator = HybridIntegrator([DummyHybridAdapter()])
    orch.adapters = {adapter.name: adapter for adapter in orch.integrator.adapters}

    # point manager registry to persistent storage
    orch.manager.registry.storage_path = storage

    module = CapabilityModule(
        module_id="m_persist",
        name="persist module",
        description="module for persistence test",
        preferred_substrate="cpu",
        complexity=1.0,
        task_type="classification",
        dataset_size=1,
        metrics={"capability_gain": 0.1},
    )

    config = TrainingConfig(task_name="persist_test", adapter_type="auto", modules=[module])

    success = orch.run_training(config, model=None, env=None)
    assert success

    # ensure file was written
    assert storage.exists()

    # registry can load the persisted file and find the artifact
    loaded = ArtifactRegistry(storage_path=str(storage))
    artifacts = loaded.find_by_module("m_persist")
    assert len(artifacts) >= 1
    assert artifacts[0].module == "m_persist"
