"""
TRON Billing Engine - Customer management, pricing, invoicing
Handles API keys, rate calculation, billing ledger, and invoice generation
"""

import sqlite3
import uuid
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, List, Tuple

from payment_providers import router as payment_router

# =========================
# DATABASE
# =========================

DB_PATH = "tron_billing.db"

def init_billing_db():
    """Initialize billing database schema."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Customers table
    c.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            customer_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            company TEXT,
            api_key TEXT UNIQUE NOT NULL,
            api_key_created_at REAL,
            created_at REAL,
            status TEXT DEFAULT 'active',
            stripe_connect_account_id TEXT
        )
    """)
    
    # Billing ledger - tracks all job charges
    c.execute("""
        CREATE TABLE IF NOT EXISTS billing_ledger (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id TEXT NOT NULL,
            customer_id TEXT NOT NULL,
            job_type TEXT,
            is_gpu BOOLEAN,
            priority INTEGER,
            base_rate REAL,
            gpu_multiplier REAL,
            priority_multiplier REAL,
            total_charge REAL,
            platform_share REAL,
            worker_share REAL,
            charged_at REAL,
            invoice_id TEXT,
            stripe_transfer_id TEXT,
            stripe_transfer_status TEXT,
            FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
        )
    """)
    
    # Invoices table
    c.execute("""
        CREATE TABLE IF NOT EXISTS invoices (
            invoice_id TEXT PRIMARY KEY,
            customer_id TEXT NOT NULL,
            invoice_number TEXT UNIQUE NOT NULL,
            month TEXT,
            total_charged REAL,
            platform_share REAL,
            status TEXT DEFAULT 'draft',
            connected_account_id TEXT,
            created_at REAL,
            due_date REAL,
            paid_at REAL,
            FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
        )
    """)

    # Add missing columns for backwards compatibility
    customer_columns = [row[1] for row in c.execute("PRAGMA table_info(customers)")]
    if "stripe_connect_account_id" not in customer_columns:
        c.execute("ALTER TABLE customers ADD COLUMN stripe_connect_account_id TEXT")

    ledger_columns = [row[1] for row in c.execute("PRAGMA table_info(billing_ledger)")]
    if "stripe_transfer_id" not in ledger_columns:
        c.execute("ALTER TABLE billing_ledger ADD COLUMN stripe_transfer_id TEXT")
    if "stripe_transfer_status" not in ledger_columns:
        c.execute("ALTER TABLE billing_ledger ADD COLUMN stripe_transfer_status TEXT")
    
    # API rate limits
    c.execute("""
        CREATE TABLE IF NOT EXISTS api_usage (
            customer_id TEXT NOT NULL,
            hour TEXT,
            request_count INTEGER DEFAULT 0,
            PRIMARY KEY (customer_id, hour),
            FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
        )
    """)
    
    conn.commit()
    conn.close()

# =========================
# PRICING ENGINE
# =========================

class PricingEngine:
    """Dynamic pricing based on GPU, priority, and demand."""
    
    # Base rates (USD per job)
    BASE_RATE_CPU = 0.10
    BASE_RATE_GPU = 1.00
    
    # Multipliers
    GPU_MULTIPLIER = {
        False: 1.0,      # CPU jobs
        True: 10.0       # GPU jobs
    }
    
    PRIORITY_MULTIPLIER = {
        1: 1.0,          # Low priority
        2: 1.2,          # Medium priority
        3: 1.5           # High priority
    }
    
    # Time-based surge pricing
    PEAK_HOURS = set(range(9, 17))  # 9am-5pm weekdays
    PEAK_MULTIPLIER = 1.1
    
    @staticmethod
    def calculate_job_cost(
        gpu_required: bool,
        priority: int = 1,
        surge_active: bool = False
    ) -> Tuple[float, Dict]:
        """Calculate total job cost and breakdown."""
        
        base_rate = PricingEngine.BASE_RATE_GPU if gpu_required else PricingEngine.BASE_RATE_CPU
        gpu_mult = PricingEngine.GPU_MULTIPLIER.get(gpu_required, 1.0)
        priority_mult = PricingEngine.PRIORITY_MULTIPLIER.get(priority, 1.0)
        surge_mult = PricingEngine.PEAK_MULTIPLIER if surge_active else 1.0
        
        total_cost = base_rate * gpu_mult * priority_mult * surge_mult
        
        breakdown = {
            "base_rate": base_rate,
            "gpu_multiplier": gpu_mult,
            "priority_multiplier": priority_mult,
            "surge_multiplier": surge_mult,
            "total_charge": round(total_cost, 6),
            "platform_share": round(total_cost * 0.15, 6),  # 15% to platform
            "worker_share": round(total_cost * 0.85, 6)     # 85% to worker
        }
        
        return total_cost, breakdown

    @staticmethod
    def is_surge_pricing_active() -> bool:
        """Check if surge pricing applies (peak hours)."""
        now = datetime.now()
        return now.weekday() < 5 and now.hour in PricingEngine.PEAK_HOURS


# =========================
# API KEY MANAGEMENT
# =========================

class APIKeyManager:
    """Manage customer API keys."""
    
    @staticmethod
    def generate_api_key() -> str:
        """Generate unique API key."""
        return f"tron_{uuid.uuid4().hex}"
    
    @staticmethod
    def create_customer(
        name: str,
        email: str,
        company: Optional[str] = None,
        stripe_connect_account_id: Optional[str] = None
    ) -> Tuple[str, str]:
        """Create new customer and API key."""
        init_billing_db()
        
        customer_id = f"cust_{uuid.uuid4().hex[:12]}"
        api_key = APIKeyManager.generate_api_key()
        now = time.time()
        
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        c.execute("""
            INSERT INTO customers 
            (customer_id, name, email, company, api_key, api_key_created_at, created_at, stripe_connect_account_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (customer_id, name, email, company, api_key, now, now, stripe_connect_account_id))
        
        conn.commit()
        conn.close()
        
        return customer_id, api_key
    
    @staticmethod
    def verify_api_key(api_key: str) -> Optional[str]:
        """Verify API key and return customer_id."""
        init_billing_db()
        
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        c.execute("""
            SELECT customer_id, status FROM customers WHERE api_key = ?
        """, (api_key,))
        
        result = c.fetchone()
        conn.close()
        
        if result and result[1] == "active":
            return result[0]
        
        return None
    
    @staticmethod
    def list_customers() -> List[Dict]:
        """List all customers."""
        init_billing_db()
        
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        c.execute("""
            SELECT customer_id, name, email, company, created_at, status, stripe_connect_account_id
            FROM customers
            ORDER BY created_at DESC
        """)
        
        customers = []
        for row in c.fetchall():
            customers.append({
                "customer_id": row[0],
                "name": row[1],
                "email": row[2],
                "company": row[3],
                "created_at": row[4],
                "status": row[5],
                "stripe_connect_account_id": row[6]
            })
        
        conn.close()
        return customers

    @staticmethod
    def update_stripe_account(customer_id: str, stripe_connect_account_id: str) -> None:
        """Associate a Stripe connected account with a customer."""
        init_billing_db()
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute(
            "UPDATE customers SET stripe_connect_account_id = ? WHERE customer_id = ?",
            (stripe_connect_account_id, customer_id)
        )
        conn.commit()
        conn.close()


# =========================
# BILLING LEDGER
# =========================

class BillingLedger:
    """Track customer charges."""
    
    @staticmethod
    def record_charge(
        job_id: str,
        customer_id: str,
        job_type: str,
        is_gpu: bool,
        priority: int = 1,
        worker_stripe_account_id: Optional[str] = None
    ) -> Dict:
        """Record job completion charge and optionally send worker payout."""
        init_billing_db()
        
        # Calculate cost
        total_charge, breakdown = PricingEngine.calculate_job_cost(is_gpu, priority)
        payout_reference = None
        payout_status = None
        
        if worker_stripe_account_id:
            try:
                transfer_result = payment_router.payout_worker(
                    breakdown["worker_share"],
                    worker_stripe_account_id,
                    metadata={"job_id": job_id, "customer_id": customer_id}
                )
                payout_reference = transfer_result.get("reference") or transfer_result.get("transfer_id")
                payout_status = transfer_result.get("status")
            except Exception as e:
                print(f"[TRON] Payout failed for job {job_id}: {e}")
                payout_reference = None
                payout_status = "failed"
        
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        c.execute("""
            INSERT INTO billing_ledger
            (job_id, customer_id, job_type, is_gpu, priority, 
             base_rate, gpu_multiplier, priority_multiplier, 
             total_charge, platform_share, worker_share, charged_at, stripe_transfer_id, stripe_transfer_status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            job_id, customer_id, job_type, is_gpu, priority,
            breakdown["base_rate"],
            breakdown["gpu_multiplier"],
            breakdown["priority_multiplier"],
            breakdown["total_charge"],
            breakdown["platform_share"],
            breakdown["worker_share"],
            time.time(),
            payout_reference,
            payout_status
        ))
        
        conn.commit()
        conn.close()
        
        return {
            "job_id": job_id,
            "customer_id": customer_id,
            "charge": breakdown["total_charge"],
            "platform_share": breakdown["platform_share"],
            "worker_share": breakdown["worker_share"],
            "stripe_transfer_id": payout_reference,
            "stripe_transfer_status": payout_status
        }

    @staticmethod
    def create_stripe_transfer(
        destination_account_id: str,
        amount_usd: float,
        description: str
    ) -> Dict[str, str]:
        """Backward-compatible wrapper for payout routing."""
        return payment_router.payout_worker(
            amount_usd,
            destination_account_id,
            metadata={"description": description}
        )
    
    @staticmethod
    def get_customer_charges(
        customer_id: str,
        days: int = 30
    ) -> List[Dict]:
        """Get recent charges for customer."""
        init_billing_db()
        
        cutoff_time = time.time() - (days * 86400)
        
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        c.execute("""
            SELECT job_id, job_type, is_gpu, priority, total_charge, 
                   platform_share, worker_share, charged_at, stripe_transfer_id, stripe_transfer_status
            FROM billing_ledger
            WHERE customer_id = ? AND charged_at > ?
            ORDER BY charged_at DESC
        """, (customer_id, cutoff_time))
        
        charges = []
        for row in c.fetchall():
            charges.append({
                "job_id": row[0],
                "job_type": row[1],
                "is_gpu": bool(row[2]),
                "priority": row[3],
                "charge": row[4],
                "platform_share": row[5],
                "worker_share": row[6],
                "timestamp": row[7],
                "stripe_transfer_id": row[8],
                "stripe_transfer_status": row[9]
            })
        
        conn.close()
        return charges
    
    @staticmethod
    def get_customer_summary(customer_id: str) -> Dict:
        """Get billing summary for customer."""
        init_billing_db()
        
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        c.execute("""
            SELECT COUNT(*), SUM(total_charge), SUM(platform_share), SUM(worker_share)
            FROM billing_ledger
            WHERE customer_id = ?
        """, (customer_id,))
        
        result = c.fetchone()
        
        # Get customer info
        c.execute("""
            SELECT name, email, company, created_at FROM customers WHERE customer_id = ?
        """, (customer_id,))
        
        cust_info = c.fetchone()
        conn.close()
        
        return {
            "customer_id": customer_id,
            "name": cust_info[0] if cust_info else None,
            "email": cust_info[1] if cust_info else None,
            "company": cust_info[2] if cust_info else None,
            "total_jobs": result[0] or 0,
            "total_charged": round(result[1] or 0.0, 6),
            "total_platform_earnings": round(result[2] or 0.0, 6),
            "total_worker_earnings": round(result[3] or 0.0, 6)
        }


# =========================
# INVOICE GENERATION
# =========================

class InvoiceGenerator:
    """Generate monthly invoices."""
    
    @staticmethod
    def generate_monthly_invoice(customer_id: str, month: str) -> str:
        """
        Generate invoice for customer for given month (YYYY-MM).
        Returns invoice_id.
        """
        init_billing_db()
        
        # Parse month
        month_obj = datetime.strptime(month, "%Y-%m")
        month_start = month_obj.timestamp()
        month_end = (month_obj + timedelta(days=32)).replace(day=1).timestamp()
        
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Get charges for this month
        c.execute("""
            SELECT SUM(total_charge), SUM(platform_share), COUNT(*)
            FROM billing_ledger
            WHERE customer_id = ? AND charged_at >= ? AND charged_at < ?
        """, (customer_id, month_start, month_end))
        
        result = c.fetchone()
        total_charged = result[0] or 0.0
        platform_share = result[1] or 0.0
        job_count = result[2] or 0
        
        if job_count == 0:
            conn.close()
            return None  # No charges this month
        
        invoice_id = f"inv_{uuid.uuid4().hex[:12]}"
        invoice_number = f"INV-{month.replace('-', '')}-{invoice_id[-6:]}"
        now = time.time()
        due_date = now + (30 * 86400)  # 30 days net
        
        # Create invoice
        c.execute("""
            INSERT INTO invoices
            (invoice_id, customer_id, invoice_number, month, 
             total_charged, platform_share, created_at, due_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            invoice_id, customer_id, invoice_number, month,
            round(total_charged, 6), round(platform_share, 6),
            now, due_date
        ))
        
        # Mark ledger entries with invoice
        c.execute("""
            UPDATE billing_ledger
            SET invoice_id = ?
            WHERE customer_id = ? AND charged_at >= ? AND charged_at < ?
        """, (invoice_id, customer_id, month_start, month_end))
        
        conn.commit()
        conn.close()
        
        return invoice_id
    
    @staticmethod
    def get_invoice(invoice_id: str) -> Dict:
        """Retrieve invoice details."""
        init_billing_db()
        
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        c.execute("""
            SELECT invoice_id, customer_id, invoice_number, month,
                   total_charged, platform_share, status, created_at, due_date
            FROM invoices
            WHERE invoice_id = ?
        """, (invoice_id,))
        
        result = c.fetchone()
        
        if not result:
            conn.close()
            return None
        
        # Get line items
        c.execute("""
            SELECT job_id, job_type, is_gpu, priority, total_charge, charged_at
            FROM billing_ledger
            WHERE invoice_id = ?
            ORDER BY charged_at DESC
        """, (invoice_id,))
        
        line_items = []
        for row in c.fetchall():
            line_items.append({
                "job_id": row[0],
                "job_type": row[1],
                "is_gpu": bool(row[2]),
                "priority": row[3],
                "charge": row[4],
                "timestamp": row[5]
            })
        
        conn.close()
        
        return {
            "invoice_id": result[0],
            "customer_id": result[1],
            "invoice_number": result[2],
            "month": result[3],
            "total_charged": result[4],
            "platform_share": result[5],
            "status": result[6],
            "created_at": result[7],
            "due_date": result[8],
            "line_items": line_items,
            "item_count": len(line_items)
        }
    
    @staticmethod
    def list_invoices(customer_id: Optional[str] = None) -> List[Dict]:
        """List invoices."""
        init_billing_db()
        
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        if customer_id:
            c.execute("""
                SELECT invoice_id, invoice_number, month, total_charged,
                       platform_share, status, created_at
                FROM invoices
                WHERE customer_id = ?
                ORDER BY created_at DESC
            """, (customer_id,))
        else:
            c.execute("""
                SELECT invoice_id, invoice_number, month, total_charged,
                       platform_share, status, created_at
                FROM invoices
                ORDER BY created_at DESC
            """)
        
        invoices = []
        for row in c.fetchall():
            invoices.append({
                "invoice_id": row[0],
                "invoice_number": row[1],
                "month": row[2],
                "total_charged": row[3],
                "platform_share": row[4],
                "status": row[5],
                "created_at": row[6]
            })
        
        conn.close()
        return invoices


# =========================
# USAGE TRACKING
# =========================

class UsageTracker:
    """Track API usage per customer."""
    
    @staticmethod
    def record_request(customer_id: str, endpoint: str = "submit"):
        """Record API request."""
        init_billing_db()
        
        now = datetime.now()
        hour_key = now.strftime("%Y-%m-%d %H:00:00")
        
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        c.execute("""
            INSERT OR IGNORE INTO api_usage (customer_id, hour, request_count)
            VALUES (?, ?, 0)
        """, (customer_id, hour_key))
        
        c.execute("""
            UPDATE api_usage
            SET request_count = request_count + 1
            WHERE customer_id = ? AND hour = ?
        """, (customer_id, hour_key))
        
        conn.commit()
        conn.close()
    
    @staticmethod
    def get_usage(customer_id: str, hours: int = 24) -> Dict:
        """Get customer API usage."""
        init_billing_db()
        
        cutoff = datetime.now() - timedelta(hours=hours)
        cutoff_str = cutoff.strftime("%Y-%m-%d %H:00:00")
        
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        c.execute("""
            SELECT SUM(request_count) FROM api_usage
            WHERE customer_id = ? AND hour >= ?
        """, (customer_id, cutoff_str))
        
        result = c.fetchone()
        conn.close()
        
        return {
            "customer_id": customer_id,
            "period_hours": hours,
            "total_requests": result[0] or 0
        }


if __name__ == "__main__":
    init_billing_db()
    print("✓ Billing database initialized")
