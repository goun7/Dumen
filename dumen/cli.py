"""
dumen.cli
=========
Dümen — açık-kaynak EU AI Act denetim motoru için komut satırı arayüzü.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

import click
import torch
import uvicorn
from pydantic import ValidationError

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
from dumen.reports.html_export import render_report_html
from dumen.reports.incident_report import SeriousIncident
from dumen.reports.scorecard import ScorecardGenerator
from dumen.reports.signing import generate_keypair, sign_chain_file, verify_chain_file


@click.group()
@click.version_option(version=__version__, prog_name="dumen")
def cli():
    """Dümen — açık-kaynak EU AI Act denetim motoru (mekanistik denetim + yönlendirme)."""
    pass


@cli.command()
@click.option("--host", default="127.0.0.1", help="Bağlanılacak sunucu IP adresi")
@click.option("--port", default=8000, type=int, help="Çalıştırılacak port numarası")
@click.option("--upstream", default=None, help="Yönlendirilecek upstream LLM API adresi")
@click.option("--api-key", default=None, help="Upstream API anahtarı")
@click.option("--strict", is_flag=True, help="Katı güvenlik modunu aktif et")
@click.option("--validator-url", default=None,
              help="İkincil (çift-ajan) LLM denetçisi OpenAI-uyumlu adresi — verilmazse tek-katman duvar")
@click.option("--validator-model", default=None,
              help="Denetçi model adı (ör. qwen2.5:3b; varsayılan gpt-4o-mini)")
@click.option("--validator-key", default=None, help="Denetçi API anahtarı")
def serve(host: str, port: int, upstream: str | None, api_key: str | None, strict: bool,
          validator_url: str | None, validator_model: str | None, validator_key: str | None):
    """🚀 Dümen Güvenlik Duvarı ve Ters Proxy Ağ Geçidini Başlatır."""
    click.echo(f"🛡️ Dümen Gateway v{__version__} başlatılıyor...")
    click.echo(f"   📡 Adres: http://{host}:{port}")
    if upstream:
        click.echo(f"   🔗 Upstream Hedef: {upstream}")
    else:
        click.echo("   ⚠️  Upstream yok: girdi filtreleri canlı çalışır,")
        click.echo("      ancak üretim isteği gitmez — /health dışındaki istekler 503 döner.")
    if validator_url:
        click.echo(f"   ⚖️  Çift-ajan denetçi ETKİN: {validator_url} ({validator_model or 'gpt-4o-mini'})")
    else:
        click.echo("   ⚖️  İkincil LLM denetçi KAPALI — karar tek-katman hızlı duvara dayanır;")
        click.echo("      açmak için: --validator-url <adres> (--validator-model ..., --validator-key ...)")

    app = create_proxy_app(
        upstream_url=upstream, api_key=api_key, strict_mode=strict,
        validator_url=validator_url, validator_model=validator_model,
        validator_api_key=validator_key,
    )
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
    # Cihaz seçimi: torch.cuda.is_available() True olsa bile, bu build'in
    # kernel'leri GPU'nun compute-capability'si için derlenmemişse ilk forward
    # AccelerError atar (ör. sm_61 Pascal + cu130-wheels). Körlemesine
    # .to("cuda") bu yüzden YASAK; makine-uyumlu taşıma DUMEN_DEVICE ile
    # açıkça istenir. Çağrı noktaları girdileri hf_model.device'a koyar
    # (CPU'da no-op; model CPU'da kaldıkça doğrulanmış yayımlanmış davranış).
    import os
    req = os.environ.get("DUMEN_DEVICE", "").strip()
    if req:
        hf_model.to(req)
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
    inputs = {k: v.to(hf_model.device) for k, v in
              tokenizer(text, return_tensors="pt").items()}
    with torch.no_grad():
        out = hf_model.generate(**inputs, max_new_tokens=max_new_tokens, do_sample=False)
    return tokenizer.decode(out[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)


def _build_model_runner(model_id: str):
    """Geriye dönük uyumlu tekil-çalıştırıcı kurucu (testler kullanır)."""
    tokenizer, hf_model = _load_transformers_pair(model_id)
    if tokenizer is None:
        return None
    return lambda prompt: _generate(tokenizer, hf_model, prompt)


def _measure_steering_efficacy(tokenizer, hf_model, max_new_tokens: int = 48,
                               extended: bool = False) -> dict:
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
    from dumen.benchmarks.capability_gate import ALL_TASKS, CAPABILITY_TASKS, CapabilityGate
    from dumen.benchmarks.steering_efficacy import SteeringEfficacyBench
    from dumen.core.miner import VectorMiner

    cfg = hf_model.config
    n_layers = getattr(cfg, "num_hidden_layers", None) or getattr(cfg, "n_layer")
    mid = max(1, n_layers // 2)
    target_layers = sorted({max(0, mid - 1), mid, min(n_layers - 1, mid + 1)})

    def last_token_acts(prompt: str) -> dict:
        inputs = {k: v.to(hf_model.device) for k, v in
                  tokenizer(_format_prompt(tokenizer, prompt), return_tensors="pt").items()}
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
    # B1 yetenek görevleri — steer-ÖNCESİ koşu (hooksuz, aynı deterministik hat)
    cap_tasks = ALL_TASKS if extended else CAPABILITY_TASKS
    cap_prompts = [t.prompt for t in cap_tasks]
    cap_un = {p: _generate(tokenizer, hf_model, p, max_new_tokens=32) for p in cap_prompts}

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
        cap_st = {p: _generate(tokenizer, hf_model, p, max_new_tokens=32) for p in cap_prompts}
    finally:
        manager.detach_all()

    result = SteeringEfficacyBench.measure_behavioral(
        attack_prompts=attack_prompts,
        unsteered_runner=unsteered.__getitem__,
        steered_runner=steered.__getitem__,
    )
    result["layers_steered"] = attached
    # TEK hook-oturumu içinde üretildi → ek externalite-ölçümü tutarlı; SteeringEngine
    # alfa-yönlü müdahale olduğundan etkinlik %0 ölçülse de kapı geçerlidir (steer
    # KOŞTU — dışsallık riski gerçek). Ölçüm her zaman raporlanır.
    result["capability"] = CapabilityGate.compare(
        CapabilityGate.evaluate(cap_un.__getitem__, tasks=cap_tasks),
        CapabilityGate.evaluate(cap_st.__getitem__, tasks=cap_tasks),
    )
    result["capability"]["task_set"] = "internal-12+gsm-style-10" if extended else "internal-12"
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
@click.option("--request-timeout", default=300.0, type=float, show_default=True,
              help="Siyah-kutu API isteği zaman aşımı (sn) — tek-VRAM ortamlarda soğuk model "
                   "yüklemesi/yavaş üretim için artırılabilir (kanıt bütünlüğü: süre aşımı hata verir, uydurma refüz değil)")
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
@click.option("--capability-extended", is_flag=True, default=False,
              help="B1 kapısını 12 iç-göreve ek 10 GSM-tarzı çok-adımlı sözel aritmetik "
                   "dış-görevle de koşar (--measure-steering gerektirir; ~2×32 üretim)")
def audit(model: str | None, endpoint: str | None, api_key: str | None,
          dataset: str | None, dataset_limit: int, request_timeout: float,
          output: str | None, refusal_baseline: bool, measure_steering: bool,
          capability_extended: bool):
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
    if capability_extended and not measure_steering:
        raise click.UsageError(
            "--capability-extended yalnız --measure-steering ile anlam taşır: dış-görev "
            "regresyonu steer-öncesi/sonrası ÇİFT koşu gerektirir. Tek başına ölçüm yoktur."
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
        runner = build_endpoint_runner(endpoint, model, api_key=api_key,
                                       timeout_s=request_timeout)  # type: ignore[arg-type]
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
            efficacy_result = _measure_steering_efficacy(tokenizer, hf_model,
                                                         extended=capability_extended)
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
            cap_result = efficacy_result.get("capability")
            if cap_result:
                _icon = {"pass": "🟢", "fail": "🔴"}.get(cap_result["verdict"], "⚪")
                click.echo(
                    f"   {_icon} Kapasite kapısı (B1): doğrulanmış görev doğruluğu "
                    f"%{cap_result['accuracy_unsteered_pct']} → %{cap_result['accuracy_steered_pct']} "
                    f"({cap_result['n_tasks']} görev) — sonuç: {cap_result['verdict'].upper()}"
                )

    # Risk skorları ELLE GİRİLMEZ: koşturulan örneklerin harm_score'larından türetilir.
    risk_scores = InspectBridge.derive_risk_scores(eval_res)
    if not risk_scores:
        raise click.ClickException("Değerlendirme örneklerinden risk skoru türetilemedi.")

    cap_value = efficacy_result.get("capability") if efficacy_result else None
    checker = EUAIActChecker()
    # Koruma iddiaları yalnız GERÇEKTEN koşturulan hatlara dayanır:
    # kırmızı takım değerlendirmesi bu komutta koştu; steering ise ancak
    # ölçüm başarıyla zafiyet azalttıysa "runtime steering var" sayılır — ve
    # B1 kapısı FAIL derse (kapasite bozuluyorsa) iddia geri çekilir:
    # zarar veren müdahale, müdahale sayılmaz.
    comp_status = checker.check_compliance(
        risk_scores=risk_scores,
        has_runtime_steering=(
            efficacy_value is not None
            and efficacy_value > 0
            and not (cap_value and cap_value["verdict"] == "fail")
        ),
        has_redteam_evaluation=True,
    )

    sc_gen = ScorecardGenerator()
    report = sc_gen.generate_report(
        model_name=audited_name,
        total_evaluations=eval_res.total_samples,
        risk_scores=risk_scores,
        compliance_status=comp_status,
        steering_efficacy=efficacy_value,
        capability_regression=cap_value,
    )

    md_report = sc_gen.to_markdown(report)
    click.echo("\n" + md_report + "\n")
    if refusal_baseline:
        click.echo(
            "ℹ️  Bu koşu refusal-baseline BORU HATTI doğrulamasıdır: steering ölçülmediği\n"
            "    için Art.14 bilinçli olarak ❌ görünür (kanıt yok → koruma iddiası yok).\n"
            "    Model-bazlı koruma kanıtı için: dumen audit --model <hf-id> --measure-steering\n"
        )

    # Kanıt-demeti (v0.7.5): audit ARTIK kendi zincirini kurar — README'nin
    # "audit → sign → export" vaatı ilk kez tek komutluk gerçek: .json çıktı,
    # raporu İÇİNDEN mühürleyen demettir (kök alanları report-kaydıyla
    # kapıdan geçer; ayrışma = bütünlük ihlali).
    chain = EvidenceChain()
    chain.append("evidence_channel", {
        "channel": ("blackbox-api" if blackbox else
                    "refusal-baseline" if refusal_baseline else
                    "whitebox-transformers"),
        "dataset": dataset or "default-suite",
        "measure_steering": measure_steering,
        "capability_extended": capability_extended,
    })
    chain.append("evaluation", {"total_evaluations": eval_res.total_samples,
                                "risk_scores": risk_scores})
    if efficacy_result:
        chain.append("steering", efficacy_result)
    chain.append("report", json.loads(report.model_dump_json()))

    if output:
        with open(output, "w", encoding="utf-8") as f:
            if output.endswith(".json"):
                bundle = json.loads(report.model_dump_json())
                bundle["evidence_chain"] = json.loads(chain.to_json())
                bundle["chain_head"] = chain.head_hash()
                f.write(json.dumps(bundle, indent=2, ensure_ascii=False))
            else:
                f.write(md_report)
        click.echo(f"📁 Rapor kaydedildi: {output}")


@cli.command("dossier")
@click.option("--model", default="dumen-target-llm", help="Dossier model adı")
@click.option("--output", default=None, help="Annex XI Markdown çıktı dosyası")
@click.option("--flops", default=3.2e26, type=float, help="Tahmini eğitim FLOPs")
@click.option("--gpu-hours", default=4.8e6, type=float, help="GPU küme-saatleri")
@click.option("--energy-mwh", default=21500.0, type=float, help="Eğitim enerjisi (MWh)")
@click.option("--provider", default=None,
              help="Sağlayıcı adı — verilmeyen kimlik ALAN-DEĞİL etiketiyle basılır "
                   "(placeholder'ın sessizce sunılabilir dosyaya dönüşmesi engellenir)")
@click.option("--contact", default=None, help="Regülatör-yüzü sağlayıcı iletişim adresi")
@click.option("--incident-log", default=None,
              help="SeriousIncident JSON-listesi dosyası — verildiğinde Art.55(1)(c) olay "
                   "takibi KOŞULLU demonstrated olur (sabit iddia yoktur; v0.7.5)")
def dossier(model: str, output: str | None, flops: float, gpu_hours: float, energy_mwh: float,
            provider: str | None, contact: str | None, incident_log: str | None):
    """📋 Refusal-baseline denetiminden Annex XI Dossier + CoP Matrisi Üretir."""
    click.echo(f"📋 '{model}' için Annex XI dossier derleniyor...")

    # 0) Olay-kaydı (yalnız GERÇEK kayıt varsa iddia — Y4 düzeltmesi): şema-bozuk
    # kayıt sessiz-atılmaz, fail-loud reddedilir (kanıt-ayaklı belge üretiriz).
    incidents = []
    if incident_log:
        try:
            raw = json.loads(Path(incident_log).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise click.ClickException(f"--incident-log okunamadı ({incident_log}): {exc}")
        if not isinstance(raw, list):
            raise click.ClickException("--incident-log bir SeriousIncident JSON-LİSTESİ olmalı.")
        for i, item in enumerate(raw):
            try:
                incidents.append(SeriousIncident.model_validate(item))
            except ValidationError as exc:
                raise click.ClickException(f"--incident-log kayıt #{i} şema-bozuk: {exc}")
        click.echo(f"   🚨 Olay defteri bağlandı: {len(incidents)} doğrulanmış SeriousIncident kaydı")
    else:
        click.echo("   🚨 Olay defteri yok (--incident-log) — IV.3 dürüstçe not_demonstrated basılacak")

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
    if incidents:
        chain.append("incidents", {
            "count": len(incidents),
            "ids": [x.incident_id for x in incidents],
            "source": incident_log,
        })

    # 3) Annex XI dossier
    gen = AnnexXIGenerator()
    dos = gen.generate_dossier(
        model_name=model,
        audit_report=report,
        identity=ModelIdentity(
            model_name=model, model_version="1.0.0",
            provider_name=provider or "[FIELD NOT SET — pass --provider before submission]",
            provider_contact=contact or "[FIELD NOT SET — pass --contact before submission]",
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
        has_annex_xi_dossier=True, has_evidence_chain=True,
        has_incident_tracking=bool(incidents),  # Y4: sabit-True yerine KAYIT-KOŞULLU
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
@click.option("--dim", default=4096, type=int,
              help="Gizli katman boyutu (head sayısına tam bölünmeli)")
@click.option("--sparsity", default=0.15, type=click.FloatRange(0.0, 1.0),
              help="KORUNAN davranışsal bileşen oranı (0.15 → %15 kalır, %85 seyreltilir)")
def steer_test(dim: int, sparsity: float):
    """⚡ StTP Yönlendirme ve OV Devresi Seyreltme Matematiğini Doğrular."""
    heads = 32  # OVCircuitMask varsayılan çoklu-head yapısı
    if dim <= 0 or dim % heads != 0:
        raise click.UsageError(
            f"--dim {heads}'in tam katı olmalı (girdi: {dim}) — "
            "ham AssertionError yerine net kullanıcı hatası.")
    click.echo(f"⚡ StTP ve Attention OV seyreltme testi (Boyut: {dim}, Korunan oran: %{sparsity*100:.1f})...")

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
    # O6 (v0.7.5): koşulsuz "BAŞARILI" YOK — matematikSEL invariant gerçekten
    # doğrulanır: steer sonrası zararlı-yön hizalanmasının BÜYÜKLÜĞÜ azalmalı ve
    # maske gerçekten seyreltmeli. Regresyonda sıfır-olmayan çıkış.
    reduced = abs(cos_sim_after) < abs(cos_sim_before) + 1e-6
    thinned = len(active_indices) < dim
    if reduced and thinned:
        click.echo("   ✅ Matematiksel doğrulama: |cos| azaldı + maske seyreltti — BAŞARILI")
    else:
        click.echo(f"   ❌ DOĞRULAMA BAŞARISIZ: |cos| azalmadı={not reduced} "
                   f"seyreltme-yok={not thinned} — steering matematiğinde regresyon!")
        raise SystemExit(1)


@cli.command()
@click.option("--model", required=True, help="HF kimliği (YEREL) veya --endpoint ile sunucu model etiketi")
@click.option("--endpoint", default=None, help="OpenAI-uyumlu sonuç (siyah-kutu yetenek koşusu)")
@click.option("--api-key", default=None)
@click.option("--request-timeout", default=300.0, type=float, show_default=True)
@click.option("--task-set",
              type=click.Choice(["internal-12", "gsm-style-10", "tr-style-10", "all"]),
              default="all", show_default=True,
              help="Koşacak görev seti; 'all' = internal-12+gsm-style-10+tr-style-10 (32 görev)")
@click.option("--output", default=None, help="JSON kanıt çıktı yolu")
def capability(model: str, endpoint: str | None, api_key: str | None,
               request_timeout: float, task_set: str, output: str | None):
    """🧭 B1 yetenek koşusu — bağımsız (steering gerektirmez); TR çok-dillilik
    kanıtı dahil. Deterministik doğrulayıcılar; LLM hakem YOK; dil-kanonik
    evet/hayır. Ölçülen sadece YETENEK-sinyalidir — refusal-stres iddia edilmez."""
    import time

    from dumen.benchmarks.capability_gate import CAPABILITY_TASKS, GSM_TASKS, TASK_SETS, TR_TASKS, CapabilityGate

    if task_set == "all":
        tasks = CAPABILITY_TASKS + GSM_TASKS + TR_TASKS
        set_name = "internal-12+gsm-style-10+tr-style-10"
    else:
        tasks = TASK_SETS[task_set]
        set_name = task_set

    if endpoint:
        from dumen.redteam.api_runner import build_endpoint_runner
        runner = build_endpoint_runner(endpoint, model, api_key=api_key,
                                       timeout_s=request_timeout)
        channel = "black-box-api"
    else:
        tokenizer, hf_model = _load_transformers_pair(model)
        if tokenizer is None:
            raise click.UsageError(f"Model '{model}' yüklenemedi — yetenek ölçülemez, uydurulmaz.")
        runner = lambda prompt: _generate(tokenizer, hf_model, prompt)  # noqa: E731
        channel = "local-hf-greedy"

    click.echo(f"🧭 '{model}' ({channel}) — {set_name}: {len(tasks)} görev...")
    result = CapabilityGate.evaluate(runner, tasks)
    result["task_set"] = set_name
    result["model"] = model
    result["channel"] = channel
    result["timestamp"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    result["note"] = ("capability signal only — NOT a refusal/stress measure; "
                      "tr-style-10 = özgün Türkçe görevler (B4-3.5 çok-dillilik dilimi)")

    chain = EvidenceChain()
    chain.append("capability", result)
    payload = {**result, "chain_head": chain.head_hash()}
    if output:
        with open(output, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
        click.echo(f"📁 Kanıt: {output}")
    click.echo(f"✅ accuracy %{result['accuracy_pct']} — geçen {len(result['passed'])}, "
               f"kalan {len(result['failed'])} {result['failed'] or ''}")
    base_floor = result["accuracy_pct"] >= CapabilityGate.BASE_FLOOR_PCT
    click.echo(f"📏 taban-yetenek bandı (≥%{CapabilityGate.BASE_FLOOR_PCT}): "
               f"{'VAR — ölçüm anlamlı' if base_floor else 'YOK — inconclusive (zorlamı)'}")


@cli.command()
@click.option("--model", required=True, help="Yerel HF modeli (aktivasyon-çıkarma için)")
@click.option("--pairs", default=16, show_default=True, type=int, help="Kontrastif çift sayısı")
@click.option("--poison-frac", default=0.25, show_default=True, type=float,
              help="Deneyde zehirlenecek çift oranı (token-takas sınıfı)")
@click.option("--swaps", default=3, show_default=True, type=int, help="Metin-başına kelime takası")
@click.option("--seed", default=20260915, show_default=True, type=int)
@click.option("--sweep", is_flag=True, default=False,
              help="takas-şiddeti eğrisi: recall/FPR/drift — 2..tüm-cümle (aynı seed, tek model yüklemesi)")
@click.option("--output", default=None, help="JSON rapor çıktı yolu")
def provenance(model: str, pairs: int, poison_frac: float, swaps: int,
               seed: int, sweep: bool, output: str | None):
    """🧬 Kontrastif-veri zehirlenmesine karşı provensans denetimi (ölçümlü)."""
    import numpy as np

    from dumen.benchmarks import ContrastiveBenchmarkSuite
    from dumen.core.provenance import DataProvenanceAuditor
    from dumen.core.types import RiskCategory

    tokenizer, hf_model = _load_transformers_pair(model)
    if tokenizer is None:
        raise click.ClickException(f"Model '{model}' yüklenemedi — provensans ölçülemez.")
    cfg = hf_model.config
    n_layers = getattr(cfg, "num_hidden_layers", None) or getattr(cfg, "n_layer")
    layer = max(0, (n_layers // 2))

    suite = ContrastiveBenchmarkSuite()
    pool: list = []
    for rc in RiskCategory:
        pool.extend(suite.get_contrastive_pairs(rc))
    # havuz küçüklüğü MAD eşiğini gevşetir → pool büyüklüğü raporlanmalı (ölçüm
    # fiziksinin kendisi bulgu: n=8'de 3-takas dedektörü ATEŞLEMEZ — bkz. sweep)
    if len(pool) < 3:
        raise click.ClickException("yeterli kontrastif çift yok — ölçüm yapılamaz, uydurulmaz.")
    pool = pool[:max(3, pairs)]

    def diff_matrix(pair_list):
        rows = []
        for harmful, safe in pair_list:
            acts = {}
            for side, text in (("h", harmful), ("s", safe)):
                inputs = {k: v.to(hf_model.device) for k, v in
                          tokenizer(_format_prompt(tokenizer, text),
                                    return_tensors="pt").items()}
                with torch.no_grad():
                    out = hf_model(**inputs, output_hidden_states=True)
                acts[side] = out.hidden_states[layer + 1][:, -1, :][0].float().cpu().numpy()
            rows.append(acts["h"] - acts["s"])
        return rows

    clean_rep = DataProvenanceAuditor.estimate(diff_matrix(pool))
    rng = np.random.default_rng(seed)
    poisoned_pairs, truth = DataProvenanceAuditor.poison_pairs(pool, poison_frac, rng, swaps)
    pois_rep = DataProvenanceAuditor.estimate(diff_matrix(poisoned_pairs))

    curve = []
    if sweep:
        # SABİT-ŞİDDET IZGARASI (2/8/16 takas): tam-aralık taraması uzun-metinli
        # çiftlerde saatlere yayıldı (canlı ders — süreç kesildi). 3 nokta
        # sınırlı-süre, sınırlı-iddia; ara-bant İNTERPOLASYONU YAPILMAZ.
        for level in (2, 8, 16):
            rr = np.random.default_rng(seed)
            sp, tr = DataProvenanceAuditor.poison_pairs(pool, poison_frac, rr, level)
            rep = DataProvenanceAuditor.estimate(diff_matrix(sp))
            ts = set(tr)
            curve.append({
                "swaps": level,
                "recall": round(len(ts & set(rep.flagged)) / max(1, len(ts)), 3),
                "fpr": round(len(set(rep.flagged) - ts) / max(1, len(pool) - len(ts)), 3),
                "mean_median_angle_deg": rep.mean_median_angle_deg,
                "cosine_median": rep.cosine_median,
                "pool_drift": (DataProvenanceAuditor.drift_verdict(
                    clean_rep.cosines, rep.cosines, seed=seed)
                    if len(clean_rep.cosines) >= 5 else None),
            })

    truth_set = set(truth)
    tp = truth_set & set(pois_rep.flagged)
    recall = round(len(tp) / len(truth_set), 3)
    fpr = round(len(set(pois_rep.flagged) - truth_set) / max(1, len(pool) - len(truth_set)), 3)
    drift_med = round(pois_rep.mean_median_angle_deg, 3)

    result = {
        "model": model, "layer": layer, "n_pairs": len(pool),
        "device": str(next(hf_model.parameters()).device),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "seed": seed, "swaps_per_text": swaps, "poison_frac": poison_frac,
        "clean": {"flags": clean_rep.flagged, "cosine_median": clean_rep.cosine_median,
                  "cosine_mad": clean_rep.cosine_mad, "mean_median_angle_deg": clean_rep.mean_median_angle_deg},
        "poisoned": {"truth": sorted(truth_set), "flagged": pois_rep.flagged,
                     "recall": recall, "false_positive_rate": fpr,
                     "mean_median_angle_deg": drift_med,
                     "cosine_median": pois_rep.cosine_median},
        "robustness": "median-direction vs mean-direction under identical poisoning",
        "pair_cosines_clean": [round(float(x), 6) for x in clean_rep.cosines],
        "pair_cosines_poisoned": [round(float(x), 6) for x in pois_rep.cosines],
        # küçük havuzda null-testi güvenilmez → None = "ölçülmedi" (çökme yok)
        "pool_drift": (DataProvenanceAuditor.drift_verdict(
            clean_rep.cosines, pois_rep.cosines, seed=seed)
            if len(clean_rep.cosines) >= 5 else None),
        "pool_size": len(pool),
        "sweep_note": "düşük-şiddette recall=0 BEKLENEN kalibrasyon sonucu — sabit 2/8/16 izgarası ara-bant iddiası taşımaz",
        "intensity_curve": curve,
        "citation": "vulnerability surface: arXiv:2606.05958 (contrastive data poisoning); detector combination: Dümen",
    }
    chain = EvidenceChain()
    chain.append("provenance", result)
    if output:
        with open(output, "w", encoding="utf-8") as f:
            json.dump({**result, "chain_head": chain.head_hash()}, f, indent=2, ensure_ascii=False)
        click.echo(f"📁 Provensans raporu: {output}")
    click.echo(f"🧬 ölçüm: {len(truth_set)} zehirli çift → recall %{recall*100:.1f}, FPR %{fpr*100:.1f}; "
               f"sürükleme açısı (mean↔median) {drift_med}°; temiz-set bayrak: {clean_rep.flagged}")
    dv = result["pool_drift"]
    if dv is None:
        click.echo("🌊 havuz-sürüklenmesi: n<5 — ölçülmedi (null-test güvenilmez)")
    else:
        click.echo(f"🌊 havuz-sürüklenmesi: Δcosmed {dv['delta']:+.4f} "
                   f"null[{dv['null_lo']:.4f},{dv['null_hi']:.4f}] → "
                   f"{'TESPİT ✓' if dv['drift_detected'] else 'eşik-içi (tespit YOK)'} "
                   f"[bootstrap n={dv['n_boot']}, seed={dv['seed']}]")
    for c in curve:
        cd = c["pool_drift"]
        click.echo(f"   📈 şiddet {c['swaps']:>2} takas → recall %{c['recall']*100:.0f} "
                   f"(FPR %{c['fpr']*100:.0f}, Δcosmed {cd['delta']:+.4f} "
                   f"{'drift✓' if cd['drift_detected'] else 'drift✗'})")


@cli.command()
@click.option("--input", "in_path", required=True, help="Dışa aktarılacak rapor/dossier (.md)")
@click.option("--output", default=None, help="HTML çıktı yolu (varsayılan: <input>.html)")
@click.option("--title", default=None, help="Belge başlığı (varsayılan: ilk başlık ya da dosya adı)")
@click.option("--chain", "chain_path", default=None, help="Kanıt zinciri (.json) — altbilgiye mühür gömülür")
@click.option("--sig", "sig_path", default=None, help="İmza kaydı (.sig) — altbilgiye gömülür")
def export(in_path: str, output: str | None, title: str | None,
           chain_path: str | None, sig_path: str | None):
    """🖨️ Rapor/dossier'ı denetçi-formatı TEK-DOSYA yazdırılabilir HTML'e çevirir."""
    try:
        text = Path(in_path).read_text(encoding="utf-8")
    except OSError as exc:
        raise click.ClickException(str(exc))
    if title is None:
        m = re.match(r"^#\s+(.+)$", text, flags=re.MULTILINE)
        title = m.group(1).strip() if m else Path(in_path).stem
    out = output or (str(in_path) + ".html")
    try:
        Path(out).write_text(
            render_report_html(text, title, chain_path=chain_path, sig_path=sig_path),
            encoding="utf-8",
        )
    except OSError as exc:
        raise click.ClickException(str(exc))
    click.echo(f"🖨️ Denetçi-formatı HTML yazıldı: {out}")
    if chain_path or sig_path:
        click.echo("   (mühür altbilgisi gömüldü — dosya tek başına kanıt bağlamı taşır)")


@cli.command()
@click.option("--interval", default=3600.0, show_default=True, type=float,
              help="Tur'lar arası bekleme (saniye)")
@click.option("--runs", default=4, show_default=True, type=int, help="Koşulacak denetim sayısı")
@click.option("--out", "out_path", default="watch_chain.json", show_default=True,
              help="İzleme kanıt-zinciri çıktısı (.json)")
@click.option("--audit-arg", multiple=True,
              help="Her turda `dumen audit`'e geçirilecek arg (tekrarlanabilir), "
                   "örn. --audit-arg=--model --audit-arg=phi3")
def watch(interval: float, runs: int, out_path: str, audit_arg: tuple[str, ...]):
    """⏱️ Sürekli-denetim: her turda tam `dumen audit` koşar, turları kanıt-zincirler."""
    from dumen.watch import run_watch
    try:
        result = run_watch(list(audit_arg), interval, runs, out_path)
    except ValueError as exc:
        raise click.ClickException(str(exc))
    click.echo(f"⏱️ watch {result['status']}: {result['completed']} tamam / "
               f"{result['failed']} hatalı → {result['out_path']}")
    if result["status"] == "halted_consecutive_failures":
        raise SystemExit(2)


@cli.command("keys")
@click.option("--name", required=True, help="Anahtar tabanı (çıktı: <name>.key + <name>.pub)")
@click.option("--dir", "out_dir", default=".", show_default=True, help="Çıktı dizini")
@click.option("--force", is_flag=True, help="Zaten varsa ez (mevcut imzalar geçersiz olur!)")
def keys_cmd(name: str, out_dir: str, force: bool):
    """🔐 Denetim raporları için yeni Ed25519 imza çifti üretir."""
    try:
        info = generate_keypair(name, out_dir, overwrite=force)
    except FileExistsError as exc:
        raise click.ClickException(str(exc))
    click.echo(f"🔐 Anahtar çifti üretildi: {info['private_key_path']} (0600) + {info['public_key_path']}")
    click.echo(f"   Parmak izi: {info['fingerprint']}")
    click.echo("   Dürüstlük sınırı: kimlik = anahtar muhafazası; eIDAS nitelikli imza DEĞİLDİR.")


@cli.command()
@click.option("--chain", "chain_path", required=True, help="İmzalanacak kanıt zinciri (.json)")
@click.option("--key", "key_path", required=True, help="Ed25519 gizli anahtar (.key)")
@click.option("--name", "signer_name", required=True, help="İmzalayan etiketi (kurum/kiş adı)")
@click.option("--output", default=None, help=".sig çıktı yolu (varsayılan: <chain>.sig)")
def sign(chain_path: str, key_path: str, signer_name: str, output: str | None):
    """✍️ Kanıt zincirinin HEAD'ini Ed25519 ile imzalar (yüklemede bütünlük kapısı çalışır)."""
    try:
        rec = sign_chain_file(chain_path, key_path, signer_name, sig_path=output)
    except (ValueError, OSError) as exc:
        raise click.ClickException(str(exc))
    click.echo(f"✍️ İmzalandı: head={rec.head_hash[:16]}… ({rec.chain_length} kayıt) → {output or chain_path + '.sig'}")
    click.echo(f"   İmzalayan: {rec.signer_name} | {rec.pubkey_fingerprint} | {rec.signed_at}")


@cli.command()
@click.option("--chain", "chain_path", required=True, help="Doğrulanacak zincir (.json)")
@click.option("--sig", "sig_path", required=True, help="İmza dosyası (.sig)")
@click.option("--pub", "pub_path", required=True, help="Kamuya açık anahtar (.pub)")
def verify(chain_path: str, sig_path: str, pub_path: str):
    """✅ Zincir bütünlüğü + imza + head eşleşmesini üçlü doğrular (exit code = sonuç)."""
    try:
        out = verify_chain_file(chain_path, sig_path, pub_path)
    except (ValueError, OSError) as exc:
        raise click.ClickException(str(exc))
    if out.valid:
        click.echo(f"✅ DOĞRULANDI — head={out.head_hash[:16]}… imzalayan={out.signer_name} "
                   f"({out.pubkey_fingerprint}) @ {out.signed_at}")
    else:
        click.echo(f"🛑 GEÇERSİZ — {out.reason}", err=True)
        raise SystemExit(1)


if __name__ == "__main__":
    cli()
