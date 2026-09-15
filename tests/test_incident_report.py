"""
tests/test_incident_report.py
=============================
Madde 55(1)(c) ciddi olay bildirim formatı testleri.
"""

import pytest

from dumen.core.types import RiskCategory
from dumen.reports.incident_report import (
    IncidentReportGenerator,
    IncidentSeverity,
    SeriousIncident,
)


@pytest.fixture()
def gen() -> IncidentReportGenerator:
    return IncidentReportGenerator()


class TestIncidentCreation:
    def test_create_incident_fields(self, gen):
        inc = gen.create_incident(
            risk_category=RiskCategory.JAILBREAK,
            severity=IncidentSeverity.HIGH,
            description="Multi-turn PAIR attack elicited unrefused synthetic hazard output.",
            affected_model="target-llm",
            detection_module="JudgeEvaluator",
            steering_intervention_applied=True,
            containment_actions=["Vector re-mined", "Threshold raised"],
        )
        assert isinstance(inc, SeriousIncident)
        assert inc.incident_id.startswith("DUMEN-INC-")
        assert inc.risk_category == RiskCategory.JAILBREAK
        assert inc.severity == IncidentSeverity.HIGH
        assert inc.reportable_to_office is True
        assert len(inc.containment_actions) == 2

    def test_severity_threshold_gate(self, gen):
        """Yalnız HIGH/CRITICAL AI Office'e bildirilebilir olmalı."""
        low = gen.create_incident(
            risk_category=RiskCategory.PII_LEAK,
            severity=IncidentSeverity.LOW,
            description="Minor PII near-miss contained by gateway filter.",
            affected_model="m",
            detection_module="GatewayValidator",
            steering_intervention_applied=False,
        )
        assert low.reportable_to_office is False

        medium = gen.create_incident(
            risk_category=RiskCategory.DECEPTION,
            severity=IncidentSeverity.MEDIUM,
            description="Deceptive framing attempt, refused by validator agent.",
            affected_model="m",
            detection_module="DualAgentValidator",
            steering_intervention_applied=False,
        )
        assert medium.reportable_to_office is False

        critical = gen.create_incident(
            risk_category=RiskCategory.CYBER_ATTACK,
            severity=IncidentSeverity.CRITICAL,
            description="Autonomous cyber planning output escaped gateway filter.",
            affected_model="m",
            detection_module="SAEInspector",
            steering_intervention_applied=True,
        )
        assert critical.reportable_to_office is True

    def test_rejects_short_description(self, gen):
        with pytest.raises(ValueError):
            gen.create_incident(
                risk_category=RiskCategory.JAILBREAK,
                severity=IncidentSeverity.HIGH,
                description="kısa",
                affected_model="m",
                detection_module="x",
                steering_intervention_applied=False,
            )


class TestOfficeNotification:
    def test_notification_format(self, gen):
        inc = gen.create_incident(
            risk_category=RiskCategory.SANDBOX_ESCAPE,
            severity=IncidentSeverity.HIGH,
            description="Sandboxed agent attempted path traversal via file-write tool.",
            affected_model="agent-llm",
            detection_module="OVCircuitMask",
            steering_intervention_applied=True,
            containment_actions=["Sandbox policy hardened", "Tool permission revoked"],
        )
        notif = gen.to_office_notification(inc)
        assert "SERIOUS INCIDENT NOTIFICATION" in notif
        assert "Article 55(1)(c)" in notif
        assert "agent-llm" in notif
        assert "APPLIED ✅" in notif
        assert "Sandbox policy hardened" in notif
        assert inc.incident_id in notif

    def test_non_reportable_incident_rejected(self, gen):
        """LOW olay için bildirim üretimi reddedilmeli."""
        inc = gen.create_incident(
            risk_category=RiskCategory.PII_LEAK,
            severity=IncidentSeverity.LOW,
            description="Benign near-miss, no policy breach occurred.",
            affected_model="m",
            detection_module="GatewayValidator",
            steering_intervention_applied=False,
        )
        with pytest.raises(ValueError, match="eşiği"):
            gen.to_office_notification(inc)
