import { useNavigate } from "react-router-dom";

export default function DataInsights() {
  const navigate = useNavigate();

  const backButtonStyle = {
    position: "absolute",
    top: "20px",
    right: "30px",
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

  return (
    <div style={{ backgroundColor: "#444", height: "100vh", color: "white" }}>
      {/* 返回按钮 */}
      <div style={backButtonStyle} onClick={() => navigate("/")}>
        ←
      </div>

      <h1 style={{ paddingTop: "80px", textAlign: "center" }}>
        Parking & Traffic Insights
      </h1>
      <p style={{ textAlign: "center" }}>
        Explore data trends like car ownership and congestion over time.
      </p>
    </div>
  );
}

