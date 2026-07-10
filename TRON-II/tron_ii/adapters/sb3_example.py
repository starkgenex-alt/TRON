"""SB3 integration example for TRON-II.

Runs a tiny training session if `stable_baselines3` and `gymnasium` are available.
"""
from pathlib import Path
from typing import Any


def run_example(total_timesteps: int = 256) -> bool:
    try:
        import stable_baselines3 as sb3  # type: ignore
        import gymnasium as gym
    except Exception as e:
        raise RuntimeError("Dependencies for SB3 example are not installed") from e

    env = gym.make("CartPole-v1")
    # Use a small training loop for CI-friendly demos
    model = sb3.PPO("MlpPolicy", env, verbose=0)
    model.learn(total_timesteps=total_timesteps)

    out = Path("sb3_demo_model")
    model.save(str(out))
    env.close()
    return out.with_suffix(".zip").exists()


if __name__ == "__main__":
    ok = run_example()
    print("SB3 example finished, model saved:", ok)
