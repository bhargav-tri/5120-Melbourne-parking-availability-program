import { useNavigate } from "react-router-dom";
import bgImage from "../assets/traffic_light.png";

export default function DataInsights() {
  const navigate = useNavigate();

  const backButtonStyle = {
    position: "absolute",
    top: "12px",          // 更贴顶
    right: "20px",
    fontSize: "2rem",
    color: "white",
    background: "rgba(0,0,0,0.3)",
    borderRadius: "50%",
    width: "40px",
    height: "40px",
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    cursor: "pointer",
    zIndex: 10,
  };

  const pageStyle = {
    minHeight: "100vh",
    backgroundImage: `url(${bgImage})`,
    backgroundSize: "cover",
    backgroundPosition: "center",
    backgroundRepeat: "no-repeat",
    // 贴顶：取消原来的 80px 顶部内边距；考虑刘海安全区
    padding: "0 20px 40px",
    paddingTop: "env(safe-area-inset-top, 0px)",
    fontFamily: "Inter, system-ui, sans-serif",
  };

  const cardContainer = {
    maxWidth: "1200px",
    margin: "0 auto",
    display: "grid",
    gridTemplateColumns: "1fr",
    gap: "24px",
  };

  const card = {
    background: "rgba(255,255,255,0.85)",
    color: "#111",
    borderRadius: 16,
    overflow: "hidden",
    boxShadow: "0 10px 30px rgba(0,0,0,0.3)",
  };

  const cardHeader = {
    padding: "16px 20px",
    borderBottom: "1px solid rgba(0,0,0,0.1)",
    color: "#111",
  };

  const cardBody = { padding: 0 };

  const meta = {
    padding: "10px 20px 16px",
    fontSize: 13,
    color: "#374151",
    display: "flex",
    gap: 16,
    flexWrap: "wrap",
  };

  const badge = {
    background: "rgba(0,0,0,0.05)",
    color: "#111",
    padding: "4px 8px",
    borderRadius: 999,
  };

  const iframeBox = {
    position: "relative",
    width: "100%",
    paddingBottom: "56.25%",
    background: "transparent",
  };

  const iframe = {
    position: "absolute",
    inset: 0,
    width: "100%",
    height: "100%",
    border: "0",
    backgroundColor: "transparent",
  };

  return (
    <div style={pageStyle}>
      {/* Back button */}
      <div style={backButtonStyle} onClick={() => navigate("/")}>←</div>

      {/* 标题贴顶：移除默认上外边距 */}
      <h1
        style={{
          textAlign: "center",
          margin: "0 0 8px 0",      // 顶部 margin 设为 0
          fontSize: "2.5rem",
          color: "white",
        }}
      >
        Parking & Traffic Insights
      </h1>
      <p
        style={{
          textAlign: "center",
          color: "#f3e7e7ff",
          margin: "0 0 28px 0",     // 同步去掉顶部 margin
          fontSize: "1.1rem",
        }}
      >
        EPIC 1.0 Visualisations: Vehicle Ownership Growth & Melbourne Population Trends
      </p>

      <div style={cardContainer}>
        {/* Vehicle Ownership Trends */}
        <div style={card}>
          <div style={cardHeader}>
            <h2 style={{ margin: 0, fontSize: 20 }}>Vehicle Ownership Trends</h2>
            <p style={{ margin: "6px 0 0", fontSize: 14 }}>
              Interactive chart showing car ownership growth over time. Hover to view exact figures.
            </p>
          </div>
          <div style={cardBody}>
            <div style={iframeBox}>
              <iframe title="Victoria Vehicle Trend" src="/victoria_car_animation.html" style={iframe} />
            </div>
            <div style={meta}>
              <span style={badge}>Source: VicRoads</span>
              <span style={badge}>Update: Annually</span>
            </div>
          </div>
        </div>

        {/* Population Growth */}
        <div style={card}>
          <div style={cardHeader}>
            <h2 style={{ margin: 0, fontSize: 20 }}>Population Growth (CBD)</h2>
            <p style={{ margin: "6px 0 0", fontSize: 14 }}>
              Chart displaying population growth over the past decade. Hover to see detailed values.
            </p>
          </div>
          <div style={cardBody}>
            <div style={iframeBox}>
              <iframe title="Melbourne Population Growth" src="/melbourne_population_animation.html" style={iframe} />
            </div>
            <div style={meta}>
              <span style={badge}>Source: ABS</span>
              <span style={badge}>Update: Census/yearly estimates</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
