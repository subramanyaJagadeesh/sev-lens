import { NavLink } from "react-router-dom";

function navClass({ isActive }: { isActive: boolean }) {
  return `button w-full justify-start ${isActive ? "button-primary" : "theme-toggle"}`;
}

export function Sidebar() {
  return (
    <aside className="flex h-full w-full flex-col overflow-hidden bg-[color:var(--surface)] p-5">
      <div>
        <p className="heading-eyebrow text-xs">OpsPulse</p>
        <h2 className="mt-2 text-2xl font-semibold">Incident Console</h2>
        <p className="mt-2 text-sm text-muted">Dashboard metrics, incident browsing, and live incident detail.</p>
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
      </nav>

      <div className="mt-auto rounded-2xl border border-[color:var(--border)] bg-[color:var(--surface-soft)] p-4">
        <p className="text-xs uppercase tracking-wide text-subtle">Workspace</p>
        <p className="mt-2 text-sm text-muted">Seeded notification-service incident flow</p>
      </div>
    </aside>
  );
}
