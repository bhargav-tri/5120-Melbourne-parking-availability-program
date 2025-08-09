# app_trends.py
import os
import re
import math
from datetime import time as dtime
from typing import Optional, Tuple, Dict, Any, List

import pandas as pd
from flask import Flask, request, jsonify
from sqlalchemy import create_engine

# =========================
# Config
# =========================
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://postgres:eSyUrNgzoGjZybYhxZRwLKaSbAxkQmIQ@trolley.proxy.rlwy.net:13392/railway"
)
engine = create_engine(DATABASE_URL)
TZ_AWARE = False  # set True only if your DB timestamps are tz-aware and you want AU/Melbourne conversion

# =========================
# Utils
# =========================
def read_sql(sql: str) -> pd.DataFrame:
    return pd.read_sql_query(sql, engine)

def normalize_street(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip().lower()) if isinstance(s, str) else ""

def wilson_interval(k: int, n: int, z: float = 1.96) -> Tuple[float, float]:
    if n <= 0:
        return 0.0, 1.0
    p = k / n
    denom = 1 + (z ** 2) / n
    centre = (p + (z ** 2) / (2 * n)) / denom
    half = (z * math.sqrt((p * (1 - p) + (z ** 2) / (4 * n)) / n)) / denom
    return max(0.0, centre - half), min(1.0, centre + half)

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

# =========================
# Load reference tables (link & sign plates)
# =========================
df_link = read_sql("SELECT * FROM parking_zones_linked_to_street_segments")
df_link.columns = df_link.columns.str.strip()
df_link["segment_id"] = pd.to_numeric(df_link["segment_id"], errors="coerce")
df_link["__street_norm__"] = df_link["onstreet"].map(normalize_street)

street_to_zones: Dict[str, List[str]] = (
    df_link.dropna(subset=["__street_norm__", "parkingzone"])
    .groupby("__street_norm__")["parkingzone"].apply(lambda s: sorted(set(s))).to_dict()
)

df_sign = read_sql("SELECT * FROM sign_plates_located_in_each_parking_zone")
df_sign.columns = df_sign.columns.str.strip()
df_sign["__wdays__"]  = df_sign["restriction_days"].map(parse_days_to_weekday_set)
df_sign["__tstart__"] = df_sign["time_restrictions_start"].map(parse_time_hhmm)
df_sign["__tfinish__"] = df_sign["time_restrictions_finish"].map(parse_time_hhmm)

def zones_for_street(street_name: str) -> List[str]:
    key = normalize_street(street_name)
    return street_to_zones.get(key, [])

def restricted_any(zones: List[str], dow: int, hour: int) -> bool:
    if not zones:
        return False
    t_local = dtime(hour, 0)
    for z in zones:
        sub = df_sign[df_sign["parkingzone"].astype(str) == str(z)]
        if sub.empty:
            continue
        for _, r in sub.iterrows():
            days = r["__wdays__"]; tstart = r["__tstart__"]; tfinish = r["__tfinish__"]
            if days is None or tstart is None or tfinish is None:
                continue
            if dow in days and time_in_window(t_local, tstart, tfinish):
                return True
    return False

# =========================
# Sensors -> historical availability
# =========================
df_s = read_sql("SELECT * FROM on_street_parking_bay_sensors")
df_s.columns = df_s.columns.str.strip()
# expected cols: lastupdated, status_timestamp, zone_number, kerbsideid, location
df_s["status_timestamp"] = pd.to_datetime(df_s["status_timestamp"], errors="coerce")
if TZ_AWARE:
    try:
        df_s["status_timestamp"] = df_s["status_timestamp"].dt.tz_convert("Australia/Melbourne")
    except Exception:
        pass
df_s["zone_number"] = pd.to_numeric(df_s["zone_number"], errors="coerce")
df_s = df_s.dropna(subset=["status_timestamp", "zone_number"])
df_s["hour"] = df_s["status_timestamp"].dt.hour
df_s["dow"]  = df_s["status_timestamp"].dt.dayofweek  # Mon=0

# Try to find an occupancy/status column (optional)
occ_cols = [c for c in df_s.columns if c.lower() in
            {"status", "status_description", "occupancy", "bay_status", "space_status"}]

def derive_is_free_column(df: pd.DataFrame, occ_candidates: List[str]) -> Optional[pd.Series]:
    if not occ_candidates:
        return None
    col = occ_candidates[0]
    s = df[col].astype(str).str.strip().str.lower()
    free_tokens = {"unoccupied", "free", "vacant", "available", "clear"}
    occ_tokens  = {"occupied", "present", "busy", "unavailable"}
    if s.isin(free_tokens | occ_tokens).any():
        return s.isin(free_tokens)
    if s.str.fullmatch(r"[01]").all():
        return s.astype(int).map(lambda x: x == 0)
    if s.str.contains("unoccupied|available|vacant", regex=True).any() or s.str.contains("occupied|present", regex=True).any():
        return s.str.contains("unoccupied|available|vacant", regex=True)
    return None

is_free = derive_is_free_column(df_s, occ_cols)
has_hist = is_free is not None

hist_zone_dow_hr: Optional[pd.DataFrame] = None
if has_hist:
    df_s["is_free"] = is_free
    hist_zone_dow_hr = (
        df_s.groupby(["zone_number", "dow", "hour"])
            .agg(total=("is_free", "size"), free=("is_free", "sum"))
            .reset_index()
    )
    hist_zone_dow_hr["availability"] = hist_zone_dow_hr["free"] / hist_zone_dow_hr["total"]

# =========================
# Aggregation helper
# =========================
def trends_for_zones(zones: List[str]) -> Dict[str, Any]:
    """
    Returns a 7x24 grid of availability and counts. If no occupancy data, returns unknown with restriction mask.
    """
    matrix = []
    total_samples = 0

    for dow in range(7):
        for hour in range(24):
            restricted = restricted_any(zones, dow, hour)
            if has_hist and hist_zone_dow_hr is not None:
                sub = hist_zone_dow_hr[hist_zone_dow_hr["zone_number"].astype(str).isin([str(z) for z in zones])]
                sub = sub[(sub["dow"] == dow) & (sub["hour"] == hour)]
                if not sub.empty:
                    total = int(sub["total"].sum())
                    free  = int(sub["free"].sum())
                    avail = (free / total) if total > 0 else None
                    total_samples += total
                    matrix.append({
                        "dow": dow, "hour": hour,
                        "availability": None if avail is None else float(avail),
                        "n": total,
                        "restricted": restricted
                    })
                    continue
            # fallback: no occupancy for this bucket
            matrix.append({"dow": dow, "hour": hour, "availability": None, "n": 0, "restricted": restricted})

    return {
        "zones": [str(z) for z in zones],
        "has_hist": has_hist,
        "samples_total": int(total_samples),
        "matrix": matrix
    }

# =========================
# Flask app
# =========================
app = Flask(__name__)

@app.route("/historical_trends_data", methods=["GET"])
def historical_trends_data():
    """
    Query params:
      - zone: string (optional)
      - street: string (optional)
    One of them is required. If street is provided, data are aggregated across all mapped zones.
    """
    zone = request.args.get("zone")
    street = request.args.get("street")

    zones: List[str] = []
    if zone:
        zones = [zone]
    elif street:
        zones = zones_for_street(street)
        if not zones:
            return jsonify({"error": f"No zone mapping found for street '{street}'."}), 404
    else:
        return jsonify({"error": "Provide either 'zone' or 'street'."}), 400

    data = trends_for_zones(zones)
    msg = "Historical availability by day-of-week and hour."
    if not data["has_hist"]:
        msg = "No occupancy column found; showing restriction mask and unknown availability."

    return jsonify({
        "message": msg,
        **data
    })

@app.route("/trends", methods=["GET"])
def trends_page():
    # Minimal heatmap page with pure JS/CSS (no external libs)
    return """
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Historical Parking Trends</title>
  <style>
    body { font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial; max-width: 1000px; margin: 32px auto; }
    .row { display:flex; gap:12px; align-items:center; flex-wrap: wrap; }
    input, button { padding: 8px; font-size: 14px; }
    #grid { margin-top: 16px; }
    .heatmap { display: grid; grid-template-columns: 80px repeat(24, 28px); gap: 2px; }
    .cell, .label { text-align:center; padding:6px 0; font-size:12px; border-radius: 4px; }
    .label { background: #f4f4f4; }
    .dow { font-weight: 600; }
    .legend { margin-top: 12px; font-size: 12px; color: #555; display:flex; align-items:center; gap:10px; }
    .swatch { width:16px; height:16px; border-radius:3px; display:inline-block; border:1px solid #ddd;}
    .hint { color:#666; font-size: 13px; }
    #status { margin-top: 10px; color: #444; }
    .restricted { position: relative; }
    .restricted::after { content: "🚫"; position:absolute; right:2px; top:2px; font-size:12px; }
  </style>
</head>
<body>
  <h2>Historical Parking Trends</h2>
  <div class="row">
    <div>
      <label>Zone (optional)</label>
      <input id="zone" placeholder="e.g., 7539" />
    </div>
    <div>
      <label>Street (optional)</label>
      <input id="street" placeholder="e.g., Swanston Street" size="28"/>
    </div>
    <div style="align-self:flex-end;">
      <button id="load">Load trends</button>
    </div>
  </div>
  <div id="status" class="hint">Enter either Zone or Street and click "Load trends".</div>
  <div id="grid"></div>
  <div class="legend">
    <span>Legend:</span>
    <span class="swatch" style="background:#eee;"></span><span>No data</span>
    <span class="swatch" style="background:rgb(255,70,70);"></span><span>Low</span>
    <span class="swatch" style="background:rgb(255,200,60);"></span><span>Medium</span>
    <span class="swatch" style="background:rgb(60,190,90);"></span><span>High</span>
    <span>🚫 = restricted</span>
  </div>

<script>
const DOWS = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"];
function colorForAvailability(a){
  if (a === null || a === undefined) return "#eee";
  // 0 -> red(255,70,70), 0.5 -> yellow(255,200,60), 1 -> green(60,190,90)
  const r0=[255,70,70], r1=[255,200,60], r2=[60,190,90];
  let c;
  if (a < 0.5) {
    const t = a/0.5;
    c = [ r0[0]+(r1[0]-r0[0])*t, r0[1]+(r1[1]-r0[1])*t, r0[2]+(r1[2]-r0[2])*t ];
  } else {
    const t = (a-0.5)/0.5;
    c = [ r1[0]+(r2[0]-r1[0])*t, r1[1]+(r2[1]-r1[1])*t, r1[2]+(r2[2]-r1[2])*t ];
  }
  return `rgb(${c.map(x=>Math.round(x)).join(",")})`;
}

function renderHeatmap(data){
  const grid = document.getElementById('grid');
  grid.innerHTML = "";
  const wrap = document.createElement('div');
  wrap.className = "heatmap";

  // header row
  wrap.appendChild(cell("","label"));
  for (let h=0; h<24; h++) wrap.appendChild(cell(String(h).padStart(2,"0"), "label"));

  // build fast lookup: key "dow-hour"
  const m = {};
  for (const r of data.matrix) m[`${r.dow}-${r.hour}`] = r;

  for (let d=0; d<7; d++){
    wrap.appendChild(cell(DOWS[d], "label dow"));
    for (let h=0; h<24; h++){
      const rec = m[`${d}-${h}`] || {availability:null, n:0, restricted:false};
      const bg = colorForAvailability(rec.availability);
      const el = cell("", "cell"+(rec.restricted?" restricted":""));
      el.style.background = bg;
      el.title = `${DOWS[d]} ${String(h).padStart(2,"0")}:00 — `
        + (rec.availability==null ? "Unknown" : (rec.availability*100).toFixed(1)+"%")
        + ` (n=${rec.n})`
        + (rec.restricted ? " — restricted" : "");
      wrap.appendChild(el);
    }
  }
  grid.appendChild(wrap);
}

function cell(text, cls){
  const d = document.createElement('div');
  d.className = cls;
  d.textContent = text;
  return d;
}

async function loadTrends(){
  const zone = document.getElementById("zone").value.trim();
  const street = document.getElementById("street").value.trim();
  const status = document.getElementById("status");
  if (!zone && !street) {
    status.textContent = "Provide either Zone or Street.";
    return;
  }
  let url = "/historical_trends_data?";
  if (zone) url += "zone="+encodeURIComponent(zone);
  else url += "street="+encodeURIComponent(street);

  status.textContent = "Loading...";
  try{
    const resp = await fetch(url);
    const data = await resp.json();
    if (!resp.ok){
      status.textContent = data.error || "Error";
      return;
    }
    status.textContent = data.message + ` Zones: ${data.zones.join(", ")} — Samples: ${data.samples_total}`;
    renderHeatmap(data);
  }catch(e){
    status.textContent = "Network error: "+e.message;
  }
}
document.getElementById("load").addEventListener("click", loadTrends);
</script>

</body>
</html>
"""

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"ok": True, "has_hist": has_hist})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5002"))
    app.run(host="0.0.0.0", port=port, debug=True)