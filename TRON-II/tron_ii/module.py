from dataclasses import dataclass
from typing import Dict

@dataclass
class CapabilityModule:
    module_id: str
    name: str
    description: str
    preferred_substrate: str
    complexity: float
    task_type: str
    dataset_size: int
    metrics: Dict[str, float]
