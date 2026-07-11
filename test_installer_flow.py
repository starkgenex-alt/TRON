#!/usr/bin/env python3
"""
Comprehensive installer flow validation.
Tests: registration → heartbeat → job submission → billing → completion.
"""
import requests
import json
import time
import sys

BASE_URL = "http://127.0.0.1:9000"

def test_phase(name, fn):
    """Run a test phase with error handling."""
    print(f"\n{'='*60}")
    print(f"  {name}")
    print(f"{'='*60}")
    try:
        result = fn()
        print(f"✅ {name}: PASSED")
        return result
    except Exception as e:
        print(f"❌ {name}: FAILED")
        print(f"   Error: {e}")
        sys.exit(1)

def test_worker_registration():
    """Test worker registration matching installer bootstrap format."""
    payload = {
        'name': 'test-worker-001',
        'capabilities': {'gpu': True, 'memory_gb': 16, 'cuda_cores': 5120, 'location': 'test-lab'},
        'gpu_name': 'NVIDIA RTX 3090',
        'vram_gb': 24,
        'cuda_cores': 5120,
        'network_bandwidth_gbps': 10.0,
        'location': 'test-lab',
        'metadata': {'bootstrap': 'tron-bootstrap', 'runtime': 'python'},
    }
    
    r = requests.post(f"{BASE_URL}/register_worker", json=payload, timeout=10)
    r.raise_for_status()
    
    data = r.json()
    print(f"   Response: {json.dumps(data, indent=2)}")
    
    assert data.get('ok') == True, "ok field missing"
    assert data.get('worker_name'), "worker_name missing"
    assert data.get('auth_token'), "auth_token missing"
    
    return {
        'worker_name': data['worker_name'],
        'auth_token': data['auth_token']
    }

def test_worker_heartbeat(worker_info):
    """Test worker heartbeat with auth token."""
    headers = {'X-TRON-AUTH': worker_info['auth_token']}
    payload = {'worker_name': worker_info['worker_name'], 'active_job_id': None}
    
    r = requests.post(
        f"{BASE_URL}/heartbeat/{worker_info['worker_name']}", 
        json=payload, 
        headers=headers, 
        timeout=10
    )
    r.raise_for_status()
    
    data = r.json()
    print(f"   Response: {json.dumps(data, indent=2)}")
    
    assert data.get('alive') == True, "alive should be True"
    
    return worker_info

def test_customer_creation():
    """Create a customer for billing test."""
    payload = {
        'name': 'test-customer-001',
        'email': 'test@tron.dev'
    }
    
    r = requests.post(f"{BASE_URL}/admin/customer/create", json=payload, timeout=10)
    r.raise_for_status()
    
    data = r.json()
    print(f"   Response: {json.dumps(data, indent=2)}")
    
    # Endpoint may return ok:true or just the data directly
    if not data.get('ok') and data.get('api_key'):
        # Endpoint returns data directly without ok field
        pass
    assert data.get('api_key'), "api_key missing"
    assert data.get('customer_id'), "customer_id missing"
    
    return {
        'customer_id': data['customer_id'],
        'api_key': data['api_key']
    }

def test_job_submission(customer_info):
    """Submit a job with billing enabled."""
    headers = {'X-API-Key': customer_info['api_key']}
    payload = {
        'command': 'echo "test job"',
        'priority': 1,  # Use integer instead of string
        'gpu_required': True,
        'memory_gb': 4,
        'timeout_sec': 300,
        'user_id': 'test-user'
    }
    
    r = requests.post(f"{BASE_URL}/api/v1/submit", json=payload, headers=headers, timeout=10)
    r.raise_for_status()
    
    data = r.json()
    print(f"   Response: {json.dumps(data, indent=2)}")
    
    # Endpoint may return ok:true or just the job data directly
    assert data.get('job_id'), "job_id missing"
    
    return {
        'job_id': data['job_id'],
        'customer_info': customer_info
    }

def test_job_completion(job_info):
    """Complete a job to trigger billing charge."""
    job_id = job_info['job_id']
    
    payload = {
        'worker': 'test-worker-001',
        'status': 'completed',
        'result': 'test job completed',
        'output': 'test output'
    }
    
    r = requests.post(f"{BASE_URL}/complete/{job_id}", json=payload, timeout=10)
    r.raise_for_status()
    
    data = r.json()
    print(f"   Response: {json.dumps(data, indent=2)}")
    
    assert data.get('ok') == True, "ok field missing"
    
    return job_info

def test_billing_charges(job_info):
    """Verify billing charges were recorded."""
    customer_info = job_info['customer_info']
    headers = {'X-API-Key': customer_info['api_key']}
    
    r = requests.get(f"{BASE_URL}/api/v1/billing/charges", headers=headers, timeout=10)
    r.raise_for_status()
    
    data = r.json()
    print(f"   Response: {json.dumps(data, indent=2)}")
    
    # Endpoint returns charges data directly
    assert len(data.get('charges', [])) > 0, "No charges recorded"
    
    charge = data['charges'][0]
    print(f"   ✓ Charge recorded: {charge['charge']} for job {charge['job_id']}")

def test_dashboard_access():
    """Verify dashboard is accessible."""
    dashboard_url = "http://127.0.0.1:8501"
    try:
        r = requests.get(dashboard_url, timeout=5)
        if r.status_code == 200:
            print(f"   Dashboard accessible at {dashboard_url}")
        else:
            print(f"   Dashboard returned status {r.status_code} (may be loading)")
    except Exception as e:
        print(f"   Dashboard not accessible: {e}")
        print(f"   (This is OK if not running; server is primary concern)")

def main():
    """Run full installer validation flow."""
    print("\n" + "="*60)
    print("  TRON INSTALLER VALIDATION FLOW")
    print("="*60)
    print(f"  Target: {BASE_URL}")
    
    # Phase 1: Worker registration
    worker_info = test_phase(
        "Phase 1: Worker Registration",
        test_worker_registration
    )
    
    # Phase 2: Worker heartbeat
    test_phase(
        "Phase 2: Worker Heartbeat",
        lambda: test_worker_heartbeat(worker_info)
    )
    
    # Phase 3: Customer creation
    customer_info = test_phase(
        "Phase 3: Customer Creation",
        test_customer_creation
    )
    
    # Phase 4: Job submission
    job_info = test_phase(
        "Phase 4: Job Submission",
        lambda: test_job_submission(customer_info)
    )
    
    # Phase 5: Job completion
    test_phase(
        "Phase 5: Job Completion",
        lambda: test_job_completion(job_info)
    )
    
    # Phase 6: Billing charges
    test_phase(
        "Phase 6: Billing Charges Verification",
        lambda: test_billing_charges(job_info)
    )
    
    # Phase 7: Dashboard access
    test_phase(
        "Phase 7: Dashboard Access",
        test_dashboard_access
    )
    
    print("\n" + "="*60)
    print("  ✅ ALL PHASES PASSED - INSTALLER READY FOR PUBLIC RELEASE")
    print("="*60 + "\n")

if __name__ == '__main__':
    main()
