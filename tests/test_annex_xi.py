"""
tests/test_annex_xi.py
======================
Annex XI Teknik Dokümantasyon Dossier Derleyicisi testleri: üretim, AuditReport
türetmesi, skor hesaplamaları, JSON ve Markdown ihracı.
"""

import json
import pytest

from dumen.core.types import AuditReport, RiskCategory
from dumen.reports.eu_ai_act import EUAIActChecker
from dumen.reports.scorecard import ScorecardGenerator
from dumen.reports.annex_xi import (
    AnnexXIDossier,
    AnnexXIGenerator,
    ModelIdentity,
    TrainingComputeResources,
    DataGovernanceRecord,
    RuntimeTechnicalMeasures,
)


# ---------------------------------------------------------------------------
# Ortak fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def audit_report() -> AuditReport:
    """Gerçek denetim zinciri (Checker → Scorecard) üzerinden AuditReport üretir."""
    checker = EUAIActChecker()
    risk_scores = {
        RiskCategory.CYBER_ATTACK.value: 0.06,
        RiskCategory.BIO_HAZARD.value: 0.02,
        RiskCategory.DECEPTION.value: 0.10,
        RiskCategory.JAILBREAK.value: 0.12,
        RiskCategory.SANDBOX_ESCAPE.value: 0.05,
    }
    comp_status = checker.check_compliance(risk_scores=risk_scores)
    generator = ScorecardGenerator()
    return generator.generate_report(
        model_name="dumen-target-llm",
        total_evaluations=120,
        risk_scores=risk_scores,
        compliance_status=comp_status,
        steering_efficacy=96.4,
    )


@pytest.fixture()
def identity() -> ModelIdentity:
    return ModelIdentity(
        model_name="dumen-target-llm",
        model_version="1.4.2",
        provider_name="Sovereign AI Labs",
        provider_contact="compliance@sovereign.example",
        license="Apache-2.0",
        intended_purpose="General-purpose assistant with agentic tool use",
    )


@pytest.fixture()
def compute() -> TrainingComputeResources:
    return TrainingComputeResources(
        estimated_training_flops=3.2e26,
        gpu_cluster_hours=4_800_000.0,
        energy_consumption_mwh=21_500.0,
        training_infrastructure="16k H-class accelerator cluster",
    )


@pytest.fixture()
def data_gov() -> DataGovernanceRecord:
    return DataGovernanceRecord(
        data_curation_summary="Multi-stage corpus filtering with dedup, quality classifiers and safety screening.",
        data_provenance="Licensed corpora, public web crawl under robots directives, and synthetic augmentation.",
        opt_out_mechanism="Standing opt-out registry honored at every crawl window; takedown within 30 days.",
        copyright_compliance_strategy="Art. 53(1)(d) compliance via rights-respecting crawl policy and opt-out enforcement.",
        public_summary_url="https://provider.example/ai-act/training-summary",
    )


# ---------------------------------------------------------------------------
# 1. Dossier üretimi ve türetme mantığı
# ---------------------------------------------------------------------------

class TestDossierGeneration:
    def test_generate_dossier_returns_valid_model(self, audit_report, identity, compute, data_gov):
        gen = AnnexXIGenerator()
        dossier = gen.generate_dossier(
            model_name="dumen-target-llm",
            audit_report=audit_report,
            identity=identity,
            training_compute=compute,
            data_governance=data_gov,
        )
        assert isinstance(dossier, AnnexXIDossier)
        assert dossier.model_identity.model_name == "dumen-target-llm"
        assert dossier.dossier_id.startswith("DUMEN-ANNEXXI-")
        assert "Regulation (EU) 2024/1689" in dossier.legal_basis

    def test_identity_name_reconciliation(self, audit_report, compute, data_gov):
        """model_name ≠ identity.model_name ise kimlik bölümü denetlenen adı kazanmalı."""
        gen = AnnexXIGenerator()
        mismatched = ModelIdentity(
            model_name="stale-name",
            model_version="0.0.1",
            provider_name="Sovereign AI Labs",
            provider_contact="compliance@sovereign.example",
            license="MIT",
            intended_purpose="testing",
        )
        dossier = gen.generate_dossier(
            model_name="dumen-target-llm",
            audit_report=audit_report,
            identity=mismatched,
            training_compute=compute,
            data_governance=data_gov,
        )
        assert dossier.model_identity.model_name == "dumen-target-llm"

    def test_penetration_rates_derived_from_audit_report(self, audit_report, identity, compute, data_gov):
        gen = AnnexXIGenerator()
        dossier = gen.generate_dossier(
            model_name="dumen-target-llm",
            audit_report=audit_report,
            identity=identity,
            training_compute=compute,
            data_governance=data_gov,
        )
        matrix = dossier.systemic_risk_matrix
        # Sızma oranları audit raporundaki risk dağılımıyla birebir eşleşmeli
        assert matrix.penetration_rate_by_category == {
            cat: round(score, 4) for cat, score in audit_report.risk_breakdown.items()
        }
        assert matrix.highest_risk_category == RiskCategory.JAILBREAK.value
        assert matrix.highest_penetration_rate == pytest.approx(0.12, abs=1e-4)

    def test_refusal_rate_is_complement_of_penetration(self, audit_report, identity, compute, data_gov):
        gen = AnnexXIGenerator()
        dossier = gen.generate_dossier(
            model_name="dumen-target-llm",
            audit_report=audit_report,
            identity=identity,
            training_compute=compute,
            data_governance=data_gov,
        )
        matrix = dossier.systemic_risk_matrix
        for cat, pen in matrix.penetration_rate_by_category.items():
            ref = matrix.refusal_rate_by_category[cat]
            assert pen + ref == pytest.approx(1.0, abs=1e-3)

    def test_runtime_measures_default_derivation(self, audit_report, identity, compute, data_gov):
        """runtime_measures verilmezse AuditReport'tan türetilmeli."""
        gen = AnnexXIGenerator()
        dossier = gen.generate_dossier(
            model_name="dumen-target-llm",
            audit_report=audit_report,
            identity=identity,
            training_compute=compute,
            data_governance=data_gov,
        )
        runtime = dossier.runtime_measures
        assert runtime.steering_efficacy_pct == pytest.approx(audit_report.steering_efficacy)
        assert runtime.activation_steering_enabled is True

    def test_adversarial_findings_populated_from_details(self, audit_report, identity, compute, data_gov):
        gen = AnnexXIGenerator()
        dossier = gen.generate_dossier(
            model_name="dumen-target-llm",
            audit_report=audit_report,
            identity=identity,
            training_compute=compute,
            data_governance=data_gov,
        )
        findings = dossier.systemic_risk_matrix.adversarial_evaluation_results
        assert len(findings) == len(audit_report.details)
        assert all(f.startswith("[") for f in findings)

    def test_compliance_attestation_content(self, audit_report, identity, compute, data_gov):
        gen = AnnexXIGenerator()
        dossier = gen.generate_dossier(
            model_name="dumen-target-llm",
            audit_report=audit_report,
            identity=identity,
            training_compute=compute,
            data_governance=data_gov,
        )
        att = dossier.compliance_attestation
        assert "120" in att  # total_evaluations
        assert "Annex XI" in att
        assert "FULFILLED" in att or "PENDING REMEDIATION" in att

    def test_empty_risk_breakdown_handled(self, identity, compute, data_gov):
        """Boş risk dağılımı olan rapor matrisi çökertmemeli."""
        empty_report = AuditReport(
            report_id="DUMEN-AUDIT-0",
            timestamp="2026-09-14 00:00:00 UTC",
            model_tested="dumen-target-llm",
            total_evaluations=0,
            overall_safety_score=100.0,
            risk_breakdown={},
            steering_efficacy=0.0,
            eu_ai_act_compliant=True,
            nist_rmf_compliant=True,
            summary="Empty audit for edge-case verification.",
        )
        gen = AnnexXIGenerator()
        dossier = gen.generate_dossier(
            model_name="dumen-target-llm",
            audit_report=empty_report,
            identity=identity,
            training_compute=compute,
            data_governance=data_gov,
        )
        assert dossier.systemic_risk_matrix.penetration_rate_by_category == {}
        assert dossier.systemic_risk_matrix.highest_risk_category == "none"
        assert dossier.systemic_risk_matrix.highest_penetration_rate == 0.0


# ---------------------------------------------------------------------------
# 2. İhraç biçimleri — JSON
# ---------------------------------------------------------------------------

class TestJSONExport:
    def test_export_json_round_trip(self, audit_report, identity, compute, data_gov):
        gen = AnnexXIGenerator()
        dossier = gen.generate_dossier(
            model_name="dumen-target-llm",
            audit_report=audit_report,
            identity=identity,
            training_compute=compute,
            data_governance=data_gov,
        )
        payload = gen.export_json(dossier)
        parsed = json.loads(payload)
        assert parsed["dossier_id"] == dossier.dossier_id
        assert parsed["model_identity"]["provider_name"] == "Sovereign AI Labs"

        # Round-trip: JSON → AnnexXIDossier
        rebuilt = AnnexXIDossier.model_validate_json(payload)
        assert rebuilt == dossier

    def test_export_json_to_file(self, audit_report, identity, compute, data_gov, tmp_path):
        gen = AnnexXIGenerator()
        dossier = gen.generate_dossier(
            model_name="dumen-target-llm",
            audit_report=audit_report,
            identity=identity,
            training_compute=compute,
            data_governance=data_gov,
        )
        target = tmp_path / "annex_xi.json"
        payload = gen.export_json(dossier, filepath=str(target))
        assert target.exists()
        assert json.loads(target.read_text(encoding="utf-8")) == json.loads(payload)


# ---------------------------------------------------------------------------
# 3. İhraç biçimleri — Markdown
# ---------------------------------------------------------------------------

class TestMarkdownExport:
    def test_export_markdown_official_sections(self, audit_report, identity, compute, data_gov):
        gen = AnnexXIGenerator()
        dossier = gen.generate_dossier(
            model_name="dumen-target-llm",
            audit_report=audit_report,
            identity=identity,
            training_compute=compute,
            data_governance=data_gov,
        )
        md = gen.export_markdown(dossier)

        # Resmi Annex XI bölüm yapısı eksiksiz olmalı
        assert "ANNEX XI — TECHNICAL DOCUMENTATION DOSSIER" in md
        assert "1. MODEL IDENTITY & PROVIDER INFORMATION" in md
        assert "2. TRAINING COMPUTATION RESOURCES" in md
        assert "3. DATA GOVERNANCE & COPYRIGHT COMPLIANCE STRATEGY" in md
        assert "4. SYSTEMIC RISK IDENTIFICATION & RED-TEAM MATRIX" in md
        assert "5. INFERENCE-TIME TECHNICAL SAFEGUARDS" in md
        assert "PROVIDER COMPLIANCE ATTESTATION" in md

    def test_export_markdown_contains_values(self, audit_report, identity, compute, data_gov):
        gen = AnnexXIGenerator()
        dossier = gen.generate_dossier(
            model_name="dumen-target-llm",
            audit_report=audit_report,
            identity=identity,
            training_compute=compute,
            data_governance=data_gov,
        )
        md = gen.export_markdown(dossier)
        assert "dumen-target-llm" in md
        assert "Sovereign AI Labs" in md
        assert "3.200e+26" in md  # FLOPs bilimsel gösterim
        assert "21,500.0 MWh" in md
        assert "jailbreak" in md
        assert "12.0%" in md  # jailbreak penetration
        assert "88.0%" in md  # jailbreak refusal (1 - 0.12)

    def test_export_markdown_to_file(self, audit_report, identity, compute, data_gov, tmp_path):
        gen = AnnexXIGenerator()
        dossier = gen.generate_dossier(
            model_name="dumen-target-llm",
            audit_report=audit_report,
            identity=identity,
            training_compute=compute,
            data_governance=data_gov,
        )
        target = tmp_path / "annex_xi.md"
        md = gen.export_markdown(dossier, filepath=str(target))
        assert target.exists()
        assert target.read_text(encoding="utf-8") == md

    def test_export_markdown_custom_runtime(self, audit_report, identity, compute, data_gov):
        """Özel runtime önlemleri dossier'a geçmeli ve Markdown'a yansımalı."""
        gen = AnnexXIGenerator()
        custom_runtime = RuntimeTechnicalMeasures(
            activation_steering_enabled=True,
            steering_efficacy_pct=99.1,
            gateway_filters_active=True,
            dual_agent_validation_active=False,
            registered_steering_vectors=42,
        )
        dossier = gen.generate_dossier(
            model_name="dumen-target-llm",
            audit_report=audit_report,
            identity=identity,
            training_compute=compute,
            data_governance=data_gov,
            runtime_measures=custom_runtime,
        )
        md = gen.export_markdown(dossier)
        assert dossier.runtime_measures.registered_steering_vectors == 42
        assert "99.1%" in md
        assert "❌ INACTIVE" in md  # dual agent kapalı → belge dürüst göstermeli
