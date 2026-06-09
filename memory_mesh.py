class MemoryMesh:
    def __init__(self):
        self.nodes = {}

    def put(self, key, value):
        self.nodes[key] = value

    def get(self, key):
        return self.nodes.get(key)

    def inject_context(self, job):
        return job

