# TRON vGPU Layer

This folder contains a prototype layer for TRON that simulates a virtual aggregated GPU cluster from multiple physical nodes.

## Purpose

The goal is to demonstrate a first step toward a `customizable vGPU` service:
- aggregate VRAM and compute metrics from multiple consumer GPUs
- expose a synthetic `vGPU` profile to clients
- route tasks against the aggregate cluster

## Files

- `cluster.py` - node registration and aggregated vGPU profile generation
- `runtime.py` - task submission and simulated execution
- `demo.py` - runnable example showing how to build and execute a synthetic vGPU task

## Run

```bash
python -m vgpu.demo
```

## Notes

This is a simulation layer, not a fully transparent GPU virtualization engine. It demonstrates how TRON can gather distributed nodes and offer them as a single synthetic resource pool.
