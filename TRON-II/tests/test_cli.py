"""Tests for the TRON-II CLI entry point."""

from tron_ii.cli import parse_args


def test_parse_args_defaults():
    args = parse_args([])
    assert args.adapter == "auto"
    assert args.task_name == "tron_cli_demo"
    assert args.timesteps == 128
    assert args.budget == 1.0
    assert args.substrate == "cpu"
    assert args.artifact_registry == "tron_artifacts.json"


def test_parse_args_custom_values():
    args = parse_args([
        "--adapter", "sb3",
        "--task-name", "demo",
        "--timesteps", "256",
        "--budget", "2.5",
        "--substrate", "gpu",
        "--artifact-registry", "./custom_registry.json",
    ])
    assert args.adapter == "sb3"
    assert args.task_name == "demo"
    assert args.timesteps == 256
    assert args.budget == 2.5
    assert args.substrate == "gpu"
    assert args.artifact_registry == "./custom_registry.json"
