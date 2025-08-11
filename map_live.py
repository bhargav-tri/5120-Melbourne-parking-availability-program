import requests, time
import folium
from folium.plugins import MarkerCluster
from datetime import datetime, timedelta, timezone

BASE = "https://data.melbourne.vic.gov.au"
DATASET = "on-street-parking-bay-sensors"
URL = f"{BASE}/api/explore/v2.1/catalog/datasets/{DATASET}/records"

# --- fetch helpers ---
def fetch(params):
    r = requests.get(URL, params=params, timeout=30, headers={"User-Agent":"melb-parking-feed/1.0"})
    r.raise_for_status()
    return r.json().get("results", [])

def fetch_all(page_size=100, where=None):
    out, offset = [], 0
    while True:
        p = {"limit": page_size, "offset": offset}
        if where: p["where"] = where
        r = requests.get(URL, params=p, timeout=30)
        if not r.ok:
            raise RuntimeError(f"{r.status_code} {r.reason}: {r.text[:300]}")
        batch = r.json().get("results", [])
        if not batch: break
        out.extend(batch)
        if len(batch) < page_size: break
        offset += page_size
        time.sleep(0.15)
    return out

# --- geo extraction ---
def get_field(row, *cands):
    for c in cands:
        if c in row: return row[c]
    return None

def extract_latlon(row):
    loc = get_field(row, "location", "geo_point_2d", "Location", "geo_shape", "geo_point")
    if not loc: return None
    if isinstance(loc, dict):
        if "lat" in loc and "lon" in loc:
            return float(loc["lat"]), float(loc["lon"])
        if "coordinates" in loc and isinstance(loc["coordinates"], (list, tuple)) and len(loc["coordinates"]) >= 2:
            lon, lat = loc["coordinates"][:2]
            return float(lat), float(lon)
        for v in loc.values():
            if isinstance(v, dict) and "coordinates" in v:
                lon, lat = v["coordinates"][:2]
                return float(lat), float(lon)
    if isinstance(loc, (list, tuple)) and len(loc) >= 2:
        lat, lon = loc[0], loc[1]
        return float(lat), float(lon)
    if isinstance(loc, str) and "," in loc:
        a, b = [s.strip() for s in loc.split(",")[:2]]
        return float(a), float(b)
    return None

def color_for_status(status):
    s = (status or "").lower()
    if "unoccupied" in s or "free" in s or "available" in s: return "green"
    if "present" in s or "occupied" in s or "busy" in s:     return "red"
    return "orange"

def main():
    # pull only recent rows (faster) – change minutes if you want more
    # since = (datetime.now(timezone.utc) - timedelta(minutes=120)).strftime("%Y-%m-%dT%H:%M:%SZ")
    # where = f'lastupdated > "{since}"'
    # rows = fetch_all(where=where)

    rows = fetch_all()  # no WHERE — fetch every page

    print("Fetched rows:", len(rows))
    print("With coordinates:", sum(1 for r in rows if extract_latlon(r)))

    sample = rows[0] if rows else {}
    key = {k.lower(): k for k in sample.keys()}
    def fld(name, default=None): return key.get(name.lower(), default or name)
    KERBSIDEID  = fld("kerbsideid")
    STATUS_DESC = fld("status_description")
    LASTUPDATED = fld("lastupdated")

    m = folium.Map(location=[-37.8136, 144.9631], zoom_start=15, control_scale=True)

    # --- custom cluster icon that reflects mix using a CSS conic-gradient donut ---
    icon_create_function = """
    function(cluster){
      var markers = cluster.getAllChildMarkers();
      var counts = {green:0, red:0, orange:0, gray:0};
      markers.forEach(function(m){
        var col = m.options.icon && m.options.icon.options && m.options.icon.options.markerColor;
        if(!col){ col = 'gray'; }
        if(counts[col] === undefined) counts[col]=0;
        counts[col]++;
      });
      var total = markers.length;
      var g = counts.green || 0, r = counts.red || 0, o = counts.orange || 0, gr = counts.gray || 0;
      var t = Math.max(total,1);
      var a1 = 360*(g/t);
      var a2 = a1 + 360*(r/t);
      var a3 = a2 + 360*(o/t);
      var style = 'background: conic-gradient('+
                  'green 0 '+a1+'deg, '+
                  'red '+a1+'deg '+a2+'deg, '+
                  'orange '+a2+'deg '+a3+'deg, '+
                  'gray '+a3+'deg 360deg);';
      var html = '<div style="width:48px;height:48px;border-radius:50%;border:2px solid #333;'+style+
                 'display:flex;align-items:center;justify-content:center;">' +
                 '<span style="background:white;border:1px solid #555;border-radius:12px;padding:1px 6px;font:12px/1.2 sans-serif;">'+total+'</span>' +
                 '</div>';
      return new L.DivIcon({html: html, className: 'cluster-pie', iconSize: [48,48]});
    }
    """

    cluster = MarkerCluster(name="Parking Bays", icon_create_function=icon_create_function).add_to(m)

    added = 0
    for r in rows:
        latlon = extract_latlon(r)
        if not latlon: continue
        lat, lon = latlon
        status = r.get(STATUS_DESC)
        kid = r.get(KERBSIDEID)
        lu = r.get(LASTUPDATED)
        color = color_for_status(status)

        # Use AwesomeMarkers so we can read markerColor in JS
        icon = folium.Icon(color=color, icon="circle", prefix="fa")
        popup = folium.Popup(folium.IFrame(html=f"""
            <b>KerbsideID:</b> {kid or '—'}<br/>
            <b>Status:</b> {status or '—'}<br/>
            <b>Last updated:</b> {lu or '—'}<br/>
            <b>Lat/Lon:</b> {lat:.6f}, {lon:.6f}
        """, width=240, height=120), max_width=260)

        folium.Marker([lat, lon], icon=icon, popup=popup).add_to(cluster)
        added += 1

    folium.LayerControl().add_to(m)

    # Legend + refresh
    legend_html = """
    <div style="position: fixed; bottom: 50px; left: 50px; width: 170px; background: white;
                border: 2px solid grey; z-index: 9999; font-size: 14px; border-radius: 6px;
                padding: 10px; box-shadow: 2px 2px 5px rgba(0,0,0,.3);">
      <b>Legend</b><br>
      <i style="background:green; width:12px; height:12px; display:inline-block;"></i> Unoccupied<br>
      <i style="background:red; width:12px; height:12px; display:inline-block;"></i> Occupied<br>
      <i style="background:orange; width:12px; height:12px; display:inline-block;"></i> Unknown/Other
    </div>
    <div style="position: fixed; top: 10px; right: 10px; z-index: 1000;">
      <button onclick="location.reload()" style="padding:8px 12px; border-radius:6px; border:1px solid #999; background:#fff; cursor:pointer;">
        🔄 Refresh
      </button>
    </div>
    <script> setTimeout(function(){ location.reload(); }, 60000); </script>
    """
    m.get_root().html.add_child(folium.Element(legend_html))

    out = "Latest_parking_map_live.html"
    m.save(out)
    print(f"Saved {out} with {added} markers.")
    print("Tip: zoom out — cluster donuts show the true mix inside (green/red/orange).")

if __name__ == "__main__":
    main()
