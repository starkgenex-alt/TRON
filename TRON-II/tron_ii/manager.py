from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .mission import MissionPlanner, MissionPlan, TrainingPhase
from .module import CapabilityModule
from .policy import TrainingPolicy
from .registry import ArtifactRegistry, ArtifactMetadata
from .substrate import SubstrateManager
from .utility import UtilityEngine

@dataclass
class TrainingMission:
    name: str
    objective: str
    budget: float
    modules: List[CapabilityModule] = field(default_factory=list)
    plan: Optional[MissionPlan] = None

class TrainingManager:
    def __init__(
        self,
        planner: MissionPlanner,
        registry: ArtifactRegistry,
        substrate_manager: SubstrateManager,
        utility_engine: UtilityEngine,
        policy: Optional[TrainingPolicy] = None,
    ):
        self.planner = planner
        self.registry = registry
        self.substrate_manager = substrate_manager
        self.utility_engine = utility_engine
        self.policy = policy or TrainingPolicy()
        self._missions: Dict[str, TrainingMission] = {}

    def create_mission(self, name: str, objective: str, budget: float, modules: List[CapabilityModule]) -> TrainingMission:
        mission = TrainingMission(name=name, objective=objective, budget=budget, modules=modules)
        self._missions[name] = mission
        return mission

    def recommend_substrate(self, module: CapabilityModule) -> str:
        substrates = self.substrate_manager.list_substrates()
        if module.preferred_substrate in substrates:
            return module.preferred_substrate

        substrate_weights = {
            name: (substrate.capabilities.get("compute", 0.0) / max(substrate.cost_per_cycle, 1e-6))
            for name, substrate in substrates.items()
        }
        chosen = self.policy.decide_substrate(module.preferred_substrate, substrate_weights)
        if chosen is None or chosen not in substrates:
            chosen = next(iter(substrates))
        return chosen

    def best_reuse_artifact(self, module: CapabilityModule) -> Optional[ArtifactMetadata]:
        artifacts = self.registry.find_by_module(module.module_id)
        if not artifacts:
            return None
        return max(
            artifacts,
            key=lambda artifact: self.utility_engine.score(artifact.metrics, artifact.size_bytes or 1.0),
        )

    def should_reuse(self, module: CapabilityModule, retrain_cost: float) -> bool:
        artifact = self.best_reuse_artifact(module)
        if artifact is None:
            return False
        reuse_score = self.utility_engine.score(artifact.metrics, artifact.size_bytes or 1.0)
        retrain_score = self.utility_engine.score(module.metrics, retrain_cost)
        return self.policy.decide_reuse(reuse_score, retrain_score)

    def plan_mission(self, mission_name: str) -> MissionPlan:
        mission = self._missions[mission_name]
        plan = self.planner.create_mission(mission.name, mission.objective, mission.budget)
        for module in mission.modules:
            substrate_name = self.recommend_substrate(module)
            phase_budget = mission.budget / max(1, len(mission.modules))
            phase = TrainingPhase(
                name=f"train-{module.module_id}",
                module=module.module_id,
                substrate=substrate_name,
                resources={"preferred_substrate": module.preferred_substrate, "task_type": module.task_type},
                budget=phase_budget,
            )
            plan.phases.append(phase)
        mission.plan = plan
        return plan
