from shared.contracts.incident_contracts import MockIncidentScenario


NOTIFICATION_SERVICE_KAFKA_TIMEOUT_SCENARIO = MockIncidentScenario(
    scenario_id="notification-service-kafka-timeout",
    service_name="notification-service",
    severity="P2",
    symptom="High error rate with KafkaTimeoutException",
    metric_name="error_rate",
    metric_value="18%",
    threshold_value="5%",
)

MOCK_INCIDENT_SCENARIOS = {
    NOTIFICATION_SERVICE_KAFKA_TIMEOUT_SCENARIO.scenario_id: NOTIFICATION_SERVICE_KAFKA_TIMEOUT_SCENARIO,
}

