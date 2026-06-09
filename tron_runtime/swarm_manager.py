class SwarmManager:
    def __init__(self):
        self.workers = {}

    def register(self, name, meta):
        self.workers[name] = meta

    def list_workers(self):
        return list(self.workers.keys())

    def should_scale(self, queue_length):
        if queue_length > 5:
            return "SCALE_UP"
        if queue_length == 0:
            return "SCALE_DOWN"
        return "STABLE"

