import pytest

from tron_ii.hybrid import HybridAdapter, HybridIntegrator, DummyHybridAdapter


class StubAdapter(HybridAdapter):
    def train(self, dataset, config):
        return {"capability_gain": 0.0, "cost": 0.0}

    def evaluate(self, model, dataset):
        return {"capability_gain": 0.0}


class StubSB3Adapter(StubAdapter):
    def __init__(self):
        super().__init__("sb3")


class StubRayAdapter(StubAdapter):
    def __init__(self):
        super().__init__("ray")


def test_hybrid_integrator_default_contains_dummy():
    integrator = HybridIntegrator.default()
    assert "dummy" in integrator.available_names()


def test_hybrid_integrator_selects_known_adapter():
    integrator = HybridIntegrator()
    adapter = DummyHybridAdapter()
    integrator.register_adapter(adapter)
    selected = integrator.select("dummy")
    assert selected.name == "dummy"


def test_hybrid_integrator_falls_back_to_default():
    integrator = HybridIntegrator.default()
    selected = integrator.select("unknown")
    assert selected.name == integrator.available_names()[0]


def test_hybrid_integrator_selects_best_by_default():
    integrator = HybridIntegrator([DummyHybridAdapter()])
    selected = integrator.select_best()
    assert selected.name == "dummy"


def test_hybrid_integrator_prefers_ray_for_gpu_substrate():
    integrator = HybridIntegrator([StubSB3Adapter(), StubRayAdapter()])
    selected = integrator.select_best(dataset={"selected_substrate": "gpu"})
    assert selected.name == "ray"


def test_hybrid_integrator_prefers_sb3_for_cpu_substrate():
    integrator = HybridIntegrator([StubSB3Adapter(), StubRayAdapter()])
    selected = integrator.select_best(dataset={"selected_substrate": "cpu"})
    assert selected.name == "sb3"


def test_hybrid_integrator_selects_best_by_estimate():
    integrator = HybridIntegrator([StubSB3Adapter(), StubRayAdapter()])
    estimates = {
        "sb3": {"capability_gain": 0.5, "cost": 0.5},
        "ray": {"capability_gain": 0.4, "cost": 0.1},
    }
    selected = integrator.select_best(dataset={"adapter_estimates": estimates})
    assert selected.name == "ray"
