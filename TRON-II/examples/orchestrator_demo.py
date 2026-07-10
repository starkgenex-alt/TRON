"""Example usage of TRON-II with SB3 via the orchestrator."""

import sys
from pathlib import Path

# Add parent directory to path so we can import tron_ii
sys.path.insert(0, str(Path(__file__).parent.parent))

from tron_ii.module import CapabilityModule
from tron_ii.orchestrator import TrainingConfig, TrainingOrchestrator


def demo_orchestrator():
    """Demonstrates TRON-II orchestrating an SB3 training session."""
    try:
        import gymnasium as gym
        import stable_baselines3 as sb3
    except Exception as e:
        raise RuntimeError("Demo requires gymnasium and stable-baselines3") from e

    orchestrator = TrainingOrchestrator()

    # Build a small mission-aware training task
    module = CapabilityModule(
        module_id="cartpole_policy",
        name="CartPole policy",
        description="PPO policy for CartPole-v1",
        preferred_substrate="cpu",
        complexity=1.0,
        task_type="reinforcement",
        dataset_size=1_000,
        metrics={"capability_gain": 1.0},
    )

    config = TrainingConfig(
        task_name="CartPole-Baseline",
        objective="stabilize cartpole",
        budget=1.0,
        total_timesteps=128,
        adapter_type="auto",
        modules=[module],
    )

    # Create a simple environment and model
    env = gym.make("CartPole-v1")
    model = sb3.PPO("MlpPolicy", env, verbose=0)

    # Run training via the orchestrator
    success = orchestrator.run_training(config, model, env)
    env.close()

    # Print summary
    summary = orchestrator.get_training_summary()
    print(f"\n[Summary]\nTotal runs: {summary['total_runs']}\nSuccessful: {summary['successful']}\nFailed: {summary['failed']}")

    return success


if __name__ == "__main__":
    ok = demo_orchestrator()
    print(f"\nDemo result: {ok}")
