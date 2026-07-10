# TRON vGPU Gateway Guide

This guide covers the TRON virtual GPU (vGPU) gateway stack: a lightweight, OpenAI-compatible API for distributed task execution on a cluster of GPUs.

## Quick Start

### Option 1: Local Standalone (Fastest)

```bash
# Terminal 1: Start scheduler
python -m vgpu.scheduler

# Terminal 2: Start gateway
python -m vgpu.openai_bridge

# Terminal 3: Start worker
python -m vgpu.worker --name worker-1 --gpu-name "RTX 3050" --vram-gb 4.0 --cuda-cores 2048
```

### Option 2: Docker Compose (Recommended for Testing)

```bash
docker-compose -f docker-compose.vgpu.yml up
```

This starts:
- Scheduler on port 9002
- Gateway on port 9003
- Two workers (worker-1, worker-2)

### Option 3: Smoke Test (Validation Only)

```bash
python vgpu_gateway_smoke_test.py
```

This script starts all needed services, runs a test request, and cleans up.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│         OpenAI-Compatible Client                        │
│  curl -X POST http://localhost:9003/v1/chat/completions │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│   TRON OpenAI Gateway (Port 9003)                       │
│   - Translates /v1/chat/completions to TRON jobs        │
│   - Polls scheduler for job completion                  │
│   - Returns OpenAI-compatible responses                 │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│   vGPU Scheduler (Port 9002)                            │
│   - Aggregates virtual GPU resources                    │
│   - Assigns jobs to workers                             │
│   - Tracks job completion & billing                     │
│   - Persists state to SQLite                            │
└────────────────┬────────────────────────────────────────┘
                 │
      ┌──────────┴──────────┬──────────┐
      ▼                     ▼          ▼
   Worker-1            Worker-2    Worker-N
   (RTX 3050)          (RTX 3060)   (Custom)
   - Poll for jobs
   - Execute tasks
   - Report completion
```

## API Endpoints

### Gateway (Port 9003)

#### Health Check
```bash
GET /health
```
Response: `{"status": "ok", "service": "tron-openai-bridge"}`

#### OpenAI Chat Completions (Primary API)
```bash
POST /v1/chat/completions
Authorization: Bearer $TRON_API_KEY (optional)

{
  "model": "tron-gateway",
  "messages": [
    {"role": "user", "content": "Hello, TRON"}
  ],
  "temperature": 0.7,
  "max_tokens": 256
}
```

Response (OpenAI-compatible):
```json
{
  "id": "chatcmpl-...",
  "object": "chat.completion",
  "created": 1234567890,
  "model": "tron-gateway",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Response from TRON distributed cluster"
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 10,
    "completion_tokens": 20,
    "total_tokens": 30
  }
}
```

#### Embeddings
```bash
POST /v1/embeddings
```

#### Batch Inference
```bash
POST /v1/batch/infer
```

#### Agent Run
```bash
POST /v1/agents/run
```

### Scheduler (Port 9002)

#### Health Check
```bash
GET /health
```

#### Submit Job
```bash
POST /submit_job

{
  "task_type": "openai_task",
  "payload": {...},
  "priority": 1,
  "requires_gpu": true,
  "required_vram_gb": 2.0,
  "required_cuda_cores": 1024
}
```

#### List Jobs
```bash
GET /jobs
```

#### Get Workers
```bash
GET /workers
```

#### Register Worker
```bash
POST /register

{
  "name": "my-worker",
  "gpu_name": "RTX 3050",
  "vram_gb": 4.0,
  "cuda_cores": 2048
}
```

## Configuration

### Environment Variables

#### Gateway (Port 9003)
```bash
TRON_MASTER_URL          # Scheduler URL (default: http://localhost:9002)
TRON_DEFAULT_MODEL       # Default model name (default: tron-gateway)
TRON_API_KEY             # Optional: require Bearer token for requests
```

#### Worker
```bash
TRON_MASTER_URL          # Scheduler URL (default: http://localhost:9002)
TRON_WORKER_NAME         # Worker name (default: vgpu-worker)
TRON_GPU_NAME            # GPU model (default: RTX 3050)
TRON_VRAM_GB             # GPU memory in GB (default: 4.0)
TRON_CUDA_CORES          # Logical CUDA cores (default: 2048)
TRON_NETWORK_BANDWIDTH_GBPS  # Network speed (default: 1.0)
TRON_WORKER_LOCATION     # Location tag (default: unknown)
TRON_WORKER_AUTH_TOKEN   # Pre-existing auth token (optional)
```

#### Scheduler
```bash
(No environment variables; uses SQLite database at ./tron_vgpu_master.db)
```

## API Key Authentication

To require API key authentication on the gateway:

```bash
export TRON_API_KEY="my-secret-key"
python -m vgpu.openai_bridge
```

Then include the Bearer token in requests:
```bash
curl -X POST http://localhost:9003/v1/chat/completions \
  -H "Authorization: Bearer my-secret-key" \
  -H "Content-Type: application/json" \
  -d '{...}'
```

Without the header, requests return 401 Unauthorized.

## Python Client Example

```python
import requests

gateway_url = "http://localhost:9003"
response = requests.post(
    f"{gateway_url}/v1/chat/completions",
    json={
        "model": "tron-gateway",
        "messages": [{"role": "user", "content": "Hello"}],
        "temperature": 0.7,
        "max_tokens": 100,
    },
    timeout=30,
)

result = response.json()
print(result["choices"][0]["message"]["content"])
```

## Advanced Usage

### Custom vGPU Profile

The scheduler aggregates worker GPU specs into a synthetic vGPU cluster:

```python
from vgpu.cluster import VirtualGPUCluster

cluster = VirtualGPUCluster(cluster_name="my-cluster")
cluster.register_node("gpu-1", "RTX 3050", vram_gb=4.0, cuda_cores=2048)
cluster.register_node("gpu-2", "RTX 3060", vram_gb=6.0, cuda_cores=3584)

profile = cluster.aggregated_profile()
print(profile)
# Aggregate: 10 GB VRAM, 5632 CUDA cores
```

### Direct Job Submission

Submit jobs directly to the scheduler without the OpenAI gateway:

```python
from vgpu.client import VGPUClient

client = VGPUClient("http://localhost:9002")
response = client.submit_vgpu_job(
    task_type="render_batch",
    payload={"frames": 60, "duration": 2.0},
    required_vram_gb=4.0,
    required_cuda_cores=2048,
)
print(response["job_id"])
```

## Troubleshooting

### Gateway Returns 502 Error
**Cause:** Scheduler is unreachable or crashed.

```bash
# Check scheduler health
curl http://localhost:9002/health

# Check if port 9002 is in use
lsof -i :9002  # macOS/Linux
netstat -ano | findstr :9002  # Windows

# Restart scheduler
python -m vgpu.scheduler
```

### Workers Not Picking Up Jobs
**Cause:** Workers not registered or scheduler stale.

```bash
# Check registered workers
curl http://localhost:9002/workers

# Verify worker can reach scheduler
ping localhost  # or check network routes
```

### Request Timeout (18s default)
The gateway polls the scheduler for 18 seconds. If a job takes longer:
- Extend the timeout in gateway code (`deadline = time.time() + 18.0`)
- Or pre-warm the cluster with idle workers

### Stale Job State
If a worker crashes mid-job, the watchdog requeues it after 20 seconds (HEARTBEAT_TIMEOUT).

## Performance Tuning

### Increase Worker Count
```bash
for i in {1..10}; do
  python -m vgpu.worker --name worker-$i &
done
```

### Resource Profiles
Adjust `--vram-gb` and `--cuda-cores` per worker to match actual hardware:
```bash
python -m vgpu.worker --name gpu-worker --gpu-name "A100" --vram-gb 80.0 --cuda-cores 6912
```

### Batch Jobs
Submit multiple requests in parallel:
```python
import concurrent.futures

with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
    futures = [
        executor.submit(submit_request, f"Request {i}")
        for i in range(100)
    ]
    results = [f.result() for f in futures]
```

## Deployment Checklist

- [ ] Scheduler listens on 0.0.0.0:9002
- [ ] Gateway listens on 0.0.0.0:9003
- [ ] At least 1 worker registered and heartbeating
- [ ] Database file persisted (`tron_vgpu_master.db`)
- [ ] Health endpoints responding
- [ ] Client can reach gateway URL
- [ ] Firewall allows 9002, 9003 if remote
- [ ] Load testing completes without errors

## Next Steps

1. **Monitor:** Add Prometheus/Grafana for job metrics
2. **Scale:** Deploy workers across multiple machines
3. **Secure:** Use TLS for remote deployments
4. **Integrate:** Connect to existing ML pipelines via the OpenAI API adapter
