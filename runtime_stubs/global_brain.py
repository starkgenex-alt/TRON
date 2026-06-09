class GlobalDecisionBrain:
    def __init__(self, pricing_engine, market, load_shaper, swarm, simulation_engine):
        self.pricing_engine = pricing_engine
        self.market = market
        self.load_shaper = load_shaper
        self.swarm = swarm
        self.simulation_engine = simulation_engine

    def decide(self, job_queue, workers, job):
        return {"score": job.get("priority", 1)}

