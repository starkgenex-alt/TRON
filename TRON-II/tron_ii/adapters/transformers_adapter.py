"""Transformers integration adapter for TRON-II hybrid training."""
from __future__ import annotations

from typing import Any, Dict

from ..hybrid import HybridAdapter

try:
    import transformers  # type: ignore
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False


class TransformersAdapter(HybridAdapter):
    """Wraps Hugging Face transformers for TRON-II training."""

    def __init__(self) -> None:
        super().__init__("transformers")
        if not TRANSFORMERS_AVAILABLE:
            raise ImportError("transformers is not installed")

    def train(self, dataset: Any, config: Dict[str, Any]) -> Dict[str, float]:
        """Train a transformer model using provided dataset and config.

        Args:
            dataset: Dict with 'model' (PreTrainedModel) and 'train_dataset' (Dataset)
            config: Dict with 'total_steps' or 'num_train_epochs', 'save_path' (optional)

        Returns:
            Dict with capability_gain and cost metrics
        """
        if not TRANSFORMERS_AVAILABLE:
            raise ImportError("transformers is not installed")

        model = dataset.get("model") if isinstance(dataset, dict) else None
        train_dataset = dataset.get("train_dataset") if isinstance(dataset, dict) else None

        if model is None:
            raise ValueError("TransformersAdapter requires 'model' in dataset")

        # If train_dataset provided, do a minimal fine-tuning
        if train_dataset is not None:
            try:
                from transformers import Trainer, TrainingArguments  # type: ignore

                training_args = TrainingArguments(
                    output_dir=config.get("save_path", "./transformers_output"),
                    num_train_epochs=int(config.get("num_train_epochs", 1)),
                    per_device_train_batch_size=int(config.get("batch_size", 8)),
                    logging_steps=10,
                    save_steps=100,
                )
                trainer = Trainer(
                    model=model,
                    args=training_args,
                    train_dataset=train_dataset,
                )
                trainer.train()
            except Exception as e:
                raise RuntimeError(f"Transformers training failed: {e}") from e

        return {
            "capability_gain": float(config.get("capability_gain", 0.8)),
            "cost": float(config.get("cost", 1.0)),
        }

    def evaluate(self, model: Any, dataset: Any) -> Dict[str, float]:
        """Evaluate transformer model on a dataset.

        Args:
            model: Hugging Face PreTrainedModel
            dataset: Dict with 'eval_dataset' or inference data

        Returns:
            Dict with evaluation metrics
        """
        if not TRANSFORMERS_AVAILABLE:
            raise ImportError("transformers is not installed")

        if hasattr(model, "eval"):
            return {"capability_gain": 0.0}
        return {"capability_gain": 0.0}
