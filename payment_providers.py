import os
import json
import urllib.request
import urllib.error
from typing import Dict, Optional


class PaymentProvider:
    """Abstract payment provider interface for collection and payout."""

    def charge_customer(self, amount_usd: float, customer_reference: str, metadata: Optional[Dict] = None) -> Dict:
        raise NotImplementedError

    def payout_worker(self, amount_usd: float, recipient_reference: str, metadata: Optional[Dict] = None) -> Dict:
        raise NotImplementedError


class StripeProvider(PaymentProvider):
    def __init__(self):
        self.api_key = os.environ.get("STRIPE_API_KEY")

    def charge_customer(self, amount_usd: float, customer_reference: str, metadata: Optional[Dict] = None) -> Dict:
        if not self.api_key:
            raise RuntimeError("STRIPE_API_KEY not configured")
        raise NotImplementedError("Stripe charge flow is not implemented in this local build")

    def payout_worker(self, amount_usd: float, recipient_reference: str, metadata: Optional[Dict] = None) -> Dict:
        if not self.api_key:
            raise RuntimeError("STRIPE_API_KEY not configured")
        raise NotImplementedError("Stripe payout flow is not implemented in this local build")


class PaystackProvider(PaymentProvider):
    def __init__(self):
        self.secret_key = os.environ.get("PAYSTACK_SECRET_KEY")

    def charge_customer(self, amount_usd: float, customer_reference: str, metadata: Optional[Dict] = None) -> Dict:
        if not self.secret_key:
            raise RuntimeError("PAYSTACK_SECRET_KEY not configured")
        return {"provider": "paystack", "status": "simulated", "reference": customer_reference, "amount_usd": amount_usd}

    def payout_worker(self, amount_usd: float, recipient_reference: str, metadata: Optional[Dict] = None) -> Dict:
        if not self.secret_key:
            raise RuntimeError("PAYSTACK_SECRET_KEY not configured")
        return {"provider": "paystack", "status": "simulated", "reference": recipient_reference, "amount_usd": amount_usd}


class FlutterwaveProvider(PaymentProvider):
    def __init__(self):
        self.secret_key = os.environ.get("FLUTTERWAVE_SECRET_KEY")

    def charge_customer(self, amount_usd: float, customer_reference: str, metadata: Optional[Dict] = None) -> Dict:
        if not self.secret_key:
            raise RuntimeError("FLUTTERWAVE_SECRET_KEY not configured")
        return {"provider": "flutterwave", "status": "simulated", "reference": customer_reference, "amount_usd": amount_usd}

    def payout_worker(self, amount_usd: float, recipient_reference: str, metadata: Optional[Dict] = None) -> Dict:
        if not self.secret_key:
            raise RuntimeError("FLUTTERWAVE_SECRET_KEY not configured")
        return {"provider": "flutterwave", "status": "simulated", "reference": recipient_reference, "amount_usd": amount_usd}


class StablecoinProvider(PaymentProvider):
    def __init__(self):
        self.rpc_url = os.environ.get("STABLECOIN_RPC_URL")
        self.private_key = os.environ.get("STABLECOIN_PRIVATE_KEY")

    def charge_customer(self, amount_usd: float, customer_reference: str, metadata: Optional[Dict] = None) -> Dict:
        if not self.private_key:
            raise RuntimeError("STABLECOIN_PRIVATE_KEY not configured")
        return {"provider": "stablecoin", "status": "simulated", "reference": customer_reference, "amount_usd": amount_usd}

    def payout_worker(self, amount_usd: float, recipient_reference: str, metadata: Optional[Dict] = None) -> Dict:
        if not self.private_key:
            raise RuntimeError("STABLECOIN_PRIVATE_KEY not configured")
        return {"provider": "stablecoin", "status": "simulated", "reference": recipient_reference, "amount_usd": amount_usd}


class PaymentRouter:
    """Route payments to the best available provider for the deployment."""

    def __init__(self):
        self.providers = {
            "stripe": StripeProvider(),
            "paystack": PaystackProvider(),
            "flutterwave": FlutterwaveProvider(),
            "stablecoin": StablecoinProvider(),
        }

    def get_default_provider(self) -> str:
        if os.environ.get("STABLECOIN_PRIVATE_KEY"):
            return "stablecoin"
        if os.environ.get("PAYSTACK_SECRET_KEY"):
            return "paystack"
        if os.environ.get("FLUTTERWAVE_SECRET_KEY"):
            return "flutterwave"
        if os.environ.get("STRIPE_API_KEY"):
            return "stripe"
        return "stablecoin"

    def charge_customer(self, amount_usd: float, customer_reference: str, metadata: Optional[Dict] = None) -> Dict:
        provider_name = self.get_default_provider()
        provider = self.providers[provider_name]
        return provider.charge_customer(amount_usd, customer_reference, metadata=metadata)

    def payout_worker(self, amount_usd: float, recipient_reference: str, metadata: Optional[Dict] = None) -> Dict:
        provider_name = self.get_default_provider()
        provider = self.providers[provider_name]
        return provider.payout_worker(amount_usd, recipient_reference, metadata=metadata)


router = PaymentRouter()
