"""
tests/test_example_pipeline.py
=============================
examples/full_audit_pipeline.py'nin bütünlük testi — README'nin vaat ettiği
script gerçekten koşmalı ve tüm çıktıları üretmeli.
"""

import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
SCRIPT = REPO / "examples" / "full_audit_pipeline.py"


@pytest.fixture(scope="module")
def pipeline_run(tmp_path_factory):
    out_dir = tmp_path_factory.mktemp("dumen_pipeline")
    res = subprocess.run(
        [sys.executable, str(SCRIPT), "--out", str(out_dir)],
        capture_output=True,
        text=True,
        cwd=str(REPO),
        timeout=300,
    )
    return res, out_dir


class TestExamplePipeline:
    def test_script_exits_zero(self, pipeline_run):
        res, _ = pipeline_run
        assert res.returncode == 0, res.stderr[-2000:]

    def test_all_artifacts_produced(self, pipeline_run):
        _, out_dir = pipeline_run
        expected = [
            "annex_xi_dossier.md",
            "annex_xi_dossier.json",
            "cop_matrix.md",
            "evidence_chain.json",
        ]
        for name in expected:
            assert (out_dir / name).exists(), f"{name} üretilmedi"

    def test_dossier_contains_sections(self, pipeline_run):
        _, out_dir = pipeline_run
        md = (out_dir / "annex_xi_dossier.md").read_text(encoding="utf-8")
        assert "ANNEX XI" in md
        assert "MODEL IDENTITY" in md
        assert "RED-TEAM MATRIX" in md

    def test_evidence_chain_valid_json(self, pipeline_run):
        import json
        _, out_dir = pipeline_run
        chain = json.loads((out_dir / "evidence_chain.json").read_text(encoding="utf-8"))
        assert isinstance(chain, list)
        assert len(chain) >= 5
        # Zincir yapısı: her kayıt prev_hash taşır
        assert all("prev_hash" in e and "entry_hash" in e for e in chain)

    def test_cop_matrix_full_coverage(self, pipeline_run):
        _, out_dir = pipeline_run
        md = (out_dir / "cop_matrix.md").read_text(encoding="utf-8")
        assert "AUDIT.1" in md
        assert "✅ demonstrated" in md
