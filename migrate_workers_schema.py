import sqlite3
from pathlib import Path

DB = Path('tron_master.db')
if not DB.exists():
    print('No DB found at tron_master.db; skipping migration')
    raise SystemExit(0)

conn = sqlite3.connect(DB)
cur = conn.cursor()
cur.execute("PRAGMA table_info(workers)")
cols = [r[1] for r in cur.fetchall()]
print('Existing worker columns:', cols)
added = False
if 'gpu_name' not in cols:
    cur.execute("ALTER TABLE workers ADD COLUMN gpu_name TEXT")
    print('Added gpu_name')
    added = True
if 'vram_gb' not in cols:
    cur.execute("ALTER TABLE workers ADD COLUMN vram_gb REAL")
    print('Added vram_gb')
    added = True
if 'cuda_cores' not in cols:
    cur.execute("ALTER TABLE workers ADD COLUMN cuda_cores INTEGER")
    print('Added cuda_cores')
    added = True
if 'network_bandwidth_gbps' not in cols:
    cur.execute("ALTER TABLE workers ADD COLUMN network_bandwidth_gbps REAL")
    print('Added network_bandwidth_gbps')
    added = True

conn.commit()
conn.close()
if not added:
    print('No changes needed')
else:
    print('Migration complete')
