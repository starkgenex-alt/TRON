# 🚀 TRON Quick Start - AI Compute Orchestrator

## Install & Setup

```bash
# Install the TRON SDK (PyPI)
pip install tron-client-py
```

If you prefer the release wheel on GitHub Releases:

```bash
pip install https://github.com/StarkX-cloud/tron-client/releases/download/v0.1.3/tron_client-0.1.3-py3-none-any.whl
```

## 3-Minute Tutorial

1. Import TRON
```python
import tron
```

2. Define your work
```python
@tron.remote
def expensive_task(x):
    return x ** 2
```

3. Call it (distributed, automatic)
```python
f = expensive_task(100)
print(f.get())  # MagicFuture returns the real result
```

## Developer tips

- For on-prem AI, keep models on local workers and call them via `@tron.remote` to avoid sending sensitive data to external clouds.
- Use `tron.start_local_environment()` for quick local testing.

## Enterprise contact

If you need an on-prem deployment or enterprise SLA, request support here:

https://tally.so/r/Bz6Lg7

