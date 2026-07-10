import requests
import time

API = "http://127.0.0.1:9000"

# Register worker
reg = requests.post(f"{API}/register", json={
    "name": "itest-worker-1",
    "capabilities": {"gpu": True},
    "gpu_name": "TestGPU",
    "vram_gb": 8.0,
    "cuda_cores": 256,
})
reg.raise_for_status()
resp = reg.json()
auth_token = resp["auth_token"]
worker_name = resp["worker_name"]
print("Registered:", worker_name, auth_token)

# Ensure platform balance before
b_before = requests.get(f"{API}/platform/balance").json()
print("Platform before:", b_before)

# Submit job
job = requests.post(f"{API}/submit_job", json={
    "task_type": "ai_task",
    "payload": {"data": "hello"},
    "runtime_seconds": 2,
    "requires_gpu": True,
})
job.raise_for_status()
job_id = job.json()["job_id"]
print("Submitted job:", job_id)

# Worker fetch next job
hdr = {"X-TRON-AUTH": auth_token}
nextj = requests.get(f"{API}/next_job", headers=hdr)
nextj.raise_for_status()
assignment = nextj.json().get("job")
print("Assigned:", assignment)

# Complete job
complete = requests.post(f"{API}/complete_job", headers=hdr, json={
    "job_id": job_id,
    "worker_name": worker_name,
    "result": {"ok": True},
    "success": True,
    "runtime_seconds": 2,
})
complete.raise_for_status()
print("Complete response:", complete.json())

# Check platform balance after
b_after = requests.get(f"{API}/platform/balance").json()
print("Platform after:", b_after)

# Basic assertion
before = float(b_before.get("platform_balance", 0.0))
after = float(b_after.get("platform_balance", 0.0))
print(f"Delta: {after - before}")

if after <= before:
    raise SystemExit("Platform balance did not increase")
print("Integration test passed")
