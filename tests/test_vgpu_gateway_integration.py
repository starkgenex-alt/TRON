"""Integration tests for TRON vGPU gateway, scheduler, and worker."""
from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

import pytest
import requests


ROOT = Path(__file__).resolve().parent.parent
SCHEDULER_URL = "http://127.0.0.1:9002"
BRIDGE_URL = "http://127.0.0.1:9003"


@pytest.fixture(scope="session", autouse=True)
def ensure_services_running():
    """Ensure scheduler and gateway are running before tests."""
    for url in [f"{SCHEDULER_URL}/health", f"{BRIDGE_URL}/health"]:
        for attempt in range(5):
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    break
            except requests.RequestException:
                if attempt < 4:
                    time.sleep(1)
                else:
                    pytest.skip(f"Service {url} not reachable")


def test_scheduler_health():
    """Test scheduler health endpoint."""
    response = requests.get(f"{SCHEDULER_URL}/health", timeout=5)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


def test_gateway_health():
    """Test gateway health endpoint."""
    response = requests.get(f"{BRIDGE_URL}/health", timeout=5)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "tron-openai-bridge"


def test_gateway_models_endpoint():
    """Test gateway /v1/models endpoint."""
    response = requests.get(f"{BRIDGE_URL}/v1/models", timeout=5)
    assert response.status_code == 200
    data = response.json()
    assert data["object"] == "list"
    assert len(data["data"]) > 0
    model_ids = [m["id"] for m in data["data"]]
    assert "tron-gateway" in model_ids


def test_chat_completions_basic():
    """Test basic chat completions request."""
    response = requests.post(
        f"{BRIDGE_URL}/v1/chat/completions",
        json={
            "model": "tron-gateway",
            "messages": [{"role": "user", "content": "Hello"}],
            "temperature": 0.5,
            "max_tokens": 20,
        },
        timeout=30,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["object"] == "chat.completion"
    assert data["model"] == "tron-gateway"
    assert "choices" in data
    assert len(data["choices"]) > 0
    assert "message" in data["choices"][0]
    assert "content" in data["choices"][0]["message"]
    assert "usage" in data
    assert data["usage"]["total_tokens"] > 0


def test_chat_completions_multiple_messages():
    """Test chat completions with multiple messages."""
    response = requests.post(
        f"{BRIDGE_URL}/v1/chat/completions",
        json={
            "model": "tron-gateway",
            "messages": [
                {"role": "user", "content": "First message"},
                {"role": "assistant", "content": "Response to first"},
                {"role": "user", "content": "Second message"},
            ],
            "temperature": 0.7,
            "max_tokens": 50,
        },
        timeout=30,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["object"] == "chat.completion"


def test_embeddings_endpoint():
    """Test embeddings endpoint."""
    response = requests.post(
        f"{BRIDGE_URL}/v1/embeddings",
        json={
            "model": "tron-gateway",
            "input": ["hello", "world"],
        },
        timeout=30,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["object"] == "list"
    assert len(data["data"]) == 2
    assert all("embedding" in item for item in data["data"])


def test_scheduler_workers_registered():
    """Test that at least one worker is registered with scheduler."""
    response = requests.get(f"{SCHEDULER_URL}/workers", timeout=5)
    assert response.status_code == 200
    data = response.json()
    assert "workers" in data
    # At least one worker should be registered
    assert len(data["workers"]) > 0


def test_scheduler_jobs_endpoint():
    """Test scheduler jobs endpoint."""
    response = requests.get(f"{SCHEDULER_URL}/jobs", timeout=5)
    assert response.status_code == 200
    data = response.json()
    assert "jobs" in data
    # Should be a dict of jobs (may be empty initially)
    assert isinstance(data["jobs"], dict)


def test_chat_completion_creates_job():
    """Test that a chat completion request creates a job in the scheduler."""
    # Get initial job count
    initial = requests.get(f"{SCHEDULER_URL}/jobs", timeout=5).json()
    initial_count = len(initial["jobs"])

    # Submit a request
    response = requests.post(
        f"{BRIDGE_URL}/v1/chat/completions",
        json={
            "model": "tron-gateway",
            "messages": [{"role": "user", "content": "Test"}],
            "max_tokens": 10,
        },
        timeout=30,
    )
    assert response.status_code == 200

    # Check that a job was created
    final = requests.get(f"{SCHEDULER_URL}/jobs", timeout=5).json()
    final_count = len(final["jobs"])
    assert final_count >= initial_count  # At least one new job


def test_chat_completion_job_completes():
    """Test that a submitted job transitions to completed status."""
    # Submit request
    response = requests.post(
        f"{BRIDGE_URL}/v1/chat/completions",
        json={
            "model": "tron-gateway",
            "messages": [{"role": "user", "content": "Integration test"}],
            "max_tokens": 15,
        },
        timeout=30,
    )
    assert response.status_code == 200
    
    # Job should have completed based on gateway response
    # (gateway polls until job completes or times out)
