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
