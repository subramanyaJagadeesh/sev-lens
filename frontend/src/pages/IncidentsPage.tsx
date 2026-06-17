import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { IncidentList } from "../components/IncidentList";
import { PageHeader } from "../components/PageHeader";
import { TriggerIncidentButton } from "../components/TriggerIncidentButton";
import { useIncidentData } from "../contexts/IncidentDataContext";
import { sortByCreatedAtDesc } from "../lib/incidentHelpers";

export function IncidentsPage() {
  const navigate = useNavigate();
  const { incidents, isLoading, error, triggerIncident } = useIncidentData();
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [severityFilter, setSeverityFilter] = useState("ALL");
  const [isTriggering, setIsTriggering] = useState(false);

  const filteredIncidents = useMemo(() => {
    const search = searchTerm.trim().toLowerCase();
    return [...incidents]
      .filter((incident) => {
        if (statusFilter !== "ALL" && incident.status !== statusFilter) {
          return false;
        }
        if (severityFilter !== "ALL" && incident.severity !== severityFilter) {
          return false;
        }
        if (!search) {
          return true;
        }
        return (
          incident.service_name.toLowerCase().includes(search) ||
          incident.symptom.toLowerCase().includes(search) ||
          incident.status.toLowerCase().includes(search) ||
          incident.severity.toLowerCase().includes(search)
        );
      })
      .sort(sortByCreatedAtDesc);
  }, [incidents, searchTerm, severityFilter, statusFilter]);

  const handleTriggerIncident = async () => {
    setIsTriggering(true);
    try {
      const created = await triggerIncident();
      navigate(`/incidents/${created.incident_id}`);
    } finally {
      setIsTriggering(false);
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Incidents"
        description="Search, filter, and open an incident to view its detail page."
        actions={<TriggerIncidentButton disabled={isTriggering} onTrigger={handleTriggerIncident} />}
      />

      {error ? <div className="panel panel-danger rounded-2xl p-4">{error}</div> : null}
      {isLoading ? <div className="panel rounded-2xl p-6 text-muted">Loading incidents…</div> : null}

      {!isLoading ? (
        <div className="panel rounded-2xl p-5">
          <div className="mb-4 grid gap-3">
            <input
              type="search"
              value={searchTerm}
              onChange={(event) => setSearchTerm(event.target.value)}
              placeholder="Search service, symptom, status, or severity"
              className="input"
            />
            <div className="grid gap-3 md:grid-cols-2">
              <label className="space-y-2 text-sm">
                <span className="text-subtle">Status</span>
                <select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)} className="input">
                  <option value="ALL">All statuses</option>
                  <option value="ANALYZING">Analyzing</option>
                  <option value="RECOMMENDED">Recommended</option>
                  <option value="APPROVED">Approved</option>
                  <option value="REJECTED">Rejected</option>
                  <option value="ESCALATED">Escalated</option>
                </select>
              </label>
              <label className="space-y-2 text-sm">
                <span className="text-subtle">Severity</span>
                <select value={severityFilter} onChange={(event) => setSeverityFilter(event.target.value)} className="input">
                  <option value="ALL">All severities</option>
                  <option value="LOW">Low</option>
                  <option value="MEDIUM">Medium</option>
                  <option value="HIGH">High</option>
                  <option value="CRITICAL">Critical</option>
                </select>
              </label>
            </div>
          </div>

          <IncidentList
            incidents={filteredIncidents}
            selectedIncidentId={null}
            onSelectIncident={(incidentId) => navigate(`/incidents/${incidentId}`)}
          />
        </div>
      ) : null}
    </div>
  );
}
