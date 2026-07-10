"""TRON Orchestrator - Adaptive training intelligence for hybrid ML workloads."""

try:
    from .orchestrator import TrainingOrchestrator, TrainingConfig
    from .mission import MissionPlanner, MissionPlan, TrainingPhase
    from .registry import ArtifactRegistry, ArtifactMetadata
    from .substrate import SubstrateManager, Substrate
    from .policy import TrainingPolicy
    from .utility import UtilityEngine
    from .depin import DePINClient
    from .hybrid import HybridIntegrator
    from .outcomes import OutcomeLog, TrainingOutcome
    from .adapters import RayAdapter, SB3Adapter, TransformersAdapter

    __all__ = [
        "TrainingOrchestrator",
        "TrainingConfig",
        "MissionPlanner",
        "MissionPlan",
        "ArtifactRegistry",
        "SubstrateManager",
        "Substrate",
        "TrainingPolicy",
        "UtilityEngine",
        "DePINClient",
        "HybridIntegrator",
        "OutcomeLog",
        "TrainingOutcome",
        "RayAdapter",
        "SB3Adapter",
        "TransformersAdapter",
    ]
except ImportError as e:
    pass
from .utility import UtilityEngine
from .module import CapabilityModule
from .policy import TrainingPolicy
from .manager import TrainingManager
from .hybrid import HybridAdapter, HybridIntegrator
from .orchestrator import TrainingOrchestrator, TrainingConfig
from .outcomes import OutcomeLog, TrainingOutcome
from .depin import DePINClient
from .cli import main as cli_main

__all__ = [
    "MissionPlanner",
    "TrainingPhase",
    "ArtifactRegistry",
    "ArtifactMetadata",
    "SubstrateManager",
    "Substrate",
    "UtilityEngine",
    "CapabilityModule",
    "TrainingPolicy",
    "TrainingManager",
    "HybridAdapter",
    "HybridIntegrator",
    "TrainingOrchestrator",
    "TrainingConfig",
    "OutcomeLog",
    "TrainingOutcome",
    "DePINClient",
    "cli_main",
]
