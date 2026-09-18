"""
tests/test_cli.py
=================
CLI komut satırı arayüzü testleri (Click CliRunner) — v0.5.0 gerçek denetim zinciri.
"""

import json
import os
import tempfile

from click.testing import CliRunner

from dumen.cli import cli
from dumen.reports.evidence_chain import EvidenceChain


def test_cli_help_and_version():
    runner = CliRunner()
    res = runner.invoke(cli, ["--version"])
    assert res.exit_code == 0
    assert "dumen" in res.output.lower()

    res_help = runner.invoke(cli, ["--help"])
    assert res_help.exit_code == 0
    assert "serve" in res_help.output
    assert "audit" in res_help.output
    assert "steer-test" in res_help.output


def test_cli_steer_test_command():
    runner = CliRunner()
    res = runner.invoke(cli, ["steer-test", "--dim", "64", "--sparsity", "0.2"])
    assert res.exit_code == 0
    assert "BAŞARILI" in res.output
    assert "Aktif OV Boyut Sayısı" in res.output


def test_cli_moe_joint_test_command():
    """MoE joint-intervention teşhisi: 3 bileşen + sessiz-başarısızlık bayrağı."""
    runner = CliRunner()
    res = runner.invoke(cli, ["moe-joint-test", "--dim", "64", "--k", "4"])
    assert res.exit_code == 0
    assert "BAŞARILI" in res.output
    # joint mod tüm bileşenleri uygulamalı
    assert "3 bileşen" in res.output
    # tek-bileşen modu sessiz başarısızlığı işaretlemeli
    assert "sessiz-başarısızlık=True" in res.output
    # arXiv referansı teşhiste olmalı
    assert "2609.09793" in res.output


def test_cli_moe_joint_test_help_lists_doctrine():
    """Komut docstring'i dürüst sınırı belirtmeli."""
    runner = CliRunner()
    res = runner.invoke(cli, ["moe-joint-test", "--help"])
    assert res.exit_code == 0
    assert "2609.09793" in res.output


def test_cli_amplification_scan_command():
    """TLCM amplifikasyon tespiti: rejim işaretlenmeli."""
    runner = CliRunner()
    res = runner.invoke(cli, ["amplification-scan", "--alpha-max", "3.0", "--steps", "12"])
    assert res.exit_code == 0
    # seed=42 ile α≈2.25'te amplifikasyon gözlenir (doğrulanmış değer)
    assert "amplifiye" in res.output
    assert "2609.07876" in res.output
    assert "güvenli-alpha" in res.output


def test_cli_amplification_scan_help_states_boundary():
    """Komut docstring'i 'tespit, önleme değil' sınırını belirtmeli."""
    runner = CliRunner()
    res = runner.invoke(cli, ["amplification-scan", "--help"])
    assert res.exit_code == 0
    assert "2609.07876" in res.output


def test_cli_audit_requires_model_or_baseline():
    """Model belirtilmeden audit koşmak reddedilmeli — sahte skor üretimi engellenir."""
    runner = CliRunner()
    res = runner.invoke(cli, ["audit"])
    assert res.exit_code != 0
    # Hata mesajı yönlendirme içermeli
    assert "--refusal-baseline" in res.output or "refusal-baseline" in res.output


def test_cli_audit_refusal_baseline_produces_real_evidence_chain():
    """
    Refusal-baseline hattı: tüm örnekler standart refusal şablonuyla değerlendirilir.
    Risk skorları ELLE GİRİLMEZ — JudgeEvaluator'ın gerçek harm_score çıktısından türetilir.
    Bu test kanıt zincirinin uçtan uca gerçek olduğunu doğrular.
    """
    runner = CliRunner()
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        json_path = tmp.name

    try:
        res = runner.invoke(cli, ["audit", "--refusal-baseline", "--output", json_path])
        assert res.exit_code == 0, res.output
        assert os.path.exists(json_path)

        with open(json_path, "r", encoding="utf-8") as f:
            report = json.load(f)

        # Karne gerçek zincirden üretilmiş olmalı
        assert report["model_tested"] == "refusal-baseline-channel"
        assert report["total_evaluations"] == 4  # 4 standart görev
        # Skorlar JudgeEvaluator'dan geldi: refusal detected → harm düşük ama nonzero olabildiğince gerçek
        assert set(report["risk_breakdown"].keys()) >= {"cyber_attack", "bio_hazard", "deception", "sandbox_escape"}
        for cat, score in report["risk_breakdown"].items():
            assert 0.0 <= score <= 1.0, f"{cat} skoru [0,1] aralığında olmalı: {score}"
        # Refusal şablonu regex fast-path'e takılırsa skor 0'a yakın çıkmalı
        assert report["risk_breakdown"]["cyber_attack"] < 0.5
    finally:
        if os.path.exists(json_path):
            os.remove(json_path)


def test_cli_audit_refusal_baseline_markdown():
    """Refusal-baseline hattı Markdown karnesi de üretmeli."""
    runner = CliRunner()
    with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as tmp:
        md_path = tmp.name

    try:
        res = runner.invoke(cli, ["audit", "--refusal-baseline", "--output", md_path])
        assert res.exit_code == 0, res.output
        with open(md_path, "r", encoding="utf-8") as f:
            content = f.read()
        assert "DÜMEN NÖRAL DENETİM VE GÜVENLİK KARNESİ" in content
        assert "refusal-baseline-channel" in content
    finally:
        if os.path.exists(md_path):
            os.remove(md_path)


def test_cli_audit_unknown_model_fails_cleanly():
    """
    Var olmayan/erişilemeyen model kimliği temiz hata vermeli — sessizce
    sahte kanıt üretmemeli. (transformers yoksa ya da model inilemezse
    UsageError; her iki durumda da exit_code != 0.)
    """
    runner = CliRunner()
    res = runner.invoke(cli, ["audit", "--model", "dumen/nonexistent-model-xyz"])
    # transformers kurulu değilse runner None → UsageError
    # kuruluysa model indirilemez → yine None → UsageError
    assert res.exit_code != 0


def test_cli_dossier_command_full_chain():
    """Dossier komutu: Annex XI + CoP matrisi + kanıt zinciri tek çağrıda üretilmeli."""
    runner = CliRunner()
    with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as tmp:
        path = tmp.name
    try:
        res = runner.invoke(cli, ["dossier", "--model", "target-1", "--output", path])
        assert res.exit_code == 0, res.output
        assert "ANNEX XI" in res.output
        assert "CODE OF PRACTICE" in res.output
        # Kanıt zinciri geçerli raporlanmalı
        assert "geçerli: True" in res.output
        with open(path, encoding="utf-8") as f:
            content = f.read()
        assert "target-1" in content
        assert "AUDIT.1" in content  # CoP matrisi dosyada
        # Kanıt dürüstlüğü: baseline kanalı dosyada damgalı, sahte etkinlik yok
        assert "refusal-baseline" in content
        assert "96.4" not in content and "96.2" not in content
    finally:
        os.remove(path)


def test_cli_serve_no_upstream_honest_message(monkeypatch):
    """
    serve --upstream yok: 'Simülasyon/Test Modu' YANILTICI mesajı kaldırıldı;
    artık 503 döneceği dürüstçe söylenir. uvicorn.run monkeypatch'lenir.
    """
    import dumen.cli as cli_mod

    called = {}

    def _fake_run(app, host, port):
        called["ran"] = True

    monkeypatch.setattr(cli_mod.uvicorn, "run", _fake_run)
    runner = CliRunner()
    res = runner.invoke(cli, ["serve", "--port", "8999"])
    assert res.exit_code == 0, res.output
    assert called.get("ran") is True
    assert "Simülasyon" not in res.output
    assert "503" in res.output  # dürüst uyarı


def test_cli_audit_no_fabricated_efficacy_in_json():
    """refusal-baseline JSON çıktısında steering_efficacy null olmalı (uydurma sayı yok)."""
    import json

    runner = CliRunner()
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        path = tmp.name
    try:
        res = runner.invoke(cli, ["audit", "--refusal-baseline", "--output", path])
        assert res.exit_code == 0, res.output
        report = json.load(open(path, encoding="utf-8"))
        assert report["steering_efficacy"] is None, \
            "ölçülmemiş etkinlik JSON'a sayı olarak sızmamalı"
    finally:
        os.remove(path)


def test_cli_signing_end_to_end(tmp_path):
    """keys → zincir üret → sign → verify: gerçek dosya akışı, exit 0."""
    from dumen.reports.evidence_chain import EvidenceChain
    runner = CliRunner()
    res = runner.invoke(cli, ["keys", "--name", "auditor", "--dir", str(tmp_path)])
    assert res.exit_code == 0 and "Parmak izi" in res.output

    chain = EvidenceChain()
    chain.append("mining", {"stage": "vectorminer", "vectors": 128})
    chain.append("dossier", {"annex": "XI", "hash_anchored": True})
    chain_file = tmp_path / "denetim.json"
    chain_file.write_text(chain.to_json(), encoding="utf-8")

    res = runner.invoke(cli, ["sign", "--chain", str(chain_file),
                              "--key", str(tmp_path / "auditor.key"),
                              "--name", "Acme Denetim A.Ş."])
    assert res.exit_code == 0 and "İmzalandı" in res.output
    assert (tmp_path / "denetim.json.sig").exists()

    res = runner.invoke(cli, ["verify", "--chain", str(chain_file),
                              "--sig", str(tmp_path / "denetim.json.sig"),
                              "--pub", str(tmp_path / "auditor.pub")])
    assert res.exit_code == 0 and "DOĞRULANDI" in res.output


def test_cli_verify_tampered_chain_exits_nonzero(tmp_path):
    """Tahrif edilmiş zincir → verify exit 1 + gerekçe (kapı gerçek olmalı)."""
    from dumen.reports.evidence_chain import EvidenceChain
    runner = CliRunner()
    runner.invoke(cli, ["keys", "--name", "k", "--dir", str(tmp_path)])
    chain = EvidenceChain()
    chain.append("evaluation", {"task": "t0"})
    cf = tmp_path / "c.json"
    cf.write_text(chain.to_json(), encoding="utf-8")
    runner.invoke(cli, ["sign", "--chain", str(cf), "--key", str(tmp_path / "k.key"),
                        "--name", "x"])
    data = json.loads(cf.read_text())
    entries = data["evidence_chain"]  # ≥0.8.0: dict içinde liste
    entries[0]["payload"]["task"] = "tahrif"
    cf.write_text(json.dumps(data), encoding="utf-8")
    res = runner.invoke(cli, ["verify", "--chain", str(cf),
                              "--sig", str(cf) + ".sig",
                              "--pub", str(tmp_path / "k.pub")])
    assert res.exit_code == 1
    assert "GEÇERSİZ" in res.output


def test_cli_error_paths_are_loud(tmp_path):
    """Honest-degradation: her komuta olmayan-dosya/bozuk-girdi → ClickException,
    sessiz-çöküş ya da traceback YOK (exit 1 + insan-mesajı)."""
    r = CliRunner()
    bad = str(tmp_path / "yok.json")

    res = r.invoke(cli, ["sign", "--chain", bad, "--key", "k", "--name", "n"])
    assert res.exit_code == 1 and "yok.json" in res.output

    res = r.invoke(cli, ["verify", "--chain", bad, "--sig", "s", "--pub", "p"])
    assert res.exit_code == 1 and "No such file" in res.output

    res = r.invoke(cli, ["export", "--input", bad])
    assert res.exit_code == 1

    res = r.invoke(cli, ["keys", "--name", "a", "--dir", "/proc/definitely-yok-alan"])
    assert res.exit_code == 1

    res = r.invoke(cli, ["watch", "--runs", "0", "--out", str(tmp_path / "w.json")])
    assert res.exit_code == 1 and "runs" in res.output

    # imzalayan anahtarı var ama zincir BOZUK → bütünlük kapısı mesajı
    from dumen.reports.signing import generate_keypair
    kp = generate_keypair("e", str(tmp_path))
    broken = tmp_path / "bozuk.json"
    broken.write_text("[{\"index\": 0}]", encoding="utf-8")
    res = r.invoke(cli, ["sign", "--chain", str(broken),
                         "--key", kp["private_key_path"], "--name", "n"])
    assert res.exit_code == 1 and "bütünlük" in res.output
    # gerçek hash-tampering senaryosu (şema-geçerli, zincir-kırık) de aynı kapı
    good = EvidenceChain()
    good.append("a", {"x": 1})
    good.append("b", {"y": 2})
    tam = json.loads(good.to_json())
    tam_entries = tam["evidence_chain"]  # ≥0.8.0: dict içinde liste
    tam_entries[-1]["payload"] = {"y": 999}
    tf = tmp_path / "tampered.json"
    tf.write_text(json.dumps(tam), encoding="utf-8")
    res = r.invoke(cli, ["sign", "--chain", str(tf), "--key", kp["private_key_path"],
                         "--name", "n"])
    assert res.exit_code == 1 and "bütünlük" in res.output


def test_cli_dossier_identity_flags_honest_placeholder(tmp_path):
    r = CliRunner()
    out = tmp_path / "d.md"
    res = r.invoke(cli, ["dossier", "--model", "m1", "--output", str(out)])
    assert res.exit_code == 0, res.output
    md = out.read_text(encoding="utf-8")
    assert "FIELD NOT SET" in md  # sunulabilir-öncesi kimlik boşluğu görünür olmalı

    res = r.invoke(cli, ["dossier", "--model", "m1", "--provider", "Acme Labs",
                         "--contact", "audit@acme.example", "--output", str(out)])
    assert res.exit_code == 0
    md = out.read_text(encoding="utf-8")
    assert "Acme Labs" in md and "FIELD NOT SET" not in md

def test_cli_dossier_incident_log_gates_the_claim(tmp_path):
    """Y4 (v0.7.5): IV.3 'demonstrated' YALNIZ gerçek SeriousIncident kaydıyla;
    sabit-True yalanı ölüdür. Bozuk kayıt fail-loud reddedilir."""
    runner = CliRunner()
    # (a) defsiz: IV.3 dürüstçe not_demonstrated
    out0 = tmp_path / "d0.md"
    res0 = runner.invoke(cli, ["dossier", "--model", "m", "--output", str(out0)])
    assert res0.exit_code == 0, res0.output
    assert "Olay defteri yok" in res0.output
    md0 = out0.read_text(encoding="utf-8")
    iv3 = [ln for ln in md0.splitlines() if "IV.3" in ln][0]
    assert "not_demonstrated" in iv3, iv3

    # (b) geçerli kayıt: demonstrated + zincire incidents-stage düşer
    rec = {
        "incident_id": "INC-001", "detected_at": "2026-09-16T00:00:00Z",
        "risk_category": "jailbreak", "severity": "critical",
        "description": "Gateway bypass attempt detected and contained via steering.",
        "affected_model": "m", "detection_module": "gateway.validator",
        "steering_intervention_applied": True, "containment_actions": ["rate_limit"],
        "reportable_to_office": True,
    }
    log = tmp_path / "inc.json"
    log.write_text(json.dumps([rec]), encoding="utf-8")
    out1 = tmp_path / "d1.md"
    res1 = runner.invoke(cli, ["dossier", "--model", "m", "--output", str(out1),
                               "--incident-log", str(log)])
    assert res1.exit_code == 0, res1.output
    assert "doğrulanmış SeriousIncident" in res1.output
    iv3b = [ln for ln in out1.read_text(encoding="utf-8").splitlines() if "IV.3" in ln][0]
    assert "demonstrated" in iv3b and "not_demonstrated" not in iv3b, iv3b

    # (c) bozuk kayıt: sessiz-atım YOK — fail-loud
    log.write_text(json.dumps([{"incident_id": "x"}]), encoding="utf-8")
    res2 = runner.invoke(cli, ["dossier", "--model", "m", "--output",
                               str(tmp_path / "d2.md"), "--incident-log", str(log)])
    assert res2.exit_code != 0
    assert "şema-bozuk" in res2.output


def test_cli_steer_test_invariant_actually_asserts():
    """O6 (v0.7.5): steer-test'in BAŞARISI koşulsuz değil — invariant ihlalinde
    sıfır-olmayan çıkış + seyreltme-yolu ve bozuk-dim UsageError kanıtı."""
    runner = CliRunner()
    ok = runner.invoke(cli, ["steer-test", "--dim", "64", "--sparsity", "0.2"])
    assert ok.exit_code == 0 and "azaldı" in ok.output
    fail = runner.invoke(cli, ["steer-test", "--dim", "64", "--sparsity", "1.0"])
    assert fail.exit_code != 0 and "BAŞARISIZ" in fail.output
    bad = runner.invoke(cli, ["steer-test", "--dim", "1"])
    assert bad.exit_code != 0 and "tam katı" in bad.output
