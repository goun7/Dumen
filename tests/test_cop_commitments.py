"""
tests/test_cop_commitments.py
=============================
GPAI Code of Practice commitment matrisi testleri.
"""

import pytest

from dumen.core.types import AuditReport
from dumen.reports.cop_commitments import CoPCommitment, CoPComplianceMatrix, CoPMatrixGenerator


@pytest.fixture()
def audit_report() -> AuditReport:
    return AuditReport(
        report_id="DUMEN-AUDIT-T1",
        timestamp="2026-09-14 22:00:00 UTC",
        model_tested="test-llm",
        total_evaluations=42,
        overall_safety_score=92.0,
        risk_breakdown={"deception": 0.05, "cyber_attack": 0.04},
        steering_efficacy=95.0,
        eu_ai_act_compliant=True,
        nist_rmf_compliant=True,
        summary="Test audit for CoP matrix generation.",
    )


class TestCoPMatrix:
    def test_full_compliance_matrix(self, audit_report):
        gen = CoPMatrixGenerator()
        matrix = gen.build_matrix(
            model_name="test-llm",
            audit_report=audit_report,
            has_annex_xi_dossier=True,
            has_evidence_chain=True,
            has_incident_tracking=True,
        )
        assert isinstance(matrix, CoPComplianceMatrix)
        assert matrix.total_count == 8
        assert matrix.demonstrated_count == 8
        assert matrix.coverage_pct == 100.0
        assert matrix.ready_for_office_submission is True

    def test_partial_capabilities_flagged(self, audit_report):
        """Kanıt ürünü eksikse matris dürüstçe 'not_demonstrated' demeli."""
        gen = CoPMatrixGenerator()
        matrix = gen.build_matrix(
            model_name="test-llm",
            audit_report=audit_report,
            has_annex_xi_dossier=False,
            has_evidence_chain=False,
            has_incident_tracking=False,
        )
        assert matrix.demonstrated_count < matrix.total_count
        assert matrix.ready_for_office_submission is False
        statuses = {c.status for c in matrix.commitments}
        assert "not_demonstrated" in statuses

    def test_non_compliant_audit_makes_risk_partial(self):
        """EU AI Act uyumsuz raporu IV.2'yi 'partial' yapmalı."""
        report = AuditReport(
            report_id="DUMEN-AUDIT-T2",
            timestamp="2026-09-14 22:00:00 UTC",
            model_tested="risky-llm",
            total_evaluations=10,
            overall_safety_score=40.0,
            risk_breakdown={"cyber_attack": 0.65},
            steering_efficacy=10.0,
            eu_ai_act_compliant=False,
            nist_rmf_compliant=False,
            summary="Non-compliant audit.",
        )
        gen = CoPMatrixGenerator()
        matrix = gen.build_matrix(model_name="risky-llm", audit_report=report)
        iv2 = next(c for c in matrix.commitments if c.commitment_id == "IV.2")
        assert iv2.status == "partial"

    def test_non_signatory_blocks_submission(self, audit_report):
        gen = CoPMatrixGenerator()
        matrix = gen.build_matrix(
            model_name="test-llm",
            audit_report=audit_report,
            signatory_intent=False,
        )
        assert matrix.ready_for_office_submission is False
        assert matrix.signatory_intent is False

    def test_commitment_fields_complete(self, audit_report):
        gen = CoPMatrixGenerator()
        matrix = gen.build_matrix(model_name="test-llm", audit_report=audit_report)
        for c in matrix.commitments:
            assert isinstance(c, CoPCommitment)
            assert c.commitment_id and c.obligation and c.measure and c.evidence
            assert c.status in {"demonstrated", "partial", "not_demonstrated"}

    def test_markdown_export(self, audit_report):
        gen = CoPMatrixGenerator()
        matrix = gen.build_matrix(model_name="test-llm", audit_report=audit_report)
        md = gen.to_markdown(matrix)
        assert "CODE OF PRACTICE" in md
        assert "test-llm" in md
        assert "III.1" in md and "IV.1" in md and "AUDIT.1" in md
        assert "demonstrated" in md
        assert "100.0" in md

    def test_markdown_shows_gaps(self, audit_report):
        gen = CoPMatrixGenerator()
        matrix = gen.build_matrix(
            model_name="test-llm",
            audit_report=audit_report,
            has_evidence_chain=False,
        )
        md = gen.to_markdown(matrix)
        assert "not_demonstrated" in md
        assert "NO" in md  # submission ready değil
