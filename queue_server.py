try:
    from fastapi import FastAPI, Request
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import StreamingResponse
    import uvicorn
    _USE_FASTAPI = True
except Exception:
    # FastAPI or Uvicorn not installed — provide a minimal fallback HTTP server
    _USE_FASTAPI = False
    import http.server
    import socketserver
    import threading
    import json

import json
import os
import time
import uuid
import threading
import asyncio
from collections import defaultdict

# =========================
# ENGINE IMPORTS (SAFE)
# =========================

from tron_runtime.session_manager import SessionManager
from tron_runtime.virtual_memory import VirtualMemory
from tron_runtime.execution_graph import ExecutionGraph
from tron_runtime.routing_engine import RoutingEngine
from tron_runtime.predictor_engine import PredictorEngine
from tron_runtime.swarm_manager import SwarmManager
from tron_runtime.auto_scaler import AutoScaler
from tron_runtime.resurrection_engine import ResurrectionEngine
from tron_runtime.memory_mesh import MemoryMesh
from tron_runtime.stream_engine import StreamEngine
from tron_runtime.simulation_engine import SimulationEngine
from tron_runtime.pricing_engine import PricingEngine
from tron_runtime.market_engine import MarketEngine
from tron_runtime.load_shaper import LoadShaper
from tron_runtime.global_brain import GlobalDecisionBrain

# =========================
# ORCHESTRATOR & GPU IMPORTS
# =========================
# Integrated TRON-II & vGPU layers
try:
    from tron.orchestrator import TrainingOrchestrator, TrainingConfig
    HAS_ORCHESTRATOR = True
except ImportError:
    HAS_ORCHESTRATOR = False

try:
    from tron.gpu import VirtualGPUCluster
    HAS_VGPU = True
except ImportError:
    HAS_VGPU = False

# =========================
# BILLING & MONETIZATION IMPORTS
# =========================
try:
    from tron_billing import (
        APIKeyManager, PricingEngine as BillingPricingEngine, BillingLedger,
        InvoiceGenerator, UsageTracker, init_billing_db
    )
    HAS_BILLING = True
except ImportError:
    HAS_BILLING = False

# =========================
# APP
# =========================

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# STATE INIT
# =========================

sessions = SessionManager()
vmemory = VirtualMemory()
graphs = ExecutionGraph()

router = RoutingEngine()
predictor = PredictorEngine()
swarm = SwarmManager()
autoscaler = AutoScaler()
resurrection = ResurrectionEngine()
memory_mesh = MemoryMesh()
stream_engine = StreamEngine()

simulation_engine = SimulationEngine()
market = MarketEngine()
pricing_engine = PricingEngine()
load_shaper = LoadShaper()

global_brain = GlobalDecisionBrain(
    pricing_engine,
    market,
    load_shaper,
    swarm,
    simulation_engine
)

provider_router = None

# Initialize integrated orchestrator & vGPU cluster
orchestrator = None
vgpu_cluster = None

if HAS_ORCHESTRATOR:
    try:
        orchestrator = TrainingOrchestrator()
        print("[TRON] ✓ TrainingOrchestrator initialized")
    except Exception as e:
        print(f"[TRON] Warning: Could not initialize TrainingOrchestrator: {e}")

if HAS_VGPU:
    try:
        vgpu_cluster = VirtualGPUCluster(cluster_name="tron-platform-0")
        print("[TRON] ✓ VirtualGPUCluster initialized")
    except Exception as e:
        print(f"[TRON] Warning: Could not initialize VirtualGPUCluster: {e}")

# Initialize billing engine
if HAS_BILLING:
    try:
        init_billing_db()
        print("[TRON] ✓ Billing engine initialized")
    except Exception as e:
        print(f"[TRON] Warning: Could not initialize billing engine: {e}")

# =========================
# STATE MEMORY
# =========================

lock = threading.Lock()

job_queue = []
job_store = {}
workers = {}
running_jobs = {}
platform_balance = 0.0
platform_royalty_rate = 0.15
platform_earnings = 0.0
total_billed = 0.0
total_payout = 0.0

event_bus = defaultdict(list)

# =========================
# EMIT
# =========================

def emit(job_id, event_type, data=None):

    event = {
        "job_id": job_id,
        "type": event_type,
        "data": data or {},
        "time": time.time()
    }

    stream_engine.emit(job_id, event_type, data)

    with lock:
        event_bus[job_id].append(event)

# =========================
# HOME
# =========================

@app.get("/")
def home():
    return {"status": "TRON_CORE_ONLINE"}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/api/v1/payments/config")
def payment_config():
    """Return the payment provider configuration currently available."""
    return {
        "provider": getattr(__import__("payment_providers", fromlist=["router"]), "router").get_default_provider(),
        "stripe_configured": bool(os.environ.get("STRIPE_API_KEY")),
        "paystack_configured": bool(os.environ.get("PAYSTACK_SECRET_KEY")),
        "flutterwave_configured": bool(os.environ.get("FLUTTERWAVE_SECRET_KEY")),
        "stablecoin_configured": bool(os.environ.get("STABLECOIN_PRIVATE_KEY")),
    }

# =========================
# SESSIONS
# =========================

@app.post("/create_session")
def create_session():
    session_id = sessions.create_session()
    return {"session_id": session_id}

@app.get("/session/{session_id}")
def get_session(session_id: str):
    return sessions.get(session_id) or {"status": "not_found"}

# =========================
# GRAPHS
# =========================

@app.post("/create_graph")
def create_graph():
    graph_id = graphs.create_graph()
    return {"graph_id": graph_id}

@app.get("/graph/{graph_id}")
def get_graph(graph_id: str):
    return graphs.get(graph_id) or {"status": "not_found"}

# =========================
# WORKERS
# =========================

@app.post("/register_worker")
def register_worker(worker: dict):

    worker_name = worker.get("name") or str(uuid.uuid4().hex[:8])
    auth_token = str(uuid.uuid4().hex)

    with lock:
        workers[worker_name] = {
            "name": worker_name,
            "auth_token": auth_token,
            "gpu": worker.get("gpu") or worker.get("capabilities", {}).get("gpu", False),
            "gpu_name": worker.get("gpu_name"),
            "memory_gb": worker.get("memory_gb") or worker.get("capabilities", {}).get("memory_gb", 4),
            "cuda_cores": worker.get("cuda_cores") or worker.get("capabilities", {}).get("cuda_cores", 1024),
            "location": worker.get("location", "unknown"),
            "stripe_connect_account_id": worker.get("stripe_connect_account_id") or worker.get("stripe_account_id"),
            "load": 0,
            "status": "idle",
            "last_heartbeat": time.time()
        }

    return {
        "ok": True,
        "worker_name": worker_name,
        "auth_token": auth_token
    }


@app.post("/register")
def register(worker: dict):
    """Compatibility alias for older worker bootstraps."""
    return register_worker(worker)


@app.post("/heartbeat/{worker_name}")
def heartbeat(worker_name: str, request: Request, payload: dict = None):
    """Worker heartbeat with optional auth validation."""
    
    auth_token = request.headers.get("X-TRON-AUTH")
    
    with lock:
        if worker_name not in workers:
            return {"alive": False, "error": "worker not registered"}, 404
        
        worker = workers[worker_name]
        
        # Validate auth token if registered
        if worker.get("auth_token") and auth_token:
            if auth_token != worker["auth_token"]:
                return {"alive": False, "error": "invalid auth token"}, 403
        
        # Update heartbeat timestamp and active job
        worker["last_heartbeat"] = time.time()
        if payload:
            worker["active_job_id"] = payload.get("active_job_id")
    
    return {"alive": True, "worker_name": worker_name}


@app.post("/heartbeat")
def heartbeat_alias(payload: dict):
    worker_name = payload.get("worker_name")
    if not worker_name:
        return {"alive": False, "error": "missing worker_name"}
    return heartbeat(worker_name)

# =========================
# SUBMIT JOB (CLEAN + SAFE)
# =========================

@app.post("/submit_ai")
def submit_ai(job: dict):

    job_id = str(uuid.uuid4())

    raw_job = {
        "id": job_id,
        "task_type": job.get("task_type", "inference"),
        "prompt": job.get("prompt", ""),
        "priority": int(job.get("priority", 1)),
        "gpu": bool(job.get("gpu", False)),
        "memory_gb": float(job.get("memory_gb", 2)),
        "submitted_at": time.time()
    }

    enriched_job = raw_job.copy()

    # attach optional session/graph metadata
    session_id = job.get("session_id")
    graph_id = job.get("graph_id")

    if session_id:
        enriched_job["session_id"] = session_id
        sessions.add_job(session_id, enriched_job)

    if graph_id:
        enriched_job["graph_id"] = graph_id
        graphs.add_node(graph_id, enriched_job)

    # pricing
    enriched_job["estimated_cost"] = pricing_engine.compute_price(
        job_queue,
        enriched_job
    )

    enriched_job["routing"] = "default"

    # memory context
    try:
        enriched_job = memory_mesh.inject_context(enriched_job)
    except:
        pass

    # predictive layer (SAFE)
    try:
        enriched_job["predicted_runtime"] = predictor.predict_runtime(enriched_job)
        enriched_job["predicted_cost"] = predictor.predict_cost(enriched_job)
    except:
        pass

    # provider routing (ONLY IF AVAILABLE)
    if provider_router:
        try:
            enriched_job["provider"] = provider_router.select(
                enriched_job["prompt"],
                enriched_job["estimated_cost"]
            )
        except:
            enriched_job["provider"] = None

    with lock:
        job_queue.append(enriched_job)

        job_store[job_id] = {
            "id": job_id,
            "status": "queued",
            "submitted_at": time.time(),
            "estimated_cost": enriched_job["estimated_cost"]
        }

    emit(job_id, "queued", enriched_job)

    return {
        "job_id": job_id,
        "status": "queued"
    }


@app.post("/submit")
def submit(job: dict):

    job_id = str(uuid.uuid4())

    raw_job = {
        "id": job_id,
        "task_type": job.get("task_type", "remote"),
        "prompt": job.get("prompt", ""),
        "priority": int(job.get("priority", job.get("priority", 1))),
        "gpu": bool(job.get("gpu", job.get("gpu_required", False))),
        "memory_gb": float(job.get("memory_gb", job.get("min_memory_gb", 1))),
        "submitted_at": time.time(),
        "function": job.get("function"),
        "compute_weight": job.get("compute_weight", 1)
    }

    if raw_job["function"] is None:
        return {"error": "Missing function payload"}

    enriched_job = raw_job.copy()

    # pricing
    enriched_job["estimated_cost"] = pricing_engine.compute_price(
        job_queue,
        enriched_job
    )

    enriched_job["routing"] = "remote"

    with lock:
        job_queue.append(enriched_job)

        job_store[job_id] = {
            "id": job_id,
            "status": "queued",
            "submitted_at": time.time(),
            "estimated_cost": enriched_job["estimated_cost"]
        }

    emit(job_id, "queued", enriched_job)

    return {
        "job_id": job_id,
        "status": "queued"
    }

# =========================
# METRICS + DASHBOARD
# =========================

@app.get("/metrics")
def metrics():
    return {
        "workers": len(workers),
        "queue_size": len(job_queue),
        "running_jobs": len(running_jobs),
        "completed_jobs": sum(1 for job in job_store.values() if job.get("status") == "completed")
    }


@app.get("/workers")
def get_workers():
    return workers


@app.get("/running")
def get_running():
    return running_jobs


@app.get("/queue")
def get_queue():
    return {"queue": job_queue}


@app.get("/history")
def get_history():
    return {"jobs": list(job_store.values())}

@app.get("/ledger")
def get_ledger():
    ledger = []
    for job in job_store.values():
        if job.get("status") != "completed":
            continue
        ledger.append({
            "job_id": job.get("id"),
            "type": job.get("task_type"),
            "amount": float(job.get("billed_amount", 0.0)),
            "payout_amount": float(job.get("payout_amount", 0.0)),
            "royalty_amount": float(job.get("royalty_amount", 0.0)),
            "platform_share": float(job.get("platform_share", 0.0)),
            "timestamp": job.get("submitted_at"),
            "result": job.get("result"),
        })
    return {"ledger": sorted(ledger, key=lambda x: x["timestamp"], reverse=True)}

@app.get("/active_jobs")
def get_active_jobs():
    return {"active_jobs": list(running_jobs.values())}

def build_royalty_summary():
    completed_jobs = [job for job in job_store.values() if job.get("status") == "completed"]
    total_billed = sum(float(job.get("billed_amount", 0.0)) for job in completed_jobs)
    total_platform_earnings = sum(float(job.get("platform_share", 0.0)) for job in completed_jobs)
    total_worker_payout = sum(float(job.get("payout_amount", 0.0)) for job in completed_jobs)
    return {
        "platform_balance": round(platform_balance, 6),
        "total_billed": round(total_billed, 6),
        "total_worker_payout": round(total_worker_payout, 6),
        "total_platform_earnings": round(total_platform_earnings, 6),
        "completed_jobs": len(completed_jobs),
        "currency": "USD"
    }

def build_launch_context():
    worker_snapshot = list(workers.values())
    active_worker_count = len(worker_snapshot)
    layers = {
        "core": True,
        "tronii": True,
        "vgpu": True,
    }
    return {
        "status": "launch_ready",
        "layers": layers,
        "active_workers": active_worker_count,
        "install_command": "curl -fsSL https://raw.githubusercontent.com/StarkX-cloud/tron-client/main/install_tron.sh | TRON_MASTER_URL=http://127.0.0.1:9000 bash",
        "dashboard_url": "http://127.0.0.1:8501",
        "summary": build_royalty_summary(),
    }

@app.get("/platform/balance")
def get_platform_balance():
    return build_royalty_summary()

@app.get("/api/v1/launch/context")
def get_launch_context():
    return build_launch_context()

@app.post("/api/v1/payouts/trigger")
def trigger_payout(payload: dict):
    """Trigger a payout for a completed job using the active payment provider."""
    job_id = payload.get("job_id")
    recipient = payload.get("recipient")
    amount = payload.get("amount")

    if not job_id or not recipient or amount is None:
        return {"ok": False, "error": "job_id, recipient, and amount are required"}

    try:
        from payment_providers import router as payment_router
        result = payment_router.payout_worker(float(amount), recipient, metadata={"job_id": job_id})
        return {"ok": True, "job_id": job_id, "result": result}
    except Exception as e:
        return {"ok": False, "error": str(e)}

# =========================
# NEXT JOB (STABLE ROUTER CORE)
# =========================

@app.get("/next_job/{worker_name}")
def next_job(worker_name: str):

    with lock:

        if worker_name not in workers:
            return {"job": None}

        if not job_queue:
            return {"job": None}

        worker = workers[worker_name]

        scale_state = swarm.should_scale(len(job_queue))

        shaped = load_shaper.reshape(job_queue, workers)

        best_job = None
        best_index = None
        best_score = -999

        for i, entry in enumerate(shaped):

            job = entry["job"]

            if entry.get("delay") == 1:
                continue

            try:
                decision = global_brain.decide(job_queue, workers, job)
                score = decision.get("score", 0)
            except:
                score = job.get("priority", 1)

            if scale_state == "SCALE_UP":
                score += 2
            elif scale_state == "SCALE_DOWN":
                score -= 0.5

            gpu_bonus = 1.5 if worker.get("gpu") else 1.0
            memory_factor = max(0.5, 1.0 - worker.get("load", 0) * 0.1)

            score *= gpu_bonus * memory_factor
            score -= job.get("memory_gb", 1) * 0.2

            if score > best_score:
                best_score = score
                best_job = job
                best_index = i

        if best_job is None:
            return {"job": None}

        job_queue.pop(best_index)

        job_id = best_job["id"]

        job_store[job_id]["status"] = "running"

        workers[worker_name]["status"] = "busy"
        workers[worker_name]["load"] += best_job.get("memory_gb", 1)

        running_jobs[job_id] = {
            "worker": worker_name,
            "start_time": time.time(),
            "job": best_job
        }

    emit(job_id, "started", {
        "worker": worker_name,
        "task_type": best_job.get("task_type"),
        "swarm_state": scale_state,
        "score": best_score
    })

    return {
        "job": best_job,
        "swarm_state": scale_state
    }

# =========================
# COMPLETE JOB (CLEAN)
# =========================

@app.post("/complete/{job_id}")
def complete(job_id: str, result: dict):

    runtime = 0
    worker_name = None

    if isinstance(result, dict) and "result" in result and len(result) == 1:
        # Workers currently wrap payloads as {"result": actual_result}
        result = result["result"]

    with lock:

        if job_id not in job_store:
            return {"ok": False}

        if job_id in running_jobs:
            runtime = time.time() - running_jobs[job_id]["start_time"]
            worker_name = running_jobs[job_id]["worker"]

        customer_id = job_store[job_id].get("customer_id")
        expected_cost = job_store[job_id].get("billing_cost")

        billed_amount = round(expected_cost if expected_cost is not None else 0.01 + runtime * 0.001, 6)
        royalty_amount = round(billed_amount * platform_royalty_rate, 6)
        payout_amount = round(billed_amount - royalty_amount, 6)
        platform_share = royalty_amount

        job_store[job_id].update({
            "status": "completed",
            "result": result,
            "runtime": runtime,
            "cost": billed_amount,
            "billed_amount": billed_amount,
            "payout_amount": payout_amount,
            "royalty_amount": royalty_amount,
            "platform_share": platform_share
        })

        if HAS_BILLING and customer_id:
            worker_stripe_account_id = None
            if worker_name:
                worker_stripe_account_id = workers.get(worker_name, {}).get("stripe_connect_account_id")
            try:
                BillingLedger.record_charge(
                    job_id=job_id,
                    customer_id=customer_id,
                    job_type=job_store[job_id].get("task_type", "compute"),
                    is_gpu=bool(job_store[job_id].get("gpu", False)),
                    priority=int(job_store[job_id].get("priority", 1)),
                    worker_stripe_account_id=worker_stripe_account_id
                )
            except Exception as e:
                print(f"[TRON] Billing record failed for job {job_id}: {e}")

        graph_id = job_store[job_id].get("graph_id")

        global platform_balance, platform_earnings, total_billed, total_payout
        platform_balance = round(platform_balance + platform_share, 6)
        platform_earnings = round(platform_earnings + platform_share, 6)
        total_billed = round(total_billed + billed_amount, 6)
        total_payout = round(total_payout + payout_amount, 6)
        if graph_id:
            graphs.update_status(graph_id, job_id, "completed")

        if worker_name:
            workers[worker_name]["status"] = "idle"
            workers[worker_name]["load"] = max(
                0,
                workers[worker_name]["load"]
                - running_jobs[job_id]["job"]["memory_gb"]
            )

            del running_jobs[job_id]

    emit(job_id, "completed", {
        "runtime": runtime,
        "result": result
    })

    return {"ok": True}


@app.post("/complete_job")
def complete_job(payload: dict):
    job_id = payload.get("job_id")
    result = payload.get("result", {})
    if not job_id:
        return {"ok": False, "error": "missing job_id"}
    return complete(job_id, result)

# =========================
# STREAM
# =========================

@app.get("/stream/{job_id}")
async def stream(job_id: str):

    async def generator():

        last_seen = 0

        # send an initial retry hint for SSE clients
        yield "retry: 1000\n\n"

        while True:

            events = stream_engine.get(job_id)

            while last_seen < len(events):
                yield f"data: {json.dumps(events[last_seen])}\n\n"
                last_seen += 1

            # keep the connection alive between events
            yield f"data: {json.dumps({'type': 'heartbeat'})}\n\n"

            if any(e["type"] == "completed" for e in events):
                break

            await asyncio.sleep(1)

    headers = {
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no"
    }
    return StreamingResponse(generator(), media_type="text/event-stream", headers=headers)
# =========================
# STATUS
# =========================

@app.get("/status/{job_id}")
def status(job_id: str):

    return job_store.get(job_id, {"status": "not_found"})

# =========================
# RESULT
# =========================

@app.get("/result/{job_id}")
def result(job_id: str):

    return job_store.get(job_id, {"status": "not_found"})

# =========================
# CUSTOMER MANAGEMENT & BILLING
# =========================

@app.post("/admin/customer/create")
def create_customer(customer: dict):
    """Admin endpoint: Create new customer."""
    if not HAS_BILLING:
        return {"error": "Billing not enabled"}
    
    name = customer.get("name")
    email = customer.get("email")
    company = customer.get("company")

    if not name or not email:
        return {"error": "Missing required customer name or email"}
    
    stripe_connect_account_id = customer.get("stripe_connect_account_id")
    try:
        customer_id, api_key = APIKeyManager.create_customer(name, email, company, stripe_connect_account_id)
        return {
            "customer_id": customer_id,
            "api_key": api_key,
            "name": name,
            "email": email,
            "stripe_connect_account_id": stripe_connect_account_id
        }
    except Exception as e:
        return {"error": str(e)}


@app.get("/admin/customers")
def list_customers():
    """Admin endpoint: List all customers."""
    if not HAS_BILLING:
        return {"error": "Billing not enabled"}
    
    try:
        customers = APIKeyManager.list_customers()
        return {"customers": customers}
    except Exception as e:
        return {"error": str(e)}


@app.post("/admin/customer/update_stripe_account")
def update_customer_stripe_account(customer: dict):
    """Admin endpoint: Associate a Stripe connected account with a customer."""
    if not HAS_BILLING:
        return {"error": "Billing not enabled"}

    customer_id = customer.get("customer_id")
    stripe_connect_account_id = customer.get("stripe_connect_account_id")

    if not customer_id or not stripe_connect_account_id:
        return {"error": "Missing customer_id or stripe_connect_account_id"}

    try:
        APIKeyManager.update_stripe_account(customer_id, stripe_connect_account_id)
        return {
            "ok": True,
            "customer_id": customer_id,
            "stripe_connect_account_id": stripe_connect_account_id
        }
    except Exception as e:
        return {"error": str(e)}


# API Key validation helper
def get_customer_from_request(request) -> str:
    """Extract and validate API key from request."""
    auth_header = request.headers.get("X-API-Key", "")
    if not auth_header:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.lower().startswith("bearer "):
            auth_header = auth_header.split(" ", 1)[1].strip()

    if not auth_header:
        return None

    return APIKeyManager.verify_api_key(auth_header)


@app.post("/api/v1/submit")
async def submit_job_with_billing(request: Request, job: dict):
    """Submit job with billing (requires API key)."""
    if not HAS_BILLING:
        return {"error": "Billing not enabled"}
    
    # Validate API key
    customer_id = get_customer_from_request(request)
    if not customer_id:
        return {"error": "Invalid or missing API key", "code": "AUTH_FAILED"}
    
    try:
        # Track usage
        UsageTracker.record_request(customer_id)
        
        # Calculate pricing
        is_gpu = bool(job.get("gpu", False))
        priority = int(job.get("priority", 1))
        job_type = job.get("task_type", "compute")
        
        # Get cost breakdown
        total_cost, breakdown = BillingPricingEngine.calculate_job_cost(
            is_gpu,
            priority,
            surge_active=BillingPricingEngine.is_surge_pricing_active()
        )
        
        # Submit job (reuse existing logic)
        job_id = str(uuid.uuid4())
        
        enriched_job = {
            "id": job_id,
            "task_type": job_type,
            "prompt": job.get("prompt", ""),
            "priority": priority,
            "gpu": is_gpu,
            "memory_gb": float(job.get("memory_gb", 1)),
            "submitted_at": time.time(),
            "customer_id": customer_id,
            "billing_cost": total_cost,
            "estimated_cost": total_cost
        }
        
        with lock:
            job_queue.append(enriched_job)
            job_store[job_id] = {
                "id": job_id,
                "status": "queued",
                "submitted_at": time.time(),
                "customer_id": customer_id,
                "billing_cost": total_cost,
                "estimated_cost": total_cost,
                "total_charge": total_cost
            }
        
        emit(job_id, "queued", enriched_job)
        
        return {
            "job_id": job_id,
            "status": "queued",
            "cost": breakdown["total_charge"],
            "platform_share": breakdown["platform_share"],
            "worker_share": breakdown["worker_share"]
        }
    
    except Exception as e:
        return {"error": str(e)}


@app.get("/api/v1/billing/charges")
async def get_billing_charges(request: Request, days: int = 30):
    """Get charges for authenticated customer."""
    if not HAS_BILLING:
        return {"error": "Billing not enabled"}
    
    customer_id = get_customer_from_request(request)
    if not customer_id:
        return {"error": "Invalid or missing API key"}
    
    try:
        charges = BillingLedger.get_customer_charges(customer_id, days)
        summary = BillingLedger.get_customer_summary(customer_id)
        
        return {
            "customer_id": customer_id,
            "period_days": days,
            "summary": summary,
            "charges": charges,
            "charge_count": len(charges)
        }
    except Exception as e:
        return {"error": str(e)}


@app.get("/api/v1/billing/summary")
async def get_billing_summary(request: Request):
    """Get billing summary for authenticated customer."""
    if not HAS_BILLING:
        return {"error": "Billing not enabled"}
    
    customer_id = get_customer_from_request(request)
    if not customer_id:
        return {"error": "Invalid or missing API key"}
    
    try:
        summary = BillingLedger.get_customer_summary(customer_id)
        usage = UsageTracker.get_usage(customer_id)
        
        return {
            "customer_id": customer_id,
            "total_jobs": summary["total_jobs"],
            "total_charged": summary["total_charged"],
            "total_platform_earnings": summary["total_platform_earnings"],
            "total_worker_earnings": summary["total_worker_earnings"],
            "api_requests_24h": usage["total_requests"]
        }
    except Exception as e:
        return {"error": str(e)}


@app.post("/admin/billing/record")
def record_charge(job_id: str, customer_id: str, job_type: str, is_gpu: bool, priority: int = 1):
    """Admin endpoint: Record charge for completed job."""
    if not HAS_BILLING:
        return {"error": "Billing not enabled"}
    
    try:
        charge_record = BillingLedger.record_charge(
            job_id, customer_id, job_type, is_gpu, priority
        )
        return charge_record
    except Exception as e:
        return {"error": str(e)}


@app.post("/admin/billing/invoice/generate")
def generate_invoice(customer_id: str, month: str):
    """Admin endpoint: Generate invoice for customer (YYYY-MM format)."""
    if not HAS_BILLING:
        return {"error": "Billing not enabled"}
    
    try:
        invoice_id = InvoiceGenerator.generate_monthly_invoice(customer_id, month)
        if not invoice_id:
            return {"error": "No charges for this period"}
        
        return {"invoice_id": invoice_id, "month": month}
    except Exception as e:
        return {"error": str(e)}


@app.get("/admin/invoices")
def list_all_invoices():
    """Admin endpoint: List all invoices."""
    if not HAS_BILLING:
        return {"error": "Billing not enabled"}
    
    try:
        invoices = InvoiceGenerator.list_invoices()
        return {"invoices": invoices}
    except Exception as e:
        return {"error": str(e)}


@app.get("/admin/invoice/{invoice_id}")
def get_invoice_details(invoice_id: str):
    """Admin endpoint: Get invoice details."""
    if not HAS_BILLING:
        return {"error": "Billing not enabled"}
    
    try:
        invoice = InvoiceGenerator.get_invoice(invoice_id)
        if not invoice:
            return {"error": "Invoice not found"}
        return invoice
    except Exception as e:
        return {"error": str(e)}


@app.get("/api/v1/invoices")
async def get_customer_invoices(request: Request):
    """Get invoices for authenticated customer."""
    if not HAS_BILLING:
        return {"error": "Billing not enabled"}
    
    customer_id = get_customer_from_request(request)
    if not customer_id:
        return {"error": "Invalid or missing API key"}
    
    try:
        invoices = InvoiceGenerator.list_invoices(customer_id)
        return {"invoices": invoices}
    except Exception as e:
        return {"error": str(e)}


# =========================
# START
# =========================

if __name__ == "__main__":
    host = os.environ.get("TRON_HOST", "0.0.0.0")
    port = int(os.environ.get("TRON_PORT", os.environ.get("PORT", 9000)))
    reload_flag = os.environ.get("TRON_RELOAD", "false").lower() in ("1", "true", "yes", "on")
    print(f"TRON CORE STARTING on {host}:{port}")

    if _USE_FASTAPI:
        uvicorn.run(app, host=host, port=port, reload=reload_flag)
    else:
        # Minimal fallback: serve only basic health and root endpoints so SDK can auto-discover
        class _SimpleHandler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path == "/" or self.path == "":
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({"status": "TRON_CORE_ONLINE"}).encode())
                elif self.path.startswith("/health"):
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({"status": "ok"}).encode())
                else:
                    self.send_response(404)
                    self.end_headers()

        def run_simple_server(host, port):
            with socketserver.TCPServer((host, port), _SimpleHandler) as httpd:
                try:
                    httpd.serve_forever()
                except KeyboardInterrupt:
                    pass

        print("[TRON] FastAPI not available; running minimal fallback server.")
        print("Install full server with: pip install -r requirements.txt")
        run_simple_server(host, port)
