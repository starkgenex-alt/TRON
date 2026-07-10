from fastapi.testclient import TestClient
import master_scheduler as ms


client = TestClient(ms.app)


def test_enterprise_license_and_optimize():
    # License a new facility
    resp = client.post("/enterprise/license", json={"location": "Test DC", "total_gpus": 10})
    assert resp.status_code == 200
    data = resp.json()
    assert "rack_id" in data
    rack_id = data["rack_id"]

    # Optimize facility throughput and get royalty
    resp2 = client.post(
        "/enterprise/optimize",
        json={"rack_id": rack_id, "tracked_daily_revenue": 2000.0},
    )
    assert resp2.status_code == 200
    assert resp2.json()["royalty_amount"] == 300.0

    # Fetch racks list and specific report
    resp3 = client.get("/enterprise/racks")
    assert resp3.status_code == 200
    racks = resp3.json()["racks"]
    assert any(r and r["rack_id"] == rack_id for r in racks)

    resp4 = client.get(f"/enterprise/racks/{rack_id}")
    assert resp4.status_code == 200
    report = resp4.json()
    assert report["royalty_amount_usd"] == 300.0
