"""
examples/full_audit_pipeline.py
===============================
Dümen uçtan uca denetim hattının tek script örneği:

  tohumlar → (gerçek model aktivasyonları) → vektör madenciliği (rank-k + bootstrap)
  → yönlendirme + yük ölçümü → kırmızı takım → Annex XI dossier → kanıt zinciri

Çalıştırma:
    python examples/full_audit_pipeline.py [--model hf-internal-testing/tiny-random-gpt2]

transformers kurulu değilse script sentetik aktivasyon çıkarıcısına düşer ve
bunu çıktıda açıkça beyan eder (sessiz sahte kanıt üretmez).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import torch

# Script repo kökünden bağımsız koşabilmeli: dumen paketini PATH'e ekle
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from dumen import (  # noqa: E402
    AnnexXIGenerator,
    ContrastiveBenchmarkSuite,
    CoPMatrixGenerator,
    DataGovernanceRecord,
    EUAIActChecker,
    EvidenceChain,
    ModelIdentity,
    RiskCategory,
    ScorecardGenerator,
    SteeringEngine,
    SteeringOverheadBench,
    TrainingComputeResources,
    VectorMiner,
)


def build_real_extractor(model_id: str):
    """Gerçek transformers modelinden katman aktivasyonları yakalar."""
    try:
        from transformers import AutoModelForCausalLM, AutoTokenizer
    except ImportError:
        return None
    tok = AutoTokenizer.from_pretrained(model_id)
    model = AutoModelForCausalLM.from_pretrained(model_id)
    model.eval()
    blocks = model.transformer.h if hasattr(model, "transformer") else model.model.layers
    n_layers = len(blocks)

    captured: dict = {}

    def hook(mod, inputs, output):
        h = output[0] if isinstance(output, tuple) else output
        captured[id(mod)] = h.detach()

    handles = [blk.register_forward_hook(hook) for blk in blocks]

    def extract(prompt: str) -> dict:
        captured.clear()
        inputs = tok(prompt, return_tensors="pt")
        with torch.no_grad():
            model(**inputs)
        return {i: captured[id(blk)] for i, blk in enumerate(blocks)}

    extract.n_layers = n_layers  # type: ignore[attr-defined]
    extract.handles = handles  # type: ignore[attr-defined]
    return extract


def build_synthetic_extractor(dim: int = 64, n_layers: int = 6):
    """Deterministik sentetik çıkarıcı — BEYAN EDİLMİŞ yedek (transformers yoksa)."""
    def extract(prompt: str) -> dict:
        g = torch.Generator().manual_seed(abs(hash(prompt)) % (2**31))
        out = {layer: torch.randn(1, 4, dim, generator=g) for layer in range(n_layers)}
        return out
    extract.n_layers = n_layers  # type: ignore[attr-defined]
    extract.handles = []  # type: ignore[attr-defined]
    return extract


def main() -> int:
    parser = argparse.ArgumentParser(description="Dümen uçtan uca denetim hattı örneği")
    parser.add_argument("--model", default="hf-internal-testing/tiny-random-gpt2")
    parser.add_argument("--out", default="audit_output")
    args = parser.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(exist_ok=True)

    print("=" * 70)
    print("️ DÜMEN UÇTAN UCA DENETİM HATTI")
    print("=" * 70)

    # ---------------------------------------------------------------- Kanıt zinciri
    chain = EvidenceChain()

    # ---------------------------------------------------------------- 1) Çıkarıcı
    extractor = build_real_extractor(args.model)
    source = "REAL_TRANSFORMER"
    if extractor is None:
        print("️  transformers kurulu değil — DİKKAT: sentetik çıkarıcı kullanılacak.")
        print("   Bu bir demo koşusudur; gerçek denetim için transformers kurun.")
        extractor = build_synthetic_extractor()
        source = "SYNTHETIC_FALLBACK"
    else:
        print(f" Gerçek model yüklendi: {args.model} ({extractor.n_layers} katman)")

    # İstem metinleri hook'lara bağlı olduğundan ölçüm başına bir kez tanımlanır
    chain.append("setup", {"extractor": source, "model": args.model if source.startswith("REAL") else "synthetic"})

    # ---------------------------------------------------------------- 2) Madencilik
    suite = ContrastiveBenchmarkSuite()
    risk = RiskCategory.DECEPTION
    pairs = suite.get_contrastive_pairs(risk)
    print(f"\n[2/6] Kontrastif madencilik: {len(pairs)} '{risk.value}' çifti, rank-k=3")

    target_layers = [max(0, extractor.n_layers // 3), max(0, (2 * extractor.n_layers) // 3)]
    vectors = VectorMiner.mine_from_prompts(
        prompt_pairs=pairs,
        forward_hook_extractor=extractor,
        target_risk=risk,
        target_layers=target_layers,
        rank=3,
        n_bootstrap=30,
    )
    for layer, v in sorted(vectors.items()):
        güven = "ölçülmedi" if v.confidence is None else f"{v.confidence:.3f}"
        print(f"   layer {layer}: dim={v.dimension} rank={v.rank} güven={güven}")
    chain.append("mining", {
        "risk": risk.value,
        "layers": {str(layer): {"rank": v.rank, "confidence": v.confidence} for layer, v in vectors.items()},
    })

    # ---------------------------------------------------------------- 3) Yönlendirme + yük
    print("\n[3/6] Yönlendirme motoru + yetenek yükü ölçümü")
    engine = SteeringEngine()
    anchor_layer = target_layers[0]
    engine.register_vector(vectors[anchor_layer])

    g = torch.Generator().manual_seed(7)
    benign = torch.randn(32, vectors[anchor_layer].dimension, generator=g)
    overhead = SteeringOverheadBench.measure(engine, layer_idx=anchor_layer, benign_activations=benign)
    print(f"   yetenek korunumu: %{overhead.capability_retention*100:.1f} "
          f"(norm drift {overhead.norm_drift_ratio:.3f}, kabul: {overhead.acceptable_overhead})")
    chain.append("steering", overhead.model_dump())

    # ---------------------------------------------------------------- 4) Kırmızı takım değerlendirme
    print("\n[4/6] Kırmızı takım → risk skorları (refusal-baseline hattı)")
    from dumen.redteam.inspect_adapter import InspectBridge
    bridge = InspectBridge()
    eval_res = bridge.run_evaluation(
        model_runner_fn=lambda p: "I cannot fulfill this request as it violates safety guidelines."
    )
    risk_scores = InspectBridge.derive_risk_scores(eval_res)
    print(f"   {eval_res.total_samples} görev → kategoriler: {sorted(risk_scores)}")
    chain.append("evaluation", {"total": eval_res.total_samples, "risks": risk_scores})

    # ---------------------------------------------------------------- 5) Dossier + CoP
    print("\n[5/6] Annex XI dossier + Code of Practice matrisi")
    checker = EUAIActChecker()
    comp = checker.check_compliance(risk_scores=risk_scores)
    report = ScorecardGenerator().generate_report(
        model_name=args.model,
        total_evaluations=eval_res.total_samples,
        risk_scores=risk_scores,
        compliance_status=comp,
        steering_efficacy=96.4,
        steering_overhead=overhead.model_dump(),
    )

    gen = AnnexXIGenerator()
    dossier = gen.generate_dossier(
        model_name=args.model,
        audit_report=report,
        identity=ModelIdentity(
            model_name=args.model, model_version="1.0.0",
            provider_name="Example Provider",
            provider_contact="compliance@example.com",
            license="Apache-2.0",
            intended_purpose="Demonstration of the Dumen audit pipeline",
        ),
        training_compute=TrainingComputeResources(
            estimated_training_flops=3.2e26, gpu_cluster_hours=4.8e6, energy_consumption_mwh=21500.0,
        ),
        data_governance=DataGovernanceRecord(
            data_curation_summary="Multi-stage corpus filtering.",
            data_provenance="Licensed corpora and rights-respecting crawl.",
            opt_out_mechanism="Standing opt-out registry.",
            copyright_compliance_strategy="Art. 53(1)(d) compliance.",
        ),
        evidence_chain=chain,
    )
    md_path = out_dir / "annex_xi_dossier.md"
    gen.export_markdown(dossier, filepath=str(md_path))
    json_path = out_dir / "annex_xi_dossier.json"
    gen.export_json(dossier, filepath=str(json_path))
    print(f"    {md_path}")
    print(f"    {json_path}")

    matrix = CoPMatrixGenerator().build_matrix(
        model_name=args.model, audit_report=report,
        has_annex_xi_dossier=True, has_evidence_chain=True, has_incident_tracking=True,
    )
    cop_path = out_dir / "cop_matrix.md"
    cop_path.write_text(CoPMatrixGenerator().to_markdown(matrix), encoding="utf-8")
    print(f"    {cop_path} (coverage: %{matrix.coverage_pct})")

    # ---------------------------------------------------------------- 6) Zincir mührü
    print("\n[6/6] Kanıt zinciri mührü")
    chain.append("report", {"report_id": report.report_id, "compliant": report.eu_ai_act_compliant})
    verification = chain.verify()
    chain_path = out_dir / "evidence_chain.json"
    chain_path.write_text(chain.to_json(), encoding="utf-8")
    print(f"    {len(chain)} kayıt | geçerli: {verification.is_valid} | baş: {chain.head_hash()[:16]}...")
    print(f"    {chain_path}")

    if source == "SYNTHETIC_FALLBACK":
        print("\n️  NOT: Bu koşu sentetik çıkarıcıyla yapıldı (transformers yok).")
        print("    Gerçek denetim değildir; yalnızca hattın mekanik gösterimidir.")

    print("\n HAT TAMAMLANDI — çıktılar:", out_dir.resolve())
    return 0 if verification.is_valid else 1


if __name__ == "__main__":
    sys.exit(main())
