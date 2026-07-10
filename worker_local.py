#!/usr/bin/env python3
import os
import time
import uuid
import json
import subprocess
from pathlib import Path
import requests

TRON_MASTER_URL = os.environ.get('TRON_MASTER_URL', 'http://127.0.0.1:9000')
WORKER_NAME = os.environ.get('TRON_WORKER_NAME', f'tron-node-{uuid.uuid4().hex[:8]}')
AUTH_PATH = Path.home() / '.tron_worker_auth.json'
LOCATION = os.environ.get('TRON_LOCATION', 'self-hosted')


def detect_gpu():
    try:
        out = subprocess.check_output(['nvidia-smi', '--query-gpu=name,memory.total,driver_version', '--format=csv,noheader'], text=True, timeout=5)
        lines = [l.strip() for l in out.splitlines() if l.strip()]
        if lines:
            parts = lines[0].split(',')
            name = parts[0].strip()
            mem = int(float(parts[1].split()[0])) if len(parts) > 1 else 0
            vram_gb = max(1, mem // 1024)
            return True, name, vram_gb, 4096
    except Exception:
        pass
    return False, None, 1, 1024


def save_auth(info):
    AUTH_PATH.write_text(json.dumps(info))


def load_auth():
    if AUTH_PATH.exists():
        try:
            return json.loads(AUTH_PATH.read_text())
        except Exception:
            return None
    return None


def register():
    gpu_ok, gpu_name, vram_gb, cuda_cores = detect_gpu()
    payload = {
        'name': WORKER_NAME,
        'capabilities': {'gpu': gpu_ok, 'memory_gb': vram_gb, 'cuda_cores': cuda_cores, 'location': LOCATION},
        'gpu_name': gpu_name,
        'vram_gb': vram_gb,
        'cuda_cores': cuda_cores,
        'network_bandwidth_gbps': 1.0,
        'location': LOCATION,
        'metadata': {'bootstrap': 'tron-local', 'runtime': 'python'},
    }
    r = requests.post(f"{TRON_MASTER_URL}/register", json=payload, timeout=10)
    r.raise_for_status()
    data = r.json()
    auth = {'worker_name': data.get('worker_name'), 'auth_token': data.get('auth_token')}
    save_auth(auth)
    return auth


def heartbeat_loop(auth):
    headers = {'X-TRON-AUTH': auth['auth_token']}
    payload = {'worker_name': auth['worker_name'], 'active_job_id': None}
    while True:
        try:
            r = requests.post(f"{TRON_MASTER_URL}/heartbeat", json=payload, headers=headers, timeout=10)
            if r.ok:
                print(f"[TRON] heartbeat ok: {time.strftime('%X')}")
            else:
                print(f"[TRON] heartbeat failed: {r.status_code}")
        except Exception as e:
            print(f"[TRON] heartbeat error: {e}")
        time.sleep(10)


def main():
    auth = load_auth()
    if not auth:
        try:
            auth = register()
            print(f"[TRON] Registered {auth.get('worker_name')}")
        except Exception as e:
            print(f"[TRON] registration failed: {e}")
            return
    else:
        print(f"[TRON] Using saved credentials for {auth.get('worker_name')}")

    try:
        heartbeat_loop(auth)
    except KeyboardInterrupt:
        print('[TRON] stopped')


if __name__ == '__main__':
    main()
