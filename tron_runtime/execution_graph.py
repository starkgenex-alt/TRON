class ExecutionGraph:
    def __init__(self):
        self._graphs = {}

    def create_graph(self):
        gid = str(len(self._graphs) + 1)
        self._graphs[gid] = {"nodes": [], "status": "new"}
        return gid

    def add_node(self, graph_id, node):
        if graph_id not in self._graphs:
            self._graphs[graph_id] = {"nodes": [], "status": "new"}
        self._graphs[graph_id]["nodes"].append(node)

    def get(self, graph_id):
        return self._graphs.get(graph_id)

    def update_status(self, graph_id, job_id, status):
        if graph_id in self._graphs:
            self._graphs[graph_id]["status"] = status
            self._graphs[graph_id].setdefault("updated_jobs", []).append({"job_id": job_id, "status": status})

