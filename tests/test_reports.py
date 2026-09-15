"""
tests/test_reports.py
=====================
EU AI Act uyumluluk denetleyicisi ve denetim karnesi üretici testleri.
"""

from dumen.core.types import RiskCategory
from dumen.reports.eu_ai_act import EUAIActChecker
from dumen.reports.scorecard import ScorecardGenerator


def test_eu_ai_act_checker_compliant():
    checker = EUAIActChecker()

    # Düşük riskli model
    safe_scores = {
        RiskCategory.CYBER_ATTACK.value: 0.05,
        RiskCategory.BIO_HAZARD.value: 0.02,
        RiskCategory.DECEPTION.value: 0.08,
    }
    status = checker.check_compliance(
        risk_scores=safe_scores,
        has_runtime_steering=True,
        has_redteam_evaluation=True,
    )
    assert status.is_compliant is True
    assert status.overall_compliance_rate == 100.0
    assert len(status.unmitigated_risks) == 0


def test_eu_ai_act_checker_non_compliant():
    checker = EUAIActChecker()

    # Yüksek riskli model (Siber zafiyet yüksek)
    risky_scores = {
        RiskCategory.CYBER_ATTACK.value: 0.65,
        RiskCategory.BIO_HAZARD.value: 0.40,
        RiskCategory.DECEPTION.value: 0.50,
    }
    status = checker.check_compliance(
        risk_scores=risky_scores,
        has_runtime_steering=False,
        has_redteam_evaluation=True,
    )
    assert status.is_compliant is False
    assert len(status.unmitigated_risks) > 0


def test_scorecard_generator_markdown():
    checker = EUAIActChecker()
    sc_gen = ScorecardGenerator()

    scores = {RiskCategory.CYBER_ATTACK.value: 0.04, RiskCategory.BIO_HAZARD.value: 0.01}
    comp_status = checker.check_compliance(scores)

    report = sc_gen.generate_report(
        model_name="test-llm-1",
        total_evaluations=10,
        risk_scores=scores,
        compliance_status=comp_status,
        steering_efficacy=98.0,
    )

    md = sc_gen.to_markdown(report)
    assert "DÜMEN NÖRAL DENETİM VE GÜVENLİK KARNESİ" in md
    assert "EU AI Act Uyumluluk" in md
    assert "test-llm-1" in md
