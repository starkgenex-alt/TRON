"""Outcome tracking and feedback for TRON-II decisions."""
from dataclasses import dataclass
from typing import Dict, List, Optional
from pathlib import Path
import json
from datetime import datetime


@dataclass
class TrainingOutcome:
    """Record of a training run outcome vs expectations."""
    artifact_id: str
    adapter_name: str
    module_id: str
    expected_capability_gain: float
    actual_capability_gain: float
    expected_cost: float
    actual_cost: float
    success: bool
    timestamp: str

    def accuracy(self) -> float:
        """How close was the estimate to reality? 0.0 to 1.0."""
        if self.expected_capability_gain <= 0.0:
            return 0.0
        error = abs(self.expected_capability_gain - self.actual_capability_gain)
        return max(0.0, 1.0 - error / max(self.expected_capability_gain, 1.0))

    def to_dict(self) -> Dict:
        return {
            "artifact_id": self.artifact_id,
            "adapter_name": self.adapter_name,
            "module_id": self.module_id,
            "expected_capability_gain": self.expected_capability_gain,
            "actual_capability_gain": self.actual_capability_gain,
            "expected_cost": self.expected_cost,
            "actual_cost": self.actual_cost,
            "success": self.success,
            "timestamp": self.timestamp,
            "accuracy": self.accuracy(),
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "TrainingOutcome":
        return cls(
            artifact_id=data["artifact_id"],
            adapter_name=data["adapter_name"],
            module_id=data["module_id"],
            expected_capability_gain=float(data["expected_capability_gain"]),
            actual_capability_gain=float(data["actual_capability_gain"]),
            expected_cost=float(data["expected_cost"]),
            actual_cost=float(data["actual_cost"]),
            success=bool(data["success"]),
            timestamp=data["timestamp"],
        )


class OutcomeLog:
    """Track training outcomes for feedback and learning."""
    def __init__(self, storage_path: Optional[str] = None):
        self.outcomes: List[TrainingOutcome] = []
        self.storage_path = Path(storage_path) if storage_path else None
        if self.storage_path and self.storage_path.exists():
            try:
                self.load(self.storage_path)
            except Exception:
                self.outcomes = []

    def record(self, outcome: TrainingOutcome) -> None:
        """Record a training outcome."""
        self.outcomes.append(outcome)

    def adapter_accuracy(self, adapter_name: str) -> Optional[float]:
        """Average accuracy for an adapter across all outcomes."""
        adapter_outcomes = [o for o in self.outcomes if o.adapter_name == adapter_name]
        if not adapter_outcomes:
            return None
        return sum(o.accuracy() for o in adapter_outcomes) / len(adapter_outcomes)

    def adapter_success_rate(self, adapter_name: str) -> Optional[float]:
        """Success rate for an adapter."""
        adapter_outcomes = [o for o in self.outcomes if o.adapter_name == adapter_name]
        if not adapter_outcomes:
            return None
        successes = sum(1 for o in adapter_outcomes if o.success)
        return successes / len(adapter_outcomes)

    def module_outcomes(self, module_id: str) -> List[TrainingOutcome]:
        """Get all outcomes for a specific module."""
        return [o for o in self.outcomes if o.module_id == module_id]

    def save(self, path: Optional[Path] = None) -> None:
        """Persist outcomes to JSON."""
        p = Path(path) if path else self.storage_path
        if p is None:
            raise ValueError("No storage path configured for OutcomeLog")
        data = [o.to_dict() for o in self.outcomes]
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(data, indent=2))

    def load(self, path: Optional[Path] = None) -> None:
        """Load outcomes from JSON."""
        p = Path(path) if path else self.storage_path
        if p is None or not p.exists():
            return
        raw = json.loads(p.read_text())
        self.outcomes = [TrainingOutcome.from_dict(d) for d in raw]
