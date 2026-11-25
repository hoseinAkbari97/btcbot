import { NavLink, Route, Routes } from "react-router-dom";

import { Dashboard } from "./pages/Dashboard";
import { Experiments } from "./pages/Experiments";

export default function App() {
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <span className="brand-icon">BQ</span>
          <div>
            <strong>BTC QUANT</strong>
            <span>RESEARCH TERMINAL</span>
          </div>
        </div>
        <nav aria-label="Primary navigation">
          <span className="nav-label">WORKSPACE</span>
          <NavLink
            to="/"
            end
            className={({ isActive }) => `nav-button${isActive ? " selected" : ""}`}
          >
            <i>◈</i>
            <span>Market overview</span>
          </NavLink>
          <NavLink
            to="/experiments"
            className={({ isActive }) => `nav-button${isActive ? " selected" : ""}`}
          >
            <i>⚗</i>
            <span>Experiments</span>
          </NavLink>
        </nav>
        <div className="sidebar-footer">
          <span className="pulse" />
          LOCAL RESEARCH
          <small>NO LIVE EXECUTION</small>
        </div>
      </aside>
      <div className="workspace-host">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/experiments" element={<Experiments />} />
        </Routes>
      </div>
    </div>
  );
}
