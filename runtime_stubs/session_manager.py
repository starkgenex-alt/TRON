import uuid

class SessionManager:
    def __init__(self):
        self._sessions = {}

    def create_session(self):
        sid = str(uuid.uuid4())
        self._sessions[sid] = {"jobs": []}
        return sid

    def get(self, session_id):
        return self._sessions.get(session_id)

    def add_job(self, session_id, job):
        if session_id not in self._sessions:
            self._sessions[session_id] = {"jobs": []}
        self._sessions[session_id]["jobs"].append(job)

