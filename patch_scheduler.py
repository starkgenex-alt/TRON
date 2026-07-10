#!/usr/bin/env python3
"""Patch master_scheduler.py to add platform account and royalty tracking."""
import re
from pathlib import Path

scheduler_file = Path('master_scheduler.py')
content = scheduler_file.read_text()

# Patch 1: Add platform_account table and royalty columns to initialize_db
old_init = r'''        conn\.execute\(
            """
            CREATE TABLE IF NOT EXISTS licensed_racks \(
                rack_id TEXT PRIMARY KEY,
                location TEXT,
                total_physical_gpus INTEGER,
                efficiency_percent REAL,
                daily_gross_revenue_usd REAL,
                licensed_at REAL
            \)
            """
        \)
    conn\.close\(\)'''

new_init = '''        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS licensed_racks (
                rack_id TEXT PRIMARY KEY,
                location TEXT,
                total_physical_gpus INTEGER,
                efficiency_percent REAL,
                daily_gross_revenue_usd REAL,
                licensed_at REAL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS platform_account (
                account_id TEXT PRIMARY KEY,
                balance REAL,
                last_update REAL
            )
            """
        )
        # Ensure royalty and platform_share columns exist for jobs table
        try:
            conn.execute("ALTER TABLE jobs ADD COLUMN royalty_amount REAL")
        except Exception:
            pass
        try:
            conn.execute("ALTER TABLE jobs ADD COLUMN platform_share REAL")
        except Exception:
            pass
    conn.close()'''

content = re.sub(old_init, new_init, content)

# Patch 2: Add platform balance getter/setter functions before save_job_state
insert_before = 'def save_job_state'
insert_text = '''def get_platform_balance() -> float:
    """Get current platform account balance."""
    conn = get_db_connection()
    try:
        row = conn.execute("SELECT balance FROM platform_account WHERE account_id = 'platform'").fetchone()
        return float(row['balance']) if row else 0.0
    except Exception:
        return 0.0
    finally:
        conn.close()


def update_platform_balance(royalty_amount: float) -> None:
    """Add royalty to platform account."""
    conn = get_db_connection()
    try:
        current = get_platform_balance()
        new_balance = current + royalty_amount
        conn.execute(
            "INSERT OR REPLACE INTO platform_account (account_id, balance, last_update) VALUES (?, ?, ?)",
            ('platform', new_balance, time.time())
        )
        conn.commit()
    finally:
        conn.close()


'''

if insert_before in content:
    idx = content.find(insert_before)
    content = content[:idx] + insert_text + content[idx:]

# Patch 3: Update complete_job to compute and store royalty
old_complete = r'''        billed_amount = \(runtime_ms / 1000\.0\) \* 2\.50 / 3600\.0
        payout_amount = \(runtime_ms / 1000\.0\) \* 1\.00 / 3600\.0

        job_record\.update\(\{
            "status": "completed" if payload\.success else "failed",
            "completed_at": now,
            "runtime_ms": runtime_ms,
            "billed_amount": billed_amount,
            "payout_amount": payout_amount,
            "result": payload\.result,
        \}\)'''

new_complete = '''        billed_amount = (runtime_ms / 1000.0) * 2.50 / 3600.0
        payout_amount = (runtime_ms / 1000.0) * 1.00 / 3600.0
        royalty_amount = round(billed_amount * 0.15, 6)
        platform_share = round(billed_amount - payout_amount, 6)

        job_record.update({
            "status": "completed" if payload.success else "failed",
            "completed_at": now,
            "runtime_ms": runtime_ms,
            "billed_amount": billed_amount,
            "payout_amount": payout_amount,
            "royalty_amount": royalty_amount,
            "platform_share": platform_share,
            "result": payload.result,
        })
        
        # Atomically transfer royalty to platform account
        update_platform_balance(platform_share)'''

content = re.sub(old_complete, new_complete, content)

scheduler_file.write_text(content)
print('[OK] master_scheduler.py patched for platform account and royalty tracking')
