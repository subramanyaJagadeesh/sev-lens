import { useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { DashboardCharts } from "../components/DashboardCharts";
import { IncidentList } from "../components/IncidentList";
import { PageHeader } from "../components/PageHeader";
import { useIncidentData } from "../contexts/IncidentDataContext";
import { useTheme } from "../contexts/ThemeContext";
import { buildEventRecords } from "../contracts/eventView";
import { sortByCreatedAtDesc } from "../lib/incidentHelpers";

export function DashboardPage() {
  const navigate = useNavigate();
  const { incidents, incidentDetailsById, isLoading, error } = useIncidentData();
  const { theme } = useTheme();

  const eventRecords = useMemo(() => buildEventRecords(Object.values(incidentDetailsById)), [incidentDetailsById]);

  const metrics = useMemo(() => {
    const totalIncidents = incidents.length;
    const totalEvents = eventRecords.length;
    const openIncidents = incidents.filter((incident) => incident.status !== "APPROVED" && incident.status !== "REJECTED").length;
    const recommendationReady = incidents.filter((incident) => incident.recommendation_status === "READY").length;
    return { totalIncidents, totalEvents, openIncidents, recommendationReady };
  }, [eventRecords.length, incidents]);

  const recentIncidents = useMemo(() => [...incidents].sort(sortByCreatedAtDesc).slice(0, 5), [incidents]);

  return (
    <div className="space-y-6">
      <PageHeader title="Dashboard" description="Charts and the latest incidents from the seeded scenario." />

      {error ? <div className="panel panel-danger rounded-2xl p-4">{error}</div> : null}
      {isLoading ? <div className="panel rounded-2xl p-6 text-muted">Loading dashboard…</div> : null}

      {!isLoading ? (
        <>
          <div className="grid gap-4 md:grid-cols-4">
            <div className="panel rounded-2xl p-4">
              <p className="text-xs uppercase tracking-wide text-subtle">Incidents</p>
              <p className="mt-2 text-3xl font-semibold">{metrics.totalIncidents}</p>
            </div>
            <div className="panel rounded-2xl p-4">
              <p className="text-xs uppercase tracking-wide text-subtle">Events</p>
              <p className="mt-2 text-3xl font-semibold">{metrics.totalEvents}</p>
            </div>
            <div className="panel rounded-2xl p-4">
              <p className="text-xs uppercase tracking-wide text-subtle">Open incidents</p>
              <p className="mt-2 text-3xl font-semibold">{metrics.openIncidents}</p>
            </div>
            <div className="panel rounded-2xl p-4">
              <p className="text-xs uppercase tracking-wide text-subtle">Ready</p>
              <p className="mt-2 text-3xl font-semibold">{metrics.recommendationReady}</p>
            </div>
          </div>

          <DashboardCharts incidents={incidents} events={eventRecords} theme={theme} />

          <div className="panel rounded-2xl p-5">
            <div className="mb-4">
              <h2 className="text-sm font-semibold uppercase tracking-wide text-subtle">Most recent incidents</h2>
              <p className="mt-1 text-sm text-muted">The latest incidents across the seeded scenario.</p>
            </div>
            <IncidentList
              incidents={recentIncidents}
              selectedIncidentId={null}
              onSelectIncident={(incidentId) => navigate(`/incidents/${incidentId}`)}
            />
          </div>
        </>
      ) : null}
    </div>
  );
}
