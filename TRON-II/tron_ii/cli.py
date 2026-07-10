"""Command-line interface for TRON-II training orchestration."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Dict, Optional

from .module import CapabilityModule
from .orchestrator import TrainingConfig, TrainingOrchestrator


def build_sb3_model(env: Any) -> Any:
    try:
        import stable_baselines3 as sb3  # type: ignore
    except ImportError as exc:
        raise RuntimeError("stable-baselines3 is required for SB3 training") from exc

    return sb3.PPO("MlpPolicy", env, verbose=0)


def build_transformers_model() -> Any:
    try:
        from transformers import AutoModelForSequenceClassification, AutoTokenizer  # type: ignore
    except ImportError as exc:
        raise RuntimeError("transformers is required for Transformers training") from exc

    tokenizer = AutoTokenizer.from_pretrained("distilbert-base-uncased")
    model = AutoModelForSequenceClassification.from_pretrained("distilbert-base-uncased", num_labels=2)
    return model


def load_transformers_data() -> Dict[str, Any]:
    try:
        from datasets import load_dataset  # type: ignore
    except ImportError as exc:
        raise RuntimeError("datasets is required for Transformers training") from exc

    dataset = load_dataset("ag_news", split="train[:1%]")
    return {"train_dataset": dataset}


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a TRON-II training demo via the orchestrator")
    parser.add_argument("--adapter", default="auto", help="Adapter to use: auto, sb3, ray, transformers")
    parser.add_argument("--task-name", default="tron_cli_demo", help="Name of the training task")
    parser.add_argument("--timesteps", type=int, default=128, help="Total timesteps for SB3/Ray training")
    parser.add_argument("--budget", type=float, default=1.0, help="Mission budget")
    parser.add_argument("--substrate", default="cpu", help="Preferred substrate hint for the mission")
    parser.add_argument("--artifact-registry", default="tron_artifacts.json", help="Path to persist artifact registry metadata")
    parser.add_argument("--outcome-log", default="tron_outcomes.json", help="Path to persist training outcomes for feedback")
    parser.add_argument("--depin-master-url", default=None, help="URL of the TRON DePIN master scheduler")
    parser.add_argument("--depin-priority", type=int, default=1, help="Priority for DePIN job submission")
    parser.add_argument("--depin-requires-gpu", action="store_true", help="Mark DePIN job as requiring GPU")
    return parser.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    args = parse_args(argv)
    orchestrator = TrainingOrchestrator(
        artifact_registry_path=args.artifact_registry,
        outcome_log_path=args.outcome_log,
    )

    module = CapabilityModule(
        module_id="cli_demo",
        name="CLI Demo Module",
        description="A small module used by the TRON-II CLI demo",
        preferred_substrate=args.substrate,
        complexity=1.0,
        task_type="reinforcement",
        dataset_size=1,
        metrics={"capability_gain": 1.0},
    )

    config = TrainingConfig(
        task_name=args.task_name,
        objective="demonstrate orchestrated training",
        budget=args.budget,
        total_timesteps=args.timesteps,
        adapter_type=args.adapter,
        modules=[module],
        depin_master_url=args.depin_master_url,
        depin_priority=args.depin_priority,
        depin_requires_gpu=args.depin_requires_gpu,
    )

    model: Optional[Any] = None
    env: Optional[Any] = None
    dataset: Dict[str, Any] = {}

    try:
        if args.adapter in ("auto", "sb3", "ray"):
            try:
                import gymnasium as gym  # type: ignore
            except ImportError as exc:
                raise RuntimeError("gymnasium is required for SB3/Ray demo") from exc

            env = gym.make("CartPole-v1")
            model = build_sb3_model(env)

        elif args.adapter == "transformers":
            model = build_transformers_model()
            dataset = load_transformers_data()
        else:
            raise ValueError(f"Unsupported adapter: {args.adapter}")

        success = orchestrator.run_training(config, model, env or dataset)
        summary = orchestrator.get_training_summary()
        print(f"\n[Summary]\nTotal runs: {summary['total_runs']}\nSuccessful: {summary['successful']}\nFailed: {summary['failed']}")
        return 0 if success else 1
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    finally:
        if env is not None and hasattr(env, "close"):
            env.close()


if __name__ == "__main__":
    raise SystemExit(main())
