import { useNavigate } from "react-router-dom";
import { useMemo, useState, useCallback, useEffect } from "react";

export default function RealTimeParking() {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState("us2.1");

  // 浅色主题
  const theme = useMemo(
    () => ({
      bg: "#ffffff",
      panel: "#ffffff",
      text: "#111111",
      subtext: "#555555",
      accent: "#007BFF",
      accentHover: "#339BFF",
      muted: "#888888",
      border: "rgba(0,0,0,0.12)",
      shadow: "0 4px 20px rgba(0,0,0,0.08)",
      radius: "12px",
    }),
    []
  );

  const tabs = [
    { id: "us2.1", label: " Find Parking (Real-time)" },
    { id: "us2.2", label: " Predicted Availability" },
    { id: "us2.3", label: " Historical Trends" },
  ];

  const backButtonStyle = {
    position: "absolute",
    top: 20,
    right: 30,
    fontSize: "1.5rem",
    color: theme.text,
    background: "rgba(0,0,0,0.04)",
    borderRadius: "50%",
    width: 40,
    height: 40,
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    cursor: "pointer",
    zIndex: 10,
    border: `1px solid ${theme.border}`,
  };

  const onKeyDownTabs = useCallback(
    (e) => {
      if (e.key !== "ArrowLeft" && e.key !== "ArrowRight") return;
      e.preventDefault();
      const idx = tabs.findIndex((t) => t.id === activeTab);
      const next =
        e.key === "ArrowRight"
          ? (idx + 1) % tabs.length
          : (idx - 1 + tabs.length) % tabs.length;
      setActiveTab(tabs[next].id);
    },
    [activeTab]
  );

  useEffect(() => window.scrollTo(0, 0), []);

  return (
    <div style={{ background: theme.bg, minHeight: "100vh", color: theme.text }}>
      {/* 返回按钮 */}
      <div
        style={backButtonStyle}
        onClick={() => navigate("/")}
        title="Back to Home"
        role="button"
        aria-label="Back"
      >
        ←
      </div>

      {/* 顶部标题 + 导航（保留居中宽度） */}
      <header
        style={{
          paddingTop: 72,
          paddingBottom: 12,
          textAlign: "center",
          maxWidth: 1100,
          margin: "0 auto",
          paddingLeft: 16,
          paddingRight: 16,
        }}
      >
        <h1 style={{ margin: 0, letterSpacing: 0.3 }}>Real-Time Parking</h1>
        <p style={{ marginTop: 8, color: theme.subtext }}>
          
        </p>

        <nav
          aria-label="Parking features"
          onKeyDown={onKeyDownTabs}
          style={{
            display: "flex",
            gap: 10,
            justifyContent: "center",
            flexWrap: "wrap",
            marginTop: 16,
          }}
        >
          {tabs.map((t) => {
            const active = activeTab === t.id;
            return (
              <button
                key={t.id}
                onClick={() => setActiveTab(t.id)}
                aria-pressed={active}
                style={{
                  border: `1px solid ${active ? theme.accent : theme.border}`,
                  background: active ? theme.accent : "#fff",
                  color: active ? "#fff" : theme.text,
                  padding: "10px 16px",
                  fontSize: "0.95rem",
                  borderRadius: 999,
                  cursor: "pointer",
                  transition: "all .15s ease",
                  boxShadow: active ? theme.shadow : "none",
                }}
                onMouseOver={(e) => {
                  if (!active) e.currentTarget.style.borderColor = theme.accentHover;
                }}
                onMouseOut={(e) => {
                  if (!active) e.currentTarget.style.borderColor = theme.border;
                }}
              >
                {t.label}
              </button>
            );
          })}
        </nav>
      </header>

      {/* 内容区：US2.1 地图做 full-bleed，US2.2/2.3 常规宽度 */}
      {activeTab === "us2.1" ? (
        <US21RealTimePanel theme={theme} />
      ) : (
        <main
          style={{
            maxWidth: 1100,
            margin: "0 auto",
            padding: 16,
            paddingBottom: 40,
          }}
        >
          <section
            style={{
              background: theme.panel,
              border: `1px solid ${theme.border}`,
              borderRadius: theme.radius,
              boxShadow: theme.shadow,
              minHeight: 420,
              padding: 20,
            }}
          >
            {activeTab === "us2.2" && <US22PredictivePanel theme={theme} />}
            {activeTab === "us2.3" && <US23HistoricalPanel theme={theme} />}
          </section>
        </main>
      )}
    </div>
  );
}

/* ---------------- 面板组件 ---------------- */

// US2.1：导航保留，地图横向铺满到视口两侧
function US21RealTimePanel({ theme }) {
  return (
    <section aria-label="Real-time map" style={{ marginTop: 8 }}>
      {/* 标题说明仍居中 */}
      <div
        style={{
          maxWidth: 1100,
          margin: "0 auto",
          padding: "0 16px",
          color: theme.subtext,
        }}
      >
        <h2 style={{ marginTop: 6, marginBottom: 4, color: "#111" }}>
          
        </h2>
        <p style={{ marginTop: 0 }}>
          Live map of legal public/commercial spots with availability status (green / yellow / red).
        </p>
      </div>

      {/* full-bleed 容器：宽度 100vw，左外边距拉到视口左缘 */}
      <div
        style={{
          width: "100vw",
          marginLeft: "calc(50% - 50vw)",
          marginTop: 12,
        }}
      >
        <div
          style={{
            height: "calc(100vh - 260px)", // 预留顶部导航高度
            minHeight: 520,
            borderTop: `1px solid ${theme.border}`,
            borderBottom: `1px solid ${theme.border}`,
            background: "#f6f7f9",
          }}
        >
          <iframe
            title="Live Parking Map"
            src="/maps/latest_parking_map_live.html"
            style={{ width: "100%", height: "100%", border: 0 }}
            allow="fullscreen"
          />
        </div>
      </div>
    </section>
  );
}

// US2.2 占位
function US22PredictivePanel({ theme }) {
  const [form, setForm] = useState({ location: "", date: "", time: "" });
  const [result, setResult] = useState(null);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setForm((s) => ({ ...s, [name]: value }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    const msg =
      form.location && form.date && form.time
        ? `Parking near “${form.location}” at ${form.time} on ${form.date} is most likely available.`
        : "Please enter location, date, and time.";
    setResult(msg);
  };

  return (
    <div>
      <h2 style={{ marginTop: 6, marginBottom: 4 }}>US2.2 — Predicted Availability</h2>
      <p style={{ color: theme.subtext, marginTop: 0 }}>
        Enter time & location to see predicted availability with a clear recommendation (e.g., “most likely / not possible”).
      </p>

      <form
        onSubmit={handleSubmit}
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 160px 140px auto",
          gap: 10,
          alignItems: "end",
          marginTop: 16,
        }}
      >
        <div style={{ display: "grid" }}>
          <label style={{ color: theme.muted, fontSize: 12, marginBottom: 6 }}>Location / Street</label>
          <input
            name="location"
            value={form.location}
            onChange={handleChange}
            placeholder="e.g., Collins St"
            style={inputStyle(theme)}
          />
        </div>
        <div style={{ display: "grid" }}>
          <label style={{ color: theme.muted, fontSize: 12, marginBottom: 6 }}>Date</label>
          <input name="date" type="date" value={form.date} onChange={handleChange} style={inputStyle(theme)} />
        </div>
        <div style={{ display: "grid" }}>
          <label style={{ color: theme.muted, fontSize: 12, marginBottom: 6 }}>Time</label>
          <input name="time" type="time" value={form.time} onChange={handleChange} style={inputStyle(theme)} />
        </div>
        <button
          type="submit"
          style={{
            height: 42,
            borderRadius: 10,
            border: `1px solid ${theme.accent}`,
            background: theme.accent,
            color: "#fff",
            padding: "0 16px",
            fontWeight: 600,
            cursor: "pointer",
          }}
        >
          Get Prediction
        </button>
      </form>

      <div style={{ marginTop: 14, color: result ? theme.text : theme.muted }}>
        {result ?? "Prediction will appear here."}
      </div>

      <div style={{ marginTop: 14, fontSize: 12, color: theme.muted }}>
        Notes: Uses ≥3 months of historical data and recent trends. Only high-confidence results will be shown in the final build.
      </div>
    </div>
  );
}

// US2.3 占位
function US23HistoricalPanel({ theme }) {
  const [filters, setFilters] = useState({ area: "" });
  const [status, setStatus] = useState("Enter a street to load data");
  const [data, setData] = useState(null);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFilters((s) => ({ ...s, [name]: value }));
  };

  const loadTrends = async () => {
    if (!filters.area.trim()) {
      setStatus("Please input a street name");
      return;
    }
    setStatus("Loading...");
    try {
      const resp = await fetch(`/api/historical_trends_data?street=${encodeURIComponent(filters.area)}`);
      const json = await resp.json();
      if (!resp.ok) {
        setStatus(json.error || "Error loading data");
        setData(null);
        return;
      }
      setData(json);
      setStatus(json.message);
    } catch (err) {
      setStatus("Network error: " + err.message);
    }
  };

  return (
    <div>
      <h2>US2.3 — Historical Availability Trends</h2>
      <input
        name="area"
        value={filters.area}
        onChange={handleChange}
        placeholder="e.g., Swanston Street"
        style={inputStyle(theme)}
      />
      <button onClick={loadTrends} style={{ marginLeft: 8, ...inputStyle(theme), height: 42 }}>
        Load Trends
      </button>
      <div style={{ marginTop: 10, color: theme.subtext }}>{status}</div>
      <pre style={{ marginTop: 10 }}>{data ? JSON.stringify(data, null, 2) : null}</pre>
    </div>
  );
}

function inputStyle(theme) {
  return {
    height: 42,
    padding: "0 12px",
    borderRadius: 10,
    border: `1px solid ${theme.border}`,
    background: "#fff",
    color: theme.text,
    outline: "none",
  };
}
