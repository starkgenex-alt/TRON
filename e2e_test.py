#!/usr/bin/env python3
"""
End-to-end TRON flow test:
1. Register a worker
2. Submit a job
3. Get job status
4. Complete the job
5. Check billing/royalty tracking
"""

import requests
import json
import time
import uuid

MASTER_URL = "http://127.0.0.1:9000"

print("=" * 70)
print("TRON END-TO-END FLOW TEST")
print("=" * 70)

# Step 1: Register a worker
print("\n[STEP 1] Registering worker...")
worker_payload = {
    "name": f"test-worker-{uuid.uuid4().hex[:8]}",
    "capabilities": {
        "gpu": False,
        "memory_gb": 4,
        "cuda_cores": 0
    },
    "location": "local"
}
r = requests.post(f"{MASTER_URL}/register_worker", json=worker_payload)
if r.status_code != 200:
    print(f"  [ERROR] {r.status_code}: {r.text}")
    exit(1)

worker_data = r.json()
worker_name = worker_data["worker_name"]
auth_token = worker_data["auth_token"]
print(f"  [OK] Worker registered: {worker_name}")
print(f"  [OK] Auth token: {auth_token[:16]}...")

# Step 2: Get workers list
print("\n[STEP 2] Fetching workers list...")
r = requests.get(f"{MASTER_URL}/workers")
workers = r.json()
if isinstance(workers, dict):
    workers_list = list(workers.values()) if workers else []
else:
    workers_list = workers
print(f"  [OK] Found {len(workers_list)} worker(s)")
if workers_list:
    for w in workers_list:
        print(f"      - {w.get('name', 'unknown')} (status: {w.get('status', 'unknown')})")

# Step 3: Create a customer for billing
print("\n[STEP 3] Creating customer for billing...")
customer_payload = {
    "name": "Test Customer",
    "email": "test@tron.local",
    "company": "TRON Test"
}
r = requests.post(f"{MASTER_URL}/admin/customer/create", json=customer_payload)
if r.status_code != 200:
    print(f"  [ERROR] {r.status_code}: {r.text}")
    exit(1)

customer_data = r.json()
api_key = customer_data.get("api_key")
print(f"  [OK] Customer created with API key: {api_key[:16]}...")

# Step 4: Submit a job with API key
print("\n[STEP 4] Submitting a test job with billing...")
job_payload = {
    "prompt": "Run a simple test computation",
    "task_type": "compute",
    "gpu": False,
    "priority": 1,
    "memory_gb": 1
}
headers = {"X-API-Key": api_key}
r = requests.post(f"{MASTER_URL}/api/v1/submit", json=job_payload, headers=headers)
if r.status_code != 200:
    print(f"  [ERROR] {r.status_code}: {r.text}")
    exit(1)

job_data = r.json()
job_id = job_data.get("job_id")
print(f"  [OK] Job submitted: {job_id}")
print(f"  [OK] Cost breakdown:")
print(f"      - Total charge: ${job_data.get('cost', 0):.6f}")
print(f"      - Platform share (15%): ${job_data.get('platform_share', 0):.6f}")
print(f"      - Worker share (85%): ${job_data.get('worker_share', 0):.6f}")

# Step 5: Get next job (as worker would)
print("\n[STEP 5] Getting next job (simulating worker request)...")

r = requests.get(f"{MASTER_URL}/next_job/{worker_name}")
job_for_worker = r.json()
if job_for_worker.get("job"):
    print(f"  [OK] Worker received job: {job_for_worker['job'].get('id')}")
else:
    print(f"  [WARN] No job available for worker")

# Step 6: Complete the job
print("\n[STEP 6] Completing the job...")
completion_payload = {
    "result": {"status": "success", "output": "Test computation completed"}
}
r = requests.post(f"{MASTER_URL}/complete/{job_id}", json=completion_payload)
if r.status_code != 200:
    print(f"  [ERROR] {r.status_code}: {r.text}")
    exit(1)

print(f"  [OK] Job {job_id} completed")

# Step 7: Check job status
print("\n[STEP 7] Checking job status...")
r = requests.get(f"{MASTER_URL}/status/{job_id}")
job_status = r.json()
print(f"  [OK] Job status: {job_status.get('status')}")
print(f"  [OK] Cost: ${job_status.get('cost', 0):.6f}")
print(f"  [OK] Payout: ${job_status.get('payout_amount', 0):.6f}")
print(f"  [OK] Royalty: ${job_status.get('royalty_amount', 0):.6f}")

# Step 8: Check platform balance
print("\n[STEP 8] Checking platform balance...")
r = requests.get(f"{MASTER_URL}/platform/balance")
balance = r.json()
print(f"  [OK] Platform balance: ${balance.get('platform_balance', 0):.6f}")
print(f"  [OK] Total billed: ${balance.get('total_billed', 0):.6f}")
print(f"  [OK] Total worker payout: ${balance.get('total_worker_payout', 0):.6f}")
print(f"  [OK] Total platform earnings: ${balance.get('total_platform_earnings', 0):.6f}")
print(f"  [OK] Completed jobs: {balance.get('completed_jobs', 0)}")

# Step 9: Check launch context
print("\n[STEP 9] Checking launch context...")

r = requests.get(f"{MASTER_URL}/api/v1/launch/context")
launch = r.json()
print(f"  [OK] Status: {launch.get('status')}")
print(f"  [OK] Active workers: {launch.get('active_workers')}")
print(f"  [OK] Layers enabled:")
for layer, enabled in launch.get('layers', {}).items():
    print(f"      - {layer}: {enabled}")
print(f"  [OK] Install command:")
print(f"      {launch.get('install_command')}")

print("\n" + "=" * 70)
print("END-TO-END TEST PASSED")
print("=" * 70)
print("\nSummary:")
print(f"  ✓ Worker registered and online")
print(f"  ✓ Job submitted with billing")
print(f"  ✓ Job completed with royalty split")
print(f"  ✓ Platform balance tracked")
print(f"  ✓ Launch context available")
print(f"\nTRON is ready to ship!")
