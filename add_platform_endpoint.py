#!/usr/bin/env python3
"""Add platform balance endpoint and ledger summary to master_scheduler.py."""
from pathlib import Path

scheduler_file = Path('master_scheduler.py')
content = scheduler_file.read_text()

# Add platform balance endpoint after the get_ledger function
new_endpoint = '''

@app.get("/platform/balance")
def get_platform_balance_endpoint() -> Dict[str, Any]:
    """Get the platform account balance and earnings summary."""
    conn = get_db_connection()
    try:
        # Get platform balance
        row = conn.execute("SELECT balance FROM platform_account WHERE account_id = 'platform'").fetchone()
        platform_balance = float(row['balance']) if row else 0.0
        
        # Get total ledger stats
        ledger_rows = conn.execute(
            """
            SELECT 
              SUM(billed_amount) as total_billed,
              SUM(payout_amount) as total_payout,
              SUM(COALESCE(platform_share, billed_amount - payout_amount)) as total_platform_share,
              COUNT(*) as job_count
            FROM jobs WHERE status IN ('completed', 'failed')
            """
        ).fetchone()
        
        total_billed = float(ledger_rows['total_billed'] or 0.0)
        total_payout = float(ledger_rows['total_payout'] or 0.0)
        total_platform_share = float(ledger_rows['total_platform_share'] or 0.0)
        job_count = int(ledger_rows['job_count'] or 0)
        
        return {
            "platform_balance": round(platform_balance, 6),
            "total_billed": round(total_billed, 6),
            "total_worker_payout": round(total_payout, 6),
            "total_platform_earnings": round(total_platform_share, 6),
            "job_count": job_count,
            "currency": "USD"
        }
    finally:
        conn.close()
'''

# Find the location to insert - right after the get_ledger function
if '@app.get("/health")' in content:
    insert_pos = content.find('@app.get("/health")')
    content = content[:insert_pos] + new_endpoint + '\n\n' + content[insert_pos:]
    
    scheduler_file.write_text(content)
    print('[OK] Platform balance endpoint added')
else:
    print('[WARN] Could not find health endpoint, endpoint not added')
