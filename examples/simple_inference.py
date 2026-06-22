#!/usr/bin/env python3
"""Simple TRON example: run a small distributed task locally.

Usage:
    pip install tron-client-py
    python examples/simple_inference.py
"""
import time
import tron

# Ensure a local server/runtime is available for development
tron.ensure_server()

@tron.remote
def square(x):
    return x * x

if __name__ == '__main__':
    inputs = list(range(5))
    futures = [square(i) for i in inputs]
    results = [f.get() for f in futures]
    print('inputs -> outputs')
    for i, r in zip(inputs, results):
        print(f'{i} -> {r}')
    print('Done')
