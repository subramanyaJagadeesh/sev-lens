CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE incidents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    service_name VARCHAR(255) NOT NULL,
    severity VARCHAR(50) NOT NULL,
    symptom TEXT NOT NULL,
    metric_name VARCHAR(255),
    metric_value VARCHAR(255),
    threshold_value VARCHAR(255),
    status VARCHAR(100) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT incidents_status_check CHECK (
        status IN (
            'CREATED',
            'QUEUED',
            'ANALYZING',
            'RECOMMENDATION_READY',
            'APPROVED',
            'REJECTED',
            'ESCALATED',
            'FAILED'
        )
    )
);

CREATE TABLE incident_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    incident_id UUID NOT NULL REFERENCES incidents(id),
    event_type VARCHAR(100) NOT NULL,
    message TEXT NOT NULL,
    payload JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT incident_events_type_check CHECK (
        event_type IN (
            'INCIDENT_CREATED',
            'ANALYSIS_QUEUED',
            'ANALYSIS_STARTED',
            'SEVERITY_CLASSIFIED',
            'LOGS_FETCHED',
            'METRICS_FETCHED',
            'DEPLOYMENT_CHECKED',
            'RUNBOOK_RETRIEVED',
            'RCA_RETRIEVED',
            'RECOMMENDATION_GENERATED',
            'HUMAN_APPROVED',
            'HUMAN_REJECTED',
            'HUMAN_ESCALATED',
            'ANALYSIS_FAILED'
        )
    )
);

CREATE INDEX incident_events_incident_id_idx ON incident_events (incident_id, created_at DESC);

CREATE TABLE incident_recommendations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    incident_id UUID NOT NULL REFERENCES incidents(id),
    summary TEXT NOT NULL,
    evidence JSONB NOT NULL,
    recommended_actions JSONB NOT NULL,
    confidence VARCHAR(50) NOT NULL,
    requires_human_approval BOOLEAN NOT NULL DEFAULT TRUE,
    raw_model_output JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT incident_recommendations_confidence_check CHECK (
        confidence IN ('low', 'medium', 'high')
    )
);

CREATE TABLE incident_decisions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    incident_id UUID NOT NULL REFERENCES incidents(id),
    decision VARCHAR(50) NOT NULL,
    decided_by VARCHAR(255) NOT NULL,
    note TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT incident_decisions_decision_check CHECK (
        decision IN ('APPROVE', 'REJECT', 'ESCALATE')
    )
);

CREATE INDEX incident_decisions_incident_id_idx ON incident_decisions (incident_id, created_at DESC);
CREATE INDEX incident_recommendations_incident_id_idx ON incident_recommendations (incident_id, created_at DESC);

CREATE TABLE incident_analysis_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    incident_id UUID NOT NULL REFERENCES incidents(id),
    scenario_id VARCHAR(255) NOT NULL,
    scenario_type VARCHAR(255) NOT NULL,
    trigger_type VARCHAR(100) NOT NULL,
    status VARCHAR(100) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    analysis_latency_ms INTEGER,
    retrieved_document_count INTEGER NOT NULL DEFAULT 0,
    expected_document_hit_rate DOUBLE PRECISION NOT NULL DEFAULT 0,
    evidence_count INTEGER NOT NULL DEFAULT 0,
    recommended_action_count INTEGER NOT NULL DEFAULT 0,
    confidence_value VARCHAR(50),
    human_decision_outcome VARCHAR(50),
    expected_evidence_signals JSONB NOT NULL DEFAULT '[]'::jsonb,
    expected_recommendation_direction VARCHAR(255) NOT NULL DEFAULT '',
    CONSTRAINT incident_analysis_runs_status_check CHECK (
        status IN ('QUEUED', 'ANALYZING', 'RECOMMENDATION_READY', 'FAILED')
    )
);

CREATE INDEX incident_analysis_runs_incident_id_idx ON incident_analysis_runs (incident_id, created_at DESC);
