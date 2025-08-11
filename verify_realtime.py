import time, requests
from datetime import datetime, timedelta, timezone

BASE = "https://data.melbourne.vic.gov.au"
DATASET = "on-street-parking-bay-sensors"
URL = f"{BASE}/api/explore/v2.1/catalog/datasets/{DATASET}/records"

def fetch(params):
    r = requests.get(URL, params=params, timeout=30)
    r.raise_for_status()
    return r.json().get("results", [])

# discover exact field names (keys differ by case sometimes)
sample = fetch({"limit": 1})
keys = set(sample[0].keys()) if sample else set()
def pick(*candidates):
    for c in candidates:
        if c in keys: return c
    # fallbacks if discovery returned no rows:
    return candidates[0]

LASTUPDATED = pick("lastupdated", "Lastupdated")
STATUS_DESC = pick("status_description", "Status_Description")
KERBSIDEID  = pick("kerbsideid", "KerbsideID")

def max_lastupdated():
    # Try order_by desc + limit 1 (simplest + reliable)
    rows = fetch({"select": LASTUPDATED, "order_by": f"{LASTUPDATED} DESC", "limit": 1})
    if not rows: return None
    ts = rows[0][LASTUPDATED]
    # make it timezone-aware
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))

# 1) Liveness: how recent is the latest row?
now = datetime.now(timezone.utc)
latest = max_lastupdated()
print("Latest lastupdated:", latest)
if latest is None:
    print("No rows returned; cannot verify yet.")
else:
    lag = now - latest
    print("Lag vs now:", lag)
    if lag <= timedelta(hours=1):
        print("✅ Liveness OK (recent update within 1 hour).")
    else:
        print("⚠️ Liveness weak (latest is older than 1 hour).")

# 2) Freshness: does lastupdated advance?
print("\nWatching for movement (3 checks, 60s apart)…")
checks = []
for i in range(3):
    ts = max_lastupdated()
    print(f"Check {i+1}: {ts}")
    checks.append(ts)
    if i < 2:
        time.sleep(60)

if all(checks) and checks[-1] and checks[0]:
    if checks[-1] > checks[0]:
        print("✅ Freshness OK: lastupdated increased while watching.")
    else:
        print("⚠️ Freshness not observed in this window (try a longer watch interval).")
