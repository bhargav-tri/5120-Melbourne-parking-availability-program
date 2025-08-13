import { useNavigate } from "react-router-dom";
import { useMemo, useState, useCallback, useEffect } from "react";

export default function RealTimeParking() {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState("us2.1"); // "us2.1" | "daily"

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
    { id: "daily", label: " Daily-Tends" },
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
    [activeTab, tabs]
  );

  useEffect(() => window.scrollTo(0, 0), []);

  return (
    <div style={{ background: theme.bg, minHeight: "100vh", color: theme.text }}>
      {/* 返回主页按钮 */}
      <div
        style={backButtonStyle}
        onClick={() => navigate("/")}
        title="Back to Home"
        role="button"
        aria-label="Back"
      >
        ←
      </div>

      {/* 标题 + 顶部按钮 */}
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

      {/* 内容区：us2.1 还是实时地图；daily 以 iframe 全屏嵌入 Flask 页 */}
      {activeTab === "us2.1" ? (
        <US21RealTimePanel theme={theme} />
      ) : (
        <main
          style={{
            width: "100vw", // 左右铺满
            marginLeft: "calc(50% - 50vw)", // 消除左右边距
            padding: 0,
          }}
        >
          <section
            style={{
              background: theme.panel,
              border: "none",
              borderRadius: 0,
              boxShadow: "none",
              height: "calc(100vh - 150px)", // 预留上方标题/按钮高度
              padding: 0,
              overflow: "hidden",
            }}
          >
            <iframe
              title="Daily & Trends"
              src="http://127.0.0.1:5000/"
              style={{ width: "100%", height: "100%", border: 0 }}
            />
          </section>
        </main>
      )}
    </div>
  );
}

/* ---------------- US2.1 实时地图 ---------------- */
function US21RealTimePanel({ theme }) {
  return (
    <section aria-label="Real-time map" style={{ marginTop: 8 }}>
      <div
        style={{
          maxWidth: 1100,
          margin: "0 auto",
          padding: "0 16px",
          color: theme.subtext,
        }}
      >
        <h2 style={{ marginTop: 6, marginBottom: 4, color: "#111" }}>
          {/* 可留空或写一句说明 */}
        </h2>
        <p style={{ marginTop: 0 }}>
          Live map of legal public/commercial spots with availability status (green / yellow / red).
        </p>
      </div>

      {/* 地图横向铺满 */}
      <div
        style={{
          width: "100vw",
          marginLeft: "calc(50% - 50vw)",
          marginTop: 12,
        }}
      >
        <div
          style={{
            height: "calc(100vh - 260px)",
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
