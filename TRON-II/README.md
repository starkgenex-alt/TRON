# TRON-II

TRON-II is the next stage of TRON: an adaptive training intelligence layer that optimizes AI capability per compute cost.

This subproject is focused on:

- strategic training mission planning
- artifact reuse and distillation
- substrate-aware training phase routing
- compute-efficient capability improvement
- stopping and phasing decisions based on marginal utility

## Goals

1. Build a mission planner that decomposes training into modules.
2. Build an artifact registry for reusable components.
3. Build a substrate abstraction layer for heterogeneous compute.
4. Build a utility engine to score compute vs capability.
5. Prototype training intelligence policies.
## Hybrid Adapter Integrations

TRON-II supports hybrid adapter integration for existing training frameworks. Current adapters include:

- `sb3` via `stable-baselines3`
- `ray` via `RayAdapter` when Ray is installed
- `scikit-learn` via `SklearnAdapter` when scikit-learn is installed
- `transformers` via `TransformerAdapter` when Hugging Face Transformers is installed

The orchestrator selects adapters by name and routes training through TRON-II's decision layer.

- `adapter_type="auto"`: TRON-II may automatically choose the highest-priority available adapter.

## Artifact Persistence

TRON-II now persists artifact metadata automatically after successful training runs.

- `ArtifactRegistry` stores artifact metadata in memory and can persist to JSON via `save()` and `load()`.
- `TrainingOrchestrator` registers artifacts after training and writes the registry to disk using the configured `storage_path`.
- By default, it saves to `tron_artifacts.json` if no registry path is provided.

Artifacts contain:

- `artifact_id`
- `module`
- `version`
- `metrics`
- `size_bytes`
- `substrates`

This enables reuse decisions to be based on actual training outcomes and artifact metadata.

## Outcome Tracking & Adaptive Policy Learning

TRON-II now learns from training outcomes to improve future decisions. This is the key mechanism for making the system truly adaptive.

### How It Works

1. **Outcome Recording**: After each training run, TRON-II records the actual results vs. what was expected:
   - Expected vs. actual capability gain
   - Expected vs. actual cost
   - Whether training succeeded
   - Timestamp of the run

2. **Historical Analysis**: The system tracks per-adapter metrics:
   - **Accuracy**: How close estimates were to reality (0-100%)
   - **Success Rate**: Percentage of successful training runs

3. **Adaptive Scoring**: When making future decisions, the policy uses historical performance to adjust adapter scores:
   - Adapters with better accuracy get higher scores
   - Adapters with better success rates get preference
   - The system gradually learns which adapters work best for which tasks

### Using Outcome Tracking

Enable outcome persistence via the CLI:

```bash
tron-ii --adapter auto --outcome-log ./tron_outcomes.json
```

Or programmatically:

```python
from tron_ii import TrainingOrchestrator, TrainingConfig

orch = TrainingOrchestrator(
    artifact_registry_path="artifacts.json",
    outcome_log_path="outcomes.json",  # New: Enable outcome tracking
)

# After training, outcomes are automatically recorded and persisted
success = orch.run_training(config, model, env)
```

### Demo: Watch It Learn

See the adaptive feedback loop in action:

```bash
python demo_outcome_feedback.py
```

This demo shows:
- How initial training runs are recorded
- How the system calculates adapter accuracy and success rates
- How the policy adjusts future decisions based on historical performance
- How the system increasingly prefers better-performing adapters

The demo output includes:
```
SB3:
  - Accuracy: 95.0% (predictions vs reality)
  - Success Rate: 100%

Ray:
  - Accuracy: 40.0%
  - Success Rate: 0%

Decision: SB3 score: 1.034 vs Ray score: 0.631
→ Policy selected: sb3
```

## CLI Usage

Install the package in editable mode or ensure the repository root is on `PYTHONPATH`.

Run the CLI demo:

```bash
python -m tron_ii.cli --adapter auto --task-name tron_demo --timesteps 128
```

Or use the console script if installed:

```bash
tron-ii --adapter auto --task-name tron_demo --timesteps 128
```

You can also specify both registry and outcome log paths:

```bash
tron-ii --adapter auto --task-name tron_demo \
  --artifact-registry ./artifacts.json \
  --outcome-log ./outcomes.json
```

