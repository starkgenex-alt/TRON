#!/usr/bin/env python3
import os
import sys
import json
import time
import uuid
import subprocess
import tempfile
from pathlib import Path
import requests

TRON_MASTER_URL = os.environ.get('TRON_MASTER_URL', 'http://127.0.0.1:9000')
TRON_WORKER_NAME = os.environ.get('TRON_WORKER_NAME', f"tron-node-{uuid.uuid4().hex[:8]}")
AUTH_PATH = Path.home() / '.tron_worker_auth.json'
LOCATION = os.environ.get('TRON_LOCATION', 'self-hosted')
START_WORKER = os.environ.get('START_WORKER', 'false').lower() in {'1', 'true', 'yes'}


def detect_gpu():
    try:
        out = subprocess.check_output([
            'nvidia-smi', '--query-gpu=name,memory.total,driver_version', '--format=csv,noheader'
        ], text=True, timeout=5)
        lines = [line.strip() for line in out.splitlines() if line.strip()]
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
    AUTH_PATH.write_text(json.dumps(info), encoding='utf-8')


def load_auth():
    if AUTH_PATH.exists():
        try:
            return json.loads(AUTH_PATH.read_text(encoding='utf-8'))
        except Exception:
            return None
    return None


def register():
    gpu_ok, gpu_name, vram_gb, cuda_cores = detect_gpu()
    payload = {
        'name': TRON_WORKER_NAME,
        'capabilities': {'gpu': gpu_ok, 'memory_gb': vram_gb, 'cuda_cores': cuda_cores, 'location': LOCATION},
        'gpu_name': gpu_name,
        'vram_gb': vram_gb,
        'cuda_cores': cuda_cores,
        'network_bandwidth_gbps': 1.0,
        'location': LOCATION,
        'metadata': {'bootstrap': 'tron-bootstrap', 'runtime': 'python'},
    }
    response = requests.post(f"{TRON_MASTER_URL}/register_worker", json=payload, timeout=10)
    response.raise_for_status()
    data = response.json()
    auth = {'worker_name': data.get('worker_name'), 'auth_token': data.get('auth_token')}
    save_auth(auth)
    return auth


def write_worker_script(boot_dir: Path):
    worker_script = boot_dir / 'worker.py'
    worker_script.write_text("""#!/usr/bin/env python3
import os
import time
import uuid
import json
import requests

TRON_MASTER_URL = os.environ.get('TRON_MASTER_URL', 'http://127.0.0.1:9000')
WORKER_NAME = os.environ.get('TRON_WORKER_NAME', f'tron-node-{uuid.uuid4().hex[:8]}')
AUTH_PATH = os.path.expanduser('~/.tron_worker_auth.json')
LOCATION = os.environ.get('TRON_LOCATION', 'self-hosted')


def load_auth():
    if os.path.exists(AUTH_PATH):
        try:
            return json.loads(open(AUTH_PATH, 'r', encoding='utf-8').read())
        except Exception:
            return None
    return None


def heartbeat_loop(auth):
    headers = {'X-TRON-AUTH': auth['auth_token']}
    payload = {'worker_name': auth['worker_name'], 'active_job_id': None}
    while True:
        try:
            r = requests.post(f"{TRON_MASTER_URL}/heartbeat/{auth['worker_name']}", json=payload, headers=headers, timeout=10)
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
        print('[TRON] no saved auth found; bootstrap registration must be completed first')
        return
    heartbeat_loop(auth)


if __name__ == '__main__':
    main()
""", encoding='utf-8')
    return worker_script


def main():
    boot_dir = Path(tempfile.gettempdir()) / 'tron-bootstrap'
    boot_dir.mkdir(parents=True, exist_ok=True)
    print(f"[TRON] Installing TRON-II worker bootstrap to {boot_dir}")
    worker_script = write_worker_script(boot_dir)
    try:
        auth = register()
        print(f"[TRON] Registered {auth.get('worker_name')}")
    except Exception as e:
        print(f"[TRON] registration failed: {e}")
        return 1

    if START_WORKER:
        print('[TRON] Starting worker process...')
        subprocess.Popen([sys.executable, str(worker_script)], cwd=str(boot_dir), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
        print('[TRON] Worker started in background.')
    else:
        print(f"[TRON] Installer completed. Run the worker: {sys.executable} {worker_script}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
