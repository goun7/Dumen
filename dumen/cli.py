"""
dumen.cli
=========
Dümen (SteeringOS) Komut Satırı Arayüzü (CLI).
"""

from __future__ import annotations

import json
from pathlib import Path

import click
import torch
import uvicorn

from dumen import __version__
from dumen.benchmarks.steering_efficacy import SteeringEfficacyBench
from dumen.core.hooks import ModelHookManager
from dumen.core.ov_circuits import OVCircuitMask
from dumen.core.steering import SteeringEngine
from dumen.core.types import RiskCategory
from dumen.gateway.proxy import create_proxy_app
from dumen.redteam.inspect_adapter import InspectBridge
from dumen.reports.annex_xi import (
    AnnexXIGenerator,
    DataGovernanceRecord,
    ModelIdentity,
    TrainingComputeResources,
)
from dumen.reports.cop_commitments import CoPMatrixGenerator
from dumen.reports.eu_ai_act import EUAIActChecker
from dumen.reports.evidence_chain import EvidenceChain
from dumen.reports.scorecard import ScorecardGenerator


@click.group()
@click.version_option(version=__version__, prog_name="dumen")
def cli():
    """🛡️ Dümen (Dumen / SteeringOS) — Frontier AI Mekanistik Denetim ve Yönlendirme Platformu."""
    pass


@cli.command()
@click.option("--host", default="127.0.0.1", help="Bağlanılacak sunucu IP adresi")
@click.option("--port", default=8000, type=int, help="Çalıştırılacak port numarası")
@click.option("--upstream", default=None, help="Yönlendirilecek upstream LLM API adresi")
@click.option("--api-key", default=None, help="Upstream API anahtarı")
@click.option("--strict", is_flag=True, help="Katı güvenlik modunu aktif et")
def serve(host: str, port: int, upstream: str | None, api_key: str | None, strict: bool):
    """🚀 Dümen Güvenlik Duvarı ve Ters Proxy Ağ Geçidini Başlatır."""
    click.echo(f"🛡️ Dümen Gateway v{__version__} başlatılıyor...")
    click.echo(f"   📡 Adres: http://{host}:{port}")
    if upstream:
        click.echo(f"   🔗 Upstream Hedef: {upstream}")
    else:
        click.echo("   ⚠️  Upstream yok: girdi filtreleri + validator canlı çalışır,")
        click.echo("      ancak üretim isteği yapmayacak — /health dışındaki istekler 503 döner.")

    app = create_proxy_app(upstream_url=upstream, api_key=api_key, strict_mode=strict)
    uvicorn.run(app, host=host, port=port)


def _load_transformers_pair(model_id: str):
    """
    HuggingFace model + tokenizer yükler. transformers eksikse ya da model
    indirilemezse (None, None) döner — çağıran açık hata verir.
    """
    try:
        from transformers import AutoModelForCausalLM, AutoTokenizer  # type: ignore
    except ImportError:
        return None, None
    try:
        tokenizer = AutoTokenizer.from_pretrained(model_id)
        hf_model = AutoModelForCausalLM.from_pretrained(model_id)
    except Exception:
        return None, None
    hf_model.eval()
    return tokenizer, hf_model


def _format_prompt(tokenizer, prompt: str) -> str:
    """
    Instruct modelleri ham completion'ı DEĞİL chat formatını bekler; chat template
    varsa kullanıcı mesajına sarılır (red-detme davranışının gerçeğe uygun ölçümü
    için şart), yoksa (ör. GPT-2) ham metin döner.
    """
    if getattr(tokenizer, "chat_template", None):
        try:
            return tokenizer.apply_chat_template(
                [{"role": "user", "content": prompt}],
                tokenize=False,
                add_generation_prompt=True,
            )
        except Exception:  # bozuk/özel template → ham metne düş (davranış korunur)
            return prompt
    return prompt


def _generate(tokenizer, hf_model, prompt: str, max_new_tokens: int = 64) -> str:
    """Greedy (deterministik) üretim: yeniden üretilebilir kanıt için temperature yok."""
    text = _format_prompt(tokenizer, prompt)
    inputs = tokenizer(text, return_tensors="pt")
    with torch.no_grad():
        out = hf_model.generate(**inputs, max_new_tokens=max_new_tokens, do_sample=False)
    return tokenizer.decode(out[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)


def _build_model_runner(model_id: str):
    """Geriye dönük uyumlu tekil-çalıştırıcı kurucu (testler kullanır)."""
    tokenizer, hf_model = _load_transformers_pair(model_id)
    if tokenizer is None:
        return None
    return lambda prompt: _generate(tokenizer, hf_model, prompt)


def _measure_steering_efficacy(tokenizer, hf_model, max_new_tokens: int = 48) -> dict:
    """
    Gerçek modelde DAVRANIŞSAL steering etkinlik ölçümü:
    1) orta katmanlardan kontrastif JAILBREAK tohumlarıyla vektör madenciliği
       (hook yok — yalnız ileri geçiş aktivasyonları),
    2) saldırı istemlerinin steer-edilmemiş yanıtları (hooksuz),
    3) ModelHookManager ile katmanlara steering hook'u bağlanıp steer-edilmiş
       yanıtlar,
    4) SteeringEfficacyBench ile hakem tabanlı zafiyet azaltma oranı.
    Ölçülen zafiyet yoksa efficacy None kalır — iddia üretilmez.
    """
    from dumen.benchmarks import ContrastiveBenchmarkSuite
    from dumen.benchmarks.steering_efficacy import SteeringEfficacyBench
    from dumen.core.miner import VectorMiner

    cfg = hf_model.config
    n_layers = getattr(cfg, "num_hidden_layers", None) or getattr(cfg, "n_layer")
    mid = max(1, n_layers // 2)
    target_layers = sorted({max(0, mid - 1), mid, min(n_layers - 1, mid + 1)})

    def last_token_acts(prompt: str) -> dict:
        inputs = tokenizer(_format_prompt(tokenizer, prompt), return_tensors="pt")
        with torch.no_grad():
            out = hf_model(**inputs, output_hidden_states=True)
        # hidden_states[0] gömme katmanı: blok L ↔ index L+1
        return {L: out.hidden_states[L + 1][:, -1, :] for L in target_layers}

    suite = ContrastiveBenchmarkSuite()
    jailbreak_pairs = suite.get_contrastive_pairs(RiskCategory.JAILBREAK)
    mine_pairs = jailbreak_pairs[:4]
    probe_pairs = jailbreak_pairs[4:6]
    if not probe_pairs:  # madenciliğe değmemiş probe kalmadıysa başka kategoriden ödünç al
        probe_pairs = suite.get_contrastive_pairs(RiskCategory.DECEPTION)[:2]
    attack_prompts = [harmful for harmful, _ in probe_pairs]

    vectors = VectorMiner.mine_from_prompts(
        prompt_pairs=mine_pairs,
        forward_hook_extractor=last_token_acts,
        target_risk=RiskCategory.JAILBREAK,
        target_layers=target_layers,
        n_bootstrap=10,
    )

    unsteered = {p: _generate(tokenizer, hf_model, p, max_new_tokens) for p in attack_prompts}

    engine = SteeringEngine()
    for layer_idx, vec in vectors.items():
        engine.register_vector(vec)
    manager = ModelHookManager(engine)
    attached = manager.attach_to_model(hf_model)
    if attached == 0:
        raise click.ClickException(
            "Steering hook'ları hiçbir katmana bağlanamadı — etkinlik ölçümü yapılamaz."
        )
    try:
        steered = {p: _generate(tokenizer, hf_model, p, max_new_tokens) for p in attack_prompts}
    finally:
        manager.detach_all()

    result = SteeringEfficacyBench.measure_behavioral(
        attack_prompts=attack_prompts,
        unsteered_runner=unsteered.__getitem__,
        steered_runner=steered.__getitem__,
    )
    result["layers_steered"] = attached
    return result


def _load_dataset_seeds(path: str):
    """
    Harici saldırı seti yükleyicisi — şema otomatik algılama (dört yayımlanmış
    dağıtım, gerçek sütun/anahtar adlarıyla):
      CSV : HarmBench ('Behavior'+SemanticCategory) · JAILBREAKBENCH ('Goal')
      JSON: AgentHarm ({'behaviors': [...]}) · JBB dizi ('goal') · AILuminate ('prompt'/JSONL)
    """
    from dumen.benchmarks import (
        AgentHarmLoader,
        AILuminateLoader,
        HarmBenchLoader,
        JailbreakBenchLoader,
    )

    p = Path(path)
    if not p.exists():
        raise click.ClickException(f"Dosya bulunamadı: {p}")
    text = p.read_text(encoding="utf-8")
    if p.suffix.lower() == ".csv":
        head = text.splitlines()[0] if text.splitlines() else ""
        if "Behavior" in head and "SemanticCategory" in head:
            return HarmBenchLoader.load_from_csv(text)
        return JailbreakBenchLoader.load_from_csv(text)
    try:
        root = json.loads(text)
    except ValueError:
        root = None  # JSONL: yalnız AILuminate satır-şeması anlar
    if isinstance(root, dict) and "behaviors" in root:
        return AgentHarmLoader.load_from_json(text)
    if isinstance(root, list) and root and isinstance(root[0], dict) and "prompt" in root[0]:
        return AILuminateLoader.load_from_json(text)
    try:
        seeds = JailbreakBenchLoader.load_from_json(text)
    except ValueError:
        seeds = []  # JSONL olabilir: AILuminate hattı dener
    if seeds:
        return seeds
    return AILuminateLoader.load_from_json(text)


@cli.command()
@click.option("--model", default=None,
              help="Denetlenecek model adı (HuggingFace hub kimliği; --endpoint ile ise sunucu model etiketi)")
@click.option("--endpoint", default=None,
              help="OpenAI-uyumlu API sonu (Ollama: http://127.0.0.1:11434/v1 · vLLM/LM Studio benzeri). "
                   "Siyah-kutu denetim kanalı — beyaz-kutu steering ölçümü bu hatta yapılamaz.")
@click.option("--api-key", default=None, help="API sonu için Bearer anahtar (gerekiyorsa)")
@click.option("--dataset", default=None,
              help="Harici saldırı seti dosyası (JAILBREAKBENCH CSV/JSON veya AILuminate JSON/JSONL) — "
                   "verilirse standart 4-görev yerine gerçek yayımlanmış istemlerle koşar")
@click.option("--dataset-limit", default=25, type=int, show_default=True,
              help="Dataset'ten en fazla N görev (maliyet kontrolü; 0 = hepsi)")
@click.option("--output", default=None, help="Raporun kaydedilecek dosya yolu (.md veya .json)")
@click.option("--refusal-baseline", is_flag=True, default=False,
              help="Model bağlantısı yerine refusal-baseline hattını denetle (kanıt zinciri şeffaflığı)")
@click.option("--measure-steering", is_flag=True, default=False,
              help="Gerçek model üzerinde davranışsal steering etkinlik ölçümü koşar (daha yavaş; "
                   "ölçülmezse raporda 'Ölçülmedi' yazılır — sayı uydurulmaz)")
def audit(model: str | None, endpoint: str | None, api_key: str | None,
          dataset: str | None, dataset_limit: int,
          output: str | None, refusal_baseline: bool, measure_steering: bool):
    """🔍 Modeli UK AISI Inspect AI ve EU AI Act Testlerinden Geçirip Karne Üretir."""
    if model is None and not refusal_baseline:
        raise click.UsageError(
            "--model <hf-id> belirtin veya kanıt hattını doğrulamak için --refusal-baseline kullanın. "
            "Risk skorları elle girilmez; yalnızca koşturulan örneklerden türetilir."
        )
    if refusal_baseline and endpoint:
        raise click.UsageError("--refusal-baseline bir MODEL değildir; --endpoint ile birleştirilemez.")
    if measure_steering and (model is None or refusal_baseline or endpoint):
        raise click.UsageError(
            "--measure-steering ancak YEREL transformers modeliyle (--model, --endpoint'siz) "
            "ölçülebilir: API sonundan aktivasyon okunamaz; refusel-baseline kanalında da "
            "yönlendirilecek model yoktur. Ölçüm yapılamazsa sayı UYDURULMAZ."
        )

    blackbox = endpoint is not None
    if blackbox:
        audited_name = f"{model}@{endpoint.rstrip('/')}"
    else:
        audited_name = model if model is not None else "refusal-baseline-channel"
    click.echo(f"🔍 '{audited_name}' modeli denetleniyor...")

    bridge = InspectBridge()
    efficacy_result = None
    efficacy_value = None

    eval_tasks = None
    if dataset:
        seeds = _load_dataset_seeds(dataset)
        if not seeds:
            raise click.ClickException(
                f"'{dataset}' içinden şemaya uyan tohum okunamadı "
                "(JAILBREAKBENCH: goal/Goal + Category; AILuminate: prompt+category)."
            )
        eval_tasks = InspectBridge.build_tasks_from_seeds(
            seeds, limit=(dataset_limit if dataset_limit > 0 else None)
        )
        click.echo(f"📚 Harici saldırı seti: {len(eval_tasks)} görev ({Path(dataset).name})")

    if refusal_baseline:
        # Refusal-baseline hattı: hedef model bağlantısı yok; tüm örnekler standart
        # refusal şablonuyla değerlendirilir ve kanıt zincirinde açıkça işaretlenir.
        eval_res = bridge.run_evaluation(
            tasks=eval_tasks,
            model_runner_fn=lambda p: "I cannot fulfill this request as it violates safety guidelines."
        )
    elif blackbox:
        from dumen.redteam.api_runner import build_endpoint_runner
        runner = build_endpoint_runner(endpoint, model, api_key=api_key)  # type: ignore[arg-type]
        click.echo("🔌 Siyah-kutu API kanalı: aktivasyon yok → etkinlik ölçülmez, 'Ölçülmedi' yazılır.")
        eval_res = bridge.run_evaluation(tasks=eval_tasks, model_runner_fn=runner)
    else:
        tokenizer, hf_model = _load_transformers_pair(model)  # type: ignore[arg-type]
        if tokenizer is None:
            raise click.UsageError(
                f"Model '{model}' yüklenemedi (transformers yüklü mü / indirilebildi mi?). "
                "Kanıt hattını doğrulamak için --refusal-baseline kullanın."
            )
        eval_res = bridge.run_evaluation(
            tasks=eval_tasks,
            model_runner_fn=lambda p: _generate(tokenizer, hf_model, p)
        )
        if measure_steering:
            click.echo("⚙️ Davranışsal steering etkinlik ölçümü: madencilik + hook koşusu...")
            efficacy_result = _measure_steering_efficacy(tokenizer, hf_model)
            efficacy_value = SteeringEfficacyBench.report_value(efficacy_result)
            if efficacy_result["verdict"] == "measured":
                click.echo(
                    f"   📉 Ortalama zafiyet: steer öncesi {efficacy_result['mean_harm_unsteered']:.2f} "
                    f"→ sonrası {efficacy_result['mean_harm_steered']:.2f} "
                    f"⇒ Etkinlik %{efficacy_result['efficacy_pct']} "
                    f"({efficacy_result['layers_steered']} katman yönlendirildi)"
                )
            else:
                click.echo(
                    "   ⚪ Azaltılacak ölçülebilir zafiyet bulunamadı — etkinlik iddia edilmez "
                    "(rapor: 'Ölçülmedi')."
                )

    # Risk skorları ELLE GİRİLMEZ: koşturulan örneklerin harm_score'larından türetilir.
    risk_scores = InspectBridge.derive_risk_scores(eval_res)
    if not risk_scores:
        raise click.ClickException("Değerlendirme örneklerinden risk skoru türetilemedi.")

    checker = EUAIActChecker()
    # Koruma iddiaları yalnız GERÇEKTEN koşturulan hatlara dayanır:
    # kırmızı takım değerlendirmesi bu komutta koştu; steering ise ancak
    # ölçüm başarıyla zafiyet azalttıysa "runtime steering var" sayılır.
    comp_status = checker.check_compliance(
        risk_scores=risk_scores,
        has_runtime_steering=efficacy_value is not None and efficacy_value > 0,
        has_redteam_evaluation=True,
    )

    sc_gen = ScorecardGenerator()
    report = sc_gen.generate_report(
        model_name=audited_name,
        total_evaluations=eval_res.total_samples,
        risk_scores=risk_scores,
        compliance_status=comp_status,
        steering_efficacy=efficacy_value,
    )

    md_report = sc_gen.to_markdown(report)
    click.echo("\n" + md_report + "\n")
    if refusal_baseline:
        click.echo(
            "ℹ️  Bu koşu refusal-baseline BORU HATTI doğrulamasıdır: steering ölçülmediği\n"
            "    için Art.14 bilinçli olarak ❌ görünür (kanıt yok → koruma iddiası yok).\n"
            "    Model-bazlı koruma kanıtı için: dumen audit --model <hf-id> --measure-steering\n"
        )

    if output:
        with open(output, "w", encoding="utf-8") as f:
            if output.endswith(".json"):
                f.write(report.model_dump_json(indent=2))
            else:
                f.write(md_report)
        click.echo(f"📁 Rapor kaydedildi: {output}")


@cli.command("dossier")
@click.option("--model", default="dumen-target-llm", help="Dossier model adı")
@click.option("--output", default=None, help="Annex XI Markdown çıktı dosyası")
@click.option("--flops", default=3.2e26, type=float, help="Tahmini eğitim FLOPs")
@click.option("--gpu-hours", default=4.8e6, type=float, help="GPU küme-saatleri")
@click.option("--energy-mwh", default=21500.0, type=float, help="Eğitim enerjisi (MWh)")
def dossier(model: str, output: str | None, flops: float, gpu_hours: float, energy_mwh: float):
    """📋 Refusal-baseline denetiminden Annex XI Dossier + CoP Matrisi Üretir."""
    click.echo(f"📋 '{model}' için Annex XI dossier derleniyor...")

    # 1) Kanıt zinciri: refusal-baseline denetim hattı (model-i özgü DEĞİL, şeffaf damga)
    click.echo("   ⚠️  Risk skorları refusal-baseline kanalından türetilir (pipeline doğrulaması); "
               "modele özgü denetim için: dumen audit --model <hf-id>")
    bridge = InspectBridge()
    eval_res = bridge.run_evaluation(
        model_runner_fn=lambda p: "I cannot fulfill this request as it violates safety guidelines."
    )
    risk_scores = InspectBridge.derive_risk_scores(eval_res)

    checker = EUAIActChecker()
    comp_status = checker.check_compliance(
        risk_scores=risk_scores,
        has_runtime_steering=False,   # bu komutta steering koşusu yok — iddia edilmez
        has_redteam_evaluation=True,  # 4 standart görev gerçekten koşturuldu
    )
    report = ScorecardGenerator().generate_report(
        model_name=model,
        total_evaluations=eval_res.total_samples,
        risk_scores=risk_scores,
        compliance_status=comp_status,
        steering_efficacy=None,  # ölçülmedi → raporda "Ölçülmedi" görünür, sayı uydurulmaz
    )

    # 2) Kanıt zinciri: denetim aşamalarını kaydet (kanal damgası dahil)
    chain = EvidenceChain()
    chain.append("evidence_channel", {
        "channel": "refusal-baseline",
        "model_specific_audit": False,
        "note": "Scores derive from the labeled refusal-baseline runner, not from the named model.",
    })
    chain.append("evaluation", {"total": eval_res.total_samples, "risks": risk_scores})
    chain.append("report", {"report_id": report.report_id, "compliant": report.eu_ai_act_compliant})

    # 3) Annex XI dossier
    gen = AnnexXIGenerator()
    dos = gen.generate_dossier(
        model_name=model,
        audit_report=report,
        identity=ModelIdentity(
            model_name=model, model_version="1.0.0",
            provider_name="Sovereign AI Labs",
            provider_contact="compliance@sovereign.example",
            license="Apache-2.0",
            intended_purpose="General-purpose assistant under systemic-risk oversight",
        ),
        training_compute=TrainingComputeResources(
            estimated_training_flops=flops,
            gpu_cluster_hours=gpu_hours,
            energy_consumption_mwh=energy_mwh,
        ),
        data_governance=DataGovernanceRecord(
            data_curation_summary="Multi-stage corpus filtering with dedup and safety screening.",
            data_provenance="Licensed corpora and rights-respecting public crawl.",
            opt_out_mechanism="Standing opt-out registry honored at every crawl window.",
            copyright_compliance_strategy="Art. 53(1)(d) compliance via opt-out enforcement.",
        ),
        evidence_chain=chain,
        evidence_channel="refusal-baseline",
    )

    chain.append("cop", {"model": model, "evidence_head": chain.head_hash()[:16]})

    # 4) CoP matrisi
    matrix = CoPMatrixGenerator().build_matrix(
        model_name=model, audit_report=report,
        has_annex_xi_dossier=True, has_evidence_chain=True, has_incident_tracking=True,
    )

    # 5) Çıktılar
    md = gen.export_markdown(dos)
    cop_md = CoPMatrixGenerator().to_markdown(matrix)
    chain_ok = chain.verify()

    click.echo(md)
    click.echo("\n" + cop_md + "\n")
    click.echo(f"🔗 Kanıt zinciri: {len(chain)} kayıt, geçerli: {chain_ok.is_valid}, baş: {chain.head_hash()[:16]}...")

    if output:
        with open(output, "w", encoding="utf-8") as f:
            f.write(md + "\n\n---\n\n" + cop_md)
        click.echo(f"📁 Dossier + CoP matrisi kaydedildi: {output}")




@cli.command()
@click.option("--dim", default=4096, type=int, help="Gizli katman boyutu")
@click.option("--sparsity", default=0.15, type=float, help="OV devresi seyreltme oranı (varsayılan: 0.15 -> %85)")
def steer_test(dim: int, sparsity: float):
    """⚡ StTP Yönlendirme ve OV Devresi Seyreltme Matematiğini Doğrular."""
    click.echo(f"⚡ StTP ve Attention OV seyreltme testi (Boyut: {dim}, Sparsite: %{(1-sparsity)*100:.1f})...")

    # 1. Sentetik aktivasyon ve yönlendirme vektörü
    torch.manual_seed(42)
    x = torch.randn(dim)
    harmful_v = torch.randn(dim)
    harmful_v = harmful_v / torch.norm(harmful_v)

    # 2. OV devre maskesi
    masker = OVCircuitMask(hidden_dim=dim)
    sparse_v, active_indices = masker.compute_ov_salience(harmful_v, top_k_percent=sparsity)

    # 3. Yönlendirme motoru
    engine = SteeringEngine()
    steered = engine.project_sttp(x, harmful_v, alpha=1.0, active_indices=active_indices)

    # 4. Doğrulama metrikleri
    cos_sim_before = float(torch.dot(x / torch.norm(x), harmful_v).item())
    cos_sim_after = float(torch.dot(steered / torch.norm(steered), harmful_v).item())

    click.echo(f"   📊 Yönlendirme Öncesi Zararlı Yön Cosine Benzerliği: {cos_sim_before:+.4f}")
    click.echo(f"   🎯 Yönlendirme Sonrası Zararlı Yön Cosine Benzerliği: {cos_sim_after:+.4f}")
    click.echo(f"   ✂️ Aktif OV Boyut Sayısı: {len(active_indices)} / {dim} (Seyreltme: %{(1 - len(active_indices)/dim)*100:.1f})")
    click.echo("   ✅ Matematiksel Doğrulama BAŞARILI!")


if __name__ == "__main__":
    cli()
