import os
import time
import requests

API = os.environ.get("TRON_API_URL", "http://127.0.0.1:9000")
TIMEOUT = 5


def test_billing_api_flow_via_api_key():
    # Create a test customer
    resp = requests.post(
        f"{API}/admin/customer/create",
        json={"name": "Test Customer", "email": "billing@test.local", "company": "TestCo"},
        timeout=TIMEOUT,
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "api_key" in data
    api_key = data["api_key"]
    customer_id = data["customer_id"]

    # Submit a billed job
    job_payload = {
        "task_type": "billing_test",
        "prompt": "run billing validation",
        "priority": 2,
        "gpu": False,
        "memory_gb": 1,
        "function": {"name": "noop", "args": []},
    }
    headers = {"X-API-Key": api_key}
    resp = requests.post(
        f"{API}/api/v1/submit",
        json=job_payload,
        headers=headers,
        timeout=TIMEOUT,
    )
    assert resp.status_code == 200, resp.text
    response_json = resp.json()
    assert response_json["status"] == "queued"
    job_id = response_json["job_id"]
    assert job_id

    # Complete the job
    resp = requests.post(
        f"{API}/complete/{job_id}",
        json={"result": {"output": "ok"}},
        timeout=TIMEOUT,
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["ok"] is True

    # Query customer billing charges
    resp = requests.get(
        f"{API}/api/v1/billing/charges",
        headers=headers,
        timeout=TIMEOUT,
    )
    assert resp.status_code == 200, resp.text
    billing_data = resp.json()
    assert billing_data["customer_id"] == customer_id
    assert billing_data["charge_count"] >= 1
    assert any(item["job_id"] == job_id for item in billing_data["charges"])

    # Query billing summary
    resp = requests.get(
        f"{API}/api/v1/billing/summary",
        headers=headers,
        timeout=TIMEOUT,
    )
    assert resp.status_code == 200, resp.text
    summary = resp.json()
    assert summary["customer_id"] == customer_id
    assert summary["total_jobs"] >= 1
    assert summary["total_charged"] > 0


def test_billing_api_flow_via_bearer_token():
    # Create another customer
    resp = requests.post(
        f"{API}/admin/customer/create",
        json={"name": "Bearer Customer", "email": "bearer@test.local", "company": "BearerCo"},
        timeout=TIMEOUT,
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    api_key = data["api_key"]

    # Submit a billed job using Authorization Bearer header
    job_payload = {
        "task_type": "billing_test",
        "prompt": "run billing validation bearer",
        "priority": 1,
        "gpu": False,
        "memory_gb": 1,
        "function": {"name": "noop", "args": []},
    }
    headers = {"Authorization": f"Bearer {api_key}"}
    resp = requests.post(
        f"{API}/api/v1/submit",
        json=job_payload,
        headers=headers,
        timeout=TIMEOUT,
    )
    assert resp.status_code == 200, resp.text
    response_json = resp.json()
    assert response_json["status"] == "queued"
    job_id = response_json["job_id"]
    assert job_id

    # Complete the job
    resp = requests.post(
        f"{API}/complete/{job_id}",
        json={"result": {"output": "ok"}},
        timeout=TIMEOUT,
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["ok"] is True

    # Query billing summary with bearer token
    resp = requests.get(
        f"{API}/api/v1/billing/summary",
        headers=headers,
        timeout=TIMEOUT,
    )
    assert resp.status_code == 200, resp.text
    summary = resp.json()
    assert summary["customer_id"] == data["customer_id"]
    assert summary["total_jobs"] >= 1
    assert summary["total_charged"] > 0
