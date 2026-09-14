"""
dumen.reports.cop_commitments
=============================
EU AI Act GPAI Code of Practice (10 Temmuz 2025, AI Office) Commitment Matrisi:
Madde 53/55 yükümlülüklerini Dümen kanıt ürünlerine eşleyen yapılandırılmış
uyum matrisi. Code of Practice imzacıları için Komisyon denetimi 'Code'e
bağlılığa odaklanır — bu matris o bağlılığın makine-okunur kanıtıdır.
"""

from __future__ import annotations
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

from dumen.core.types import AuditReport


class CoPCommitment(BaseModel):
    """Tek bir Code of Practice commitment'i ve Dümen kanıtı."""
    commitment_id: str = Field(description="Code of Practice bölüm/komite numarası (ör. 'III.1')")
    obligation: str = Field(description="AI Act yükümlülüğü (Madde 53/55)")
    measure: str = Field(description="Dümen kanıt ürünü / modül")
    evidence: str = Field(description="Kanıtın nerede üretildiği")
    status: str = Field(description="'demonstrated' | 'partial' | 'not_demonstrated'")


class CoPComplianceMatrix(BaseModel):
    """Sağlayıcı bazlı Code of Practice uyum matrisi."""
    model_name: str
    signatory_intent: bool = Field(default=True, description="Sağlayıcı Code of Practice imzacısı mı")
    commitments: List[CoPCommitment]
    demonstrated_count: int
    total_count: int
    coverage_pct: float = Field(ge=0.0, le=100.0)
    ready_for_office_submission: bool


class CoPMatrixGenerator:
    """
    AuditReport + Annex XI dossier varlığından Code of Practice
    commitment matrisi üretir.
    """

    def build_matrix(
        self,
        model_name: str,
        audit_report: AuditReport,
        has_annex_xi_dossier: bool = True,
        has_evidence_chain: bool = True,
        has_incident_tracking: bool = True,
        signatory_intent: bool = True,
    ) -> CoPComplianceMatrix:
        """
        Matris maddeleri Code of Practice'in üç yükümlülük alanını kapsar:
        Şeffaflık (III), Telif (II), Güvenlik ve Sistemik Risk (IV).
        """
        commitments = [
            # --- Şeffaflık bölümü (Art. 53(1)(a)-(d)) ---
            CoPCommitment(
                commitment_id="III.1",
                obligation="Art. 53(1)(a): Teknik dokümantasyon (Annex XI) AI Office'e sunulması",
                measure="AnnexXIGenerator — resmi Annex XI dossier derleyicisi",
                evidence="dumen.reports.annex_xi: 5 bölümlü teknik dosya (MD + JSON)",
                status="demonstrated" if has_annex_xi_dossier else "not_demonstrated",
            ),
            CoPCommitment(
                commitment_id="III.2",
                obligation="Art. 53(1)(d): Eğitim içeriği özeti yayımı (IR (EU) 2024/2899 şablonu)",
                measure="DataGovernanceRecord.public_summary_url + eğitim verisi yönetim beyanı",
                evidence="dossier.data_governance: curation, provenance, opt-out alanları",
                status="demonstrated" if has_annex_xi_dossier else "not_demonstrated",
            ),
            CoPCommitment(
                commitment_id="III.3",
                obligation="Art. 53(1)(c): Telif politikası ve makine-okunur opt-outlara saygı",
                measure="DataGovernanceRecord.copyright_compliance_strategy + opt_out_mechanism",
                evidence="dossier.data_governance: hak sahibi dışlama mekanizması",
                status="demonstrated" if has_annex_xi_dossier else "not_demonstrated",
            ),
            # --- Güvenlik ve sistemik risk bölümü (Art. 55) ---
            CoPCommitment(
                commitment_id="IV.1",
                obligation="Art. 55(1)(a): Model değerlendirme + adversarial (kırmızı takım) test",
                measure="HierarchicalRedTeamEngine (PAIR) + JudgeEvaluator + InspectBridge",
                evidence=f"audit_report: {audit_report.total_evaluations} değerlendirme, "
                        f"{len(audit_report.risk_breakdown)} kategori risk dağılımı",
                status="demonstrated" if audit_report.total_evaluations > 0 else "not_demonstrated",
            ),
            CoPCommitment(
                commitment_id="IV.2",
                obligation="Art. 55(1)(b): Sistemik risk değerlendirmesi ve azaltımı",
                measure="EUAIActChecker Art. 55(1)(b) denetimi + risk eşiği (%20)",
                evidence=f"eu_ai_act_compliant={audit_report.eu_ai_act_compliant}, "
                        f"risk_breakdown={ {k: round(v,3) for k, v in list(audit_report.risk_breakdown.items())[:3]} }",
                status="demonstrated" if audit_report.eu_ai_act_compliant else "partial",
            ),
            CoPCommitment(
                commitment_id="IV.3",
                obligation="Art. 55(1)(c): Ciddi olay takibi ve AI Office'e raporlama",
                measure="IncidentReportGenerator — Madde 55(1)(c) olay formatı",
                evidence="dumen.reports.incident_report: yapılandırılmış olay bildirimi",
                status="demonstrated" if has_incident_tracking else "not_demonstrated",
            ),
            CoPCommitment(
                commitment_id="IV.4",
                obligation="Art. 55(1)(c) devamı: Çıkarım zamanı teknik önlemler",
                measure="SteeringEngine (StTP/StMP) + Gateway dual-agent validator",
                evidence=f"steering_efficacy={audit_report.steering_efficacy}%, "
                        f"steering_overhead={audit_report.steering_overhead is not None}",
                status="demonstrated" if audit_report.steering_efficacy > 0 else "not_demonstrated",
            ),
            # --- Kanıt bütünlüğü (denetim güvenilirliği) ---
            CoPCommitment(
                commitment_id="AUDIT.1",
                obligation="Kanıt zinciri bütünlüğü (hash-chain, tamper tespiti)",
                measure="EvidenceChain — SHA-256 append-only kanıt zinciri",
                evidence="dumen.reports.evidence_chain: her kayıt prev_hash taşır",
                status="demonstrated" if has_evidence_chain else "not_demonstrated",
            ),
        ]

        demonstrated = sum(1 for c in commitments if c.status == "demonstrated")
        total = len(commitments)
        coverage = (demonstrated / total) * 100.0

        return CoPComplianceMatrix(
            model_name=model_name,
            signatory_intent=signatory_intent,
            commitments=commitments,
            demonstrated_count=demonstrated,
            total_count=total,
            coverage_pct=round(coverage, 1),
            ready_for_office_submission=(demonstrated == total and signatory_intent),
        )

    def to_markdown(self, matrix: CoPComplianceMatrix) -> str:
        """Matrisi Code of Practice denetim formatında Markdown'a döker."""
        md = [
            "# 📜 GPAI CODE OF PRACTICE — COMMITMENT COMPLIANCE MATRIX",
            f"**Model:** `{matrix.model_name}` | **Coverage:** %{matrix.coverage_pct} "
            f"({matrix.demonstrated_count}/{matrix.total_count})",
            f"**Signatory Intent:** {'YES' if matrix.signatory_intent else 'NO'} | "
            f"**AI Office Submission Ready:** {'YES ✅' if matrix.ready_for_office_submission else 'NO ❌'}",
            "",
            "| ID | AI Act Obligation | Dumen Evidence Product | Evidence Source | Status |",
            "| :--- | :--- | :--- | :--- | :--- |",
        ]
        for c in matrix.commitments:
            icon = {"demonstrated": "✅", "partial": "🟡", "not_demonstrated": "❌"}[c.status]
            md.append(
                f"| **{c.commitment_id}** | {c.obligation} | {c.measure} | {c.evidence} | {icon} {c.status} |"
            )
        md.append("")
        md.append(
            "*Matrix generated by Dumen (SteeringOS). Each row maps a Code of Practice "
            "commitment to a mechanically-produced evidence artifact in the audit chain.*"
        )
        return "\n".join(md)
