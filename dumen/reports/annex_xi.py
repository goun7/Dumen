"""
dumen.reports.annex_xi
======================
Avrupa Yapay Zeka Ofisi (EU AI Office) — Sistemik Risk Taşıyan Genel Amaçlı
Yapay Zeka (GPAI) Modelleri için Annex XI Teknik Dokümantasyon Dosyası
(Technical Documentation Dossier) Derleyicisi.

Hukuki dayanak:
- EU AI Act Madde 53(1)(a): Sistemik riskli GPAI sağlayıcıları, eğitim ve
  test verisiyle ilgili bilgi özetini içeren teknik dokümantasyonu AI Office'e
  sunmakla yükümlüdür.
- Annex XI: Dokümantasyonun zorunlu içerik şeması (model kimliği, hesaplama
  kaynakları, veri yönetimi, sistemik risk değerlendirmesi, çıkarım zamanı
  önlemleri).
- Commission Implementing Regulation (EU) 2024/2899: GPAI modellerinin
  eğitim içeriği özetini yayımlama şablonu.

Bu modül, Dümen denetim zincirinin (VectorMiner → SteeringEngine → PAIR
kırmızı takım → EUAIActChecker → ScorecardGenerator) çıktısını resmi
yasal dosyaya derler: madde madde Annex XI uyumlu Markdown ve JSON şeması.
"""

from __future__ import annotations
import json
import time
from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from dumen.core.types import AuditReport, RiskCategory


# ---------------------------------------------------------------------------
# Alt Veri Modelleri — Annex XI zorunlu bölümleri
# ---------------------------------------------------------------------------

class ModelIdentity(BaseModel):
    """Annex XI Bölüm 1 — Model kimliği ve sağlayıcı bilgisi."""
    model_name: str = Field(description="Modelin resmi adı")
    model_version: str = Field(description="Denetlenen model sürümü")
    provider_name: str = Field(description="Sağlayıcı tüzel kişiliğin adı")
    provider_contact: str = Field(description="Sağlayıcı irtibat kanalı (e-posta/adres)")
    license: str = Field(description="Model dağıtım lisansı")
    intended_purpose: str = Field(description="Beyan edilen kullanım amacı")
    deployment_date: str = Field(default="", description="Piyasaya sürüm / hizmete başlama tarihi")
    systemic_risk_classification: str = Field(
        default="designated_systemic_risk_gpai",
        description="Madde 51 kapsamında sistemik risk sınıflandırması",
    )


class TrainingComputeResources(BaseModel):
    """Annex XI Bölüm 2 — Eğitim hesaplama kaynakları (Madde 53(1)(b) tetik eşiği)."""
    estimated_training_flops: float = Field(
        gt=0.0,
        description="Eğitim için tahmini toplam kayan nokta işlem sayısı (FLOPs)",
    )
    gpu_cluster_hours: float = Field(
        ge=0.0,
        description="Toplam GPU küme-saat tüketimi",
    )
    energy_consumption_mwh: float = Field(
        ge=0.0,
        description="Eğitim enerji tüketimi (megavatsaat, MWh)",
    )
    training_infrastructure: str = Field(
        default="",
        description="Kullanılan donanım/altyapı özeti (küme mimarisi)",
    )
    exceeds_ai_act_threshold: bool = Field(
        default=True,
        description="10^25 FLOPs eğitim eşiğini aşıyor mu (Madde 3(63) tanımı)",
    )


class DataGovernanceRecord(BaseModel):
    """Annex XI Bölüm 3 — Veri yönetimi ve telif uyum stratejisi."""
    data_curation_summary: str = Field(
        description="Eğitim verisi seçim, temizlik ve filtreleme süreçleri özeti",
    )
    data_provenance: str = Field(
        description="Veri kaynaklarının kökeni (public crawl, lisanslı, sentetik)",
    )
    opt_out_mechanism: str = Field(
        description="Hak sahiplerinin verilerinin dışlanması (opt-out) mekanizması",
    )
    copyright_compliance_strategy: str = Field(
        description="Telif hakkı (Madde 53(1)(d)) uyum stratejisi",
    )
    public_summary_url: str = Field(
        default="",
        description="Eğitim içeriği özetinin yayımlandığı adres (IR 2024/2899 şablonu)",
    )


class SystemicRiskRedTeamMatrix(BaseModel):
    """Annex XI Bölüm 4 — Sistemik risk tanımlama ve kırmızı takım değerlendirme matrisi."""
    penetration_rate_by_category: Dict[str, float] = Field(
        description="Kategori bazına sızma (zafiyet) oranı — AuditReport.risk_breakdown'tan türetilir",
    )
    refusal_rate_by_category: Dict[str, float] = Field(
        description="Kategori bazına reddetme oranı (1 − sızma oranı)",
    )
    adversarial_evaluation_results: List[str] = Field(
        description="PAIR/Inspect kırmızı takım bulgularının madde bazlı özeti",
    )
    highest_risk_category: str = Field(
        description="En yüksek sızma oranına sahip kategori",
    )
    highest_penetration_rate: float = Field(
        description="En yüksek sızma oranı değeri",
    )
    systemic_risk_threshold: float = Field(
        default=0.20,
        description="Sistemik risk kabul eşiği (Art. 55(1)(b) bağlamında)",
    )


class RuntimeTechnicalMeasures(BaseModel):
    """Annex XI Bölüm 5 — Çıkarım zamanı teknik önlemler."""
    activation_steering_enabled: bool = Field(
        default=True,
        description="StTP/StMP aktivasyon yönlendirmesi etkin mi",
    )
    steering_efficacy_pct: float = Field(
        ge=0.0, le=100.0,
        description="Yönlendirme ile zafiyet azaltma oranı (%)",
    )
    gateway_filters_active: bool = Field(
        default=True,
        description="Hat içi API güvenlik duvarı (injection/PII) filtreleri etkin mi",
    )
    dual_agent_validation_active: bool = Field(
        default=True,
        description="Çift ajanlı (Generator-Validator) doğrulama hattı etkin mi",
    )
    registered_steering_vectors: int = Field(
        default=0,
        ge=0,
        description="Üretimde kayıtlı yönlendirme vektörü sayısı",
    )


# ---------------------------------------------------------------------------
# Ana Dossier Modeli
# ---------------------------------------------------------------------------

class AnnexXIDossier(BaseModel):
    """
    Madde 53(1)(a) ve Annex XI uyarınca AI Office'e sunulacak teknik
    dokümantasyon dosyasının derlenmiş hali.
    """
    dossier_id: str = Field(description="Dossier benzersiz tanımlayıcısı")
    generated_at: str = Field(description="UTC zaman damgası")
    legal_basis: str = Field(
        default="Regulation (EU) 2024/1689, Art. 53(1)(a) & Annex XI",
        description="Hukuki dayanak atfı",
    )
    model_identity: ModelIdentity
    training_compute: TrainingComputeResources
    data_governance: DataGovernanceRecord
    systemic_risk_matrix: SystemicRiskRedTeamMatrix
    runtime_measures: RuntimeTechnicalMeasures
    compliance_attestation: str = Field(
        description="Sağlayıcı uyum beyanı (Madde 53(1) taahhüdü)",
    )


# ---------------------------------------------------------------------------
# Jeneratör
# ---------------------------------------------------------------------------

class AnnexXIGenerator:
    """
    Dümen denetim raporunu (AuditReport) ve sağlayıcı beyanlarını resmi
    Annex XI teknik dokümantasyon dosyasına derleyen jeneratör.
    """

    def generate_dossier(
        self,
        model_name: str,
        audit_report: AuditReport,
        identity: ModelIdentity,
        training_compute: TrainingComputeResources,
        data_governance: DataGovernanceRecord,
        runtime_measures: Optional[RuntimeTechnicalMeasures] = None,
    ) -> AnnexXIDossier:
        """
        AuditReport + sağlayıcı beyanlarından Annex XI dosyasını üretir.

        Args:
            model_name: Kimlik bölümünde geçecek model adı (AuditReport ile
                aynı olmalı; farklıysa kimlik kazanır).
            audit_report: Dümen denetim karnesi (risk dağılımı, yönlendirme
                etkinliği, uyum bayrakları).
            identity: Sağlayıcı ve model kimlik beyanı.
            training_compute: Eğitim hesaplama kaynakları.
            data_governance: Veri yönetimi ve telif uyum stratejisi.
            runtime_measures: Çıkarım zamanı önlemleri (None ise audit
                raporundan türetilir).
        """
        # --- Kimlik: audit raporundaki model adıyla uyum --------------------------------
        if identity.model_name != model_name:
            # Audit raporu denetlenen modelin kanonik adını taşır
            identity = identity.model_copy(update={"model_name": model_name})

        # --- Sistemik risk matrisi: AuditReport'tan türet --------------------------------
        risk_breakdown = audit_report.risk_breakdown
        penetration = {
            cat: float(round(score, 4))
            for cat, score in risk_breakdown.items()
        }
        refusal = {
            cat: float(round(max(0.0, 1.0 - score), 4))
            for cat, score in penetration.items()
        }
        highest_cat = max(penetration, key=penetration.get) if penetration else "none"
        highest_rate = penetration.get(highest_cat, 0.0) if penetration else 0.0

        adversarial_findings: List[str] = []
        for det in audit_report.details:
            marker = "PASS" if det.get("passed") else "FAIL"
            adversarial_findings.append(
                f"[{marker}] {det.get('article', 'N/A')} — {det.get('title', 'N/A')}: "
                f"{det.get('details', '')}"
            )
        if not adversarial_findings:
            adversarial_findings.append(
                f"[INFO] Denetim özeti: {audit_report.summary}"
            )

        risk_matrix = SystemicRiskRedTeamMatrix(
            penetration_rate_by_category=penetration,
            refusal_rate_by_category=refusal,
            adversarial_evaluation_results=adversarial_findings,
            highest_risk_category=highest_cat,
            highest_penetration_rate=highest_rate,
        )

        # --- Çıkarım zamanı önlemleri ----------------------------------------------------
        if runtime_measures is None:
            runtime_measures = RuntimeTechnicalMeasures(
                activation_steering_enabled=audit_report.steering_efficacy > 0.0,
                steering_efficacy_pct=float(audit_report.steering_efficacy),
                gateway_filters_active=True,
                dual_agent_validation_active=True,
            )

        # --- Uyum beyanı ------------------------------------------------------------------
        attestation = (
            f"The provider attests that model '{identity.model_name}' (v{identity.model_version}) "
            f"has been evaluated under the Dumen mechanistic audit framework across "
            f"{audit_report.total_evaluations} adversarial scenarios. Overall safety score: "
            f"{audit_report.overall_safety_score:.1f}/100. EU AI Act Art. 55 obligations: "
            f"{'FULFILLED' if audit_report.eu_ai_act_compliant else 'PENDING REMEDIATION'}. "
            f"This dossier is compiled under Art. 53(1)(a) and Annex XI and is submitted to the "
            f"EU AI Office for systemic-risk oversight."
        )

        dossier_id = f"DUMEN-ANNEXXI-{int(time.time())}"
        generated_at = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())

        return AnnexXIDossier(
            dossier_id=dossier_id,
            generated_at=generated_at,
            model_identity=identity,
            training_compute=training_compute,
            data_governance=data_governance,
            systemic_risk_matrix=risk_matrix,
            runtime_measures=runtime_measures,
            compliance_attestation=attestation,
        )

    # -----------------------------------------------------------------------
    # İhraç biçimleri
    # -----------------------------------------------------------------------

    def export_markdown(
        self,
        dossier: AnnexXIDossier,
        filepath: Optional[str] = None,
    ) -> str:
        """
        Dossier'ı resmi yasal denetim formatında Markdown belgesi olarak üretir.
        filepath verilirse dosyaya yazar; her durumda metni döndürür.
        """
        ident = dossier.model_identity
        compute = dossier.training_compute
        data = dossier.data_governance
        matrix = dossier.systemic_risk_matrix
        runtime = dossier.runtime_measures

        md: List[str] = []
        md.append("# 📋 ANNEX XI — TECHNICAL DOCUMENTATION DOSSIER")
        md.append("## Technical Documentation for General-Purpose AI Models with Systemic Risk")
        md.append("")
        md.append(f"**Dossier ID:** `{dossier.dossier_id}` | **Generated:** {dossier.generated_at}")
        md.append(f"**Legal Basis:** {dossier.legal_basis}")
        md.append(f"**Regulatory Authority:** European AI Office (Madde 53(1)(a) & Annex XI)")
        md.append("")
        md.append("---")
        md.append("")

        # Bölüm 1 — Model Kimliği
        md.append("## 1. MODEL IDENTITY & PROVIDER INFORMATION")
        md.append("")
        md.append("| Field | Value |")
        md.append("| :--- | :--- |")
        md.append(f"| **Model Name** | `{ident.model_name}` |")
        md.append(f"| **Model Version** | {ident.model_version} |")
        md.append(f"| **Provider** | {ident.provider_name} |")
        md.append(f"| **Provider Contact** | {ident.provider_contact} |")
        md.append(f"| **License** | {ident.license} |")
        md.append(f"| **Intended Purpose** | {ident.intended_purpose} |")
        if ident.deployment_date:
            md.append(f"| **Deployment Date** | {ident.deployment_date} |")
        md.append(f"| **Systemic Risk Classification** | {ident.systemic_risk_classification} |")
        md.append("")

        # Bölüm 2 — Eğitim Hesaplama Kaynakları
        md.append("## 2. TRAINING COMPUTATION RESOURCES")
        md.append("")
        md.append("| Metric | Value |")
        md.append("| :--- | :--- |")
        md.append(f"| **Estimated Training FLOPs** | {compute.estimated_training_flops:.3e} |")
        md.append(f"| **GPU Cluster Hours** | {compute.gpu_cluster_hours:,.1f} |")
        md.append(f"| **Energy Consumption** | {compute.energy_consumption_mwh:,.1f} MWh |")
        if compute.training_infrastructure:
            md.append(f"| **Training Infrastructure** | {compute.training_infrastructure} |")
        md.append(
            f"| **Exceeds 10^25 FLOPs Threshold (Art. 3(63))** | "
            f"{'YES — systemic risk GPAI designation applies' if compute.exceeds_ai_act_threshold else 'NO'} |"
        )
        md.append("")

        # Bölüm 3 — Veri Yönetimi
        md.append("## 3. DATA GOVERNANCE & COPYRIGHT COMPLIANCE STRATEGY")
        md.append("")
        md.append("### 3.1 Data Curation Summary")
        md.append(f"> {data.data_curation_summary}")
        md.append("")
        md.append("### 3.2 Data Provenance")
        md.append(f"> {data.data_provenance}")
        md.append("")
        md.append("### 3.3 Opt-Out Mechanism")
        md.append(f"> {data.opt_out_mechanism}")
        md.append("")
        md.append("### 3.4 Copyright Compliance Strategy (Art. 53(1)(d))")
        md.append(f"> {data.copyright_compliance_strategy}")
        md.append("")
        if data.public_summary_url:
            md.append(f"**Public Training-Content Summary (IR (EU) 2024/2899):** {data.public_summary_url}")
            md.append("")

        # Bölüm 4 — Sistemik Risk Matrisi
        md.append("## 4. SYSTEMIC RISK IDENTIFICATION & RED-TEAM MATRIX")
        md.append("")
        md.append("### 4.1 Category Penetration / Refusal Rates")
        md.append("")
        md.append("| Risk Category | Penetration Rate | Refusal Rate | Level |")
        md.append("| :--- | :--- | :--- | :--- |")
        for cat, rate in matrix.penetration_rate_by_category.items():
            lvl = "🟢 LOW" if rate < 0.20 else ("🟡 ELEVATED" if rate < 0.50 else "🔴 CRITICAL")
            md.append(f"| `{cat}` | {rate*100:.1f}% | {matrix.refusal_rate_by_category.get(cat, 0.0)*100:.1f}% | {lvl} |")
        md.append("")
        md.append(
            f"**Highest-Risk Category:** `{matrix.highest_risk_category}` "
            f"({matrix.highest_penetration_rate*100:.1f}% penetration)"
        )
        md.append(f"**Systemic Risk Threshold (Art. 55(1)(b)):** {matrix.systemic_risk_threshold*100:.0f}%")
        md.append("")
        md.append("### 4.2 Adversarial Evaluation Results (PAIR / Inspect AI)")
        md.append("")
        for finding in matrix.adversarial_evaluation_results:
            md.append(f"- {finding}")
        md.append("")

        # Bölüm 5 — Çıkarım Zamanı Önlemleri
        md.append("## 5. INFERENCE-TIME TECHNICAL SAFEGUARDS")
        md.append("")
        md.append("| Measure | Status |")
        md.append("| :--- | :--- |")
        md.append(
            f"| **Activation Steering (StTP/StMP)** | "
            f"{'✅ ACTIVE' if runtime.activation_steering_enabled else '❌ INACTIVE'} |"
        )
        md.append(f"| **Steering Efficacy (vulnerability reduction)** | {runtime.steering_efficacy_pct:.1f}% |")
        md.append(
            f"| **Gateway Filters (Injection / PII)** | "
            f"{'✅ ACTIVE' if runtime.gateway_filters_active else '❌ INACTIVE'} |"
        )
        md.append(
            f"| **Dual-Agent Validation (Generator-Validator)** | "
            f"{'✅ ACTIVE' if runtime.dual_agent_validation_active else '❌ INACTIVE'} |"
        )
        md.append(f"| **Registered Steering Vectors** | {runtime.registered_steering_vectors} |")
        md.append("")

        # Uyum beyanı
        md.append("---")
        md.append("## PROVIDER COMPLIANCE ATTESTATION")
        md.append("")
        md.append(f"> {dossier.compliance_attestation}")
        md.append("")
        md.append(
            "*This dossier was compiled mechanically by the Dumen (SteeringOS) mechanistic audit "
            "platform and reflects the audit evidence chain: VectorMiner → SteeringEngine → PAIR "
            "Red-Team → EUAIActChecker → Scorecard.*"
        )

        document = "\n".join(md)
        if filepath is not None:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(document)
        return document

    def export_json(
        self,
        dossier: AnnexXIDossier,
        filepath: Optional[str] = None,
    ) -> str:
        """
        Dossier'ı Annex XI JSON şeması çıktısı olarak üretir.
        filepath verilirse dosyaya yazar; her durumda JSON metnini döndürür.
        """
        payload = dossier.model_dump_json(indent=2)
        if filepath is not None:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(payload)
        return payload
