"""
dumen.reports
=============
Mevzuat Denetim ve Sertifikasyon Raporlama Motoru (EU AI Act & NIST AI RMF).
"""

from dumen.reports.eu_ai_act import EUAIActChecker, ComplianceStatus
from dumen.reports.scorecard import ScorecardGenerator
from dumen.reports.annex_xi import (
    AnnexXIDossier,
    AnnexXIGenerator,
    ModelIdentity,
    TrainingComputeResources,
    DataGovernanceRecord,
    RuntimeTechnicalMeasures,
)
from dumen.reports.cop_commitments import CoPMatrixGenerator, CoPComplianceMatrix, CoPCommitment
from dumen.reports.incident_report import IncidentReportGenerator, IncidentSeverity, SeriousIncident
from dumen.reports.evidence_chain import EvidenceChain, ChainEntry, ChainVerification

__all__ = [
    "EUAIActChecker",
    "ComplianceStatus",
    "ScorecardGenerator",
    "AnnexXIDossier",
    "AnnexXIGenerator",
    "ModelIdentity",
    "TrainingComputeResources",
    "DataGovernanceRecord",
    "RuntimeTechnicalMeasures",
    "CoPMatrixGenerator",
    "CoPComplianceMatrix",
    "CoPCommitment",
    "IncidentReportGenerator",
    "IncidentSeverity",
    "SeriousIncident",
    "EvidenceChain",
    "ChainEntry",
    "ChainVerification",
]
