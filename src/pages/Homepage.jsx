import React from "react";
import melbourneBg from "../assets/melbourne.jpg";
import { useNavigate } from "react-router-dom";


export default function Homepage() {
  const navigate = useNavigate();

  

  const pageStyle = {
  backgroundImage: `url(${melbourneBg})`,
  backgroundSize: "cover",
  backgroundPosition: "center",
  height: "100vh",
  width: "100vw",
  color: "white",
  display: "flex",
  flexDirection: "column",
  justifyContent: "center",
  alignItems: "center",
  textAlign: "center",
  position: "relative",
  overflow: "hidden",
  fontFamily: "'Segoe UI', sans-serif",
};

const overlayStyle = {
  position: "absolute",
  top: 0,
  left: 0,
  width: "100%",
  height: "100%",
  backgroundColor: "rgba(0, 0, 0, 0.6)", // Darker overlay for better contrast
  zIndex: 1,
};

const navbarStyle = {
  position: "absolute",
  top: 0,
  left: 0,
  right: 0,
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
  padding: "20px 40px",
  zIndex: 2,
  backgroundColor: "rgba(0, 0, 0, 0.3)", // semi-transparent navbar background
  backdropFilter: "blur(6px)",
};

const navLinksStyle = {
  display: "flex",
  gap: "24px",
};

const linkStyle = {
  textDecoration: "none",
  color: "white",
  fontWeight: "600",
  fontSize: "1.1rem",
  position: "relative",
  padding: "6px 10px",
  transition: "color 0.3s ease",
};

const linkHoverStyle = {
  color: "#a3e635", // Light green on hover
};

const buttonStyle = {
  marginTop: "24px",
  padding: "12px 30px",
  backgroundColor: "#22c55e", // Tailwind green-500
  color: "white",
  border: "none",
  borderRadius: "30px",
  cursor: "pointer",
  fontSize: "1.1rem",
  fontWeight: "600",
  transition: "background-color 0.3s ease, transform 0.2s ease",
};

const buttonHoverStyle = {
  backgroundColor: "#16a34a", // Darker green
  transform: "scale(1.05)",
};

const contentStyle = {
  zIndex: 2,
  padding: "20px 30px",
  maxWidth: "600px",
  backgroundColor: "rgba(0, 0, 0, 0.4)",
  borderRadius: "16px",
  boxShadow: "0 4px 20px rgba(0,0,0,0.4)",
};



  return (
    <div style={pageStyle}>
      <div style={overlayStyle}></div>

      {/* 顶部左侧 Logo + 导航 */}
      <header style={navbarStyle}>
        <div style={{ fontSize: "1.8rem", fontWeight: "bold" }}>
          ECO - PARKING
        </div>
        <nav style={navLinksStyle}>
          {/* <a href="/real-time-parking" style={linkStyle}>
            Real-Time Parking
          </a>
          <a href="/data-insights" style={linkStyle}>
            Data Insights
          </a> */}
          <button style={buttonStyle} onClick={() => navigate("/real-time-parking")} >
            Real-Time Parking
          </button>

          <button style={buttonStyle} onClick={() => navigate("/data-insights")} >
            Data Insights
          </button>

        </nav>
      </header>

      {/* 中间宣传语 */}
      <div style={contentStyle}>
        <h1 style={{ fontSize: "3rem", fontWeight: "bold" }}>
          Melbourne - Make Parking Easy
        </h1>
        <button
  onClick={() => navigate("/real-time-parking")}
  style={{
    marginTop: "20px",
    padding: "10px 25px",
    backgroundColor: "#2b2be8",
    color: "white",
    border: "none",
    borderRadius: "25px",
    cursor: "pointer",
    fontSize: "1.1rem",
    fontWeight: "bold",
  }}
>
  Find Parking
</button>

      </div>
    </div>
  );
}
