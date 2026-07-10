"""TRON-II adaptive training intelligence package."""

from .mission import MissionPlanner, TrainingPhase
from .registry import ArtifactRegistry, ArtifactMetadata
from .substrate import SubstrateManager, Substrate
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
