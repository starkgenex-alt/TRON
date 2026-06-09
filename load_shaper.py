class LoadShaper:
    def __init__(self):
        pass

    def shape(self, job):
        return job

    def reshape(self, job_queue, workers):
        return [{"job": job, "delay": 0} for job in job_queue]

