import time, requests
from datetime import datetime, timedelta, timezone

BASE = "https://data.melbourne.vic.gov.au"
DATASET = "on-street-parking-bay-sensors"
URL = f"{BASE}/api/explore/v2.1/catalog/datasets/{DATASET}/records"

# Start 5 minutes ago (UTC, timezone-aware)
since = (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat(timespec="seconds")

def fetch(params):
    r = requests.get(URL, params=params, timeout=30)
    if not r.ok:
        raise RuntimeError(f"{r.status_code} {r.reason}: {r.text[:400]}")
    return r.json().get("results", [])
# --- field discovery, with robust fallbacks ---
def discover_fields():
    # try a couple of times in case the API is momentarily empty
    for _ in range(3):
        try:
            sample = fetch({"limit": 1, "order_by": "lastupdated DESC"})
            break
        except Exception:
            sample = []
    keys = set(sample[0].keys()) if sample else set()
    lower_to_actual = {k.lower(): k for k in keys}

    def resolve(candidates):
        # pick first candidate that exists (case-insensitive), else return the first as a guess
        for c in candidates:
            if c.lower() in lower_to_actual:
                return lower_to_actual[c.lower()]
        return candidates[0]  # best guess

    LASTUPDATED = resolve(["lastupdated", "Lastupdated", "status_timestamp", "modified"])
    STATUS_DESC = resolve(["status_description", "status", "Status_Description"])
    KERBSIDEID  = resolve(["kerbsideid", "KerbsideID", "bay_id", "kerbside_id"])
    return LASTUPDATED, STATUS_DESC, KERBSIDEID

LASTUPDATED, STATUS_DESC, KERBSIDEID = discover_fields()
print("Using fields:", KERBSIDEID, STATUS_DESC, LASTUPDATED)

def fetch_since(since_iso):
    # Only select columns that actually exist (avoid 400s on bad names)
    select_cols = [c for c in {KERBSIDEID, STATUS_DESC, LASTUPDATED} if c]
    params = {
        "select": ",".join(select_cols) if select_cols else "*",
        "where":  f'{LASTUPDATED} > "{since_iso}"',
        "order_by": f"{LASTUPDATED} ASC",
        "limit": 100
    }
    return fetch(params)

print("Listening for new sensor updates…")
watermark = since
while True:
    try:
        rows = fetch_since(watermark)
        if rows:
            for r in rows:
                print(r.get(KERBSIDEID), r.get(STATUS_DESC), r.get(LASTUPDATED))
            watermark = rows[-1][LASTUPDATED]
    except Exception as e:
        print("Fetch error:", e)
        # quick probe to keep going
        try:
            probe = fetch({"limit": 1})
            print("Probe keys:", list(probe[0].keys()) if probe else "no rows")
        except Exception as e2:
            print("Probe failed:", e2)
    time.sleep(10)
