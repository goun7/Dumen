"""
Dümen (Dumen / SteeringOS)
Frontier AI Mekanistik Denetim ve Çıkarım Anı Aktivasyon Yönlendirme Platformu.
"""

__version__ = "0.7.5"
__author__ = "Dümen contributors"

from dumen.benchmarks import BenchmarkSeed, ContrastiveBenchmarkSuite
from dumen.benchmarks.agentharm_loader import AgentHarmLoader
from dumen.benchmarks.gateway_selfredteam import GatewaySelfRedTeam
from dumen.benchmarks.harmbench_loader import HarmBenchLoader
from dumen.benchmarks.jailbreakbench_loader import AILuminateLoader, JailbreakBenchLoader
from dumen.benchmarks.judge_calibration import JudgeCalibrationHarness, JudgeCalibrationReport
from dumen.benchmarks.sae_quality import SAEQualityBench, SAEQualityReport
from dumen.benchmarks.steering_efficacy import SteeringEfficacyBench
from dumen.benchmarks.steering_overhead import OverheadReport, SteeringOverheadBench
from dumen.core.hooks import ModelHookManager
from dumen.core.kv_drift import KVDriftGuard
from dumen.core.miner import ContrastivePair, VectorMiner
from dumen.core.ov_circuits import OVCircuitMask
from dumen.core.quantization import QuantizationCalibrator, QuantizationType
from dumen.core.sae_engine import SparseAutoencoderEngine
from dumen.core.serialization import ModelSerializer
from dumen.core.steering import SteeringEngine
from dumen.core.transcoder import TranscoderEngine
from dumen.core.types import (
    AuditReport,
    InspectionResult,
    RiskCategory,
    SteeringMethod,
    SteeringVector,
)
from dumen.reports.annex_xi import (
    AnnexXIDossier,
    AnnexXIGenerator,
    DataGovernanceRecord,
    ModelIdentity,
    RuntimeTechnicalMeasures,
    TrainingComputeResources,
)
from dumen.reports.cop_commitments import CoPComplianceMatrix, CoPMatrixGenerator
from dumen.reports.eu_ai_act import ComplianceStatus, EUAIActChecker
from dumen.reports.evidence_chain import ChainVerification, EvidenceChain
from dumen.reports.incident_report import IncidentReportGenerator, IncidentSeverity, SeriousIncident
from dumen.reports.scorecard import ScorecardGenerator

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
    "JailbreakBenchLoader",
    "AILuminateLoader",
    "HarmBenchLoader",
    "AgentHarmLoader",
    "GatewaySelfRedTeam",
    "SAEQualityBench",
    "SAEQualityReport",
    "OverheadReport",
    "SteeringOverheadBench",
    "SteeringEfficacyBench",
    "JudgeCalibrationHarness",
    "JudgeCalibrationReport",
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
