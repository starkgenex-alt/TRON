"""Demo: Adaptive Policy Learning from Training Outcomes

This demo shows how TRON-II becomes smarter over time by learning
from training outcomes and adjusting decisions based on what actually worked.
"""
import tempfile
from pathlib import Path
from datetime import datetime

from tron_ii import (
    TrainingOrchestrator,
    TrainingConfig,
    CapabilityModule,
    OutcomeLog,
    TrainingOutcome,
)


def demonstrate_outcome_feedback():
    """Show how the system learns from outcomes and improves decisions."""
    print("=" * 70)
    print("TRON-II: Adaptive Policy Learning from Outcomes")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as tmpdir:
        # Setup persistent storage
        artifact_path = Path(tmpdir) / "artifacts.json"
        outcome_path = Path(tmpdir) / "outcomes.json"

        print("\n[PHASE 1] Initial Training Runs")
        print("-" * 70)
        print("Running first batch of training with different adapters...")
        print("The policy starts with heuristic defaults.\n")

        # Create first orchestrator (no outcome history yet)
        orch1 = TrainingOrchestrator(
            artifact_registry_path=str(artifact_path),
            outcome_log_path=str(outcome_path),
        )

        module = CapabilityModule(
            module_id="learning_module",
            name="Learning Module",
            description="Module that will be trained multiple times",
            preferred_substrate="cpu",
            complexity=1.0,
            task_type="reinforcement",
            dataset_size=1,
            metrics={"capability_gain": 1.0},
        )

        # Simulate first run with sb3
        print("→ Run 1: Training with SB3 adapter")
        config1 = TrainingConfig(
            task_name="run_1_sb3",
            adapter_type="sb3",
            modules=[module],
            total_timesteps=100,
        )
        # Simulate outcome where sb3 performs well
        outcome1 = TrainingOutcome(
            artifact_id="run_1_sb3-learning_module-sb3",
            adapter_name="sb3",
            module_id="learning_module",
            expected_capability_gain=1.0,
            actual_capability_gain=0.95,  # Excellent - near expected
            expected_cost=1.0,
            actual_cost=0.9,  # Cheaper than expected!
            success=True,
            timestamp=datetime.now().isoformat(),
        )
        orch1.outcome_log.record(outcome1)
        print(f"  ✓ SB3 delivered: {outcome1.actual_capability_gain:.2f} capability (expected {outcome1.expected_capability_gain:.2f})")
        print(f"    Accuracy: {outcome1.accuracy():.1%}\n")

        # Simulate second run with ray
        print("→ Run 2: Training with Ray adapter")
        config2 = TrainingConfig(
            task_name="run_2_ray",
            adapter_type="ray",
            modules=[module],
            total_timesteps=100,
        )
        outcome2 = TrainingOutcome(
            artifact_id="run_2_ray-learning_module-ray",
            adapter_name="ray",
            module_id="learning_module",
            expected_capability_gain=0.9,
            actual_capability_gain=0.3,  # Poor - way below expected
            expected_cost=0.8,
            actual_cost=1.5,  # Much more expensive
            success=False,
            timestamp=datetime.now().isoformat(),
        )
        orch1.outcome_log.record(outcome2)
        print(f"  ✗ Ray delivered: {outcome2.actual_capability_gain:.2f} capability (expected {outcome2.expected_capability_gain:.2f})")
        print(f"    Accuracy: {outcome2.accuracy():.1%}\n")

        # Simulate third run with transformers
        print("→ Run 3: Training with Transformers adapter")
        outcome3 = TrainingOutcome(
            artifact_id="run_3_transformers-learning_module-transformers",
            adapter_name="transformers",
            module_id="learning_module",
            expected_capability_gain=0.8,
            actual_capability_gain=0.75,  # Good
            expected_cost=2.0,
            actual_cost=1.8,
            success=True,
            timestamp=datetime.now().isoformat(),
        )
        orch1.outcome_log.record(outcome3)
        print(f"  ✓ Transformers delivered: {outcome3.actual_capability_gain:.2f} capability (expected {outcome3.expected_capability_gain:.2f})")
        print(f"    Accuracy: {outcome3.accuracy():.1%}\n")

        # Persist outcomes
        orch1.outcome_log.save()
        print("✓ Outcomes saved to disk\n")

        # Show historical performance
        print("[PHASE 2] Policy Analysis - What We Learned")
        print("-" * 70)
        sb3_accuracy = orch1.outcome_log.adapter_accuracy("sb3")
        ray_accuracy = orch1.outcome_log.adapter_accuracy("ray")
        transformers_accuracy = orch1.outcome_log.adapter_accuracy("transformers")

        sb3_success = orch1.outcome_log.adapter_success_rate("sb3")
        ray_success = orch1.outcome_log.adapter_success_rate("ray")
        transformers_success = orch1.outcome_log.adapter_success_rate("transformers")

        print("\nAdapter Historical Performance:")
        print(f"  SB3:")
        print(f"    - Accuracy: {sb3_accuracy:.1%} (predictions vs reality)")
        print(f"    - Success Rate: {sb3_success:.0%}")
        print(f"\n  Ray:")
        print(f"    - Accuracy: {ray_accuracy:.1%}")
        print(f"    - Success Rate: {ray_success:.0%}")
        print(f"\n  Transformers:")
        print(f"    - Accuracy: {transformers_accuracy:.1%}")
        print(f"    - Success Rate: {transformers_success:.0%}\n")

        # Now show how this affects decisions
        print("[PHASE 3] Adaptive Decision Making")
        print("-" * 70)

        # Create new orchestrator that loads the historical outcomes
        orch2 = TrainingOrchestrator(
            artifact_registry_path=str(artifact_path),
            outcome_log_path=str(outcome_path),
        )

        print("\nPolicy now has access to historical outcomes.")
        print("When choosing which adapter to use, it will adjust scores based on")
        print("how well each adapter performed in the past.\n")

        # Score the same estimates with historical knowledge
        test_estimates = {
            "sb3": {"capability_gain": 1.0, "cost": 1.0},
            "ray": {"capability_gain": 1.0, "cost": 1.0},
            "transformers": {"capability_gain": 1.0, "cost": 1.0},
        }

        print("Scoring identical estimates for all adapters:")
        print("(Before: all would score equally → After: scored by history)\n")

        sb3_score = orch2.manager.policy.score_estimate(
            test_estimates["sb3"], preferred_substrate="cpu", adapter_name="sb3"
        )
        ray_score = orch2.manager.policy.score_estimate(
            test_estimates["ray"], preferred_substrate="gpu", adapter_name="ray"
        )
        transformers_score = orch2.manager.policy.score_estimate(
            test_estimates["transformers"], preferred_substrate="cpu", adapter_name="transformers"
        )

        print(f"  SB3 score:           {sb3_score:.3f} ⬆️  (historically accurate)")
        print(f"  Ray score:           {ray_score:.3f} ⬇️  (historically inaccurate)")
        print(f"  Transformers score:  {transformers_score:.3f} ✓  (moderately good)\n")

        print("Decision: The system will now PREFER SB3 for similar tasks,")
        print("         because it demonstrated the best accuracy and success rate.\n")

        # Show policy decision
        best_adapter = orch2.manager.policy.decide_adapter(
            estimates=test_estimates,
            preferred_substrate="cpu",
            available=["sb3", "ray", "transformers"],
            requested=None,
        )
        print(f"✓ Policy selected: {best_adapter}\n")

        print("=" * 70)
        print("KEY INSIGHT: Without outcome tracking, the policy would have")
        print("had no way to learn. Now it's data-driven and becomes smarter")
        print("each time a training run completes!")
        print("=" * 70)


if __name__ == "__main__":
    demonstrate_outcome_feedback()
