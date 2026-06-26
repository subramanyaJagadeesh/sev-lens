import { NavLink } from "react-router-dom";

function navClass({ isActive }: { isActive: boolean }) {
  return `button w-full justify-start ${isActive ? "button-primary" : "theme-toggle"}`;
}

export function Sidebar() {
  return (
    <aside className="flex h-full w-full flex-col overflow-hidden bg-[color:var(--surface)] p-5">
      <div>
        <p className="heading-eyebrow text-xs">SevLens</p>
        <h2 className="mt-2 text-2xl font-semibold">Incident Intelligence</h2>
        <p className="mt-2 text-sm text-muted">Live metrics, incidents, knowledge, and RCA memory.</p>
      </div>

      <nav className="mt-6 space-y-2">
        <NavLink to="/" end className={navClass}>
          <span aria-hidden="true">🏠</span>
          <span>Dashboard</span>
        </NavLink>
        <NavLink to="/incidents" className={navClass}>
          <span aria-hidden="true">📋</span>
          <span>Incidents</span>
        </NavLink>
        <NavLink to="/knowledge" className={navClass}>
          <span aria-hidden="true">📚</span>
          <span>Knowledge Base</span>
        </NavLink>
        <NavLink to="/rca-memory" className={navClass}>
          <span aria-hidden="true">🧠</span>
          <span>RCA Memory</span>
        </NavLink>
      </nav>

    </aside>
  );
}
