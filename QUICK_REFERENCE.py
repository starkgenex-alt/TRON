#!/usr/bin/env python3
"""
TRON Quick Reference — Copy/paste commands for common tasks
"""

import os
import sys

TASKS = {
    "1. Start Server": {
        "Description": "Launch master node on http://0.0.0.0:9000",
        "Command": 'cd "c:\\Users\\HP\\Documents\\TRON" && python queue_server.py',
        "Windows": True,
        "Linux": True,
        "Mac": True
    },
    
    "2. View Dashboard": {
        "Description": "Open Streamlit UI for monitoring (http://localhost:8501)",
        "Command": 'streamlit run "c:\\Users\\HP\\Documents\\TRON\\dashboard\\app.py"',
        "Windows": True,
        "Linux": False,
        "Mac": False
    },
    
    "3. Register Worker": {
        "Description": "Connect a worker node to the master server",
        "Command": '$env:TRON_MASTER_URL="http://127.0.0.1:9000"; cd "c:\\Users\\HP\\Documents\\TRON" && python install_tron.py',
        "Windows": True,
        "Linux": False,
        "Mac": False
    },
    
    "4. Run E2E Test": {
        "Description": "Full pipeline test: register → submit → complete → bill",
        "Command": 'cd "c:\\Users\\HP\\Documents\\TRON" && python e2e_test.py',
        "Windows": True,
        "Linux": True,
        "Mac": True
    },
    
    "5. Check Health": {
        "Description": "Verify server is responding on all endpoints",
        "Command": 'curl http://127.0.0.1:9000/workers && echo "" && curl http://127.0.0.1:9000/platform/balance && echo ""',
        "Windows": True,
        "Linux": True,
        "Mac": True
    },
    
    "6. View Platform Balance": {
        "Description": "Check total earnings, payouts, and completed jobs",
        "Command": 'curl http://127.0.0.1:9000/platform/balance | python -m json.tool',
        "Windows": True,
        "Linux": True,
        "Mac": True
    },
    
    "7. Get Launch Context": {
        "Description": "Fetch installer command and layer status",
        "Command": 'curl http://127.0.0.1:9000/api/v1/launch/context | python -m json.tool',
        "Windows": True,
        "Linux": True,
        "Mac": True
    },
    
    "8. Create Test Customer": {
        "Description": "Generate API key for job submission",
        "Command": 'curl -X POST http://127.0.0.1:9000/admin/customer/create -H "Content-Type: application/json" -d \'{"name": "Test", "email": "test@tron.local", "company": "TRON"}\' | python -m json.tool',
        "Windows": True,
        "Linux": True,
        "Mac": True
    },
    
    "9. Submit Job (Manual)": {
        "Description": 'Submit job with API key (replace tron_YOURKEY)',
        "Command": 'curl -X POST http://127.0.0.1:9000/api/v1/submit -H "Content-Type: application/json" -H "X-API-Key: tron_YOURKEY" -d \'{"prompt": "test", "task_type": "compute", "gpu": false, "priority": 1, "memory_gb": 1}\' | python -m json.tool',
        "Windows": True,
        "Linux": True,
        "Mac": True
    },
    
    "10. Activate Python Env": {
        "Description": "Activate virtual environment before any Python work",
        "Command": '"c:\\Users\\HP\\Documents\\TRON\\.venv\\Scripts\\Activate.ps1"',
        "Windows": True,
        "Linux": False,
        "Mac": False
    },
    
    "11. Run Tests": {
        "Description": "Run unit tests (pytest coverage)",
        "Command": 'cd "c:\\Users\\HP\\Documents\\TRON" && python -m pytest tests/test_*.py -v',
        "Windows": True,
        "Linux": True,
        "Mac": True
    },
    
    "12. Check Syntax": {
        "Description": "Validate Python files for errors",
        "Command": 'cd "c:\\Users\\HP\\Documents\\TRON" && python -m py_compile queue_server.py tron_billing.py payment_providers.py dashboard/app.py',
        "Windows": True,
        "Linux": True,
        "Mac": True
    }
}

def show_menu():
    print("\n" + "="*70)
    print("TRON PLATFORM — QUICK REFERENCE")
    print("="*70 + "\n")
    
    for idx, (title, details) in enumerate(TASKS.items(), 1):
        print(f"{title}")
        print(f"  📝 {details['Description']}")
        print(f"  💻 {details['Command']}\n")
    
    print("="*70)
    print("\n💡 TIPS:")
    print("  • Always start the server FIRST before running other commands")
    print("  • Dashboard runs on http://localhost:8501 (requires server running)")
    print("  • E2E test validates: register → submit → execute → bill → payout")
    print("  • API key needed for job submission (get from /admin/customer/create)")
    print("  • Platform takes 15%, worker gets 85% of job cost")
    print("  • Default job cost: $0.10 (for testing)")
    print("\n📊 KEY METRICS:")
    print("  • Platform Balance: GET /platform/balance")
    print("  • Active Workers: GET /workers")
    print("  • Job Status: GET /status/{job_id}")
    print("  • Launch Context: GET /api/v1/launch/context")
    print("\n" + "="*70)

if __name__ == "__main__":
    show_menu()
    
    print("\n📋 NEXT STEPS:")
    print("  1. Start server:  python queue_server.py")
    print("  2. Run E2E test:  python e2e_test.py")
    print("  3. Open dashboard:  streamlit run dashboard/app.py")
    print("  4. Deploy to cloud when ready")
    print("\n🚀 PLATFORM IS PRODUCTION READY\n")
