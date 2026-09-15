"""
Dümen (Dumen / SteeringOS)
Frontier AI Mekanistik Denetim ve Çıkarım Anı Aktivasyon Yönlendirme Platformu.
"""

__version__ = "0.5.0"
__author__ = "Antigravity Sovereign"

from dumen.core.types import (
    RiskCategory,
    SteeringMethod,
    SteeringVector,
    InspectionResult,
    AuditReport,
)
from dumen.core.steering import SteeringEngine
from dumen.core.sae_engine import SparseAutoencoderEngine
from dumen.core.ov_circuits import OVCircuitMask
from dumen.core.hooks import ModelHookManager
from dumen.core.transcoder import TranscoderEngine
from dumen.core.kv_drift import KVDriftGuard
from dumen.core.quantization import QuantizationCalibrator, QuantizationType
from dumen.core.miner import VectorMiner, ContrastivePair
from dumen.core.serialization import ModelSerializer
from dumen.benchmarks import ContrastiveBenchmarkSuite, BenchmarkSeed
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
from dumen.reports.cop_commitments import CoPMatrixGenerator, CoPComplianceMatrix
from dumen.reports.incident_report import IncidentReportGenerator, IncidentSeverity, SeriousIncident
from dumen.reports.evidence_chain import EvidenceChain, ChainVerification

__all__ = [
    "__version__",
    "RiskCategory",
    "SteeringMethod",
    "SteeringVector",
    "InspectionResult",
    "AuditReport",
    "SteeringEngine",
    "SparseAutoencoderEngine",
    "OVCircuitMask",
    "ModelHookManager",
    "TranscoderEngine",
    "KVDriftGuard",
    "QuantizationCalibrator",
    "QuantizationType",
    "VectorMiner",
    "ContrastivePair",
    "ModelSerializer",
    "ContrastiveBenchmarkSuite",
    "BenchmarkSeed",
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
    "IncidentReportGenerator",
    "IncidentSeverity",
    "SeriousIncident",
    "EvidenceChain",
    "ChainVerification",
]
