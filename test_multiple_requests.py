#!/usr/bin/env python
"""Test multiple chat completions to verify stability."""
import requests
import json
import time

tests = [
    {
        'name': 'Simple greeting',
        'message': 'Hello, how are you?'
    },
    {
        'name': 'Technical question',
        'message': 'What is a distributed system?'
    },
    {
        'name': 'Creative request',
        'message': 'Write a haiku about AI.'
    }
]

print('Testing end-to-end chat completions...\n')

for i, test in enumerate(tests, 1):
    req = {
        'model': 'tron-gateway',
        'messages': [{'role': 'user', 'content': test['message']}],
        'temperature': 0.7,
        'max_tokens': 128
    }
    
    start = time.time()
    try:
        r = requests.post('http://127.0.0.1:9003/v1/chat/completions', json=req, timeout=30)
        elapsed = time.time() - start
        
        if r.status_code == 200:
            data = r.json()
            content = data['choices'][0]['message']['content']
            print(f'Test {i}: {test["name"]}')
            print(f'  Status: {r.status_code}, Time: {elapsed:.2f}s')
            print(f'  Prompt: {test["message"]}')
            print(f'  Response: {content}')
            print()
        else:
            print(f'Test {i}: FAILED (Status {r.status_code})')
            print()
    except Exception as e:
        print(f'Test {i}: ERROR - {e}\n')

# Show final job state
print('=== Final Job State ===')
r = requests.get('http://127.0.0.1:9002/jobs')
jobs = r.json()['jobs']
completed = sum(1 for j in jobs.values() if j['status'] == 'completed')
print(f'Total jobs: {len(jobs)}, Completed: {completed}')
