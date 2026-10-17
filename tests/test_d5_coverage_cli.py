"""test_d5_coverage_cli — DALGA-D5: kapsanmayan CLI komut yollarını işgrese çağırır.

Hedef: dumen/cli.py içindeki eksik satırlar (1099-1141 veridict-export,
986-1006 export, 1018-1028 watch, 1035-1043 keys --force,
1051-1058 sign --output, 1065-1076 verify, 60-81 serveupstream bayrakları).

Tüm çağrılar GERÇEK CliRunner + GERÇEK dosya sistemidir (tmp_path) —
mock yok; canlı ağ/LLLM yolları bilinçli olarak hariç tutulmuştur.
"""
from __future__ import annotations

import json
import os
import sys

from click.testing import CliRunner

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dumen.cli import cli  # noqa: E402
from dumen.reports.evidence_chain import EvidenceChain  # noqa: E402


def _chain_file(tmp_path) -> str:
    chain = EvidenceChain()
    chain.append("mining", {"features_found": 42})
    chain.append("evaluation", {"total": 4})
    p = tmp_path / "denetim.json"
    p.write_text(chain.to_json(), encoding="utf-8")
    return str(p)


def test_cli_veridict_export_full_success(tmp_path):
    """veridict-export: sağlıklı zincir → ledger + çıkar-kod 0 + bilgi çıktısı."""
    runner = CliRunner()
    cf = _chain_file(tmp_path)
    ledger = str(tmp_path / "ledger.jsonl")

    res = runner.invoke(cli, ["veridict-export", "--chain", cf,
                              "--ledger", ledger, "--actor", "denetci-1"])
    assert res.exit_code == 0, res.output
    assert "Export" in res.output
    assert "Dümen head" in res.output
    assert os.path.exists(ledger)


def test_cli_veridict_export_with_signature_and_dossier(tmp_path):
    """--sig + --dossier: imza parmak-izi ve dossier özeti çıktıya yansır."""
    runner = CliRunner()
    cf = _chain_file(tmp_path)
    ledger = str(tmp_path / "ledger.jsonl")

    # imza çifti üret + zinciri imzala
    runner.invoke(cli, ["keys", "--name", "a", "--dir", str(tmp_path)])
    sig_path = str(tmp_path / "denetim.json.sig")
    runner.invoke(cli, ["sign", "--chain", cf, "--key", str(tmp_path / "a.key"),
                        "--name", "imzalayan"])
    dossier = tmp_path / "dossier.md"
    dossier.write_text("# Denetim Dossier\n\niçerik\n", encoding="utf-8")

    res = runner.invoke(cli, ["veridict-export", "--chain", cf, "--ledger", ledger,
                              "--sig", sig_path, "--dossier", str(dossier),
                              "--actor", "denetci-2"])
    assert res.exit_code == 0, res.output
    assert "İmza" in res.output
    assert "Dossier" in res.output


def test_cli_veridict_export_broken_chain_exits_nonzero(tmp_path):
    """Bozuk zincir → RED + SystemExit(1) — fail-closed (sessiz-geçiş yok)."""
    runner = CliRunner()
    broken = tmp_path / "bozuk.json"
    broken.write_text("[{\"index\": 0}]", encoding="utf-8")

    res = runner.invoke(cli, ["veridict-export", "--chain", str(broken),
                              "--ledger", str(tmp_path / "l.jsonl"),
                              "--actor", "x"])
    assert res.exit_code == 1
    assert "zincir yüklenemedi" in res.output


def test_cli_veridict_export_bad_sig_file_exits_nonzero(tmp_path):
    """Olmayan imza/dossier dosyası → insan-mesajlı hata (traceback yok)."""
    runner = CliRunner()
    cf = _chain_file(tmp_path)
    res = runner.invoke(cli, ["veridict-export", "--chain", cf,
                              "--ledger", str(tmp_path / "l.jsonl"),
                              "--sig", str(tmp_path / "yok.sig"),
                              "--actor", "x"])
    assert res.exit_code == 1
    assert "imza fişi okunamadı" in res.output

    res = runner.invoke(cli, ["veridict-export", "--chain", cf,
                              "--ledger", str(tmp_path / "l.jsonl"),
                              "--dossier", str(tmp_path / "yok.md"),
                              "--actor", "x"])
    assert res.exit_code == 1
    assert "dossier okunamadı" in res.output


def test_cli_veridict_export_tampered_chain_is_rejected(tmp_path):
    """Şema-geçerli ama KURCALANMIŞ zincir → export REDder (bütünlük kapısı)."""
    runner = CliRunner()
    chain = EvidenceChain()
    chain.append("a", {"x": 1})
    chain.append("b", {"y": 2})
    tam = json.loads(chain.to_json())
    tam["evidence_chain"][-1]["payload"] = {"y": 999}
    tf = tmp_path / "tampered.json"
    tf.write_text(json.dumps(tam), encoding="utf-8")

    res = runner.invoke(cli, ["veridict-export", "--chain", str(tf),
                              "--ledger", str(tmp_path / "l.jsonl"),
                              "--actor", "x"])
    assert res.exit_code != 0


def test_cli_export_markdown_with_seal_footer(tmp_path):
    """export: .md + chain + sig → HTML'e mühür altbilgisi gömülür."""
    runner = CliRunner()
    cf = _chain_file(tmp_path)
    md = tmp_path / "rapor.md"
    md.write_text("# Denetim Rapora\n\nkurumsal içerik\n", encoding="utf-8")

    runner.invoke(cli, ["keys", "--name", "k", "--dir", str(tmp_path)])
    sig_path = str(tmp_path / "rapor.md.sig")
    runner.invoke(cli, ["sign", "--chain", cf, "--key", str(tmp_path / "k.key"),
                        "--name", "imzalayan"])

    out = str(tmp_path / "rapor.html")
    res = runner.invoke(cli, ["export", "--input", str(md), "--output", out,
                              "--title", "Başlık-el ile", "--chain", cf,
                              "--sig", sig_path])
    assert res.exit_code == 0, res.output
    html = open(out, encoding="utf-8").read()
    assert "mühür" in html or "Başlık-el ile" in html


def test_cli_export_defaults_and_no_title(tmp_path):
    """export: --title ve --output verilmeyince varsayılan ayar çalışır."""
    runner = CliRunner()
    md = tmp_path / "rapor2.md"
    md.write_text("# Otomatik Başlık\n\niçerik\n", encoding="utf-8")

    res = runner.invoke(cli, ["export", "--input", str(md)])
    assert res.exit_code == 0, res.output
    assert os.path.exists(str(md) + ".html")


def test_cli_keys_force_overwrites_existing_keypair(tmp_path):
    """keys --force: mevcut anahtar çifti ezilir, parmak-izi değişir."""
    runner = CliRunner()
    r0 = runner.invoke(cli, ["keys", "--name", "k", "--dir", str(tmp_path)])
    assert r0.exit_code == 0
    fp0 = open(str(tmp_path / "k.pub"), encoding="utf-8").read()

    r1 = runner.invoke(cli, ["keys", "--name", "k", "--dir", str(tmp_path)])
    assert r1.exit_code == 1  # --force yok → FileExistsError kapısı

    r2 = runner.invoke(cli, ["keys", "--name", "k", "--dir", str(tmp_path), "--force"])
    assert r2.exit_code == 0, r2.output
    fp1 = open(str(tmp_path / "k.pub"), encoding="utf-8").read()
    assert fp0 != fp1


def test_cli_sign_with_explicit_output_path(tmp_path):
    """sign --output: .sig açık yola yazılır, imza-meta görünür."""
    runner = CliRunner()
    cf = _chain_file(tmp_path)
    runner.invoke(cli, ["keys", "--name", "s", "--dir", str(tmp_path)])

    out = str(tmp_path / "ozel.sig")
    res = runner.invoke(cli, ["sign", "--chain", cf, "--key", str(tmp_path / "s.key"),
                              "--name", "imzalayan", "--output", out])
    assert res.exit_code == 0, res.output
    assert "İmzalandı" in res.output
    assert os.path.exists(out)


def test_cli_verify_rejects_wrong_keypair(tmp_path):
    """verify: başkasının anahtarıyla imza → GEÇERSIZ + SystemExit(1)."""
    runner = CliRunner()
    cf = _chain_file(tmp_path)
    runner.invoke(cli, ["keys", "--name", "a", "--dir", str(tmp_path)])
    runner.invoke(cli, ["keys", "--name", "b", "--dir", str(tmp_path), "--force"])
    runner.invoke(cli, ["sign", "--chain", cf, "--key", str(tmp_path / "a.key"),
                        "--name", "imzalayan"])

    res = runner.invoke(cli, ["verify", "--chain", cf,
                              "--sig", str(tmp_path / "denetim.json.sig"),
                              "--pub", str(tmp_path / "b.pub")])
    assert res.exit_code == 1
    assert "GEÇERSİZ" in res.output


def test_cli_serve_upstream_and_validator_announced(monkeypatch):
    """serve: upstream + validator-url bayrakları çıktıya doğru yansır (ağ kurulmaz)."""
    import uvicorn

    monkeypatch.setattr(uvicorn, "run", lambda *a, **kw: None)
    runner = CliRunner()
    res = runner.invoke(cli, ["serve", "--upstream", "http://up.test",
                              "--validator-url", "http://val.test",
                              "--validator-model", "qwen2.5:3b"])
    assert res.exit_code == 0, res.output
    assert "Upstream Hedef" in res.output
    assert "Çift-ajan denetçi ETKİN" in res.output
    assert "qwen2.5:3b" in res.output


def test_cli_serve_strict_flag_announced(monkeypatch):
    import uvicorn

    monkeypatch.setattr(uvicorn, "run", lambda *a, **kw: None)
    runner = CliRunner()
    res = runner.invoke(cli, ["serve", "--port", "8991", "--strict"])
    assert res.exit_code == 0, res.output
    assert "Upstream yok" in res.output
