#!/usr/bin/env python
"""Test job completion state after chat request."""
import requests
import json

r = requests.get('http://127.0.0.1:9002/jobs', timeout=10)
jobs = r.json()['jobs']

print(f'Total jobs: {len(jobs)}')
print()

for job_id, job in list(jobs.items())[-2:]:
    print(f'Job ID: {job_id}')
    print(f'  Status: {job["status"]}')
    print(f'  Result: {job["result"] is not None}')
    print(f'  Assigned: {job["assigned_nodes"]}')
    print(f'  Completed: {job["completed_nodes"]}')
    if job['job_shards']:
        for node, shard in job['job_shards'].items():
            print(f'    Shard[{node}]: {shard["status"]}')
    print()
