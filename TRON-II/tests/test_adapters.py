import pytest

from tron_ii.adapters import SB3Adapter

try:
    import stable_baselines3  # type: ignore
    HAS_SB3 = True
except Exception:
    HAS_SB3 = False


def test_sb3_adapter_raises_when_missing():
    adapter = SB3Adapter()
    dataset = {"model": None, "env": None}
    config = {"total_timesteps": 1}

    if HAS_SB3:
        with pytest.raises((RuntimeError, ValueError)) as exc:
            adapter.train(dataset=dataset, config=config)
        assert "stable-baselines3" in str(exc.value) or "requires 'model' and 'env'" in str(exc.value)
    else:
        with pytest.raises(RuntimeError) as exc:
            adapter.train(dataset=dataset, config=config)
        assert "stable-baselines3 is not available" in str(exc.value)
