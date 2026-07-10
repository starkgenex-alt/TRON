from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Sequence

from .utility import UtilityEngine


class HybridAdapter(ABC):
    name: str

    def __init__(self, name: str) -> None:
        self.name = name

    @abstractmethod
    def train(self, dataset: Any, config: Dict[str, Any]) -> Dict[str, float]:
        raise NotImplementedError()

    @abstractmethod
    def evaluate(self, model: Any, dataset: Any) -> Dict[str, float]:
        raise NotImplementedError()


class DummyHybridAdapter(HybridAdapter):
    def __init__(self) -> None:
        super().__init__("dummy")

    def train(self, dataset: Any, config: Dict[str, Any]) -> Dict[str, float]:
        return {"capability_gain": 0.0, "cost": float(config.get("cost", 0.0))}

    def evaluate(self, model: Any, dataset: Any) -> Dict[str, float]:
        return {"capability_gain": 0.0}


try:
    from sklearn.base import BaseEstimator  # type: ignore
    from sklearn.model_selection import train_test_split  # type: ignore
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False


class SklearnAdapter(HybridAdapter):
    def __init__(self) -> None:
        super().__init__("scikit-learn")
        if not SKLEARN_AVAILABLE:
            raise ImportError("scikit-learn is not installed")

    def train(self, dataset: Any, config: Dict[str, Any]) -> Dict[str, float]:
        if not SKLEARN_AVAILABLE:
            raise ImportError("scikit-learn is not installed")
        model = config.get("model")
        if hasattr(model, "fit"):
            x_train, x_test, y_train, y_test = train_test_split(dataset["X"], dataset["y"], test_size=0.2)
            model.fit(x_train, y_train)
            score = model.score(x_test, y_test)
            return {"capability_gain": float(score), "cost": float(config.get("cost", 1.0))}
        return {"capability_gain": 0.0, "cost": float(config.get("cost", 1.0))}

    def evaluate(self, model: Any, dataset: Any) -> Dict[str, float]:
        if not SKLEARN_AVAILABLE:
            raise ImportError("scikit-learn is not installed")
        if hasattr(model, "score"):
            return {"capability_gain": float(model.score(dataset["X"], dataset["y"]))}
        return {"capability_gain": 0.0}


try:
    import ray  # type: ignore
    RAY_AVAILABLE = True
except ImportError:
    RAY_AVAILABLE = False


class RayAdapter(HybridAdapter):
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
            raise RuntimeError("Provided model is not compatible with Ray training semantics")

        if not ray.is_initialized():
            ray.init(ignore_reinit_error=True, include_dashboard=False)

        @ray.remote
        def train_remote(remote_model: Any, remote_timesteps: int) -> Any:
            remote_model.learn(total_timesteps=remote_timesteps)
            return remote_model

        model = ray.get(train_remote.remote(model, total_timesteps))

        if hasattr(model, "save") and config.get("save_path"):
            model.save(str(config.get("save_path")))

        return {
            "capability_gain": float(config.get("capability_gain", 1.0)),
            "cost": float(config.get("cost", 1.0)),
        }

    def evaluate(self, model: Any, dataset: Any) -> Dict[str, float]:
        if hasattr(model, "predict"):
            return {"capability_gain": 0.0}
        return {"capability_gain": 0.0}


class HybridIntegrator:
    def __init__(self, adapters: Optional[Sequence[HybridAdapter]] = None) -> None:
        self.adapters: List[HybridAdapter] = list(adapters or [DummyHybridAdapter()])
        self.utility = UtilityEngine()

    def register_adapter(self, adapter: HybridAdapter) -> None:
        self.adapters.append(adapter)

    def available_names(self) -> List[str]:
        return [adapter.name for adapter in self.adapters]

    def select(self, preferred: str) -> HybridAdapter:
        match = next((adapter for adapter in self.adapters if adapter.name == preferred), None)
        if match is not None:
            return match
        return self.adapters[0]

    def select_best(self, preferred: Optional[str] = None, dataset: Any = None) -> HybridAdapter:
        if preferred:
            return self.select(preferred)

        available = self.available_names()
        if dataset and isinstance(dataset, dict):
            adapter_estimates = dataset.get("adapter_estimates")
            if isinstance(adapter_estimates, dict):
                best_adapter: Optional[HybridAdapter] = None
                best_score = float("-inf")
                for name, estimate in adapter_estimates.items():
                    if name not in available or not isinstance(estimate, dict):
                        continue
                    score = self.utility.score(estimate, float(estimate.get("cost", 1.0)))
                    if score > best_score:
                        best_score = score
                        best_adapter = self.select(name)
                if best_adapter is not None:
                    return best_adapter

            preferred_substrate = dataset.get("selected_substrate")
            model = dataset.get("model")
            env = dataset.get("env")

            if preferred_substrate == "gpu" and "ray" in available:
                return self.select("ray")
            if preferred_substrate == "cpu" and "sb3" in available:
                return self.select("sb3")

            if model is not None and env is not None:
                if "sb3" in available:
                    return self.select("sb3")
                if "ray" in available:
                    return self.select("ray")
            if "scikit-learn" in available and "X" in dataset and "y" in dataset:
                return self.select("scikit-learn")

        for preferred_name in ["sb3", "ray", "transformers", "scikit-learn"]:
            if preferred_name in available:
                return self.select(preferred_name)

        return self.adapters[0]

    @classmethod
    def default(cls) -> "HybridIntegrator":
        adapters: List[HybridAdapter] = [DummyHybridAdapter()]
        if SKLEARN_AVAILABLE:
            adapters.append(SklearnAdapter())

        try:
            from .adapters.transformers_adapter import TransformersAdapter

            adapters.append(TransformersAdapter())
        except Exception:
            pass

        try:
            from .adapters.sb3_adapter import SB3Adapter

            adapters.append(SB3Adapter())
        except Exception:
            pass

        if RAY_AVAILABLE:
            try:
                from .adapters.ray_adapter import RayAdapter

                adapters.append(RayAdapter())
            except Exception:
                pass

        return cls(adapters)
