"""Tests for outcome tracking and feedback system."""
import pytest
import tempfile
from pathlib import Path
from datetime import datetime

from tron_ii.outcomes import TrainingOutcome, OutcomeLog
from tron_ii.policy import TrainingPolicy


def test_training_outcome_accuracy():
    """Test accuracy calculation for outcomes."""
    outcome = TrainingOutcome(
        artifact_id="test-1",
        adapter_name="sb3",
        module_id="module-1",
        expected_capability_gain=1.0,
        actual_capability_gain=0.95,
        expected_cost=1.0,
        actual_cost=1.0,
        success=True,
        timestamp=datetime.now().isoformat(),
    )
    # Should be close to 1.0 since actual (0.95) is close to expected (1.0)
    assert 0.9 < outcome.accuracy() < 1.0


def test_training_outcome_accuracy_large_error():
    """Test accuracy when estimate is very wrong."""
    outcome = TrainingOutcome(
        artifact_id="test-2",
        adapter_name="ray",
        module_id="module-1",
        expected_capability_gain=1.0,
        actual_capability_gain=0.1,
        expected_cost=1.0,
        actual_cost=1.0,
        success=True,
        timestamp=datetime.now().isoformat(),
    )
    # Should be much lower since error is large
    assert outcome.accuracy() < 0.2


def test_outcome_log_persistence():
    """Test saving and loading outcomes."""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = Path(tmpdir) / "outcomes.json"
        log = OutcomeLog(storage_path=str(log_path))

        outcome1 = TrainingOutcome(
            artifact_id="test-1",
            adapter_name="sb3",
            module_id="module-1",
            expected_capability_gain=1.0,
            actual_capability_gain=0.95,
            expected_cost=1.0,
            actual_cost=0.95,
            success=True,
            timestamp=datetime.now().isoformat(),
        )
        log.record(outcome1)
        log.save()

        # Load in new instance
        log2 = OutcomeLog(storage_path=str(log_path))
        assert len(log2.outcomes) == 1
        assert log2.outcomes[0].artifact_id == "test-1"
        assert log2.outcomes[0].adapter_name == "sb3"


def test_outcome_log_adapter_accuracy():
    """Test adapter accuracy calculation."""
    log = OutcomeLog()

    # Add multiple outcomes for sb3
    for i in range(3):
        outcome = TrainingOutcome(
            artifact_id=f"test-{i}",
            adapter_name="sb3",
            module_id="module-1",
            expected_capability_gain=1.0,
            actual_capability_gain=0.9,
            expected_cost=1.0,
            actual_cost=1.0,
            success=True,
            timestamp=datetime.now().isoformat(),
        )
        log.record(outcome)

    accuracy = log.adapter_accuracy("sb3")
    assert accuracy is not None
    assert 0.8 < accuracy < 0.95  # All outcomes should have similar accuracy


def test_outcome_log_adapter_success_rate():
    """Test adapter success rate calculation."""
    log = OutcomeLog()

    # Add 3 successful outcomes
    for i in range(3):
        outcome = TrainingOutcome(
            artifact_id=f"success-{i}",
            adapter_name="transformers",
            module_id="module-1",
            expected_capability_gain=1.0,
            actual_capability_gain=1.0,
            expected_cost=1.0,
            actual_cost=1.0,
            success=True,
            timestamp=datetime.now().isoformat(),
        )
        log.record(outcome)

    # Add 1 failed outcome
    outcome = TrainingOutcome(
        artifact_id="fail-1",
        adapter_name="transformers",
        module_id="module-1",
        expected_capability_gain=1.0,
        actual_capability_gain=0.0,
        expected_cost=1.0,
        actual_cost=1.0,
        success=False,
        timestamp=datetime.now().isoformat(),
    )
    log.record(outcome)

    success_rate = log.adapter_success_rate("transformers")
    assert success_rate == 0.75  # 3/4


def test_outcome_log_module_outcomes():
    """Test filtering outcomes by module."""
    log = OutcomeLog()

    # Add outcomes for module-1
    for i in range(2):
        outcome = TrainingOutcome(
            artifact_id=f"mod1-{i}",
            adapter_name="sb3",
            module_id="module-1",
            expected_capability_gain=1.0,
            actual_capability_gain=1.0,
            expected_cost=1.0,
            actual_cost=1.0,
            success=True,
            timestamp=datetime.now().isoformat(),
        )
        log.record(outcome)

    # Add outcome for module-2
    outcome = TrainingOutcome(
        artifact_id="mod2-1",
        adapter_name="sb3",
        module_id="module-2",
        expected_capability_gain=1.0,
        actual_capability_gain=1.0,
        expected_cost=1.0,
        actual_cost=1.0,
        success=True,
        timestamp=datetime.now().isoformat(),
    )
    log.record(outcome)

    outcomes_mod1 = log.module_outcomes("module-1")
    assert len(outcomes_mod1) == 2
    assert all(o.module_id == "module-1" for o in outcomes_mod1)


def test_policy_uses_outcome_history():
    """Test that policy adjusts scores based on historical outcomes."""
    log = OutcomeLog()

    # Record excellent outcomes for sb3
    for i in range(5):
        outcome = TrainingOutcome(
            artifact_id=f"good-{i}",
            adapter_name="sb3",
            module_id="module-1",
            expected_capability_gain=1.0,
            actual_capability_gain=0.95,
            expected_cost=1.0,
            actual_cost=0.95,
            success=True,
            timestamp=datetime.now().isoformat(),
        )
        log.record(outcome)

    # Record poor outcomes for ray
    for i in range(3):
        outcome = TrainingOutcome(
            artifact_id=f"bad-{i}",
            adapter_name="ray",
            module_id="module-1",
            expected_capability_gain=1.0,
            actual_capability_gain=0.3,
            expected_cost=1.0,
            actual_cost=1.5,
            success=False,
            timestamp=datetime.now().isoformat(),
        )
        log.record(outcome)

    policy = TrainingPolicy(outcome_log=log)

    # Score estimates
    estimates = {
        "sb3": {"capability_gain": 1.0, "cost": 1.0},
        "ray": {"capability_gain": 1.0, "cost": 1.0},
    }

    sb3_score = policy.score_estimate(estimates["sb3"], preferred_substrate="cpu", adapter_name="sb3")
    ray_score = policy.score_estimate(estimates["ray"], preferred_substrate="gpu", adapter_name="ray")

    # sb3 should score higher due to excellent history
    assert sb3_score > ray_score


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
