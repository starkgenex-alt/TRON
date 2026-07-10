"""Convenience launcher for the TRON AI gateway stack."""
from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main() -> None:
    scheduler_cmd = [sys.executable, "-m", "vgpu.scheduler"]
    bridge_cmd = [sys.executable, "-m", "vgpu.openai_bridge"]

    print("Starting TRON vGPU scheduler...")
    scheduler = subprocess.Popen(scheduler_cmd, cwd=str(ROOT), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    time.sleep(2)

    print("Starting TRON OpenAI-compatible gateway...")
    bridge = subprocess.Popen(bridge_cmd, cwd=str(ROOT), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    time.sleep(2)

    print("TRON AI gateway stack is launching.")
    print("Scheduler: http://localhost:9002")
    print("Bridge: http://localhost:9003")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        scheduler.terminate()
        bridge.terminate()
        scheduler.wait(timeout=5)
        bridge.wait(timeout=5)


if __name__ == "__main__":
    main()
