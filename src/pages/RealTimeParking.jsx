import { useNavigate } from "react-router-dom";
import { useMemo, useState, useCallback, useEffect } from "react";

export default function RealTimeParking() {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState("us2.1");


const theme = useMemo(
  () => ({
    bg: "#ffffff",         
    panel: "#ffffff",      
    text: "#000000",       
    subtext: "#555555",    
    accent: "#007BFF",     
    accentHover: "#339BFF",
    muted: "#888888",
    border: "rgba(0,0,0,0.12)",
    shadow: "0 4px 20px rgba(0,0,0,0.1)",
    radius: "12px",
  }),
  []
);


  const tabs = [
    { id: "us2.1", label: "US2.1  Find Parking (Real‑time)" },
    { id: "us2.2", label: "US2.2  Predicted Availability" },
    { id: "us2.3", label: "US2.3  Historical Trends" },
  ];

  const backButtonStyle = {
    position: "absolute",
    top: "20px",
    right: "30px",
    fontSize: "2rem",
    color: theme.text,
    background: "rgba(255,255,255,0.08)",
    borderRadius: "50%",
    width: "44px",
    height: "44px",
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    cursor: "pointer",
    zIndex: 10,
    backdropFilter: "blur(6px)",
    border: `1px solid ${theme.border}`,
  };

  // 键盘左右方向键切换
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
    [activeTab, tabs]
  );

  useEffect(() => {
    window.scrollTo(0, 0);
  }, []);

  return (
    <div style={{ backgroundColor: theme.bg, minHeight: "100vh", color: theme.text }}>
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

      {/* 标题区 */}
      <header
        style={{
          paddingTop: 80,
          paddingBottom: 18,
          textAlign: "center",
          maxWidth: 1100,
          margin: "0 auto",
          paddingLeft: 16,
          paddingRight: 16,
        }}
      >
        <h1 style={{ margin: 0, letterSpacing: 0.5 }}>Real‑Time Parking</h1>
        <p style={{ marginTop: 8, color: theme.subtext }}>
          Explore real‑time parking, predictions, and historical trends for Melbourne CBD.
        </p>

        {/* 导航按钮 */}
        <nav
          aria-label="Parking features"
          onKeyDown={onKeyDownTabs}
          style={{
            display: "flex",
            gap: 10,
            justifyContent: "center",
            flexWrap: "wrap",
            marginTop: 18,
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
                  background: active ? theme.accent : "transparent",
                  color: active ? "#121212" : theme.text,
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

      {/* 内容区 */}
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
          {activeTab === "us2.1" && <US21RealTimePanel theme={theme} />}
          {activeTab === "us2.2" && <US22PredictivePanel theme={theme} />}
          {activeTab === "us2.3" && <US23HistoricalPanel theme={theme} />}
        </section>
      </main>
    </div>
  );
}

/* ---------------- 面板组件 ---------------- */

// US2.1 实时停车：嵌入已生成的 HTML（该 HTML 内部自带刷新逻辑）
function US21RealTimePanel({ theme }) {
  return (
    <div>
      <h2 style={{ marginTop: 6, marginBottom: 4 }}>US2.1 — Find Available Parking (Real‑time)</h2>
      <p style={{ color: theme.subtext, marginTop: 0 }}>
        Live map of legal public/commercial spots with availability status (green / yellow / red).
      </p>

      <div
        style={{
          marginTop: 16,
          height: "78vh",
          borderRadius: 12,
          overflow: "hidden",
          border: `1px solid ${theme.border}`,
          background:
            "linear-gradient(135deg, rgba(255,255,255,0.03) 0%, rgba(255,255,255,0.06) 100%)",
        }}
      >
        <iframe
          title="Live Parking Map"
          // 确保 HTML 位于 public/maps/latest_parking_map_live.html
          src="/maps/latest_parking_map_live.html"
          style={{ width: "100%", height: "100%", border: "0" }}
          allow="fullscreen"
        />
      </div>
    </div>
  );
}

// US2.2 预测可用性（浅色表单 + 高对比按钮）
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
          <label style={{ color: theme.muted, fontSize: 12, marginBottom: 6 }}>
            Location / Street
          </label>
          <input
            name="location"
            value={form.location}
            onChange={handleChange}
            placeholder="e.g., Collins St"
            style={{
              ...inputStyle(theme),
              background: "#ffffff",
              color: theme.text,
              borderColor: theme.border,
            }}
          />
        </div>

        <div style={{ display: "grid" }}>
          <label style={{ color: theme.muted, fontSize: 12, marginBottom: 6 }}>Date</label>
          <input
            name="date"
            type="date"
            value={form.date}
            onChange={handleChange}
            style={{
              ...inputStyle(theme),
              background: "#ffffff",
              color: theme.text,
              borderColor: theme.border,
            }}
          />
        </div>

        <div style={{ display: "grid" }}>
          <label style={{ color: theme.muted, fontSize: 12, marginBottom: 6 }}>Time</label>
          <input
            name="time"
            type="time"
            value={form.time}
            onChange={handleChange}
            style={{
              ...inputStyle(theme),
              background: "#ffffff",
              color: theme.text,
              borderColor: theme.border,
            }}
          />
        </div>

        <button
          type="submit"
          style={{
            height: 42,
            borderRadius: 10,
            border: `1px solid ${theme.accent}`,
            background: theme.accent,
            color: "#ffffff",
            padding: "0 16px",
            fontWeight: 600,
            cursor: "pointer",
            transition: "background .15s ease, box-shadow .15s ease",
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.background = theme.accentHover || theme.accent;
            e.currentTarget.style.boxShadow = "0 6px 16px rgba(0,0,0,0.1)";
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = theme.accent;
            e.currentTarget.style.boxShadow = "none";
          }}
        >
          Get Prediction
        </button>
      </form>

      <div style={{ marginTop: 14, color: result ? theme.text : theme.muted }}>
        {result ?? "Prediction will appear here."}
      </div>

      <div style={{ marginTop: 14, fontSize: 12, color: theme.muted }}>
        Notes: Uses ≥3 months of historical data and recent trends. Only high‑confidence results will be shown in the final build.
      </div>
    </div>
  );
}


// US2.3 历史趋势（占位）
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
    background: "#ffffffff",
    color: theme.text,
    outline: "none",
  };
}
