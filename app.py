# app.py
import os
import math
import re
from datetime import time as dtime
from typing import Optional, Tuple, Dict, Any, List

import pandas as pd
import psycopg2
from flask import Flask, request, jsonify

# =========================
# Configuration
# =========================
# Prefer env var in real deployments. Falls back to your provided URL for convenience.
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://postgres:eSyUrNgzoGjZybYhxZRwLKaSbAxkQmIQ@trolley.proxy.rlwy.net:13392/railway"
)
TZ_AWARE = False  # set True only if your DB timestamps are tz-aware and you want AU/Melbourne conversion

# =========================
# DB helpers
# =========================
def read_sql(sql: str) -> pd.DataFrame:
    with psycopg2.connect(DATABASE_URL) as conn:
        return pd.read_sql_query(sql, conn)

# =========================
# Utility / parsing
# =========================
def wilson_interval(k: int, n: int, z: float = 1.96) -> Tuple[float, float]:
    if n <= 0:
        return 0.0, 1.0
    p = k / n
    denom = 1 + (z ** 2) / n
    centre = (p + (z ** 2) / (2 * n)) / denom
    half = (z * math.sqrt((p * (1 - p) + (z ** 2) / (4 * n)) / n)) / denom
    return max(0.0, centre - half), min(1.0, centre + half)

def confidence_from_history(k: int, n: int) -> str:
    low, high = wilson_interval(k, n)
    halfwidth = (high - low) / 2
    if n >= 80 and halfwidth <= 0.10:
        return "High"
    if n >= 30 and halfwidth <= 0.20:
        return "Medium"
    return "Low"

def parse_days_to_weekday_set(day_str: str) -> Optional[set]:
    if not isinstance(day_str, str) or not day_str.strip():
        return None
    s = day_str.strip().lower()
    if "all" in s:
        return set(range(7))
    name_to_idx = {
        "mon": 0, "monday": 0,
        "tue": 1, "tues": 1, "tuesday": 1,
        "wed": 2, "wednesday": 2,
        "thu": 3, "thur": 3, "thurs": 3, "thursday": 3,
        "fri": 4, "friday": 4,
        "sat": 5, "saturday": 5,
        "sun": 6, "sunday": 6,
    }
    parts = [p.strip() for p in re.split(r"[;,]", s) if p.strip()]
    wd = set()

    def add_range(a: str, b: str):
        a_idx = name_to_idx.get(a[:3]); b_idx = name_to_idx.get(b[:3])
        if a_idx is None or b_idx is None:
            return
        if a_idx <= b_idx:
            for i in range(a_idx, b_idx + 1):
                wd.add(i)
        else:
            for i in list(range(a_idx, 7)) + list(range(0, b_idx + 1)):
                wd.add(i)

    if not parts:
        return None
    for p in parts:
        rng = re.split(r"[-–—to]+", p)
        rng = [r.strip() for r in rng if r.strip()]
        if len(rng) == 2:
            add_range(rng[0], rng[1])
        else:
            key = p.split()[0][:3]
            if key in name_to_idx:
                wd.add(name_to_idx[key])
    return wd if wd else None

def parse_time_hhmm(x: Any) -> Optional[dtime]:
    if pd.isna(x):
        return None
    if isinstance(x, dtime):
        return x
    try:
        return pd.to_datetime(str(x), format="%H:%M", errors="coerce").time()
    except Exception:
        return None

def time_in_window(t: dtime, start: dtime, finish: dtime) -> bool:
    if start is None or finish is None or t is None:
        return False
    if start <= finish:
        return start <= t <= finish
    return t >= start or t <= finish  # overnight window

def normalize_street(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip().lower()) if isinstance(s, str) else ""

# =========================
# Load data from Postgres
# =========================
# 1) Sensors (core time series)
df_s = read_sql("SELECT * FROM on_street_parking_bay_sensors")
df_s.columns = df_s.columns.str.strip()
# expected columns: lastupdated, status_timestamp, zone_number, kerbsideid, location
df_s["status_timestamp"] = pd.to_datetime(df_s["status_timestamp"], errors="coerce")
if TZ_AWARE:
    try:
        df_s["status_timestamp"] = df_s["status_timestamp"].dt.tz_convert("Australia/Melbourne")
    except Exception:
        pass
df_s["zone_number"] = pd.to_numeric(df_s["zone_number"], errors="coerce")

# Try to find an occupancy/status column (optional)
occ_cols = [c for c in df_s.columns if c.lower() in
            {"status", "status_description", "occupancy", "bay_status", "space_status"}]

# 2) Bays (for capacity)
df_bays = read_sql("SELECT * FROM on_street_parking_bays")
df_bays.columns = df_bays.columns.str.strip()
df_bays["roadsegmentid"] = pd.to_numeric(df_bays["roadsegmentid"], errors="coerce")
df_bays["kerbsideid"]    = pd.to_numeric(df_bays["kerbsideid"], errors="coerce")

# 3) Zone ↔ Street segments (mapping)
df_link = read_sql("SELECT * FROM parking_zones_linked_to_street_segments")
df_link.columns = df_link.columns.str.strip()
df_link["segment_id"] = pd.to_numeric(df_link["segment_id"], errors="coerce")
df_link["__street_norm__"] = df_link["onstreet"].map(normalize_street)

# 4) Sign plates (time restrictions)
df_sign = read_sql("SELECT * FROM sign_plates_located_in_each_parking_zone")
df_sign.columns = df_sign.columns.str.strip()
df_sign["__wdays__"]  = df_sign["restriction_days"].map(parse_days_to_weekday_set)
df_sign["__tstart__"] = df_sign["time_restrictions_start"].map(parse_time_hhmm)
df_sign["__tfinish__"] = df_sign["time_restrictions_finish"].map(parse_time_hhmm)

# Zone capacity via bays -> link
capacity_by_zone: Dict[str, int] = {}
try:
    bays_link = df_bays.merge(
        df_link[["segment_id", "parkingzone"]],
        left_on="roadsegmentid", right_on="segment_id", how="left"
    )
    cap = bays_link.groupby("parkingzone", dropna=True)["kerbsideid"].nunique().rename("bay_count")
    capacity_by_zone = cap.to_dict()
except Exception:
    capacity_by_zone = {}

# Street -> zones mapping
street_to_zones: Dict[str, List[str]] = (
    df_link.dropna(subset=["__street_norm__", "parkingzone"])
    .groupby("__street_norm__")["parkingzone"].apply(lambda s: sorted(set(s))).to_dict()
)

# =========================
# Historical availability (only if occupancy exists)
# =========================
def derive_is_free_column(df: pd.DataFrame, occ_candidates: List[str]) -> Optional[pd.Series]:
    if not occ_candidates:
        return None
    col = occ_candidates[0]
    s = df[col].astype(str).str.strip().str.lower()

    free_tokens = {"unoccupied", "free", "vacant", "available", "clear"}
    occ_tokens  = {"occupied", "present", "busy", "unavailable"}

    # direct text match
    if s.isin(free_tokens | occ_tokens).any():
        return s.isin(free_tokens)
    # 0/1 encoding
    if s.str.fullmatch(r"[01]").all():
        return s.astype(int).map(lambda x: x == 0)
    # substring heuristic
    if s.str.contains("unoccupied|available|vacant", regex=True).any() or s.str.contains("occupied|present", regex=True).any():
        return s.str.contains("unoccupied|available|vacant", regex=True)

    return None

has_hist = False
hist_df = None

df_s = df_s.dropna(subset=["status_timestamp", "zone_number"])
df_s["hour"] = df_s["status_timestamp"].dt.hour
df_s["dow"]  = df_s["status_timestamp"].dt.dayofweek  # Mon=0

is_free_series = derive_is_free_column(df_s, occ_cols)
if is_free_series is not None:
    df_s["is_free"] = is_free_series
    agg = (
        df_s.groupby(["zone_number", "dow", "hour"])
        .agg(total=("is_free", "size"), free=("is_free", "sum"))
        .reset_index()
    )
    agg["availability"] = agg["free"] / agg["total"]
    hist_df = agg
    has_hist = True

# =========================
# Restriction logic
# =========================
def is_restricted(zone: str, dt: pd.Timestamp) -> bool:
    if zone is None or not isinstance(zone, str):
        return False
    sub = df_sign[df_sign["parkingzone"].astype(str) == str(zone)]
    if sub.empty:
        return False
    wd = int(dt.dayofweek)
    t_local = dtime(dt.hour, dt.minute)
    for _, r in sub.iterrows():
        days = r["__wdays__"]; tstart = r["__tstart__"]; tfinish = r["__tfinish__"]
        if days is None or tstart is None or tfinish is None:
            continue
        if wd in days and time_in_window(t_local, tstart, tfinish):
            return True
    return False

# =========================
# Zone/street resolution
# =========================
def zones_for_street(street_name: str) -> List[str]:
    key = normalize_street(street_name)
    return street_to_zones.get(key, [])

def best_zone_for_street(street_name: str) -> Optional[str]:
    zlist = zones_for_street(street_name)
    if not zlist:
        return None
    zlist_sorted = sorted(zlist, key=lambda z: capacity_by_zone.get(z, 0), reverse=True)
    return zlist_sorted[0]

# =========================
# Prediction
# =========================
def predict_for_zone(zone: str, dt: pd.Timestamp) -> Dict[str, Any]:
    # 1) Hard restriction overrides
    if is_restricted(zone, dt):
        return {
            "availability": 0.0,
            "confidence": "High",
            "model": "rules-only",
            "reason": "Restricted by sign plate at this time."
        }

    # 2) Historical (if available)
    if has_hist:
        dow = int(dt.dayofweek); hr = int(dt.hour)
        cnd = (hist_df["zone_number"].astype(str) == str(zone)) & (hist_df["dow"] == dow) & (hist_df["hour"] == hr)
        sub = hist_df[cnd]
        if sub.empty:
            cnd2 = (hist_df["zone_number"].astype(str) == str(zone)) & (hist_df["hour"] == hr)
            sub = hist_df[cnd2]
        if sub.empty:
            cnd3 = (hist_df["zone_number"].astype(str) == str(zone))
            sub = hist_df[cnd3]
        if not sub.empty:
            sub = sub.sort_values("total", ascending=False).iloc[0]
            k = int(sub["free"]); n = int(sub["total"])
            avail = float(sub["availability"])
            conf = confidence_from_history(k, n)
            return {
                "availability": avail,
                "confidence": conf,
                "model": "historical",
                "reason": f"Based on {n} historical samples in this bucket."
            }

    # 3) Fallback (no occupancy column found)
    cap = capacity_by_zone.get(zone, None)
    base_msg = "No occupancy column detected; returning rule-based fallback."
    if cap is None:
        return {"availability": None, "confidence": "Low", "model": "rules-only",
                "reason": base_msg + " Zone capacity unknown."}
    return {"availability": None, "confidence": "Low", "model": "rules-only",
            "reason": base_msg + f" Zone has ~{cap} bays; availability not estimated."}

# =========================
# Flask app + routes (API + Demo page)
# =========================
app = Flask(__name__)

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"ok": True, "has_hist": has_hist})

@app.route("/predict_parking", methods=["GET"])
def predict_parking():
    """
    Query params:
      - time: "YYYY-MM-DD HH:MM" (required)
      - zone: string (optional) — matches `parkingzone` or `zone_number` values
      - street: string (optional) — if zone omitted, resolve street -> best zone
    """
    time_str = request.args.get("time")
    zone = request.args.get("zone")
    street = request.args.get("street")

    if not time_str:
        return jsonify({"error": "Missing 'time' (YYYY-MM-DD HH:MM)."}), 400
    try:
        dt = pd.to_datetime(time_str)
        if TZ_AWARE:
            dt = dt.tz_convert("Australia/Melbourne")
    except Exception:
        return jsonify({"error": "Invalid 'time' format. Use 'YYYY-MM-DD HH:MM'."}), 400

    resolved_zone = zone
    notes = None
    if not resolved_zone and street:
        resolved_zone = best_zone_for_street(street)
        if not resolved_zone:
            return jsonify({"error": f"No zone mapping found for street '{street}'."}), 404
        notes = f"Resolved street '{street}' to zone '{resolved_zone}'."

    if not resolved_zone:
        return jsonify({"error": "Provide either 'zone' or 'street'."}), 400

    res = predict_for_zone(str(resolved_zone), dt)

    if res["availability"] is None:
        avail_msg = "Unknown"
    else:
        avail_msg = f"{round(res['availability'] * 100, 1)}%"

    human = f"{res['confidence']} confidence — availability: {avail_msg} at {dt.strftime('%H:00')}"
    if notes:
        human = notes + " " + human

    return jsonify({
        "zone": str(resolved_zone),
        "time": dt.strftime("%Y-%m-%d %H:%M"),
        "availability": res["availability"],
        "confidence": res["confidence"],
        "model": res["model"],
        "reason": res["reason"],
        "message": human
    })

@app.route("/", methods=["GET"])
def demo_page():
    return """
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Parking Availability Demo</title>
  <style>
    body { font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial; max-width: 760px; margin: 40px auto; }
    label { display:block; margin: 12px 0 6px; }
    input, button { padding: 8px; font-size: 14px; }
    .row { display:flex; gap:12px; align-items:center; flex-wrap: wrap; }
    .hint { color:#666; font-size: 13px; }
    #result { margin-top:20px; padding:12px; border:1px solid #eee; border-radius:8px; background:#fafafa; }
  </style>
</head>
<body>
  <h2>Predict Parking Availability</h2>
  <div>
    <label>Time (local):</label>
    <input id="time" type="datetime-local" />
    <div class="hint">Example: 2025-08-08 10:00</div>

    <div class="row">
      <div>
        <label>Zone (optional):</label>
        <input id="zone" type="text" placeholder="e.g., 7539" />
      </div>
      <div>
        <label>Street (optional):</label>
        <input id="street" type="text" placeholder="e.g., Swanston Street" />
      </div>
    </div>

    <button id="go">Predict</button>
    <div id="result"></div>
  </div>

  <script>
    async function predict() {
      const t = document.getElementById('time').value; // "YYYY-MM-DDTHH:MM"
      const zone = document.getElementById('zone').value.trim();
      const street = document.getElementById('street').value.trim();
      const result = document.getElementById('result');
      result.textContent = 'Loading...';

      if (!t) {
        result.textContent = 'Please select a time.';
        return;
      }
      const timeParam = encodeURIComponent(t.replace('T',' '));

      let url = `/predict_parking?time=${timeParam}`;
      if (zone) url += `&zone=${encodeURIComponent(zone)}`;
      else if (street) url += `&street=${encodeURIComponent(street)}`;
      else {
        result.textContent = 'Provide either Zone or Street.';
        return;
      }

      try {
        const resp = await fetch(url);
        const data = await resp.json();
        if (!resp.ok) {
          result.textContent = data.error || 'Error';
          return;
        }
        const pct = (data.availability == null) ? 'Unknown' : (data.availability * 100).toFixed(1) + '%';
        result.innerHTML = `
          <b>${data.message}</b><br/>
          <div class="hint">
            Zone: ${data.zone} | Model: ${data.model} | Reason: ${data.reason}
          </div>`;
      } catch (e) {
        result.textContent = 'Network error: ' + e.message;
      }
    }
    document.getElementById('go').addEventListener('click', predict);
  </script>
</body>
</html>
"""

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=True)
