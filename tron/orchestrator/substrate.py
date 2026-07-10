from dataclasses import dataclass
from typing import Dict, List

@dataclass
class Substrate:
    name: str
    type: str
    cost_per_cycle: float
    capabilities: Dict[str, float]

class SubstrateManager:
    def __init__(self):
        self._substrates: Dict[str, Substrate] = {}

    def register(self, substrate: Substrate) -> None:
        self._substrates[substrate.name] = substrate

    def get(self, name: str) -> Substrate:
        return self._substrates[name]

    def select(self, hint: str) -> Substrate:
        if hint in self._substrates:
            return self._substrates[hint]
        return next(iter(self._substrates.values()))

    def list_substrates(self) -> Dict[str, Substrate]:
        return dict(self._substrates)
