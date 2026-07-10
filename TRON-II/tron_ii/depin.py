"""TRON-II integration with the TRON DePIN master scheduler."""
from __future__ import annotations

from typing import Any, Dict, Optional


class DePINClient:
    def __init__(self, master_url: str, auth_token: Optional[str] = None):
        self.master_url = master_url.rstrip("/")
        self.auth_token = auth_token

    def _headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.auth_token:
            headers["X-TRON-AUTH"] = self.auth_token
        return headers

    def submit_job(
        self,
        task_type: str,
        payload: Dict[str, Any],
        runtime_seconds: Optional[float] = None,
        priority: int = 1,
        requires_gpu: bool = False,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        try:
            import requests
        except ImportError as exc:
            raise RuntimeError("requests is required for DePIN integration") from exc

        url = f"{self.master_url}/submit_job"
        body = {
            "task_type": task_type,
            "payload": payload,
            "runtime_seconds": runtime_seconds,
            "priority": priority,
            "requires_gpu": requires_gpu,
            "metadata": metadata or {},
        }
        response = requests.post(url, json=body, headers=self._headers(), timeout=10)
        response.raise_for_status()
        return response.json()

    def register_worker(
        self,
        name: str,
        capabilities: Dict[str, Any],
        location: str = "unknown",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        try:
            import requests
        except ImportError as exc:
            raise RuntimeError("requests is required for DePIN integration") from exc

        url = f"{self.master_url}/register"
        body = {
            "name": name,
            "capabilities": capabilities,
            "location": location,
            "metadata": metadata or {},
        }
        response = requests.post(url, json=body, headers=self._headers(), timeout=10)
        response.raise_for_status()
        return response.json()
