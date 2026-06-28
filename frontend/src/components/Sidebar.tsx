import { NavLink } from "react-router-dom";
import { DashboardIcon, IncidentsIcon, KnowledgeIcon, RcaIcon } from "./NavIcons";

function navClass({ isActive }: { isActive: boolean }) {
  return `button w-full justify-start text-left ${isActive ? "button-primary" : "theme-toggle"}`;
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
          <DashboardIcon className="h-4 w-4" />
          <span className="flex-1">Dashboard</span>
        </NavLink>
        <NavLink to="/incidents" className={navClass}>
          <IncidentsIcon className="h-4 w-4" />
          <span className="flex-1">Incidents</span>
        </NavLink>
        <NavLink to="/knowledge" className={navClass}>
          <KnowledgeIcon className="h-4 w-4" />
          <span className="flex-1">Knowledge Base</span>
        </NavLink>
        <NavLink to="/rca-memory" className={navClass}>
          <RcaIcon className="h-4 w-4" />
          <span className="flex-1">RCA Memory</span>
        </NavLink>
      </nav>

    </aside>
  );
}
