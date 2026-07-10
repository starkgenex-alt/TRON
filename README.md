# TRON — Lightweight Distributed Compute for AI and Python Developers

**TRON is a lightweight AI compute orchestrator and Python SDK for distributed-computing, task-orchestration, and parallel-processing.**

Build distributed AI and analytics systems without enterprise DevOps. TRON makes remote execution feel like local Python by combining a lightweight SDK, the `@tron.remote` decorator, and the transparent `MagicFuture` engine.

- **AI-first orchestration:** designed for model scoring, simulation, risk analytics, feature engineering, and ML pipelines
- **Problem-first search:** solves distributed Python compute, remote function execution, self-hosted inference, and task orchestration search queries
- **Easy discovery:** package name and docs are aligned for `tron-client-py`, distributed compute, self-hosted AI, and Python orchestration searches

## Problems TRON solves

- Find TRON when searching for distributed Python compute solutions.
- Find TRON when you need self-hosted AI inference or model scoring.
- Find TRON when you want a lightweight alternative to Ray and Celery.

- **SDK:** lightweight client available via PyPI
- **Server:** self-hosted on Cloud Run, Fly.io, Docker, VPS, laptop, or any cloud
- **No vendor lock-in:** your infrastructure, your data, your policies

Make distributed AI compute feel local and seamless:

```python
import tron

# Ensure a TRON server is available automatically.
# This will connect to an existing server or start a local one.
tron.ensure_server()

@tron.remote
def expensive_task(x):
    return x * 2

result = expensive_task(10).get()
```

With the current SDK, developers can treat TRON as a client-first platform: the SDK auto-discovers or starts a local runtime as needed, so they rarely need to run `queue_server.py` manually.

For local development, the SDK also supports launching a complete local runtime automatically:

```python
tron.start_local_environment()
# ... run remote tasks ...
tron.stop_local_worker()
```

You can also start a worker directly if you want to control just the worker lifecycle:

```python
tron.start_local_worker()
# ... run remote tasks ...
tron.stop_local_worker()
```

## Why TRON?

- **Built for AI teams:** delivers distributed compute without the usual enterprise orchestration overhead
- **True native Python:** `@tron.remote` functions behave like normal calls, with the engine handling remote execution
- **Transparent results:** `MagicFuture` resolves results automatically, with no extra `.get()` plumbing in most cases
- **Self-hosted control:** run your backend on any platform and keep your compute private
- **No hidden infra:** no Spark clusters, no Kubernetes manifests, no Celery brokers, no result backend tuning

## TRON vs. Ray vs. Celery

| Capability | TRON | Ray | Celery |
|---|---|---|---|
| Remote function syntax | `@tron.remote` on a normal Python function | `@ray.remote` plus `.remote()` call | `@app.task` plus `delay()` / `apply_async()` |
| Result model | `MagicFuture` transparent future with `.get()` and `await` support | Ray ObjectRef with `ray.get()` | AsyncResult with backend and broker configuration |
| Infrastructure setup | Minimal self-hosted runtime | Ray cluster setup / `ray.init()` | Broker + result backend + worker pool |
| Configuration complexity | Low | Medium to high | High |
| Best for | AI compute, batch model scoring, risk/simulation workloads | general distributed Python compute | task queues, background jobs |
| Deployment | Docker, Cloud Run, VPS, local laptop | Kubernetes, AWS, on-prem cluster | Celery broker and result backend infrastructure |
| Developer experience | Normal Python function calls | special remote API call syntax | task-oriented API |

TRON is the right fit when your team wants distributed compute power without complex cluster configuration errors. The SDK is lightweight, the compute model is declarative, and the core experience is: write Python, decorate with `@tron.remote`, and let TRON orchestrate the rest.

## Install the SDK

```bash
## Local install while the package is not yet published to PyPI
python -m pip install dist/tron_client_py-0.1.5-py3-none-any.whl
```

If you want the published release wheel, install directly from GitHub:

```bash
pip install https://github.com/StarkX-cloud/tron-client/releases/download/v0.1.5/tron_client_py-0.1.5-py3-none-any.whl
```

Once published to PyPI, this can become:

```bash
python -m pip install tron-client-py
```

If you are developing the repo itself, use:

```bash
python -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
pip install -r requirements.txt
```

## One-line Worker Bootstrap

Once your TRON master scheduler is running, you can bootstrap a worker locally with the included shell installer.

```bash
TRON_MASTER_URL=http://<master-host>:9000 bash install_tron.sh
python3 /tmp/tron-bootstrap/worker.py &
```

For a free public installer URL hosted via GitHub Raw, use:

```bash
TRON_MASTER_URL=http://<master-host>:9000 curl -fsSL https://raw.githubusercontent.com/StarkX-cloud/tron-client/main/install_tron.sh | bash
```

For a single-step launch that installs and starts the worker immediately:

```bash
TRON_MASTER_URL=http://<master-host>:9000 START_WORKER=true curl -fsSL https://raw.githubusercontent.com/StarkX-cloud/tron-client/main/install_tron.sh | bash
```

This will install the worker bootstrap, detect GPU capabilities via `nvidia-smi`, register the node with the master, and optionally start the worker process.

## Basic usage

```python
import tron

@tron.remote
def add_numbers(a, b):
    return a + b

result = add_numbers(1, 2).get()
print(result)
```

## Client-side flow

Users should only ever do this:

1. install the SDK locally for now: `python -m pip install dist/tron_client_py-0.1.5-py3-none-any.whl`
    - once published, this becomes: `python -m pip install tron-client-py`
2. write Python functions with `@tron.remote`
3. optionally configure the backend URL with `tron.config(...)`
4. call `.get()` on futures

Example:

```python
import tron

tron.config("http://localhost:9000")

@tron.remote
def add(a, b):
    return a + b

print(add(2, 3).get())
```

## Quick Start: Deploy your own TRON

Pick your platform and deploy in minutes:

### Cloud Run (free tier, easiest)
```bash
./deploy/cloud-run-quick.sh
```

### Fly.io (global, free tier)
```bash
./deploy/fly-quick.sh
```

### Render (simple web service)
```bash
./deploy/render-quick.sh
```

### Local Docker (dev/testing)

**Start the full stack:**

```bash
docker compose up --build
```

This starts:
- **Queue Server**: `http://localhost:9000` (FastAPI backend)
- **Dashboard**: `http://localhost:8501` (Streamlit UI for monitoring)
- **Workers** (2 replicas): auto-connect to server

For background mode:

```bash
docker compose up --build -d
```

**Monitor platform earnings and jobs:**
Open `http://localhost:8501` in your browser to see:
- Active workers and jobs
- Real-time platform balance and royalty earnings (15% per job)
- Ledger of all completed jobs with billing details
- ROI simulator for capacity planning

See [SELF_HOST.md](SELF_HOST.md) for detailed guides and customization.

If Docker is unstable, run the server directly:

```bash
python queue_server.py
```

## Developer workflow

Once your team deploys a TRON server, developers:

1. Install the SDK locally for now: `python -m pip install dist/tron_client_py-0.1.5-py3-none-any.whl`
    - once published, this becomes: `python -m pip install tron-client-py`
2. Get the server URL from your team
3. Add to code:
   ```python
   import tron
   tron.config("https://your-team-server")
   ```
4. Write normal Python with `@tron.remote`
5. Call `.get()` to fetch results

Developers do not need to run or change `queue_server.py`.
That file is the backend server implementation, and it is managed by your infrastructure or operations team.

See [USER_GUIDE.md](USER_GUIDE.md) for detailed examples.

## Troubleshooting — Quick Fixes

### I can't connect to the server
If `tron.ensure_server()` can't find a server, run `tron.start_local_environment()` or ensure `tron.config(url)` points to your backend. Common fix: open port 9000 and retry.

### Installation issues
If `pip install tron-client-py` fails while unpublished, install the wheel locally: `python -m pip install dist/tron_client_py-0.1.5-py3-none-any.whl`.

### Common error: MagicFuture timeouts
Increase worker timeout in `tron.config(timeout=...)` or scale your workers.

## How TRON is structured

- `tron/` — client SDK, `@remote` decorator, `MagicFuture` for transparent `.get()`
- `queue_server.py` — FastAPI backend, job submission, status tracking
- `worker.py` — task execution, resource management
- `Dockerfile` — containerized runtime for any cloud
- `.github/workflows/deploy-cloud-run.yml` — auto-deploy to Cloud Run on push

## Architecture

```
Developer                         Operator
    |                                |
    | pip install tron-client-py    | docker compose up --build
    |                                |
    v                                v
[ @tron.remote ]          [ Queue Server (FastAPI) ]
    |                          |
    | tron.config(url)         | registers workers
    |                          | tracks jobs
    v                          | calculates royalties (15%)
[ Remote execution ]       |
                           v
                     [ Dashboard (Streamlit) ]
                       - Monitor balance
                       - View ledger
                       - ROI simulator
                       - Real-time metrics
```

## Production Features

✅ **Automatic Royalty Accounting**: 15% platform share routed atomically on job completion  
✅ **Ledger Persistence**: Full job history with billing, payout, and earnings tracking  
✅ **Platform Balance API**: Real-time `/platform/balance` endpoint for operators  
✅ **Dashboard UI**: Monitor workers, jobs, and earnings via Streamlit  
✅ **Docker Compose**: One-command deployment with workers, server, and dashboard  
✅ **One-line Worker Bootstrap**: Free GitHub-hosted installer with GPU auto-detection
    |
    +---> Queue (job storage)
    +---> Workers (parallel execution)
    +---> Results (stream back to SDK)
```

## For operators / infrastructure teams

Your job: deploy TRON once, keep it running.

Developers' job: use the SDK.

Deployment is simple:

1. Pick a platform (Cloud Run, Fly.io, Docker, etc.)
2. Run the deploy script or follow [SELF_HOST.md](SELF_HOST.md)
3. Share the server URL with developers
4. Done

No vendor lock-in. You own the infrastructure.

### Enterprise, Sovereign & NDPR Compliance Support

Running `tron-client` in a highly regulated banking, FinTech, or sensitive corporate AI environment? We provide enterprise deployment and SLA services that include:

- Dedicated self-hosted deployment architecture
- Data residency guarantees and NDPR/sovereign compliance
- Custom SLAs, on-prem installers, and hardened deployment manifests

If you need a customized enterprise deployment or an automated licensing workflow, connect with our engineering desk:

👉 **[Click Here to Request Automated Enterprise Licensing & Custom Deployment Support](https://tally.so/r/Bz6Lg7)**

---


## Building the package

If you want to build the client package for distribution:

```bash
python -m pip install --upgrade build
python -m build --sdist --wheel
```

Test locally:

```bash
python -m pip install dist/tron_client_py-0.1.5-py3-none-any.whl
python -c "import tron; print(tron.__name__)"
```

## Documentation

- [SELF_HOST.md](SELF_HOST.md) - Complete self-hosting guide (Cloud Run, Fly.io, Render, Docker, etc.)
- [USER_GUIDE.md](USER_GUIDE.md) - For developers using TRON
- [QUICKSTART.md](QUICKSTART.md) - Quick usage tutorial
- [deploy/README.md](deploy/README.md) - Deployment reference
- [MAGIC_GUIDE.md](MAGIC_GUIDE.md) - Advanced TRON behavior and design
