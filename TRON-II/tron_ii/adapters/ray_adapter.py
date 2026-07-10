"""Ray integration adapter for TRON-II hybrid training."""
from __future__ import annotations

from typing import Any, Dict

from ..hybrid import HybridAdapter

try:
    import ray  # type: ignore
    RAY_AVAILABLE = True
except ImportError:
    RAY_AVAILABLE = False


class RayAdapter(HybridAdapter):
    """Wraps Ray remote execution for TRON-II training."""

    def __init__(self) -> None:
        super().__init__("ray")
        if not RAY_AVAILABLE:
            raise ImportError("ray is not installed")

    def train(self, dataset: Any, config: Dict[str, Any]) -> Dict[str, float]:
        if not RAY_AVAILABLE:
            raise ImportError("ray is not installed")

        model = dataset.get("model") if isinstance(dataset, dict) else None
        env = dataset.get("env") if isinstance(dataset, dict) else None
        total_timesteps = int(config.get("total_timesteps", 10_000))

        if model is None or env is None:
            raise ValueError("RayAdapter requires 'model' and 'env' in dataset")
        if not hasattr(model, "learn"):
            raise RuntimeError("Provided model is not compatible with ray training semantics")

        if not ray.is_initialized():
            ray.init(ignore_reinit_error=True, include_dashboard=False)

        @ray.remote
        def train_remote(model: Any, total_timesteps: int) -> bool:
            model.learn(total_timesteps=total_timesteps)
            return True

        ray.get(train_remote.remote(model, total_timesteps))

        return {
            "capability_gain": float(config.get("capability_gain", 1.0)),
            "cost": float(config.get("cost", 1.0)),
        }

    def evaluate(self, model: Any, dataset: Any) -> Dict[str, float]:
        if hasattr(model, "predict"):
            return {"capability_gain": 0.0}
        return {"capability_gain": 0.0}
