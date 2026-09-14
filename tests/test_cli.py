"""
tests/test_cli.py
=================
CLI komut satırı arayüzü testleri (Click CliRunner).
"""

import os
import tempfile
import pytest
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


def test_cli_audit_command_output_file():
    runner = CliRunner()
    with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        res = runner.invoke(cli, ["audit", "--model", "llama-3-8b", "--output", tmp_path])
        assert res.exit_code == 0
        assert os.path.exists(tmp_path)
        with open(tmp_path, "r", encoding="utf-8") as f:
            content = f.read()
        assert "DÜMEN NÖRAL DENETİM VE GÜVENLİK KARNESİ" in content
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
