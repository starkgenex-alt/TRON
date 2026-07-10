"""FastAPI master scheduler for TRON DePIN infrastructure."""
from __future__ import annotations

from datetime import datetime
import time
import uuid
import sqlite3
import threading
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

from vgpu.cluster import VirtualGPUCluster
from tron_enterprise_core import TronEnterpriseLicensingEngine, EnterpriseDataCenterRack

DATABASE_PATH = Path("tron_master.db")
HEARTBEAT_TIMEOUT = 20.0
AUTH_TOKEN_HEADER = "X-TRON-AUTH"

app = FastAPI(title="TRON Master Scheduler")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

lock = threading.Lock()

# In-memory state for fast scheduling
workers: Dict[str, Dict[str, Any]] = {}
jobs: Dict[str, Dict[str, Any]] = {}
active_jobs: Dict[str, Dict[str, Any]] = {}
vgpu_cluster = VirtualGPUCluster(cluster_name="tron-vgpu-cluster")

# Enterprise licensing engine (onboard large data centers / MSPs)
enterprise_engine = TronEnterpriseLicensingEngine()


class EnterpriseLicenseRequest(BaseModel):
    location: str
    total_gpus: int


class EnterpriseOptimizeRequest(BaseModel):
    rack_id: str
    tracked_daily_revenue: float


class WorkerRegistration(BaseModel):
    name: str = Field(..., description="Worker unique name")
    capabilities: Dict[str, Any] = Field(default_factory=dict)
    gpu_name: Optional[str] = Field(None, description="Physical GPU name if present")
    vram_gb: Optional[float] = Field(None, description="Available GPU memory in GB")
    cuda_cores: Optional[int] = Field(None, description="Physical CUDA core count")
    network_bandwidth_gbps: Optional[float] = Field(None, description="Network bandwidth to master")
    location: Optional[str] = Field(None, description="Worker public location or tag")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class JobSubmission(BaseModel):
    task_type: str = Field("ai_task", description="Type of task")
    payload: Dict[str, Any] = Field(..., description="Task payload")
    runtime_seconds: Optional[float] = Field(None, description="Estimated runtime in seconds")
    priority: int = Field(1, description="Job priority")
    requires_gpu: bool = Field(False, description="GPU required")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class JobAssignment(BaseModel):
    job_id: str
    task_type: str
    payload: Dict[str, Any]
    assigned_at: float
    billing_rate: float
    payout_rate: float


class HeartbeatPayload(BaseModel):
    worker_name: str
    active_job_id: Optional[str] = None


class JobCompletion(BaseModel):
    job_id: str
    worker_name: str
    result: Dict[str, Any]
    success: bool = True
    runtime_seconds: Optional[float] = None


def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_db() -> None:
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = get_db_connection()
    with conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS workers (
                worker_name TEXT PRIMARY KEY,
                auth_token TEXT NOT NULL,
                capabilities TEXT,
                gpu_name TEXT,
                vram_gb REAL,
                cuda_cores INTEGER,
                network_bandwidth_gbps REAL,
                location TEXT,
                metadata TEXT,
                registered_at REAL,
                last_heartbeat REAL,
                status TEXT,
                active_job_id TEXT
            )
            """
        )
        # add missing worker columns for older databases
        columns = [row[1] for row in conn.execute("PRAGMA table_info(workers)").fetchall()]
        if "location" not in columns:
            conn.execute("ALTER TABLE workers ADD COLUMN location TEXT")
        if "metadata" not in columns:
            conn.execute("ALTER TABLE workers ADD COLUMN metadata TEXT")
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS jobs (
                job_id TEXT PRIMARY KEY,
                task_type TEXT,
                payload TEXT,
                submitted_at REAL,
                priority INTEGER,
                requires_gpu INTEGER,
                assigned_to TEXT,
                assigned_at REAL,
                completed_at REAL,
                runtime_ms INTEGER,
                billed_amount REAL,
                payout_amount REAL,
                status TEXT,
                result TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS licensed_racks (
                rack_id TEXT PRIMARY KEY,
                location TEXT,
                total_physical_gpus INTEGER,
                efficiency_percent REAL,
                daily_gross_revenue_usd REAL,
                licensed_at REAL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS platform_account (
                account_id TEXT PRIMARY KEY,
                balance REAL,
                last_update REAL
            )
            """
        )
        platform_columns = [row[1] for row in conn.execute("PRAGMA table_info(jobs)").fetchall()]
        if "royalty_amount" not in platform_columns:
            conn.execute("ALTER TABLE jobs ADD COLUMN royalty_amount REAL")
        if "platform_share" not in platform_columns:
            conn.execute("ALTER TABLE jobs ADD COLUMN platform_share REAL")
    conn.close()


def save_worker_state(worker_name: str, worker_info: Dict[str, Any]) -> None:
    conn = get_db_connection()
    with conn:
        conn.execute(
            "REPLACE INTO workers (worker_name, auth_token, capabilities, gpu_name, vram_gb, cuda_cores, network_bandwidth_gbps, location, metadata, registered_at, last_heartbeat, status, active_job_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                worker_name,
                worker_info["auth_token"],
                json_dumps(worker_info.get("capabilities", {})),
                worker_info.get("gpu_name"),
                worker_info.get("vram_gb"),
                worker_info.get("cuda_cores"),
                worker_info.get("network_bandwidth_gbps"),
                worker_info.get("location"),
                json_dumps(worker_info.get("metadata", {})),
                worker_info["registered_at"],
                worker_info["last_heartbeat"],
                worker_info["status"],
                worker_info.get("active_job_id"),
            ),
        )
    conn.close()

def get_platform_balance() -> float:
    """Get current platform account balance."""
    conn = get_db_connection()
    try:
        row = conn.execute("SELECT balance FROM platform_account WHERE account_id = 'platform'").fetchone()
        return float(row['balance']) if row else 0.0
    except Exception:
        return 0.0
    finally:
        conn.close()


def update_platform_balance(royalty_amount: float) -> None:
    """Add royalty to platform account."""
    conn = get_db_connection()
    try:
        current = get_platform_balance()
        new_balance = current + royalty_amount
        conn.execute(
            "INSERT OR REPLACE INTO platform_account (account_id, balance, last_update) VALUES (?, ?, ?)",
            ('platform', new_balance, time.time())
        )
        conn.commit()
    finally:
        conn.close()


def save_job_state(job_id: str, job_record: Dict[str, Any]) -> None:
    conn = get_db_connection()
    with conn:
        conn.execute(
            "REPLACE INTO jobs (job_id, task_type, payload, submitted_at, priority, requires_gpu, assigned_to, assigned_at, completed_at, runtime_ms, billed_amount, payout_amount, status, result) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                job_id,
                job_record["task_type"],
                json_dumps(job_record["payload"]),
                job_record["submitted_at"],
                job_record["priority"],
                int(job_record["requires_gpu"]),
                job_record.get("assigned_to"),
                job_record.get("assigned_at"),
                job_record.get("completed_at"),
                job_record.get("runtime_ms"),
                job_record.get("billed_amount"),
                job_record.get("payout_amount"),
                job_record["status"],
                json_dumps(job_record.get("result")) if job_record.get("result") is not None else None,
            ),
        )
    conn.close()


def save_licensed_rack(report: Dict[str, Any]) -> None:
    conn = get_db_connection()
    with conn:
        conn.execute(
            "REPLACE INTO licensed_racks (rack_id, location, total_physical_gpus, efficiency_percent, daily_gross_revenue_usd, licensed_at) VALUES (?, ?, ?, ?, ?, ?)",
            (
                report.get("rack_id"),
                report.get("location"),
                report.get("total_physical_gpus"),
                report.get("efficiency_percent"),
                report.get("daily_gross_revenue_usd"),
                time.time(),
            ),
        )
    conn.close()


def json_dumps(value: Any) -> str:
    return json.dumps(value, default=str)


def json_loads(value: Optional[str]) -> Any:
    if not value:
        return None
    return json.loads(value)


def load_persistent_state() -> None:
    conn = get_db_connection()
    with conn:
        worker_rows = conn.execute("SELECT * FROM workers").fetchall()
        for row in worker_rows:
            workers[row["worker_name"]] = {
                "auth_token": row["auth_token"],
                "capabilities": json_loads(row["capabilities"]),
                "gpu_name": row["gpu_name"],
                "vram_gb": row["vram_gb"],
                "cuda_cores": row["cuda_cores"],
                "network_bandwidth_gbps": row["network_bandwidth_gbps"],
                "location": row["location"],
                "metadata": json_loads(row["metadata"]),
                "registered_at": row["registered_at"],
                "last_heartbeat": row["last_heartbeat"],
                "status": row["status"],
                "active_job_id": row["active_job_id"],
            }
        job_rows = conn.execute("SELECT * FROM jobs").fetchall()
        for row in job_rows:
            jobs[row["job_id"]] = {
                "job_id": row["job_id"],
                "task_type": row["task_type"],
                "payload": json_loads(row["payload"]),
                "submitted_at": row["submitted_at"],
                "priority": row["priority"],
                "requires_gpu": bool(row["requires_gpu"]),
                "assigned_to": row["assigned_to"],
                "assigned_at": row["assigned_at"],
                "completed_at": row["completed_at"],
                "runtime_ms": row["runtime_ms"],
                "billed_amount": row["billed_amount"],
                "payout_amount": row["payout_amount"],
                "status": row["status"],
                "result": json_loads(row["result"]),
            }
            if row["status"] == "running" and row["assigned_to"]:
                active_jobs[row["job_id"]] = {
                    "worker": row["assigned_to"],
                    "job_id": row["job_id"],
                    "start_time": row["assigned_at"] or time.time(),
                    "billed_rate": 2.50 / 3600.0,
                    "payout_rate": 1.00 / 3600.0,
                }

        # Load persisted licensed racks into the enterprise engine
        rack_rows = conn.execute("SELECT * FROM licensed_racks").fetchall()
        for row in rack_rows:
            try:
                rack = EnterpriseDataCenterRack(
                    rack_id=row["rack_id"],
                    location=row["location"],
                    total_physical_gpus=row["total_physical_gpus"],
                    current_software_efficiency_percent=row["efficiency_percent"],
                    daily_gross_revenue_usd=row["daily_gross_revenue_usd"],
                    licensed_at=row["licensed_at"],
                )
                enterprise_engine.licensed_racks[rack.rack_id] = rack
            except Exception:
                # skip malformed rows
                continue
    conn.close()


def verify_auth_token(auth_token: str = Header(..., alias=AUTH_TOKEN_HEADER)) -> str:
    with lock:
        for worker_name, worker_info in workers.items():
            if worker_info["auth_token"] == auth_token:
                return worker_name
    raise HTTPException(status_code=401, detail="Invalid authentication token")


@app.on_event("startup")
def startup_event() -> None:
    initialize_db()
    load_persistent_state()
    threading.Thread(target=worker_watchdog, daemon=True).start()


@app.post("/register")
def register_worker(payload: WorkerRegistration) -> Dict[str, Any]:
    worker_name = payload.name
    auth_token = str(uuid.uuid4())
    now = time.time()
    worker_info = {
        "auth_token": auth_token,
        "capabilities": payload.capabilities,
        "gpu_name": payload.gpu_name,
        "vram_gb": payload.vram_gb,
        "cuda_cores": payload.cuda_cores,
        "network_bandwidth_gbps": payload.network_bandwidth_gbps,
        "location": payload.location,
        "metadata": payload.metadata,
        "registered_at": now,
        "last_heartbeat": now,
        "status": "idle",
        "active_job_id": None,
    }

    with lock:
        if worker_name in workers:
            raise HTTPException(status_code=409, detail="Worker name already registered")
        workers[worker_name] = worker_info
        save_worker_state(worker_name, worker_info)
        if payload.gpu_name and payload.vram_gb and payload.cuda_cores:
            vgpu_cluster.register_node(
                node_id=worker_name,
                gpu_name=payload.gpu_name,
                vram_gb=payload.vram_gb,
                cuda_cores=payload.cuda_cores,
                network_bandwidth_gbps=payload.network_bandwidth_gbps or 1.0,
            )

    return {"worker_name": worker_name, "auth_token": auth_token}


@app.post("/heartbeat")
def heartbeat(payload: HeartbeatPayload, worker_name: str = Depends(verify_auth_token)) -> Dict[str, Any]:
    now = time.time()
    with lock:
        if worker_name not in workers:
            raise HTTPException(status_code=404, detail="Worker not found")

        workers[worker_name]["last_heartbeat"] = now
        workers[worker_name]["status"] = "busy" if payload.active_job_id else "idle"
        workers[worker_name]["active_job_id"] = payload.active_job_id
        save_worker_state(worker_name, workers[worker_name])

    return {"status": "ok", "time": now}


@app.post("/submit_job")
def submit_job(payload: JobSubmission) -> Dict[str, Any]:
    job_id = str(uuid.uuid4())
    now = time.time()
    job_record = {
        "job_id": job_id,
        "task_type": payload.task_type,
        "payload": payload.payload,
        "submitted_at": now,
        "priority": payload.priority,
        "requires_gpu": payload.requires_gpu,
        "assigned_to": None,
        "assigned_at": None,
        "completed_at": None,
        "runtime_ms": None,
        "billed_amount": None,
        "payout_amount": None,
        "status": "queued",
        "result": None,
    }

    with lock:
        jobs[job_id] = job_record
        save_job_state(job_id, job_record)

    return {"job_id": job_id, "status": "queued"}


def choose_next_job(worker_name: str) -> Optional[Dict[str, Any]]:
    worker = workers[worker_name]
    available = []
    for job in jobs.values():
        if job["status"] != "queued":
            continue
        if job["requires_gpu"] and not worker["capabilities"].get("gpu", False):
            continue
        available.append(job)

    if not available:
        return None

    available.sort(key=lambda j: (-j["priority"], j["submitted_at"]))
    return available[0]


@app.get("/next_job")
def next_job(auth_token: str = Header(..., alias=AUTH_TOKEN_HEADER)) -> Dict[str, Any]:
    worker_name = verify_auth_token(auth_token)
    now = time.time()
    with lock:
        if worker_name not in workers:
            raise HTTPException(status_code=404, detail="Worker not found")

        worker = workers[worker_name]
        worker["last_heartbeat"] = now
        save_worker_state(worker_name, worker)

        if worker["active_job_id"]:
            return {"job": None, "reason": "worker already running a job"}

        job_record = choose_next_job(worker_name)
        if not job_record:
            return {"job": None}

        job_record["status"] = "running"
        job_record["assigned_to"] = worker_name
        job_record["assigned_at"] = now
        job_record["billed_amount"] = 0.0
        job_record["payout_amount"] = 0.0
        save_job_state(job_record["job_id"], job_record)

        worker["status"] = "busy"
        worker["active_job_id"] = job_record["job_id"]
        save_worker_state(worker_name, worker)

        active_jobs[job_record["job_id"]] = {
            "worker": worker_name,
            "job_id": job_record["job_id"],
            "start_time": now,
            "billed_rate": 2.50 / 3600.0,
            "payout_rate": 1.00 / 3600.0,
        }

    assignment = JobAssignment(
        job_id=job_record["job_id"],
        task_type=job_record["task_type"],
        payload=job_record["payload"],
        assigned_at=now,
        billing_rate=2.50,
        payout_rate=1.00,
    )
    return {"job": assignment.dict()}


@app.post("/complete_job")
def complete_job(payload: JobCompletion, worker_name: str = Depends(verify_auth_token)) -> Dict[str, Any]:
    now = time.time()
    with lock:
        if payload.job_id not in jobs:
            raise HTTPException(status_code=404, detail="Job not found")

        job_record = jobs[payload.job_id]
        if job_record["assigned_to"] != worker_name:
            raise HTTPException(status_code=403, detail="Job assigned to another worker")

        runtime_ms = int((payload.runtime_seconds if payload.runtime_seconds is not None else 0.0) * 1000)
        if payload.runtime_seconds is None and payload.job_id in active_jobs:
            runtime_ms = int((now - active_jobs[payload.job_id]["start_time"]) * 1000)

        billed_amount = (runtime_ms / 1000.0) * 2.50 / 3600.0
        payout_amount = (runtime_ms / 1000.0) * 1.00 / 3600.0
        royalty_amount = round(billed_amount * 0.15, 6)
        platform_share = round(billed_amount - payout_amount, 6)

        job_record.update({
            "status": "completed" if payload.success else "failed",
            "completed_at": now,
            "runtime_ms": runtime_ms,
            "billed_amount": billed_amount,
            "payout_amount": payout_amount,
            "royalty_amount": royalty_amount,
            "platform_share": platform_share,
            "result": payload.result,
        })
        
        # Atomically transfer royalty to platform account
        update_platform_balance(platform_share)
        save_job_state(payload.job_id, job_record)

        if payload.job_id in active_jobs:
            del active_jobs[payload.job_id]

        worker = workers[worker_name]
        worker["status"] = "idle"
        worker["active_job_id"] = None
        worker["last_heartbeat"] = now
        save_worker_state(worker_name, worker)

    return {"ok": True, "runtime_ms": runtime_ms, "billed": billed_amount, "payout": payout_amount}


@app.post("/enterprise/license")
def enterprise_license(payload: EnterpriseLicenseRequest) -> Dict[str, Any]:
    rack_id = enterprise_engine.license_new_facility(location=payload.location, total_gpus=payload.total_gpus)
    # persist the new rack
    report = enterprise_engine.get_rack_report(rack_id)
    if report:
        save_licensed_rack(report)
    return {"rack_id": rack_id}


@app.post("/enterprise/optimize")
def enterprise_optimize(payload: EnterpriseOptimizeRequest) -> Dict[str, Any]:
    royalty = enterprise_engine.optimize_facility_throughput(payload.rack_id, payload.tracked_daily_revenue)
    if royalty is None:
        raise HTTPException(status_code=404, detail="Rack not found")
    # persist updated metrics
    report = enterprise_engine.get_rack_report(payload.rack_id)
    if report:
        save_licensed_rack(report)
    return {"royalty_amount": royalty}


@app.get("/enterprise/racks")
def enterprise_racks() -> Dict[str, Any]:
    return {"racks": [enterprise_engine.get_rack_report(r) for r in enterprise_engine.licensed_racks]}


@app.get("/enterprise/racks/{rack_id}")
def enterprise_rack(rack_id: str) -> Dict[str, Any]:
    report = enterprise_engine.get_rack_report(rack_id)
    if not report:
        raise HTTPException(status_code=404, detail="Rack not found")
    return report


@app.get("/workers")
def get_workers() -> Dict[str, Any]:
    with lock:
        return {"workers": workers}


@app.get("/jobs")
def get_jobs() -> Dict[str, Any]:
    with lock:
        return {"jobs": jobs}


@app.get("/active_jobs")
def get_active_jobs() -> Dict[str, Any]:
    with lock:
        return {"active_jobs": active_jobs}


@app.get("/ledger")
def get_ledger() -> Dict[str, Any]:
    conn = get_db_connection()
    with conn:
        rows = conn.execute("SELECT * FROM jobs ORDER BY submitted_at DESC").fetchall()

    ledger = []
    for row in rows:
        entry = dict(row)
        billed_amount = float(row["billed_amount"] or 0.0)
        payout_amount = float(row["payout_amount"] or 0.0)
        entry["amount"] = billed_amount
        entry["royalty_amount"] = round(billed_amount * 0.15, 6)
        entry["platform_share"] = round(billed_amount - payout_amount, 6)
        entry["timestamp"] = datetime.fromtimestamp(row["completed_at"] or row["submitted_at"]).isoformat()
        entry["type"] = row["task_type"]
        ledger.append(entry)
    return {"ledger": ledger}




@app.get("/platform/balance")
def get_platform_balance_endpoint() -> Dict[str, Any]:
    """Get the platform account balance and earnings summary."""
    conn = get_db_connection()
    try:
        # Get platform balance
        row = conn.execute("SELECT balance FROM platform_account WHERE account_id = 'platform'").fetchone()
        platform_balance = float(row['balance']) if row else 0.0
        
        # Get total ledger stats
        ledger_rows = conn.execute(
            """
            SELECT 
              SUM(billed_amount) as total_billed,
              SUM(payout_amount) as total_payout,
              SUM(COALESCE(platform_share, billed_amount - payout_amount)) as total_platform_share,
              COUNT(*) as job_count
            FROM jobs WHERE status IN ('completed', 'failed')
            """
        ).fetchone()
        
        total_billed = float(ledger_rows['total_billed'] or 0.0)
        total_payout = float(ledger_rows['total_payout'] or 0.0)
        total_platform_share = float(ledger_rows['total_platform_share'] or 0.0)
        job_count = int(ledger_rows['job_count'] or 0)
        
        return {
            "platform_balance": round(platform_balance, 6),
            "total_billed": round(total_billed, 6),
            "total_worker_payout": round(total_payout, 6),
            "total_platform_earnings": round(total_platform_share, 6),
            "job_count": job_count,
            "currency": "USD"
        }
    finally:
        conn.close()


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


def worker_watchdog() -> None:
    while True:
        now = time.time()
        requeued = []
        with lock:
            stale_workers = [name for name, info in workers.items() if now - info["last_heartbeat"] > HEARTBEAT_TIMEOUT]
            for worker_name in stale_workers:
                worker_info = workers[worker_name]
                active_job_id = worker_info.get("active_job_id")
                if active_job_id and active_job_id in jobs:
                    job_record = jobs[active_job_id]
                    if job_record["status"] == "running":
                        job_record["status"] = "queued"
                        job_record["assigned_to"] = None
                        job_record["assigned_at"] = None
                        job_record["billed_amount"] = None
                        job_record["payout_amount"] = None
                        jobs[active_job_id] = job_record
                        save_job_state(active_job_id, job_record)
                        requeued.append(active_job_id)

                        if active_job_id in active_jobs:
                            del active_jobs[active_job_id]

                worker_info["status"] = "offline"
                worker_info["active_job_id"] = None
                workers[worker_name] = worker_info
                save_worker_state(worker_name, worker_info)

        if requeued:
            print(f"[WATCHDOG] Requeued stale jobs: {requeued}")
        time.sleep(HEARTBEAT_TIMEOUT / 2)


def main() -> None:
    host = "0.0.0.0"
    port = 9000
    initialize_db()
    load_persistent_state()
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
