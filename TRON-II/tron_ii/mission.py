from dataclasses import dataclass
from typing import Any, Dict, List

@dataclass
class TrainingPhase:
    name: str
    module: str
    substrate: str
    resources: Dict[str, Any]
    budget: float

@dataclass
class MissionPlan:
    mission_name: str
    phases: List[TrainingPhase]
    objective: str
    budget: float

class MissionPlanner:
    def __init__(self):
        self._missions = {}

    def create_mission(self, mission_name: str, objective: str, budget: float) -> MissionPlan:
        plan = MissionPlan(mission_name=mission_name, phases=[], objective=objective, budget=budget)
        self._missions[mission_name] = plan
        return plan

    def add_phase(self, mission_name: str, phase: TrainingPhase) -> None:
        plan = self._missions[mission_name]
        plan.phases.append(phase)

    def get_plan(self, mission_name: str) -> MissionPlan:
        return self._missions[mission_name]
