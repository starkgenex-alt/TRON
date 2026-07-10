from tron_enterprise_core import TronEnterpriseLicensingEngine


def test_enterprise_licensing_engine_calculates_royalty_correctly():
    engine = TronEnterpriseLicensingEngine(platform_royalty_percent=0.15)
    rack_id = engine.license_new_facility(location="Test DC", total_gpus=42)

    royalty_amount = engine.optimize_facility_throughput(rack_id, tracked_daily_revenue=10000.0)

    assert royalty_amount == 1500.0
    report = engine.get_rack_report(rack_id)
    assert report is not None
    assert report["location"] == "Test DC"
    assert report["total_physical_gpus"] == 42
    assert report["efficiency_percent"] == 95.0
    assert report["daily_gross_revenue_usd"] == 10000.0
    assert report["royalty_percent"] == 15.0
    assert report["royalty_amount_usd"] == 1500.0


def test_get_rack_report_returns_none_for_unknown_rack():
    engine = TronEnterpriseLicensingEngine(platform_royalty_percent=0.15)
    assert engine.get_rack_report("nonexistent") is None
