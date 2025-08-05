import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Homepage from "./pages/Homepage";
import RealTimeParking from "./pages/RealTimeParking";
import DataInsights from "./pages/DataInsights";

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Homepage />} />
        <Route path="/real-time-parking" element={<RealTimeParking />} />
        <Route path="/data-insights" element={<DataInsights />} />
      </Routes>
    </Router>
  );
}

export default App;
