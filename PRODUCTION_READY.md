# TRON v1.0 - Production Ready

## Quick Start: Full Stack (2 commands)

### Command 1: Deploy with Docker
```bash
cd /path/to/tron
docker compose up --build
```

**Services started:**
- Queue Server (FastAPI): `http://localhost:9000`
- Dashboard (Streamlit): `http://localhost:8501`
- 2 Workers (auto-registered)

### Command 2: Write Your Code
```python
import tron

tron.config("http://localhost:9000")

@tron.remote
def my_task(x):
    return x * 2

result = my_task(21).get()
print(result)  # 42
```

---

## Platform Features

### ✅ Automatic Royalty Accounting
- 15% platform share automatically calculated and persisted on job completion
- Atomic transfer to platform account before worker payout
- Real-time balance tracking in SQLite ledger

### ✅ Dashboard Monitoring
**URL:** `http://localhost:8501`

Tabs:
1. **Overview** - Workers, jobs, platform balance, real-time metrics
2. **License** - Onboard new data center capacity
3. **Infrastructure** - Connected workers and licensed racks
4. **Royalties** - Ledger, earnings history, transaction detail
5. **ROI** - Simulator for capacity planning (5-year projections)

### ✅ REST API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Server health check |
| `/platform/balance` | GET | Platform earnings and stats |
| `/ledger` | GET | Job history with royalty details |
| `/active_jobs` | GET | Currently running jobs |
| `/workers` | GET | Connected worker status |
| `/metrics` | GET | Queue and job metrics |
| `/register_worker` | POST | Worker registration |
| `/submit` | POST | Submit job for execution |
| `/complete/{job_id}` | POST | Report job completion (with royalty calc) |

**Example: Check platform earnings**
```bash
curl http://localhost:9000/platform/balance
```

Response:
```json
{
  "platform_balance": 2.45,
  "total_billed": 16.33,
  "total_worker_payout": 13.88,
  "total_platform_earnings": 2.45,
  "job_count": 8,
  "currency": "USD"
}
```

### ✅ One-Line Worker Bootstrap
```bash
TRON_MASTER_URL=http://<master-ip>:9000 curl -fsSL https://raw.githubusercontent.com/StarkX-cloud/tron-client/main/install_tron.sh | bash
```

Features:
- Auto-detects GPU (nvidia-smi)
- Registers with master scheduler
- Saves auth token to `~/.tron_worker_auth.json`
- Starts heartbeat loop (10s interval)

---

## Deployment Scenarios

### Local Dev (MacOS/Linux/Windows)
```bash
docker compose up --build
# Open http://localhost:8501
```

### Cloud Run (Google Cloud)
```bash
./deploy/cloud-run-quick.sh
# Deploys queue_server.py + dashboard
# Auto-provisions free tier resources
```

### Fly.io (Global Edge)
```bash
./deploy/fly-quick.sh
# Deploys to 6+ global regions
# Auto-scaling enabled
```

### Self-Hosted VPS
```bash
# 1. Install Docker
# 2. Clone repo
# 3. docker compose up --build
# 4. Set firewall: allow :9000 from trusted networks only
# 5. Configure DNS for your domain
```

---

## Database Schema

**Royalty accounting tables in SQLite:**

```sql
CREATE TABLE jobs (
  job_id TEXT PRIMARY KEY,
  task_type TEXT,
  billed_amount REAL,           -- $2.50/hr
  payout_amount REAL,           -- $1.00/hr
  royalty_amount REAL,          -- 15% of billed
  platform_share REAL,          -- billed - payout
  status TEXT,                  -- queued/running/completed/failed
  completed_at REAL,
  ...
);
```

**Platform account balance:**
```sql
CREATE TABLE platform_account (
  account_id TEXT PRIMARY KEY,  -- "platform"
  balance REAL,                 -- cumulative royalties
  last_update REAL
);
```

---

## Security Checklist

- [ ] Port 9000 (queue server) restricted to internal IPs only
- [ ] Port 8501 (dashboard) behind authentication proxy (OAuth2/SSO)
- [ ] HTTPS enabled for remote deployments
- [ ] Worker auth tokens stored securely (`~/.tron_worker_auth.json`, mode 600)
- [ ] Database backups automated (daily SQLite exports)
- [ ] Logs exported to central monitoring (Datadog/CloudWatch)
- [ ] Rate limiting enabled on job submission endpoint
- [ ] Job timeouts configured (default 3600s)

---

## Monitoring & Alerts

**Real-time dashboard**: Open `http://localhost:8501`

**Metrics endpoints**:
```bash
# Queue size
curl http://localhost:9000/metrics

# Platform earnings summary
curl http://localhost:9000/platform/balance

# Full job ledger
curl http://localhost:9000/ledger
```

**Recommended alerts**:
1. Queue size > 100 jobs → Scale workers
2. Platform balance unchanged for 1h → Check job execution
3. Worker heartbeat missed → Auto-restart or remove from pool
4. Job timeout rate > 5% → Increase timeout or reduce job size

---

## Troubleshooting

**Dashboard won't load**
```bash
# Check dashboard container
docker logs tron-dashboard

# Verify API URL
docker exec tron-dashboard env | grep TRON_API_BASE

# Test API directly
curl http://localhost:9000/health
```

**Royalties not appearing**
```bash
# Check job completion
curl http://localhost:9000/ledger

# Verify platform balance
curl http://localhost:9000/platform/balance

# Check job ID in response
```

**Workers not registering**
```bash
# Check worker logs
cat ~/.tron-worker.log

# Verify master URL
echo $TRON_MASTER_URL

# Test connectivity
curl http://localhost:9000/health
```

---

## What's New in v1.0

✅ 15% platform royalty automatically routed on job completion  
✅ Real-time platform balance tracking  
✅ Full ledger persistence in SQLite  
✅ Dashboard UI for operator monitoring  
✅ `/platform/balance` and `/ledger` REST endpoints  
✅ One-line worker bootstrap with GPU detection  
✅ Docker Compose stack (server + dashboard + workers)  
✅ Production-grade error handling and timeouts  

---

**Status**: ✅ Production Ready  
**Last Updated**: 2026-07-10  
**Maintainer**: TRON Team
