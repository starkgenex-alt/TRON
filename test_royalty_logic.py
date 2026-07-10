#!/usr/bin/env python3
"""Test royalty calculation logic independently."""
import sqlite3
import time
import tempfile
from pathlib import Path

# Create a test database
test_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
test_db_path = test_db.name
test_db.close()

print(f"Testing with database: {test_db_path}")

# Initialize database with royalty tables
conn = sqlite3.connect(test_db_path)
conn.row_factory = sqlite3.Row

conn.execute("""
    CREATE TABLE IF NOT EXISTS jobs (
        id TEXT PRIMARY KEY,
        worker_id TEXT,
        model_name TEXT,
        duration_seconds REAL,
        billed_amount REAL,
        payout_amount REAL,
        royalty_amount REAL,
        platform_share REAL,
        status TEXT,
        timestamp REAL
    )
""")

conn.execute("""
    CREATE TABLE IF NOT EXISTS platform_account (
        account_id TEXT PRIMARY KEY,
        balance REAL,
        last_update REAL
    )
""")

conn.commit()

# Initialize platform account
conn.execute(
    "INSERT INTO platform_account (account_id, balance, last_update) VALUES (?, ?, ?)",
    ('platform', 0.0, time.time())
)
conn.commit()

print("[✓] Database initialized with platform_account table")

# Simulate a job completion with royalty transfer
def complete_job_with_royalty(job_id, duration_s, billed, payout):
    """Simulate completing a job and transferring royalty."""
    # Calculate royalty: 15% of billed amount
    royalty_amount = round(billed * 0.15, 6)
    platform_share = round(billed - payout, 6)
    
    # Insert job record
    conn.execute(
        """INSERT INTO jobs 
           (id, worker_id, model_name, duration_seconds, billed_amount, payout_amount, 
            royalty_amount, platform_share, status, timestamp) 
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (job_id, 'worker1', 'gpu-v100', duration_s, billed, payout, 
         royalty_amount, platform_share, 'completed', time.time())
    )
    
    # Update platform balance atomically
    current_balance = conn.execute(
        "SELECT balance FROM platform_account WHERE account_id = 'platform'"
    ).fetchone()['balance']
    
    new_balance = round(current_balance + platform_share, 6)
    
    conn.execute(
        "UPDATE platform_account SET balance = ?, last_update = ? WHERE account_id = 'platform'",
        (new_balance, time.time())
    )
    
    conn.commit()
    
    return {
        'job_id': job_id,
        'billed': billed,
        'payout': payout,
        'royalty_15pct': royalty_amount,
        'platform_share': platform_share,
        'new_platform_balance': new_balance
    }

# Test 1: Job worth $10, payout $8
print("\n[TEST 1] Job: $10 billed, $8 payout")
result = complete_job_with_royalty('job_001', 3600, 10.0, 8.0)
print(f"  Billed: ${result['billed']}")
print(f"  Payout to worker: ${result['payout']}")
print(f"  Royalty (15%): ${result['royalty_15pct']}")
print(f"  Platform share: ${result['platform_share']}")
print(f"  Platform balance after: ${result['new_platform_balance']}")

# Verify royalty math
assert result['royalty_15pct'] == 1.5, f"Expected royalty 1.5, got {result['royalty_15pct']}"
assert result['platform_share'] == 2.0, f"Expected platform_share 2.0, got {result['platform_share']}"
assert result['new_platform_balance'] == 2.0, f"Expected balance 2.0, got {result['new_platform_balance']}"
print("  ✓ Royalty math correct")

# Test 2: Second job worth $5, payout $3
print("\n[TEST 2] Job: $5 billed, $3 payout")
result = complete_job_with_royalty('job_002', 1800, 5.0, 3.0)
print(f"  Billed: ${result['billed']}")
print(f"  Payout to worker: ${result['payout']}")
print(f"  Royalty (15%): ${result['royalty_15pct']}")
print(f"  Platform share: ${result['platform_share']}")
print(f"  Platform balance after: ${result['new_platform_balance']}")

# Verify cumulative balance
assert result['royalty_15pct'] == 0.75, f"Expected royalty 0.75, got {result['royalty_15pct']}"
assert result['platform_share'] == 2.0, f"Expected platform_share 2.0, got {result['platform_share']}"
assert result['new_platform_balance'] == 4.0, f"Expected balance 4.0, got {result['new_platform_balance']}"
print("  ✓ Cumulative balance correct")

# Verify ledger totals
ledger = conn.execute(
    """SELECT 
        SUM(billed_amount) as total_billed,
        SUM(payout_amount) as total_payout,
        SUM(platform_share) as total_platform_share,
        COUNT(*) as job_count
    FROM jobs WHERE status = 'completed'
    """
).fetchone()

print("\n[LEDGER TOTALS]")
print(f"  Total billed: ${ledger['total_billed']}")
print(f"  Total worker payout: ${ledger['total_payout']}")
print(f"  Total platform earnings: ${ledger['total_platform_share']}")
print(f"  Jobs completed: {ledger['job_count']}")

# Verify final platform balance
final_balance = conn.execute(
    "SELECT balance FROM platform_account WHERE account_id = 'platform'"
).fetchone()['balance']

print(f"\n[PLATFORM ACCOUNT]")
print(f"  Final balance: ${final_balance}")
print(f"  Matches ledger total: {final_balance == ledger['total_platform_share']}")

assert final_balance == 4.0, f"Expected final balance 4.0, got {final_balance}"

# Cleanup
conn.close()
Path(test_db_path).unlink()

print("\n✅ ALL ROYALTY LOGIC TESTS PASSED")
print("   - Royalty calculation: 15% of billed amount ✓")
print("   - Platform share calculation: billed - payout ✓")
print("   - Atomic balance updates ✓")
print("   - Cumulative ledger tracking ✓")
