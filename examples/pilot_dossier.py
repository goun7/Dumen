#!/usr/bin/env python3
"""Pilot numune: GERÇEK yayımlanmış denetim artifact'ından tam uyumluluk dosyası.

Bu betik, satılması planlanan "Art.50/Annex XI dosya hizmeti" çıktısının
dürüst bir NUMUNESİDİR:

  - Skorlar uydurma DEĞİL: examples/audits/qwen2.5-3b_ollama_jbb40.json —
    15-Eyl-2026'da bu makinede qwen2.5:3b'ye karşı 40 gerçek JBB göreviyle
    ölçülmüş, depo-history'li yayımlanmış karnedir. Dosya onu SHA-256 ile
    kanıt-zincirine mühürler (değiştirilirse zincir kırılır).
  - Sağlayıcı-beyanı alanları (kimlik/opt-out/telif) Qwen2.5-3B için KAMU
    kaynaklardan dolduruldu; doğrulanamayan her alan köşeli-parantez
    [Beyan bekliyor] etiketlidir — numune, gerçek teslimde müşteri beyanıyla
    tamamlanacak KISMI açıkça gösterir.
  - Hesaplama alanı: 6·N·D kuralı, N=3.09B parametre, D=18T token
    (kaynak: Qwen2.5 Technical Report, arXiv:2412.15115 — soyut metninde
    "18 trillion tokens" beyanı 15-Eyl'de canlı doğrulandı). Bu bir
    SIRALI-BÜYÜKLÜK tahminidir ve dosyada öyle etiketlenir; sonuç:
    6·3.09e9·18e12 = 3.34e23 FLOPs < 1e25 → Madde 3(63) eşik-ALTI (tahmini)
    — numunenin eğitim-kaynaklı GÖSTERDİĞİ asıl şey, eşik mantığının
    beyandan otomatik hesaplanmasıdır. Saat/enerji bu FLOPs'tan türetilir:
    H100-sınıfı 4e14 etkili-flop/sn → ~2.3e5 GPU-saat; 0.7 kW → ~162 MWh.

Çıktılar (yalnız examples/pilot/ altına; deterministik, yeniden üretilebilir):
  sample_dossier.md / sample_dossier.json / sample_cop.md / evidence_chain.json
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from dumen import (  # noqa: E402
    AnnexXIGenerator,
    CoPMatrixGenerator,
    DataGovernanceRecord,
    EvidenceChain,
    ModelIdentity,
    TrainingComputeResources,
)
from dumen.core.types import AuditReport  # noqa: E402

AUDIT = REPO / "examples" / "audits" / "qwen2.5-3b_ollama_jbb40.json"
OUT = REPO / "examples" / "pilot"


def main() -> int:
    raw = AUDIT.read_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    data = json.loads(raw)
    report = AuditReport.model_validate(data)  # yayımlanmış karnenin kendi alanları

    chain = EvidenceChain()
    chain.append("public_audit_artifact", {"path": str(AUDIT.relative_to(REPO)), "sha256": sha})
    chain.append("evaluation", {
        "total": report.total_evaluations,
        "safety_pct": report.overall_safety_score,
        "risks": report.risk_breakdown,
        "channel": "black_box_api_ollama",  # etkinlik Ölçülmedi → dosyada None kalır
    })

    gen = AnnexXIGenerator()
    dossier = gen.generate_dossier(
        model_name="Qwen2.5-3B-Instruct",
        audit_report=report,
        identity=ModelIdentity(
            model_name="Qwen2.5-3B-Instruct",
            model_version="2.5 (open-weights)",
            provider_name="Alibaba Cloud — Qwen team",
            provider_contact="[Müşteri-beyanı bekliyor: gerçek teslimde sağlayıcı irtibatı]",
            license="Apache-2.0",
            intended_purpose="Açık-ağırlıklı genel-amaçlı LLM; bu numune denetimi "
                             "JBB-40 kamusal saldırı setiyle siyah-kutu API kanalından yapıldı.",
            systemic_risk_classification="eşik-altı-tahmini (6ND≈3.3e23 < 1e25; bkz. Bölüm 2)",
        ),
        training_compute=TrainingComputeResources(
            estimated_training_flops=6 * 3.09e9 * 18e12,  # 6ND; D=18T arXiv:2412.15115 → 3.34e23
            gpu_cluster_hours=2.32e5,  # 3.34e23 / (H100 4e14 etkili-flop/sn) / 3600
            energy_consumption_mwh=162.0,  # 2.32e5 gpu-saat × 0.7 kW
            training_infrastructure=(
                "SIRALI-BÜYÜKLÜK TAHMİNİ (6·N·D kuralı; N=3.09B, D=18T token — "
                "Qwen2.5 Tech Report arXiv:2412.15115). Saat/enerji bu FLOPs "
                "tahmininden türetildi; gerçek teslimde sağlayıcı beyanı ile "
                "değiştirilmelidir — Dümen uydurma-kesinlik üretmez."
            ),
            exceeds_ai_act_threshold=False,  # 1.08e23 < 1e25 (Madde 3(63))
        ),
        data_governance=DataGovernanceRecord(
            data_curation_summary=(
                "Çok-aşamalı ön-eğitim hattı; 18T token (arXiv:2412.15115)."
            ),
            data_provenance="[Sağlayıcı beyanı bekliyor — rapor korpus detayı yayımlamıyor]",
            opt_out_mechanism="[Sağlayıcı beyanı bekliyor]",
            copyright_compliance_strategy="[Sağlayıcı beyanı bekliyor — Madde 53(1)(d)]",
            public_summary_url="https://arxiv.org/abs/2412.15115",
        ),
        evidence_chain=chain,
        evidence_channel="black-box API (Ollama) — JBB-40, temperature=0",
    )

    OUT.mkdir(parents=True, exist_ok=True)
    gen.export_markdown(dossier, filepath=str(OUT / "sample_dossier.md"))
    gen.export_json(dossier, filepath=str(OUT / "sample_dossier.json"))

    matrix = CoPMatrixGenerator().build_matrix(
        model_name="Qwen2.5-3B-Instruct", audit_report=report,
        has_annex_xi_dossier=True, has_evidence_chain=True, has_incident_tracking=False,
    )
    (OUT / "sample_cop.md").write_text(
        CoPMatrixGenerator().to_markdown(matrix), encoding="utf-8")

    chain.append("report", {"report_id": report.report_id, "artifact_sha256": sha})
    verify = chain.verify()
    (OUT / "evidence_chain.json").write_text(chain.to_json(), encoding="utf-8")

    print(f"numune üretildi → {OUT}/  (4 dosya)")
    print(f"kaynak-karne sha256={sha[:16]}…  zincir geçerli: {verify.is_valid}")
    print(f"CoP kapsama: %{matrix.coverage_pct:.0f}  |  etkinlik: "
          f"{'Ölçülmedi (siyah-kutu — dürüst None)' if report.steering_efficacy is None else report.steering_efficacy}")
    return 0 if verify.is_valid else 1


if __name__ == "__main__":
    sys.exit(main())
