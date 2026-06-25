import { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { AnalysisContextPanel } from "../components/AnalysisContextPanel";
import { AnalysisRunSelector } from "../components/AnalysisRunSelector";
import { DecisionButtons } from "../components/DecisionButtons";
import { EventDetailPanel } from "../components/EventDetailPanel";
import { EvaluationPanel } from "../components/EvaluationPanel";
import { IncidentHeader } from "../components/IncidentHeader";
import { LogEvidencePanel } from "../components/LogEvidencePanel";
import { PageHeader } from "../components/PageHeader";
import { RecommendationPanel } from "../components/RecommendationPanel";
import { useIncidentData } from "../contexts/IncidentDataContext";
import type { IncidentEvent } from "../contracts/incidentContracts";
import { getDefaultAnalysisRunId, getRunEvents, getSelectedAnalysisRun } from "../lib/analysisView";
import { formatStatusLabel } from "../lib/statusLabels";
import { useIncidentStream } from "../hooks/useIncidentStream";

function normalizeDecision(value: string | null | undefined) {
  return value === "APPROVE" || value === "REJECT" || value === "ESCALATE" ? value : null;
}

function getFailureMessage(events: IncidentEvent[]) {
  const failureEvent = events.find((event) => event.event_type === "ANALYSIS_FAILED" && event.payload && typeof event.payload === "object");
  if (failureEvent?.payload && typeof failureEvent.payload.error === "string") {
    return failureEvent.payload.error;
  }
  return "The analysis worker could not complete this incident.";
}

export function IncidentDetailsPage() {
  const navigate = useNavigate();
  const { incidentId } = useParams();
  const { getIncidentDetail, mergeStreamEvent, retryAnalysis, submitDecision, isLoading } = useIncidentData();
  const detail = incidentId ? getIncidentDetail(incidentId) : null;
  const analysisRuns = detail?.analysis_runs ?? [];
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null);
  const [isActionLoading, setIsActionLoading] = useState(false);
  const [isDecisionEditing, setIsDecisionEditing] = useState(false);

  const defaultRunId = useMemo(() => getDefaultAnalysisRunId(analysisRuns), [analysisRuns]);

  useEffect(() => {
    if (!analysisRuns.length) {
      setSelectedRunId(null);
      return;
    }
    setSelectedRunId((current) => {
      if (
        current &&
        analysisRuns.some((run) => run.analysis_run_id === current) &&
        (!defaultRunId || current === defaultRunId || (analysisRuns.find((run) => run.analysis_run_id === current)?.status ?? "") === "RECOMMENDATION_READY")
      ) {
        return current;
      }
      return defaultRunId;
    });
  }, [analysisRuns, defaultRunId]);

  const selectedRun = useMemo(
    () => getSelectedAnalysisRun(analysisRuns, selectedRunId),
    [analysisRuns, selectedRunId],
  );
  const latestRunId = analysisRuns.at(-1)?.analysis_run_id ?? null;
  const selectedRecommendation = selectedRun?.recommendation ?? (!analysisRuns.length ? detail?.recommendation ?? null : null);
  const selectedEvents = getRunEvents(selectedRun, detail?.events ?? []);
  const isSelectedRunFailed = selectedRun?.status === "FAILED";
  const isSelectedRunQueued = selectedRun?.status === "QUEUED" || selectedRun?.status === "ANALYZING";
  const isLiveRun = Boolean(selectedRun && selectedRun.analysis_run_id === latestRunId && isSelectedRunQueued);
  const timelineStateLabel = isLiveRun
    ? formatStatusLabel("LIVE")
    : isSelectedRunQueued
      ? formatStatusLabel("PAUSED")
      : selectedRun?.status === "FAILED"
        ? formatStatusLabel("FAILED")
        : formatStatusLabel("FINISHED");
  const failureMessage = getFailureMessage(selectedEvents);

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
        description="Live timeline, recommendation, analysis run history, and decisions for the selected incident."
        showBackButton
        onBack={() => navigate("/incidents")}
      />

      {detail ? (
        <>
          <IncidentHeader incident={detail.incident} />
          {analysisRuns.length > 1 ? (
            <AnalysisRunSelector
              runs={analysisRuns}
              selectedRunId={selectedRun?.analysis_run_id ?? null}
              defaultRunId={defaultRunId}
              onSelectRun={setSelectedRunId}
            />
          ) : null}

          <div className="grid gap-6 lg:grid-cols-[minmax(0,1.12fr)_minmax(0,0.88fr)]">
            <div className="min-w-0 space-y-4">
              <RecommendationPanel
                recommendation={selectedRecommendation}
                queued={isSelectedRunQueued}
                failed={isSelectedRunFailed}
                failureMessage={failureMessage}
              />
              <LogEvidencePanel analysisRun={selectedRun} />
              <AnalysisContextPanel analysisRun={selectedRun} />

              {isSelectedRunFailed ? (
                <div className="panel rounded-2xl p-5">
                  <h3 className="mb-3 text-lg font-semibold">Analysis failed</h3>
                  <p className="text-sm text-muted">{failureMessage}</p>
                  <button
                    type="button"
                    disabled={isActionLoading}
                    className="button button-warning mt-4"
                    onClick={() => {
                      setIsActionLoading(true);
                      void retryAnalysis(incidentId).finally(() => {
                        setIsActionLoading(false);
                        setIsDecisionEditing(false);
                      });
                    }}
                  >
                    Retry analysis
                  </button>
                </div>
              ) : selectedRecommendation ? (
                <div className="panel rounded-2xl p-5">
                  <h3 className="mb-3 text-lg font-semibold">Decision</h3>
                  <DecisionButtons
                    disabled={isActionLoading}
                    currentDecision={normalizeDecision(detail.incident.approval_status)}
                    editing={isDecisionEditing}
                    onBeginChange={() => setIsDecisionEditing(true)}
                    onDecision={(decision) => {
                      setIsActionLoading(true);
                      void submitDecision(incidentId, decision).finally(() => {
                        setIsActionLoading(false);
                        setIsDecisionEditing(false);
                      });
                    }}
                  />
                </div>
              ) : (
                <div className="panel rounded-2xl p-5">
                  <h3 className="mb-3 text-lg font-semibold">Decision</h3>
                  <p className="text-sm text-muted">Decision actions will appear once the selected run has a recommendation.</p>
                </div>
              )}
            </div>

            <div className="min-w-0 space-y-4">
              <EventDetailPanel
                events={selectedEvents}
                stateLabel={timelineStateLabel}
                title="Selected run timeline"
                description="Events recorded for the currently selected analysis attempt."
              />
              <EvaluationPanel analysisRun={selectedRun} />
            </div>
          </div>
        </>
      ) : (
        <div className="panel rounded-2xl p-6 text-muted">Loading incident detail…</div>
      )}
    </div>
  );
}
