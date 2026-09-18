"""tests/test_watch.py — sürekli-denetim planlayıcısı (deterministic injectables).

Kanıt zorunlulukları: tur-sayısı=sleep-sayısı+1, ardışık-hata fail-loud duruşu,
hata-sonrası-başarı sayaç sıfırlaması, zincirin geri-yükleme-doğrulanabilirliği,
CLI'nin halt'ta nonzero çıkması.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from click.testing import CliRunner

from dumen import watch as watch_mod
from dumen.cli import cli
from dumen.reports.evidence_chain import EvidenceChain
from dumen.watch import run_watch


class Fake:
    def __init__(self, rcs):
        self.rcs = list(rcs)
        self.calls = 0
        self.sleeps = []
        self.argvs = []

    def spawn(self, argv):
        rc = self.rcs[min(self.calls, len(self.rcs) - 1)]
        self.calls += 1
        self.argvs.append(argv)
        return rc

    def sleeper(self, s):
        self.sleeps.append(s)

    def clock(self):
        return self.calls * 1.5  # türasyonları ayırt-edilebilir kılar


def test_happy_schedule(tmp_path):
    f = Fake([0, 0, 0])
    out = tmp_path / "w.json"
    res = run_watch(["--model", "phi3"], 30.0, 3, str(out),
                    sleeper=f.sleeper, spawn=f.spawn, clock=f.clock)
    assert res["status"] == "done" and res["completed"] == 3
    assert f.calls == 3 and f.sleeps == [30.0, 30.0]  # turlar arası, sondan sonra UYKU YOK
    chain = EvidenceChain.from_json(out.read_text(encoding="utf-8"))
    stages = [e.stage for e in chain.get_entries()]
    assert stages == ["watch-run", "watch-run", "watch-run", "watch-summary"]
    run1 = chain.get_entries()[0].payload
    assert run1["exit_code"] == 0 and "--model" in run1["command"]
    assert run1["duration_s"] == 1.5


def test_three_consecutive_failures_halt_loud(tmp_path):
    f = Fake([1])
    out = tmp_path / "w.json"
    res = run_watch([], 5.0, 10, str(out), sleeper=f.sleeper, spawn=f.spawn, clock=f.clock)
    assert res["status"] == "halted_consecutive_failures"
    assert f.calls == 3  # 4. tura ASLA başlanmaz (fail-loud)
    chain = EvidenceChain.from_json(out.read_text(encoding="utf-8"))
    stages = [e.stage for e in chain.get_entries()]
    assert "watch-halt" in stages and stages[-1] == "watch-summary"


def test_recovery_resets_failure_counter(tmp_path):
    f = Fake([1, 1, 0, 1, 1, 0, 0])
    out = tmp_path / "w.json"
    res = run_watch([], 5.0, 7, str(out), sleeper=f.sleeper, spawn=f.spawn, clock=f.clock)
    assert res["status"] == "done" and res["completed"] == 3 and res["failed"] == 4
    assert f.calls == 7  # hiçbir noktada 3 ardışık olmadı → erken duruş YOK


def test_invalid_params_rejected(tmp_path):
    f = Fake([0])
    for kwargs in ({"runs": 0}, {"interval": -1.0}):
        try:
            run_watch([], kwargs.get("interval", 1.0), kwargs.get("runs", 1),
                      str(tmp_path / "x.json"), sleeper=f.sleeper,
                      spawn=f.spawn, clock=f.clock)
            raise AssertionError("ValueError beklenirdi: " + str(kwargs))
        except ValueError:
            pass


def test_no_tmp_leftover_and_atomicity(tmp_path):
    f = Fake([0])
    out = tmp_path / "w.json"
    run_watch([], 0.0, 1, str(out), sleeper=f.sleeper, spawn=f.spawn, clock=f.clock)
    assert out.exists()
    assert not (tmp_path / "w.json.tmp").exists()


class TestCliWatch:
    def test_watch_cli_exit_zero(self, tmp_path, monkeypatch):
        monkeypatch.setattr(watch_mod, "_default_spawn", lambda argv: 0)
        out = tmp_path / "cliw.json"
        res = CliRunner().invoke(cli, ["watch", "--interval", "0", "--runs", "2",
                                       "--out", str(out),
                                       "--audit-arg=--model", "--audit-arg=phi3"])
        assert res.exit_code == 0, res.output
        data = json.loads(out.read_text(encoding="utf-8"))
        # ≥0.8.0: to_json dict üretir — kayıtlar evidence_chain altında
        entries = data["evidence_chain"] if isinstance(data, dict) else data
        assert sum(1 for e in entries if e["stage"] == "watch-run") == 2

    def test_watch_cli_halt_nonzero(self, tmp_path, monkeypatch):
        monkeypatch.setattr(watch_mod, "_default_spawn", lambda argv: 1)
        res = CliRunner().invoke(cli, ["watch", "--interval", "0", "--runs", "9",
                                       "--out", str(tmp_path / "h.json")])
        assert res.exit_code == 2
        assert "halted" in Path(str(tmp_path / "h.json")).read_text(encoding="utf-8")


def test_default_spawn_real_subprocess(tmp_path):
    """Üretim spawn'ı GERÇEK subprocess'tir: ölü bir komutla rc!=0 döner."""
    rc = watch_mod._default_spawn([sys.executable, "-c", "raise SystemExit(3)"])
    assert rc == 3
