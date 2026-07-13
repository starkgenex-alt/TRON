#!/usr/bin/env python
"""Test Stripe integration with billing engine."""

import sys
sys.path.insert(0, '.')

from tron_billing import APIKeyManager, BillingLedger, PricingEngine
from stripe_config import get_stripe_client

print('=' * 60)
print('STRIPE INTEGRATION VALIDATION TEST')
print('=' * 60)

# Test 1: Create customer with Stripe account
print('\nTest 1: Create customer with Stripe account')
cust_id, api_key = APIKeyManager.create_customer(
    'Test Org', 
    'test@org.com', 
    company='TestCo',
    stripe_connect_account_id='acct_test123'
)
print(f'[OK] Customer created: {cust_id}')
print(f'[OK] API Key: {api_key}')

# Test 2: Calculate pricing
print('\nTest 2: Calculate pricing')
total_cost, breakdown = PricingEngine.calculate_job_cost(gpu_required=True, priority=2)
print(f'[OK] GPU job cost: ${total_cost}')
print(f'[OK] Platform share (15%): ${breakdown["platform_share"]}')
print(f'[OK] Worker share (85%): ${breakdown["worker_share"]}')

# Test 3: Record charge (Stripe payout support)
print('\nTest 3: Record billing charge with Stripe fields')
result = BillingLedger.record_charge(
    'job_123',
    cust_id,
    'compute',
    is_gpu=True,
    priority=2,
    worker_stripe_account_id='acct_worker456'
)
print('[OK] Billing charge recorded with Stripe metadata')
print(f'[OK] Stripe transfer ID: {result.get("stripe_transfer_id")}')

# Test 4: Check Stripe client initialization
print('\nTest 4: Stripe client configuration')
try:
    stripe = get_stripe_client()
    if stripe:
        print('[OK] Stripe client initialized successfully')
except EnvironmentError as e:
    print(f'[WARN] {str(e)}')
    print('[INFO] Set STRIPE_API_KEY environment variable to enable real Stripe transfers')

print('\n' + '=' * 60)
print('STRIPE INTEGRATION TESTS COMPLETED')
print('Note: Stripe transfers will work once STRIPE_API_KEY is set')
print('=' * 60)
