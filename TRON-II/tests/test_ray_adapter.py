import pytest

from tron_ii.adapters.ray_adapter import RayAdapter

try:
    import ray  # type: ignore
    HAS_RAY = True
except Exception:
    HAS_RAY = False


def test_ray_adapter_requires_ray_installed():
    if not HAS_RAY:
        with pytest.raises(ImportError):
            RayAdapter()
    else:
        adapter = RayAdapter()
        assert adapter.name == "ray"


def test_ray_adapter_rejects_invalid_dataset():
    if not HAS_RAY:
        pytest.skip("ray is not installed")

    adapter = RayAdapter()
    with pytest.raises(ValueError):
        adapter.train(dataset={"model": None, "env": None}, config={"total_timesteps": 1})
