import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';
import Homepage from './pages/Homepage';
import RealTimeParking from './pages/RealTimeParking';
import DataInsights from './pages/DataInsights';

ReactDOM.createRoot(document.getElementById('root')).render(
  <BrowserRouter>
    <nav>
      <Link to="/">Home</Link> |{" "}
      <Link to="/real-time-parking">Real-Time Parking</Link> |{" "}
      <Link to="/data-insights">Data Insights</Link>
    </nav>
    <Routes>
      <Route path="/" element={<Homepage />} />
      <Route path="/real-time-parking" element={<RealTimeParking />} />
      <Route path="/data-insights" element={<DataInsights />} />
    </Routes>
  </BrowserRouter>
);
