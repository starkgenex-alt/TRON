from typing import Dict

class UtilityEngine:
    def score(self, metrics: Dict[str, float], cost: float) -> float:
        if cost <= 0:
            return 0.0
        return metrics.get("capability_gain", 0.0) / cost
