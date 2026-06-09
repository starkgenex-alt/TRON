class RoutingEngine:
    def __init__(self):
        pass

    def pick_worker(self, job, workers):
        # simple policy: return first idle worker name
        for name, info in workers.items():
            if info.get("status") == "idle":
                return name
        # fallback: any worker
        return next(iter(workers), None)

