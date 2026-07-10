import pytest

try:
    import stable_baselines3  # type: ignore
    import gymnasium  # type: ignore
    HAS_SB3 = True
except Exception:
    HAS_SB3 = False

from tron_ii.adapters.sb3_example import run_example


@pytest.mark.skipif(not HAS_SB3, reason="stable-baselines3 or gymnasium not installed")
def test_sb3_example_runs_quickly():
    # Run a very short training to validate integration.
    ok = run_example(total_timesteps=64)
    assert ok
