"""Simple adapter scaffold for Stable-Baselines3 integration."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from ..hybrid import HybridAdapter


class SB3Adapter(HybridAdapter):
    """Wraps Stable-Baselines3 training calls for TRON-II."""

    def __init__(self) -> None:
        super().__init__("sb3")

    def train(self, dataset: Any, config: Dict[str, Any]) -> Dict[str, float]:
        try:
            import stable_baselines3 as sb3  # type: ignore
        except Exception as e:
            raise RuntimeError("stable-baselines3 is not available: install it to use SB3Adapter") from e

        model = dataset.get("model") if isinstance(dataset, dict) else None
        env = dataset.get("env") if isinstance(dataset, dict) else None
        total_timesteps = int(config.get("total_timesteps", 10_000))
        save_path = config.get("save_path", "sb3_demo_model")

        if model is None or env is None:
            raise ValueError("SB3Adapter requires 'model' and 'env' in dataset")
        if not hasattr(model, "learn"):
            raise RuntimeError("Provided model is not compatible with Stable-Baselines3")

        model.learn(total_timesteps=total_timesteps)
        if hasattr(model, "save"):
            model.save(str(Path(save_path)))

        return {
            "capability_gain": float(config.get("capability_gain", 1.0)),
            "cost": float(config.get("cost", 1.0)),
        }

    def evaluate(self, model: Any, dataset: Any) -> Dict[str, float]:
        if hasattr(model, "predict"):
            return {"capability_gain": 0.0}
        return {"capability_gain": 0.0}
