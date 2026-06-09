TRON — Deployment Handoff (Partner)

Overview
- Purpose: provide everything a partner needs to deploy the TRON backend and verify the SDK release.
- Release: https://github.com/StarkX-cloud/tron-client/releases/tag/v0.1.2
- Repo: https://github.com/StarkX-cloud/tron-client
- Recommended flow: deploy to a staging environment, run acceptance tests, then promote to production.

What to fetch
- SDK (wheel): https://github.com/StarkX-cloud/tron-client/releases/download/v0.1.2/tron_client-0.1.0-py3-none-any.whl
- Source archives (release assets): `source_code.zip` / `source_code.tar.gz`
- If you need full git history: clone the repo URL above (ask owner for access if private).

Quick start (Docker Compose)
1. Extract the release or clone the repo and ensure `docker-compose.yml` and `Dockerfile` files are present.
2. Build and start:

```bash
# Build and run in background
docker compose up --build -d
```
3. The API will be available at `http://0.0.0.0:9000` by default (bind address and port are configurable).

Quick start (Python virtualenv)

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python queue_server.py
```

Environment variables and secrets
- `TRON_API_KEY` — a server-side API key used by workers/clients (must be generated and stored securely).
- `TRON_BIND_HOST` — host to bind (default 0.0.0.0)
- `TRON_BIND_PORT` — port (default 9000)
- `DATABASE_URL` — optional DB backend for persistence (if configured)
- `LOG_LEVEL` — e.g., INFO/WARN/ERROR

Security & TLS (must before public exposure)
- Terminate TLS at a reverse proxy (nginx, Cloud Load Balancer, or Cloud Run managed TLS).
- Do NOT expose `queue_server.py` directly on a public IP without TLS.
- Require `TRON_API_KEY` for client submissions; rotate keys regularly.

Running as a service (example systemd)

```ini
[Unit]
Description=TRON Queue Server
After=network.target

[Service]
User=tron
WorkingDirectory=/opt/tron
ExecStart=/opt/tron/.venv/bin/python queue_server.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Verification / acceptance tests
1. Ensure server is reachable at the configured URL.
2. On a developer machine (or container) install the wheel and run the bundled simulation:

```bash
# Install SDK from release URL
pip install https://github.com/StarkX-cloud/tron-client/releases/download/v0.1.2/tron_client-0.1.0-py3-none-any.whl

# Run the quick simulation (from the release or cloned repo)
python debug_sim.py
# or
python live_simulation.py
```

Expected: the simulation prints distributed task submission, waits, and returns a final summary with design/thermal/cost/validation keys.

Staging & rollout
- Deploy first to a staging cluster (separate DB and API keys).
- Run acceptance/smoke tests and load tests with representative workloads.
- Once validated, promote the same container image (or commit) to production.

Rollback plan
- Keep previous container image/tag in the registry for quick rollback.
- If DB migrations are required, ensure reversible migrations or backups before applying.

Contact & support
- Primary owner: share your contact info here before handing off (email/phone)
- If anything is missing in the release, request `source_code.zip` or a temporary private repo invite.

Notes
- Do not hardcode environment-specific secrets in `queue_server.py` or any source file.
- If the partner needs a private copy of the repo, consider giving them a release asset instead of the full public repo (for security).
