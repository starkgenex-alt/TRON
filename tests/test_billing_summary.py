import queue_server


def test_build_royalty_summary_uses_completed_jobs():
    queue_server.job_store = {
        "job-1": {
            "id": "job-1",
            "status": "completed",
            "billed_amount": 10.0,
            "payout_amount": 8.5,
            "royalty_amount": 1.5,
            "platform_share": 1.5,
        },
        "job-2": {
            "id": "job-2",
            "status": "queued",
            "billed_amount": 5.0,
            "payout_amount": 4.0,
            "royalty_amount": 1.0,
            "platform_share": 1.0,
        },
    }

    summary = queue_server.build_royalty_summary()

    assert summary["completed_jobs"] == 1
    assert summary["total_billed"] == 10.0
    assert summary["total_platform_earnings"] == 1.5
    assert summary["total_worker_payout"] == 8.5
