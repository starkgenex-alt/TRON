import requests

API = "http://127.0.0.1:9000"
for path in ["/health", "/platform/balance", "/ledger"]:
    try:
        r = requests.get(API + path, timeout=5)
        print(path, r.status_code, r.text)
    except Exception as exc:
        print(path, "ERROR", exc)
