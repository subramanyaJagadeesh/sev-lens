import { useCallback, useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { DecisionButtons } from "../components/DecisionButtons";
import { EventDetailPanel } from "../components/EventDetailPanel";
import { IncidentHeader } from "../components/IncidentHeader";
import { PageHeader } from "../components/PageHeader";
import { RecommendationPanel } from "../components/RecommendationPanel";
import { useIncidentData } from "../contexts/IncidentDataContext";
import { useIncidentStream } from "../hooks/useIncidentStream";
import type { IncidentEvent } from "../contracts/incidentContracts";

function normalizeDecision(value: string | null | undefined) {
  return value === "APPROVE" || value === "REJECT" || value === "ESCALATE" ? value : null;
}

export function IncidentDetailsPage() {
  const navigate = useNavigate();
  const { incidentId } = useParams();
  const { getIncidentDetail, mergeStreamEvent, submitDecision, isLoading } = useIncidentData();
  const detail = incidentId ? getIncidentDetail(incidentId) : null;
  const [isActionLoading, setIsActionLoading] = useState(false);
  const [isDecisionEditing, setIsDecisionEditing] = useState(false);

  useEffect(() => {
    setIsDecisionEditing(!detail?.incident.approval_status);
  }, [detail, incidentId]);

  const handleStreamEvent = useCallback(
    (event: IncidentEvent) => {
      mergeStreamEvent(event);
    },
    [mergeStreamEvent],
  );

  useIncidentStream(incidentId ?? null, Boolean(detail), handleStreamEvent);

  if (!incidentId) {
    return (
      <div className="space-y-6">
        <PageHeader title="Incident details" description="Open an incident from the incidents page." />
        <div className="panel rounded-2xl p-6 text-muted">No incident selected.</div>
      </div>
    );
  }

  if (!detail && !isLoading) {
    return (
      <div className="space-y-6">
        <PageHeader
          title="Incident details"
          description="The requested incident could not be found."
          actions={
            <button type="button" className="button theme-toggle" onClick={() => navigate("/incidents")}>
              Back to incidents
            </button>
          }
        />
        <div className="panel rounded-2xl p-6 text-muted">Incident not found.</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Incident details"
        description="Live timeline, recommendation, and decisions for the selected incident."
        showBackButton
        onBack={() => navigate("/incidents")}
      />

      {detail ? (
        <>
          <IncidentHeader incident={detail.incident} />
          <div className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
            <EventDetailPanel detail={detail} live />
            <div className="space-y-4">
              <RecommendationPanel recommendation={detail.recommendation} />
              <div className="panel rounded-2xl p-5">
                <h3 className="mb-3 text-lg font-semibold">Decision</h3>
                {normalizeDecision(detail.incident.approval_status) ? (
                  <p className="mb-4 text-sm text-muted">
                    Current decision: <span className="text-strong">{detail.incident.approval_status}</span>
                  </p>
                ) : null}
                <DecisionButtons
                  disabled={isActionLoading}
                  currentDecision={normalizeDecision(detail.incident.approval_status)}
                  editing={isDecisionEditing}
                  onBeginChange={() => setIsDecisionEditing(true)}
                  onCancelChange={() => setIsDecisionEditing(false)}
                  onDecision={(decision) => {
                    setIsActionLoading(true);
                    void submitDecision(incidentId, decision).finally(() => {
                      setIsActionLoading(false);
                      setIsDecisionEditing(false);
                    });
                  }}
                />
              </div>
            </div>
          </div>
        </>
      ) : (
        <div className="panel rounded-2xl p-6 text-muted">Loading incident detail…</div>
      )}
    </div>
  );
}
