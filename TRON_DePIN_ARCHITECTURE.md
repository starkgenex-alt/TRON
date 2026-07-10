# TRON DePIN Architecture Blueprint

## Overview
This document describes the Phase 2 architecture for transforming TRON into a commercial Decentralized Physical Infrastructure Network (DePIN) for distributed AI workloads.

The new DePIN layer is built as a **separate infrastructure plane** from the existing TRON task orchestration client. It provides:

- Secure remote worker registration
- Authenticated heartbeat and connectivity monitoring
- Task assignment and execution tracking
- Precise runtime meter and financial ledger
- Automatic requeueing of failed or disconnected jobs

The architecture is intentionally separate from TRON-II's internal training intelligence. TRON-II remains a training decision layer, while the DePIN layer provides the physical execution fabric.

## Components

### 1. `master_scheduler.py`
A FastAPI-based centralized scheduler and ledger server that:

- Accepts remote worker registration
- Issues authentication tokens
- Tracks worker capabilities, status, and heartbeats
- Accepts job submissions for AI workloads
- Assigns queued jobs to idle authenticated workers
- Records runtime, billing, and payout metrics in SQLite
- Requeues jobs if workers disconnect mid-task

### 2. `tron_worker_daemon.py`
A lightweight worker process for remote hosts that:

- Registers itself with the master scheduler
- Polls the scheduler for new tasks
- Sends periodic heartbeats
- Executes task payloads locally
- Reports job completion, runtime, and success status

### 3. Persistent Ledger
Implemented inside `master_scheduler.py` via SQLite:

- `workers` table stores registered workers and heartbeat state
- `jobs` table stores job lifecycle state and financials
- `/ledger` endpoint exposes billing history

## Data Flow

1. Worker boots and calls `/register`.
2. Master returns `auth_token`.
3. Worker sends periodic `/heartbeat` updates.
4. Clients submit jobs to `/submit_job`.
5. Worker polls `/next_job` to claim work.
6. Master marks job as `running` and records assignment.
7. Worker executes and calls `/complete_job`.
8. Master stores runtime in milliseconds and computes billing.
9. If worker heartbeats stop, watchdog requeues the task.

## Failure Handling

### Network disconnects
- Worker heartbeats are required every 10 seconds.
- If a worker misses heartbeats for more than 20 seconds, the watchdog marks it offline.
- Any running job assigned to that worker is requeued and made available to other active nodes.

### Job resume semantics
- Jobs are requeued as `queued`, with assignment state cleared.
- No partial results are trusted without explicit completion.

## Billing Model

- Client billing rate: **$2.50 / hour**
- Worker payout rate: **$1.00 / hour**
- Runtime measured in **milliseconds** for precision
- Ledger stores:
  - `runtime_ms`
  - `billed_amount`
  - `payout_amount`
  - `status`
  - `completed_at`

## Integration with TRON and TRON-II

### TRON (Core)
This DePIN layer is best treated as an **extension of TRON's distributed execution capabilities**. It lives alongside TRON's existing `queue_server.py` and worker APIs, but introduces a more secure, production-grade remote execution fabric.

### TRON-II (Training Intelligence)
TRON-II can be integrated on top of this DePIN infrastructure by:

- Submitting training jobs to the DePIN master scheduler
- Using DePIN workers as compute execution agents
- Feeding execution telemetry back into TRON-II policy learning

This keeps TRON-II focused on model/adapter selection, while the DePIN layer handles untrusted worker registration, routing, and metering.

## Recommended Deployment

- Deploy `master_scheduler.py` on a public server with TLS.
- Open a single port (e.g. `9001`) for worker and client communication.
- Distribute `tron_worker_daemon.py` to remote nodes.
- Use environment variables or CLI flags for `TRON_MASTER_URL`, worker name, and optional pre-shared auth token.

## Summary
This design creates a robust DePIN execution layer that is:

- Secure: token-based worker auth
- Resilient: heartbeat monitoring and requeueing
- Accountable: runtime metering and ledger billing
- Lightweight: easy remote deployment via a simple CLI daemon

The DePIN layer should be built as a network infrastructure complement to the existing TRON orchestration and TRON-II intelligence layers. It is not a duplicate implementation but a new infrastructure service plane.
