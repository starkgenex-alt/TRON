from payment_providers import PaymentRouter


def test_paystack_simulation():
    import os
    os.environ["PAYSTACK_SECRET_KEY"] = "test_key"
    router = PaymentRouter()
    result = router.charge_customer(10.5, "cus_123")
    assert result["provider"] == "paystack"
    assert result["status"] == "simulated"


def test_stablecoin_simulation():
    import os
    os.environ["STABLECOIN_PRIVATE_KEY"] = "test_key"
    router = PaymentRouter()
    result = router.payout_worker(4.2, "wallet_123")
    assert result["provider"] == "stablecoin"
    assert result["status"] == "simulated"
