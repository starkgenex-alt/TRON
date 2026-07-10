#!/usr/bin/env python
"""
Example: Using the TRON vGPU gateway as an OpenAI-compatible API client.

This script demonstrates:
- Single chat completion request
- Batch requests
- Error handling
- Custom parameters
"""
from __future__ import annotations

import time
from typing import Any

import requests


GATEWAY_URL = "http://localhost:9003"
GATEWAY_TIMEOUT = 30  # seconds


def create_chat_request(prompt: str, max_tokens: int = 100) -> dict[str, Any]:
    """Create a chat completion request."""
    return {
        "model": "tron-gateway",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": max_tokens,
    }


def submit_request(prompt: str, max_tokens: int = 100) -> str:
    """Submit a single request and return the response text."""
    try:
        response = requests.post(
            f"{GATEWAY_URL}/v1/chat/completions",
            json=create_chat_request(prompt, max_tokens),
            timeout=GATEWAY_TIMEOUT,
        )
        response.raise_for_status()
        result = response.json()
        return result["choices"][0]["message"]["content"]
    except requests.RequestException as exc:
        raise RuntimeError(f"Gateway request failed: {exc}") from exc


def batch_requests(prompts: list[str], max_tokens: int = 100) -> list[str]:
    """Submit multiple requests sequentially."""
    results = []
    for i, prompt in enumerate(prompts):
        print(f"Submitting request {i+1}/{len(prompts)}...", end=" ", flush=True)
        start = time.time()
        result = submit_request(prompt, max_tokens)
        elapsed = time.time() - start
        print(f"({elapsed:.2f}s)")
        results.append(result)
    return results


def main() -> None:
    print("TRON vGPU Gateway Client Example")
    print("=" * 60)

    # Check gateway health
    print("\n1. Checking gateway health...")
    try:
        health = requests.get(f"{GATEWAY_URL}/health", timeout=5).json()
        print(f"   Status: {health}")
    except requests.RequestException as exc:
        print(f"   ERROR: Gateway not reachable at {GATEWAY_URL}")
        print(f"   {exc}")
        return

    # Single request
    print("\n2. Submitting a single request...")
    try:
        response = submit_request("What is TRON?")
        print(f"   Response: {response}")
    except Exception as exc:
        print(f"   ERROR: {exc}")

    # Multiple requests
    print("\n3. Submitting batch of requests...")
    prompts = [
        "Explain distributed computing in one sentence",
        "What are virtual GPUs?",
        "List 3 benefits of serverless compute",
    ]
    try:
        responses = batch_requests(prompts)
        for prompt, response in zip(prompts, responses):
            print(f"   Q: {prompt}")
            print(f"   A: {response[:100]}...")
            print()
    except Exception as exc:
        print(f"   ERROR: {exc}")

    # Custom parameters
    print("4. Using custom parameters...")
    try:
        response = requests.post(
            f"{GATEWAY_URL}/v1/chat/completions",
            json={
                "model": "tron-gateway",
                "messages": [{"role": "user", "content": "Be creative"}],
                "temperature": 0.9,  # Higher = more creative
                "max_tokens": 50,
            },
            timeout=GATEWAY_TIMEOUT,
        )
        response.raise_for_status()
        result = response.json()
        print(f"   Response: {result['choices'][0]['message']['content']}")
    except Exception as exc:
        print(f"   ERROR: {exc}")

    print("\n" + "=" * 60)
    print("Example complete!")


if __name__ == "__main__":
    main()
