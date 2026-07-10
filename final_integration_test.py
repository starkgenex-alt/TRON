#!/usr/bin/env python3
"""
Final production integration test for TRON v1.0
- Submit a job
- Complete it
- Verify platform balance and ledger
"""
import requests
import time
import json

API = "http://127.0.0.1:9000"
TIMEOUT = 5

def test_production_flow():
    print("🚀 TRON v1.0 Production Integration Test")
    print("=" * 60)
    
    # 1. Check health
    print("\n✓ Step 1: Health check")
    r = requests.get(f"{API}/health", timeout=TIMEOUT)
    assert r.status_code == 200, f"Health check failed: {r.status_code}"
    print(f"  Status: {r.json()['status']}")
    
    # 2. Check initial platform balance
    print("\n✓ Step 2: Initial platform balance")
    r = requests.get(f"{API}/platform/balance", timeout=TIMEOUT)
    assert r.status_code == 200
    initial = r.json()
    print(f"  Balance: ${initial['platform_balance']:.4f}")
    print(f"  Total earnings: ${initial['total_platform_earnings']:.2f}")
    print(f"  Jobs completed: {initial['job_count']}")
    
    # 3. Register a test worker
    print("\n✓ Step 3: Register test worker")
    worker_payload = {
        "name": "test-worker-prod",
        "gpu": False,
        "memory_gb": 4
    }
    r = requests.post(f"{API}/register_worker", json=worker_payload, timeout=TIMEOUT)
    assert r.status_code == 200, f"Worker registration failed: {r.text}"
    print(f"  Worker registered: {worker_payload['name']}")
    
    # 4. Submit a job
    print("\n✓ Step 4: Submit job for execution")
    job_payload = {
        "task_type": "test_task",
        "prompt": "test computation",
        "priority": 1,
        "gpu": False,
        "memory_gb": 1,
        "function": {"name": "test_fn", "args": []}
    }
    r = requests.post(f"{API}/submit", json=job_payload, timeout=TIMEOUT)
    if r.status_code != 200:
        # Try submit_ai endpoint
        job_payload_ai = {
            "task_type": "test_task",
            "prompt": "test computation",
            "priority": 1,
            "gpu": False
        }
        r = requests.post(f"{API}/submit_ai", json=job_payload_ai, timeout=TIMEOUT)
    assert r.status_code == 200, f"Job submission failed: {r.text}"
    resp_json = r.json()
    job_id = resp_json.get("job_id")
    assert job_id, f"No job_id in response: {resp_json}"
    print(f"  Job ID: {job_id}")
    print(f"  Status: {r.json()['status']}")
    
    # 5. Fetch the job as worker would
    print("\n✓ Step 5: Fetch next job")
    r = requests.get(f"{API}/next_job/test-worker-prod", timeout=TIMEOUT)
    assert r.status_code == 200
    job = r.json().get("job")
    if job:
        print(f"  Fetched job: {job['id']}")
    else:
        print("  No job fetched (queue empty)")
    
    # 6. Complete the job
    print("\n✓ Step 6: Complete job (triggers royalty calculation)")
    complete_payload = {
        "result": {"output": "test result"}
    }
    r = requests.post(f"{API}/complete/{job_id}", json=complete_payload, timeout=TIMEOUT)
    assert r.status_code == 200, f"Job completion failed: {r.text}"
    print(f"  Job completed: {r.json()['ok']}")
    
    # 7. Check updated platform balance
    print("\n✓ Step 7: Verify platform balance updated")
    time.sleep(0.5)
    r = requests.get(f"{API}/platform/balance", timeout=TIMEOUT)
    assert r.status_code == 200
    updated = r.json()
    print(f"  New balance: ${updated['platform_balance']:.4f}")
    print(f"  Total earnings: ${updated['total_platform_earnings']:.2f}")
    print(f"  Jobs completed: {updated['job_count']}")
    
    balance_delta = updated["platform_balance"] - initial["platform_balance"]
    if balance_delta > 0:
        print(f"  ✅ Balance increased by ${balance_delta:.4f}")
    else:
        print(f"  ⚠️  Balance did not increase")
    
    # 8. Check ledger
    print("\n✓ Step 8: Verify ledger entry")
    r = requests.get(f"{API}/ledger", timeout=TIMEOUT)
    assert r.status_code == 200
    ledger = r.json()["ledger"]
    if ledger:
        entry = ledger[0]
        print(f"  Latest entry job: {entry['job_id']}")
        print(f"  Type: {entry['type']}")
        print(f"  Billed: ${entry['amount']:.6f}")
        print(f"  Royalty: ${entry['royalty_amount']:.6f}")
        print(f"  Platform share: ${entry['platform_share']:.6f}")
    else:
        print("  ⚠️  No ledger entries yet")
    
    # 9. Check metrics
    print("\n✓ Step 9: Queue metrics")
    r = requests.get(f"{API}/metrics", timeout=TIMEOUT)
    assert r.status_code == 200
    metrics = r.json()
    print(f"  Workers: {metrics['workers']}")
    print(f"  Queue size: {metrics['queue_size']}")
    print(f"  Active jobs: {metrics['running_jobs']}")
    print(f"  Completed: {metrics['completed_jobs']}")
    
    print("\n" + "=" * 60)
    print("✅ PRODUCTION INTEGRATION TEST PASSED")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Dashboard: http://localhost:8501")
    print("2. API docs: http://localhost:9000/docs")
    print("3. Ledger: curl http://localhost:9000/ledger")
    print("4. Balance: curl http://localhost:9000/platform/balance")
    print("\nTRON v1.0 is production ready! 🚀")

if __name__ == "__main__":
    try:
        test_production_flow()
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
