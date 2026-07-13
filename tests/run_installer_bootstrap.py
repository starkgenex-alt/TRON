import os
import subprocess
import sys
import tempfile
import textwrap
import time
from pathlib import Path

root = Path(__file__).resolve().parents[1]
install_script = root / 'install_tron.sh'
text = install_script.read_text(encoding='utf-8')

start_marker = "cat > \"$BOOT_DIR/worker.py\" <<'PY'\n"
end_marker = "PY\n\nchmod +x \"$BOOT_DIR/worker.py\""
start = text.index(start_marker) + len(start_marker)
end = text.index(end_marker, start)
worker_code = text[start:end]

worker_path = Path(tempfile.gettempdir()) / 'tron_bootstrap_test_worker.py'
worker_path.write_text(worker_code, encoding='utf-8')
print(f'Bootstrap worker written to {worker_path}')

env = os.environ.copy()
env['TRON_MASTER_URL'] = 'http://127.0.0.1:9000'
env['TRON_WORKER_NAME'] = 'local-e2e-worker'
proc = subprocess.Popen([sys.executable, str(worker_path)], cwd=str(root), env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

try:
    deadline = time.time() + 15
    output = []
    while time.time() < deadline:
        line = proc.stdout.readline()
        if line:
            output.append(line.rstrip())
            print(line.rstrip())
        if proc.poll() is not None:
            break
        time.sleep(0.2)
    if proc.poll() is None:
        proc.terminate()
        proc.wait(timeout=5)
finally:
    if proc.poll() is None:
        proc.terminate()
        proc.wait(timeout=5)

print('\nBootstrap output summary:')
print('\n'.join(output[-20:]))
