from __future__ import annotations

from shared.contract_store import fetch_incident_scenarios


MOCK_INCIDENT_SCENARIOS = {
    str(record["scenario_id"]): record for record in fetch_incident_scenarios()
}
