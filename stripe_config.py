import os

STRIPE_API_KEY = os.environ.get("STRIPE_API_KEY")
STRIPE_CONNECT_PLATFORM_ACCOUNT_ID = os.environ.get("STRIPE_CONNECT_PLATFORM_ACCOUNT_ID")


def get_stripe_client():
    if not STRIPE_API_KEY:
        raise EnvironmentError("STRIPE_API_KEY must be set in environment for Stripe integration.")
    import stripe
    stripe.api_key = STRIPE_API_KEY
    return stripe
