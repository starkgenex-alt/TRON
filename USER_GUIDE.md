# TRON User Guide

This guide is for developers using TRON to power AI workloads, analytics, and high-parallel simulations on self-hosted infrastructure.

## What is TRON?

TRON is an AI Compute Orchestrator for privacy-first teams. Developers write normal Python functions, decorate them with `@tron.remote`, and TRON transparently executes them across local or self-hosted worker fleets. The `MagicFuture` abstraction makes results feel synchronous while enabling massive parallelism and secure on-prem execution.

TRON removes DevOps friction: no Kubernetes manifests, no broker tuning, and no special cluster APIs — just Python.

## Install the SDK

```bash
# Install the TRON SDK from the published release (preferred)
pip install tron-client-py
```

If you are working from the repo directly, you can still use:

```bash
python -m pip install --upgrade build
python -m build --sdist --wheel
python -m pip install dist/tron_client-0.1.3-py3-none-any.whl
```

## Developer workflow

1. Install the SDK: `pip install tron-client-py` (or the release wheel)
2. Configure your server URL with `tron.config(...)` or rely on auto-discovery
3. Write normal Python functions and add `@tron.remote`
4. Call `.get()` on results or use `await` — `MagicFuture` resolves transparently

## Example: Distributed inference

```python
import tron

@tron.remote
def run_model_inference(chunk):
    # load local model and run inference (on-prem GPU or CPU)
    return local_model.generate(chunk)

chunks = ["c1", "c2", "c3"]
futures = [run_model_inference(c) for c in chunks]
results = [f.get() for f in futures]
```

## Enterprise & Compliance

For regulated environments requiring NDPR, data residency, or custom SLAs, request enterprise deployment and support:

👉 Request Enterprise Support & Deployment: https://tally.so/r/Bz6Lg7

