# app_2.3.py
from flask import Flask, request, Response, render_template_string
import pandas as pd
import numpy as np
import os
from sqlalchemy import create_engine

AUS_TZ = "Australia/Melbourne"
WEEKDAY_LABELS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

# ---------- DB CONFIG (read from Railway Postgres) ----------
DB_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+psycopg2://postgres:eSyUrNgzoGjZybYhxZRwLKaSbAxkQmIQ@trolley.proxy.rlwy.net:13392/railway"
)
TABLE = "parking_merged_all"

# ---------------- Templates (单文件内置) ----------------
INDEX_HTML = r"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Melbourne Parking — Daily Forecast</title>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.min.css">
  <style>
    .container { max-width: 1100px; }
    .muted { color: #6b7280; font-size: 0.9rem; }
    canvas { max-height: 320px; }
    .card { border: 1px solid #e5e7eb; border-radius: 12px; padding: 1rem; }
    .pill { border-radius: 9999px; padding: 0.2rem 0.6rem; font-weight: 600; }
    .pill.high { background: #e6ffed; color: #065f46; }
    .pill.medium { background: #fff7ed; color: #9a3412; }
    .pill.low { background: #fee2e2; color: #991b1b; }
    .flex { display: flex; gap: 1rem; align-items: end; }
    nav { margin: 1rem 0; }
  </style>
</head>
<body>
  <main class="container">
    <nav>
      <ul>
        <li><strong>Daily</strong></li>
        <li><a href="/trends?street={{ street }}&cross_from={{ cross_from_sel }}&cross_to={{ cross_to_sel }}">Trends</a></li>
      </ul>
    </nav>

    <h2>🅿️ Melbourne Parking — Daily Forecast</h2>
    <p class="muted">Pick a weekday to see the full-day availability profile for the selected location.</p>

    <form method="get">
      <div class="grid">
        <div>
          <label for="street">Street</label>
          <select id="street" name="street" onchange="this.form.submit()">
            {% for s in streets %}
              <option value="{{s}}" {% if s == street %}selected{% endif %}>{{s}}</option>
            {% endfor %}
          </select>
        </div>
        <div>
          <label for="cross_from">Between (from)</label>
          <select id="cross_from" name="cross_from">
            <option value="(Any)" {% if cross_from_sel == "(Any)" %}selected{% endif %}>(Any)</option>
            {% for cf in cross_from_opts %}
              <option value="{{cf}}" {% if cf == cross_from_sel %}selected{% endif %}>{{cf}}</option>
            {% endfor %}
          </select>
        </div>
        <div>
          <label for="cross_to">Between (to)</label>
          <select id="cross_to" name="cross_to">
            <option value="(Any)" {% if cross_to_sel == "(Any)" %}selected{% endif %}>(Any)</option>
            {% for ct in cross_to_opts %}
              <option value="{{ct}}" {% if ct == cross_to_sel %}selected{% endif %}>{{ct}}</option>
            {% endfor %}
          </select>
        </div>
      </div>

      <div class="flex">
        <div>
          <label for="weekday">Weekday</label>
          <select id="weekday" name="weekday">
            {% for wd in weekday_labels %}
              <option value="{{wd}}" {% if wd == weekday_label %}selected{% endif %}>{{wd}}</option>
            {% endfor %}
          </select>
        </div>
        <button type="submit">Update</button>
      </div>
    </form>

    <section class="card">
      <h4>Daily Forecast ({{ weekday_label }})</h4>
      {% if not has_data %}
        <p><strong>No data</strong> for this weekday at the selected location. Unable to provide a forecast.</p>
      {% else %}
        {% if fallback %}<p class="muted">No exact cross-street match; fell back to the whole street.</p>{% endif %}
      {% endif %}
      <canvas id="chart" aria-label="Hourly availability chart" role="img"></canvas>
      <p class="muted">Availability is computed as the share of records with status "Unoccupied".</p>
    </section>

    <details>
      <summary>Show hourly details</summary>
      <table>
        <thead>
          <tr><th>Hour</th><th>Availability</th><th>n</th><th>Confidence</th></tr>
        </thead>
        <tbody>
        {% for h in range(24) %}
          <tr>
            <td>{{ "%02d:00"|format(h) }}</td>
            {% if chart_values[h] is not none %}
              <td>{{ (chart_values[h] * 100) | round(0) }}%</td>
              <td>{{ chart_samples[h] }}</td>
              {% set cl = chart_conf[h].lower() %}
              <td><span class="pill {{cl}}">{{ chart_conf[h] }}</span></td>
            {% else %}
              <td colspan="3" class="muted">No data</td>
            {% endif %}
          </tr>
        {% endfor %}
        </tbody>
      </table>
    </details>
  </main>

  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <script>
    const hours = {{ chart_hours | tojson }};
    const values = {{ chart_values | tojson }};
    const ctx = document.getElementById('chart').getContext('2d');
    new Chart(ctx, {
      type: 'line',
      data: {
        labels: hours.map(h => String(h).padStart(2,'0') + ':00'),
        datasets: [{
          label: 'Availability (share Unoccupied)',
          data: values,
          spanGaps: true,
          tension: 0.2
        }]
      },
      options: {
        responsive: true,
        scales: {
          y: { min: 0, max: 1, ticks: { callback: v => (v*100).toFixed(0) + '%' } }
        }
      }
    });
  </script>
</body>
</html>
"""

TRENDS_HTML = r"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Melbourne Parking — Historical Trends</title>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.min.css">
  <style>
    .container { max-width: 1100px; }
    .muted { color: #6b7280; font-size: 0.9rem; }
    canvas { max-height: 520px; }
    .card { border: 1px solid #e5e7eb; border-radius: 12px; padding: 1rem; }
    nav { margin: 1rem 0; }
    .legend { display:flex; align-items:center; gap:8px; }
    .swatch { width: 16px; height: 12px; border-radius: 2px; display:inline-block; }
  </style>
</head>
<body>
  <main class="container">
    <nav>
      <ul>
        <li><a href="/">Daily</a></li>
        <li><strong>Trends</strong></li>
      </ul>
    </nav>

    <h2>🗺️ Historical Parking Availability — Trends</h2>
    <p class="muted">Heatmap of availability by <strong>time of day × day of week</strong> at your selected destination.</p>

    <form method="get">
      <div class="grid">
        <div>
          <label for="street">Street</label>
          <select id="street" name="street" onchange="this.form.submit()">
            {% for s in streets %}
              <option value="{{s}}" {% if s == street %}selected{% endif %}>{{s}}</option>
            {% endfor %}
          </select>
        </div>
        <div>
          <label for="cross_from">Between (from)</label>
          <select id="cross_from" name="cross_from">
            <option value="(Any)" {% if cross_from_sel == "(Any)" %}selected{% endif %}>(Any)</option>
            {% for cf in cross_from_opts %}
              <option value="{{cf}}" {% if cf == cross_from_sel %}selected{% endif %}>{{cf}}</option>
            {% endfor %}
          </select>
        </div>
        <div>
          <label for="cross_to">Between (to)</label>
          <select id="cross_to" name="cross_to">
            <option value="(Any)" {% if cross_to_sel == "(Any)" %}selected{% endif %}>(Any)</option>
            {% for ct in cross_to_opts %}
              <option value="{{ct}}" {% if ct == cross_to_sel %}selected{% endif %}>{{ct}}</option>
            {% endfor %}
          </select>
        </div>
      </div>
      <div style="margin-top:.5rem">
        <button type="submit">Update</button>
        <a class="secondary" href="/trends.csv?street={{ street }}&cross_from={{ cross_from_sel }}&cross_to={{ cross_to_sel }}">Download CSV</a>
      </div>
    </form>

    <section class="card">
      <h4>Availability Heatmap</h4>
      {% if fallback %}<p class="muted">No exact cross-street match; fell back to the whole street.</p>{% endif %}
      {% if not has_data %}
        <p><strong>No data</strong> for this destination. Unable to render trends.</p>
      {% endif %}
      <canvas id="heatmap" aria-label="Availability heatmap" role="img"></canvas>
      <div class="muted legend">
        <span>0%</span>
        <span class="swatch" style="background:#fca5a5"></span>
        <span class="swatch" style="background:#f59e0b"></span>
        <span class="swatch" style="background:#84cc16"></span>
        <span class="swatch" style="background:#22c55e"></span>
        <span>100%</span>
      </div>
      <p class="muted">Each cell shows the average share of records with status "Unoccupied" for that weekday & hour. Tooltip includes sample size (n).</p>
    </section>
  </main>

  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/chartjs-chart-matrix@2.0.1/dist/chartjs-chart-matrix.min.js"></script>
  <script>
    const matrix = {{ matrix | tojson }};
    const weekdayOrder = {{ weekday_labels | tojson }};

    function colorFor(val) {
      if (val === null || val === undefined) return 'rgba(200,200,200,0.2)';
      const p = Math.max(0, Math.min(1, val));
      const r = p < 0.5 ? 239 + (245-239)* (p/0.5) : 245 + (34-245) * ((p-0.5)/0.5);
      const g = p < 0.5 ? 68  + (158-68) * (p/0.5) : 158 + (197-158)* ((p-0.5)/0.5);
      const b = p < 0.5 ? 68  + (11-68)  * (p/0.5) : 11  + (94-11)  * ((p-0.5)/0.5);
      return `rgb(${Math.round(r)}, ${Math.round(g)}, ${Math.round(b)})`;
    }

    const data = matrix.map(d => ({
      x: d.x, y: weekdayOrder.indexOf(d.y), v: d.v, n: d.n
    }));

    const ctx = document.getElementById('heatmap').getContext('2d');
    new Chart(ctx, {
      type: 'matrix',
      data: {
        datasets: [{
          label: 'Availability',
          data: data,
          width: ({chart}) => (chart.chartArea || {}).width / 24 - 2,
          height: ({chart}) => (chart.chartArea || {}).height / 7 - 2,
          backgroundColor: (ctx) => colorFor(ctx.raw.v),
          borderColor: 'rgba(0,0,0,0.05)',
          borderWidth: 1
        }]
      },
      options: {
        responsive: true,
        scales: {
          x: {
            type: 'linear',
            ticks: { callback: (v) => String(v).padStart(2,'0') + ':00', stepSize: 1, min: -0.5, max: 23.5 },
            grid: { display: false }
          },
          y: {
            type: 'linear',
            ticks: { callback: (v) => weekdayOrder[v] || '' },
            reverse: true, min: -0.5, max: 6.5,
            grid: { display: false }
          }
        },
        plugins: {
          tooltip: {
            callbacks: {
              label: (ctx) => {
                const d = ctx.raw;
                const pct = d.v == null ? 'No data' : `${(d.v*100).toFixed(0)}%`;
                const hour = String(d.x).padStart(2,'0') + ':00';
                const day = weekdayOrder[d.y];
                return ` ${day} ${hour}: ${pct} (n=${d.n})`;
              }
            }
          },
          legend: { display: false }
        }
      }
    });
  </script>
</body>
</html>
"""

# ---------------- App & helpers ----------------
app = Flask(__name__)

def to_str_strip(series: pd.Series) -> pd.Series:
    return series.astype("string").fillna("").str.strip()

def map_status_to_available(s: str) -> float:
    if isinstance(s, str):
        ss = s.strip().lower()
        if ss == "unoccupied": return 1.0
        if ss == "present":    return 0.0
    return np.nan

# --- NEW: load from Postgres instead of local CSV ---
def load_data_from_db(db_url: str, table: str) -> pd.DataFrame:
    engine = create_engine(db_url, connect_args={"sslmode": "require"}, pool_pre_ping=True, future=True)
    with engine.connect() as conn:
        df = pd.read_sql(f"SELECT * FROM {table}", conn)

    # 文本规范
    for col in ["OnStreet", "StreetFrom", "StreetTo"]:
        if col in df.columns:
            df[col] = to_str_strip(df[col])

    # 状态 -> 可用
    if "Status_Description" in df.columns:
        df["available"] = df["Status_Description"].apply(map_status_to_available)
    else:
        df["available"] = np.nan

    # 时间戳 -> 本地周/小时
    if "Status_Timestamp" in df.columns:
        df["ts"] = pd.to_datetime(df["Status_Timestamp"], errors="coerce", utc=True)
    else:
        df["ts"] = pd.NaT

    if df["ts"].notna().any():
        try:
            df["ts_local"] = df["ts"].dt.tz_convert(AUS_TZ)
        except Exception:
            df["ts_local"] = df["ts"]
        df["hour"] = df["ts_local"].dt.hour
        df["weekday"] = df["ts_local"].dt.weekday
    else:
        df["hour"] = np.nan
        df["weekday"] = np.nan

    return df

def aggregate_by_time(loc_df: pd.DataFrame) -> pd.DataFrame:
    loc_df = loc_df.dropna(subset=["available", "hour", "weekday"])
    if loc_df.empty:
        return pd.DataFrame(columns=["weekday", "hour", "availability", "samples"])
    return (loc_df.groupby(["weekday","hour"], as_index=False)
            .agg(availability=("available","mean"),
                 samples=("available","size")))

# === Load once from DB ===
DF = load_data_from_db(DB_URL, TABLE)
STREETS = sorted([s for s in DF.get("OnStreet", pd.Series(dtype=str)).dropna().unique() if s])

def get_crossing_options(street: str):
    df_street = DF[DF["OnStreet"] == street].copy()
    cross_from = sorted([s for s in df_street.get("StreetFrom", pd.Series(dtype=str)).dropna().unique() if s])
    cross_to   = sorted([s for s in df_street.get("StreetTo",   pd.Series(dtype=str)).dropna().unique() if s])
    return cross_from, cross_to

def location_slice(street: str, cross_from_sel: str, cross_to_sel: str):
    mask = (DF["OnStreet"] == street)
    if "StreetFrom" in DF.columns and cross_from_sel and cross_from_sel != "(Any)":
        mask &= (DF["StreetFrom"] == cross_from_sel)
    if "StreetTo" in DF.columns and cross_to_sel and cross_to_sel != "(Any)":
        mask &= (DF["StreetTo"] == cross_to_sel)
    loc_df = DF.loc[mask].copy()
    fallback = False
    if loc_df.empty:
        loc_df = DF[DF["OnStreet"] == street].copy()
        fallback = True
    return loc_df, fallback

# ---------------- Routes ----------------
@app.route("/", methods=["GET"])
def daily_view():
    if not STREETS:
        return "No street data available (OnStreet column empty)."
    street = request.args.get("street") or ("Spring Street" if "Spring Street" in STREETS else STREETS[0])
    cross_from_sel = request.args.get("cross_from") or "(Any)"
    cross_to_sel = request.args.get("cross_to") or "(Any)"
    weekday_label = request.args.get("weekday") or WEEKDAY_LABELS[pd.Timestamp.now(tz=AUS_TZ).weekday()]
    weekday_req = WEEKDAY_LABELS.index(weekday_label) if weekday_label in WEEKDAY_LABELS else 0

    cross_from_opts, cross_to_opts = get_crossing_options(street)
    loc_df, fallback = location_slice(street, cross_from_sel, cross_to_sel)
    grouped = aggregate_by_time(loc_df)
    day = grouped[grouped["weekday"] == weekday_req].sort_values("hour")

    chart_hours = list(range(24))
    chart_values = [None]*24
    chart_samples = [0]*24
    chart_conf = ["Low"]*24

    if not day.empty:
        for _, r in day.iterrows():
            h = int(r["hour"]); p = float(r["availability"]); n = int(r["samples"])
            chart_values[h] = p; chart_samples[h] = n
            chart_conf[h] = "High" if n >= 100 else ("Medium" if n >= 20 else "Low")
    has_data = any(v is not None for v in chart_values)

    return render_template_string(
        INDEX_HTML,
        streets=STREETS, street=street,
        cross_from_opts=cross_from_opts, cross_to_opts=cross_to_opts,
        cross_from_sel=cross_from_sel, cross_to_sel=cross_to_sel,
        weekday_label=weekday_label, weekday_labels=WEEKDAY_LABELS,
        chart_hours=chart_hours, chart_values=chart_values,
        chart_samples=chart_samples, chart_conf=chart_conf,
        has_data=has_data, fallback=fallback
    )

@app.route("/trends", methods=["GET"])
def trends_view():
    if not STREETS:
        return "No street data available (OnStreet column empty)."
    street = request.args.get("street") or ("Spring Street" if "Spring Street" in STREETS else STREETS[0])
    cross_from_sel = request.args.get("cross_from") or "(Any)"
    cross_to_sel = request.args.get("cross_to") or "(Any)"

    cross_from_opts, cross_to_opts = get_crossing_options(street)
    loc_df, fallback = location_slice(street, cross_from_sel, cross_to_sel)
    grouped = aggregate_by_time(loc_df)

    matrix = []
    has_data = False
    cell = {(w,h): {"v": None, "n": 0} for w in range(7) for h in range(24)}
    for _, r in grouped.iterrows():
        w = int(r["weekday"]); h = int(r["hour"])
        v = float(r["availability"]); n = int(r["samples"])
        cell[(w,h)] = {"v": v, "n": n}
        if v is not None:
            has_data = True
    for w in range(7):
        for h in range(24):
            matrix.append({"x": h, "y": WEEKDAY_LABELS[w], "v": cell[(w,h)]["v"], "n": cell[(w,h)]["n"]})

    return render_template_string(
        TRENDS_HTML,
        streets=STREETS, street=street,
        cross_from_opts=cross_from_opts, cross_to_opts=cross_to_opts,
        cross_from_sel=cross_from_sel, cross_to_sel=cross_to_sel,
        matrix=matrix, has_data=has_data, fallback=fallback,
        weekday_labels=WEEKDAY_LABELS
    )

@app.route("/trends.csv", methods=["GET"])
def trends_csv():
    street = request.args.get("street")
    cross_from_sel = request.args.get("cross_from")
    cross_to_sel = request.args.get("cross_to")
    if not street:
        return Response("Missing 'street' parameter", status=400)
    loc_df, _ = location_slice(street, cross_from_sel or "(Any)", cross_to_sel or "(Any)")
    grouped = aggregate_by_time(loc_df).sort_values(["weekday","hour"])
    csv = grouped.to_csv(index=False)
    return Response(csv, mimetype="text/csv",
        headers={"Content-Disposition":"attachment; filename=parking_trends.csv"})

if __name__ == "__main__":
    # 依赖：pip install flask pandas numpy sqlalchemy psycopg2-binary
    app.run(debug=True)