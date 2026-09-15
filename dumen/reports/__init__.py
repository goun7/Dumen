"""
dumen.reports
=============
Mevzuat Denetim ve Sertifikasyon Raporlama Motoru (EU AI Act & NIST AI RMF).
"""

from dumen.reports.annex_xi import (
    AnnexXIDossier,
    AnnexXIGenerator,
    DataGovernanceRecord,
    ModelIdentity,
    RuntimeTechnicalMeasures,
    TrainingComputeResources,
)
from dumen.reports.cop_commitments import CoPCommitment, CoPComplianceMatrix, CoPMatrixGenerator
from dumen.reports.eu_ai_act import ComplianceStatus, EUAIActChecker
from dumen.reports.evidence_chain import ChainEntry, ChainVerification, EvidenceChain
from dumen.reports.incident_report import IncidentReportGenerator, IncidentSeverity, SeriousIncident
from dumen.reports.scorecard import ScorecardGenerator

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
