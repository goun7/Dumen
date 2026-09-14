"""
dumen.reports
=============
Mevzuat Denetim ve Sertifikasyon Raporlama Motoru (EU AI Act & NIST AI RMF).
"""

from dumen.reports.eu_ai_act import EUAIActChecker, ComplianceStatus
from dumen.reports.scorecard import ScorecardGenerator

__all__ = [
    "EUAIActChecker",
    "ComplianceStatus",
    "ScorecardGenerator",
]
