"""
dumen.reports.incident_report
=============================
EU AI Act Madde 55(1)(c) — Ciddi Olay (Serious Incident) Bildirim Formatı:
Sistemik riskli GPAI sağlayıcıları, ciddi olayları AI Office'e bildirmekle
yükümlüdür. Bu modül, olayın makine-okunur + insan-denetlenebilir ikili
temsilini üretir.
"""

from __future__ import annotations
import time
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field

from dumen.core.types import RiskCategory


class IncidentSeverity(str, Enum):
    """Olay ciddiyet sınıfı (AI Office bildirim eşiği bağlamında)."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SeriousIncident(BaseModel):
    """Tek bir ciddi olay kaydı."""
    incident_id: str = Field(description="Olay benzersiz kimliği")
    detected_at: str = Field(description="UTC tespit zaman damgası")
    risk_category: RiskCategory
    severity: IncidentSeverity
    description: str = Field(min_length=10, description="Olayın teknik açıklaması")
    affected_model: str
    detection_module: str = Field(description="Olayı yakalayan Dümen modülü")
    steering_intervention_applied: bool = Field(description="Çıkarım zamanı müdahale devreye girdi mi")
    containment_actions: List[str] = Field(default_factory=list, description="Alınan/önerilen çevrim önlemleri")
    reportable_to_office: bool = Field(description="Madde 55(1)(c) bildirim eşiğini aşıyor mu")


class IncidentReportGenerator:
    """
    Ciddi olay kayıtlarından Madde 55(1)(c) formatında bildirim üretir.
    """

    # Bildirim gerektiren ciddiyet eşiği: HIGH ve CRITICAL AI Office'e raporlanır
    REPORTABLE_SEVERITIES = {IncidentSeverity.HIGH, IncidentSeverity.CRITICAL}

    def create_incident(
        self,
        risk_category: RiskCategory,
        severity: IncidentSeverity,
        description: str,
        affected_model: str,
        detection_module: str,
        steering_intervention_applied: bool,
        containment_actions: Optional[List[str]] = None,
    ) -> SeriousIncident:
        """Yeni olay kaydı oluşturur ve bildirilebilirlik bayrağını hesaplar."""
        if len(description) < 10:
            raise ValueError("Olay açıklaması en az 10 karakter olmalı.")
        incident_id = f"DUMEN-INC-{int(time.time())}"
        detected_at = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
        return SeriousIncident(
            incident_id=incident_id,
            detected_at=detected_at,
            risk_category=risk_category,
            severity=severity,
            description=description,
            affected_model=affected_model,
            detection_module=detection_module,
            steering_intervention_applied=steering_intervention_applied,
            containment_actions=containment_actions or [],
            reportable_to_office=severity in self.REPORTABLE_SEVERITIES,
        )

    def to_office_notification(self, incident: SeriousIncident) -> str:
        """
        AI Office'e sunulacak Madde 55(1)(c) bildirim metnini üretir.
        Yalnızca reportable olaylar için çağrılmalıdır.
        """
        if not incident.reportable_to_office:
            raise ValueError(
                f"Olay {incident.severity.value} ciddiyetinde — bildirim eşiği (HIGH) altında, "
                "AI Office bildirimi üretilmez."
            )
        lines = [
            "# ⚠️ SERIOUS INCIDENT NOTIFICATION — Article 55(1)(c)",
            "**To:** European AI Office | **From:** Model Provider (via Dumen SteeringOS)",
            "",
            f"**Incident ID:** `{incident.incident_id}`",
            f"**Detected At:** {incident.detected_at}",
            f"**Affected Model:** `{incident.affected_model}`",
            f"**Risk Category:** {incident.risk_category.value}",
            f"**Severity:** {incident.severity.value.upper()}",
            "",
            "## Incident Description",
            incident.description,
            "",
            "## Detection & Containment",
            f"- **Detection Module:** {incident.detection_module}",
            f"- **Runtime Steering Intervention:** {'APPLIED ✅' if incident.steering_intervention_applied else 'NOT APPLIED ❌'}",
        ]
        if incident.containment_actions:
            lines.append("- **Containment Actions:**")
            for action in incident.containment_actions:
                lines.append(f"  - {action}")
        lines += [
            "",
            "---",
            "*This notification was generated mechanically from the Dumen evidence chain "
            "and reflects the provider's Article 55(1)(c) serious-incident reporting obligation.*",
        ]
        return "\n".join(lines)
