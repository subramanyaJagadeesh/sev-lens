import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { fetchContracts } from "../api";
import { IncidentList } from "../components/IncidentList";
import { PageHeader } from "../components/PageHeader";
import { Select } from "../components/forms/Select";
import { TriggerIncidentButton } from "../components/TriggerIncidentButton";
import { useIncidentData } from "../contexts/IncidentDataContext";
import type { ScenarioRecord } from "../contracts/incidentContracts";
import { sortByCreatedAtDesc } from "../lib/incidentHelpers";
import { formatStatusLabel } from "../lib/statusLabels";

export function IncidentsPage() {
  const navigate = useNavigate();
  const { incidents, isLoading, error, triggerIncident } = useIncidentData();
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [severityFilter, setSeverityFilter] = useState("ALL");
  const [isTriggering, setIsTriggering] = useState(false);
  const [scenarioOptions, setScenarioOptions] = useState<ScenarioRecord[]>([]);
  const [selectedScenarioId, setSelectedScenarioId] = useState("notification-service-kafka-timeout");

  useEffect(() => {
    let cancelled = false;
    void fetchContracts()
      .then((contracts) => {
        if (cancelled) {
          return;
        }
        setScenarioOptions(contracts.incident_scenarios);
        const defaultScenario = contracts.incident_scenarios.find((scenario) => scenario.is_default);
        setSelectedScenarioId(defaultScenario?.scenario_id ?? contracts.incident_scenarios[0]?.scenario_id ?? "notification-service-kafka-timeout");
      })
      .catch(() => undefined);
    return () => {
      cancelled = true;
    };
  }, []);

  const severityOptions = useMemo(() => {
    const values = new Set(incidents.map((incident) => incident.severity).filter(Boolean));
    return ["ALL", ...Array.from(values).sort()];
  }, [incidents]);

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
      const created = await triggerIncident(selectedScenarioId);
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
      />

      {error ? <div className="panel panel-danger rounded-2xl p-4">{error}</div> : null}
      {isLoading ? <div className="panel rounded-2xl p-6 text-muted">Loading incidents…</div> : null}

      {!isLoading ? (
        <div className="panel rounded-2xl p-5">
          <div className="mb-4 grid gap-3">
            <div className="grid gap-3 md:grid-cols-[1fr_auto]">
              <label className="space-y-2 text-sm">
                <span className="text-subtle">Scenario</span>
                <Select
                  value={selectedScenarioId}
                  onChange={setSelectedScenarioId}
                  options={scenarioOptions.map((scenario) => ({
                    value: scenario.scenario_id,
                    label: scenario.label,
                  }))}
                />
              </label>
              <div className="flex items-end">
                <TriggerIncidentButton disabled={isTriggering} onTrigger={handleTriggerIncident} />
              </div>
            </div>
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
                <Select
                  value={statusFilter}
                  onChange={setStatusFilter}
                  options={[
                    { value: "ALL", label: "All statuses" },
                    { value: "QUEUED", label: formatStatusLabel("QUEUED") },
                    { value: "ANALYZING", label: formatStatusLabel("ANALYZING") },
                    { value: "RECOMMENDATION_READY", label: formatStatusLabel("RECOMMENDATION_READY") },
                    { value: "APPROVED", label: formatStatusLabel("APPROVED") },
                    { value: "REJECTED", label: formatStatusLabel("REJECTED") },
                    { value: "ESCALATED", label: formatStatusLabel("ESCALATED") },
                  ]}
                />
              </label>
              <label className="space-y-2 text-sm">
                <span className="text-subtle">Severity</span>
                <Select
                  value={severityFilter}
                  onChange={setSeverityFilter}
                  options={[
                    { value: "ALL", label: "All severities" },
                    ...severityOptions
                      .filter((severity) => severity !== "ALL")
                      .map((severity) => ({
                        value: severity,
                        label: severity,
                      })),
                  ]}
                />
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
