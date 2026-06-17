from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from shared.contract_store import fetch_contract_values, fetch_recommendation_schema


_contract_values = fetch_contract_values()

IncidentStatus = Enum(
    "IncidentStatus",
    {value: value for value in _contract_values["incident_statuses"]},
    type=str,
)

IncidentEventType = Enum(
    "IncidentEventType",
    {value: value for value in _contract_values["event_types"]},
    type=str,
)

DecisionType = Enum("DecisionType", {value: value for value in _contract_values["decision_types"]}, type=str)


INCIDENT_STATUSES = list(_contract_values["incident_statuses"])
EVENT_TYPES = list(_contract_values["event_types"])
DECISION_TYPES = list(_contract_values["decision_types"])

RECOMMENDATION_SCHEMA = fetch_recommendation_schema()


@dataclass(frozen=True)
class MockIncidentScenario:
    scenario_id: str
    service_name: str
    severity: str
    symptom: str
    metric_name: str
    metric_value: str
    threshold_value: str
