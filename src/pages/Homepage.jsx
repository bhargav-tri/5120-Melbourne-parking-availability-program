import React from "react";
import melbourneBg from "../assets/melbourne.jpg";

export default function Homepage() {
  const pageStyle = {
    backgroundImage: `url(${melbourneBg})`,
    backgroundSize: "cover",
    backgroundPosition: "center",
    height: "100vh",
    color: "white",
    display: "flex",
    flexDirection: "column",
    justifyContent: "center",
    alignItems: "center",
    textAlign: "center",
    position: "relative",
  };

  const overlayStyle = {
    position: "absolute",
    top: 0,
    left: 0,
    width: "100%",
    height: "100%",
    backgroundColor: "rgba(0,0,0,0.4)",
    zIndex: 1,
  };

  const navbarStyle = {
    position: "absolute",
    top: 0,
    left: 0,
    display: "flex",
    flexDirection: "column", // 纵向排列
    alignItems: "flex-start", // 靠左
    padding: "20px 40px",
    zIndex: 2,
  };

  const navLinksStyle = {
    display: "flex",
    gap: "30px",
    marginTop: "8px", // Logo 和导航之间的间距
  };

  const linkStyle = {
    textDecoration: "none",
    color: "white",
    fontWeight: "bold",
    fontSize: "1.2rem",
    whiteSpace: "nowrap",
  };

  const contentStyle = {
    zIndex: 2,
  };

  return (
    <div style={pageStyle}>
      <div style={overlayStyle}></div>

      {/* 顶部左侧 Logo + 导航 */}
      <header style={navbarStyle}>
        <div style={{ fontSize: "1.8rem", fontWeight: "bold" }}>
          MELBOURNE PARKING
        </div>
        <nav style={navLinksStyle}>
          <a href="/real-time-parking" style={linkStyle}>
            Real-Time Parking
          </a>
          <a href="/data-insights" style={linkStyle}>
            Data Insights
          </a>
        </nav>
      </header>

      {/* 中间宣传语 */}
      <div style={contentStyle}>
        <h1 style={{ fontSize: "3rem", fontWeight: "bold" }}>
          Melbourne - Make Park Easy
        </h1>
        <button
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
