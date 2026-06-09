class PricingEngine:
    def __init__(self):
        pass

    def compute_price(self, job_queue, job=None):
        # simple flat pricing estimate
        try:
            return 0.01
        except Exception:
            return 0.0

