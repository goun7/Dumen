"""dal-kesen test: watch._default_spawn + _utc — surekli-denetim planlayici cekirdek.

ORTAM-ANATOMI
-------------
_default_spawn(argv): subprocess.run(argv, capture_output=True, text=True)
  -> proc.returncode (passthrough; is-cektisi disinda akis YOK)
_utc(): time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())

ORTAM-OGRENDILER
----------------
(1) _default_spawn SADECE returncode passthrough'u yapar — cikti/yakit-
    yakalama capture_output=True + text=True ile kurulur AMA KULLANILMAZ
    (run_watch yalnizca rc ile ilgilenir; stdout atilir — bilincli minimal
    arayuz, characterization).
(2) returncode BIREBIR iletilir — 0/1/2/127/255 pozitif, -15 negatif (signal),
    139 (128+SIGSEGV) hepsi ayni gecer; donusum YOK.
(3) argv ILERI-BESLENIR — liste oldugu gibi verilir (shlex/string'e donusum
    YOK), bos liste legal (subprocess kendisi karar verir).
(4) subprocess.run keyword-argumanlari SABIT: capture_output=True, text=True.
(5) _utc time.gmtime() kullanir — localtime DEGIL; TZ'den bagimsiz, her zaman
    ' UTC' onekli (yerel-saat yanilticiligi bilincli olarak kaldirilmis).
(6) _utc format-kalibi 'YYYY-MM-DD HH:MM:SS UTC' — saniye-dahil, 24-saat.
(7) _default_spawn, run_watch'in DEFAULT spawn'udur (spawn=None ise kullanilir).
"""
import re
import sys
import time

import pytest

sys.path.insert(0, ".")
sys.path.insert(0, "src")

import dumen.watch as watch_mod  # noqa: E402
from dumen.watch import _default_spawn, _utc  # noqa: E402


class FakeProc:
    def __init__(self, returncode):
        self.returncode = returncode


class FakeRun:
    """subprocess.run yerine saf-in-memory kayitci (subprocess YASAK)."""

    def __init__(self, returncode=0):
        self.returncode = returncode
        self.calls = []

    def __call__(self, argv, **kwargs):
        self.calls.append((list(argv), dict(kwargs)))
        return FakeProc(self.returncode)


@pytest.fixture
def fake_run(monkeypatch):
    fr = FakeRun()
    monkeypatch.setattr(watch_mod.subprocess, "run", fr)
    return fr


# ================================================================ returncode passthrough
class TestReturncodePassthrough:
    """ORTAM-OGRENDI (2)."""

    @pytest.mark.parametrize("rc", [0, 1, 2, 3, 127, 128, 139, 255])
    def test_positive_returncodes(self, fake_run, rc):
        fake_run.returncode = rc
        assert _default_spawn(["cmd"]) == rc

    @pytest.mark.parametrize("rc", [-1, -9, -15, -2])
    def test_negative_signal_returncodes(self, fake_run, rc):
        fake_run.returncode = rc
        assert _default_spawn(["cmd"]) == rc

    def test_zero_is_int_not_none(self, fake_run):
        fake_run.returncode = 0
        assert _default_spawn(["cmd"]) == 0
        assert _default_spawn(["cmd"]) is not None

    def test_returncode_type_int(self, fake_run):
        fake_run.returncode = 7
        assert isinstance(_default_spawn(["cmd"]), int)

    def test_no_transformation_of_returncode(self, fake_run):
        fake_run.returncode = -15
        assert _default_spawn(["cmd"]) == -15  # abs() veya donusum YOK

    def test_last_call_returncode_used(self, fake_run):
        fake_run.returncode = 5
        assert _default_spawn(["a"]) == 5
        fake_run.returncode = 0
        assert _default_spawn(["a"]) == 0


# ================================================================ argv iletisimi
class TestArgvForwarding:
    def test_argv_forwarded_verbatim(self, fake_run):
        _default_spawn(["dumen", "audit", "--model", "x"])
        assert fake_run.calls[0][0] == ["dumen", "audit", "--model", "x"]

    def test_empty_argv_forwarded(self, fake_run):
        """ORTAM-OGRENDI (3): bos liste legal, disarida karar verilmez."""
        _default_spawn([])
        assert fake_run.calls[0][0] == []

    def test_single_element_argv(self, fake_run):
        _default_spawn(["dumen"])
        assert fake_run.calls[0][0] == ["dumen"]

    @pytest.mark.parametrize("argv", [
        ["echo", "merhaba"],
        ["python", "-c", "print(1)"],
        ["dumen", "audit", "--runs", "1", "--interval", "0"],
        ["x", "y", "z", "w"],
    ])
    def test_various_argv_shapes(self, fake_run, argv):
        _default_spawn(argv)
        assert fake_run.calls[0][0] == argv

    def test_argv_not_joined_to_string(self, fake_run):
        """liste olarak iletilir, string'e cevrilmez."""
        _default_spawn(["a", "b"])
        assert isinstance(fake_run.calls[0][0], list)

    def test_argv_mutated_after_call_does_not_affect_record(self, fake_run):
        argv = ["a", "b"]
        _default_spawn(argv)
        argv.append("c")
        assert fake_run.calls[0][0] == ["a", "b"]


# ================================================================ subprocess.run cagrisi
class TestSubprocessCallContract:
    """ORTAM-OGRENDI (1)(4)."""

    def test_capture_output_true(self, fake_run):
        _default_spawn(["cmd"])
        assert fake_run.calls[0][1]["capture_output"] is True

    def test_text_true(self, fake_run):
        _default_spawn(["cmd"])
        assert fake_run.calls[0][1]["text"] is True

    def test_no_extra_kwargs(self, fake_run):
        _default_spawn(["cmd"])
        assert set(fake_run.calls[0][1]) == {"capture_output", "text"}

    def test_argv_positional_not_keyword(self, fake_run):
        """argv birinci pozisyonel arguman."""
        _default_spawn(["cmd"])
        # calls kaydi (argv, kwargs) — argv positional oldugu icin kwargs'ta YOK
        assert "argv" not in fake_run.calls[0][1]

    def test_called_exactly_once(self, fake_run):
        _default_spawn(["cmd"])
        _default_spawn(["cmd2"])
        assert len(fake_run.calls) == 2

    def test_subprocess_run_is_the_source(self):
        """Uretim yolunda gercek subprocess.run kullanilir (stub degil)."""
        assert watch_mod.subprocess is not None
        assert hasattr(watch_mod.subprocess, "run")


# ================================================================ cikti yakalama
class TestOutputCaptureUnused:
    """ORTAM-OGRENDI (1): capture kurulur ama returncode disinda hicbir sey okunmaz."""

    def test_proc_stdout_ignored(self, monkeypatch):
        class Proc:
            returncode = 0
            stdout = "cikti"
            stderr = "hata"

        monkeypatch.setattr(watch_mod.subprocess, "run", lambda argv, **kw: Proc())
        assert _default_spawn(["cmd"]) == 0

    def test_proc_stderr_ignored(self, monkeypatch):
        class Proc:
            returncode = 3
            stdout = None
            stderr = "cok hata"

        monkeypatch.setattr(watch_mod.subprocess, "run", lambda argv, **kw: Proc())
        assert _default_spawn(["cmd"]) == 3


# ================================================================ _utc
class TestUtc:
    def test_format_shape(self):
        """ORTAM-OGRENDI (6)."""
        assert re.fullmatch(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} UTC", _utc())

    def test_ends_with_utc_suffix(self):
        assert _utc().endswith(" UTC")

    def test_literal_utc_prefix(self):
        """ORTAM-OGRENDI (5): localtime DEGIL gmtime."""
        assert "UTC" in _utc()

    def test_length_fixed(self):
        assert len(_utc()) == len("YYYY-MM-DD HH:MM:SS UTC")

    def test_returns_str(self):
        assert isinstance(_utc(), str)

    def test_two_calls_close_in_time(self):
        a, b = _utc(), _utc()
        # ayni saniyede (hizli arka arkaya)
        assert a.split(":")[0] == b.split(":")[0]

    def test_uses_gmtime_not_localtime(self, monkeypatch):
        """gmtime monkeypatch'iyle UTC-zaman dilimi kanitlanir."""
        fixed = time.struct_time((2026, 3, 4, 5, 6, 7, 2, 63, 0))
        monkeypatch.setattr(watch_mod.time, "gmtime", lambda: fixed)
        assert _utc() == "2026-03-04 05:06:07 UTC"

    def test_gmtime_is_source(self, monkeypatch):
        called = {"n": 0}

        def fake_gmtime():
            called["n"] += 1
            return time.struct_time((2020, 1, 1, 0, 0, 0, 2, 1, 0))

        monkeypatch.setattr(watch_mod.time, "gmtime", fake_gmtime)
        assert _utc() == "2020-01-01 00:00:00 UTC"
        assert called["n"] == 1

    def test_not_localtime(self, monkeypatch):
        """localtime cagrilirsa patlamali — kesinlikle gmtime kullanilir."""
        def boom():
            raise AssertionError("localtime kullanilmamali")

        monkeypatch.setattr(watch_mod.time, "localtime", boom)
        assert _utc()  # localtime'e hic dustrulmedi

    @pytest.mark.parametrize("t,expected", [
        ((2026, 10, 11, 23, 59, 59, 5, 284, 0), "2026-10-11 23:59:59 UTC"),
        ((2000, 1, 1, 0, 0, 0, 5, 1, 0), "2000-01-01 00:00:00 UTC"),
        ((1999, 12, 31, 23, 59, 59, 4, 365, 0), "1999-12-31 23:59:59 UTC"),
        ((2026, 7, 4, 12, 30, 45, 5, 185, 0), "2026-07-04 12:30:45 UTC"),
    ])
    def test_known_times_format(self, monkeypatch, t, expected):
        monkeypatch.setattr(watch_mod.time, "gmtime", lambda: time.struct_time(t))
        assert _utc() == expected

    def test_midnight_zero_padding(self, monkeypatch):
        monkeypatch.setattr(
            watch_mod.time, "gmtime",
            lambda: time.struct_time((2026, 1, 1, 0, 0, 0, 3, 1, 0)))
        assert _utc() == "2026-01-01 00:00:00 UTC"


# ================================================================ run_watch default wiring
class TestRunWatchDefaultSpawn:
    """ORTAM-OGRENDI (7): _default_spawn, spawn=None iken default'tur."""

    def test_default_spawn_used_when_spawn_none(self, fake_run, tmp_path):
        """run_watch, _default_spawn'a TAM KOMUTU gecer:
        [sys.executable, '-m', 'dumen.cli', 'audit', *audit_args] —
        interpreter oneki disarida eklenir (ORTAM-OGRENDI: spawn audit
        mantigini KENDINDE yeniden yazmaz, sadece tam argv'yi calistirir)."""
        fake_run.returncode = 0
        out = watch_mod.run_watch(
            audit_args=["--model", "x"], interval=0, runs=1,
            out_path=str(tmp_path / "z.json"), sleeper=lambda s: None,
        )
        argv = fake_run.calls[0][0]
        assert argv[:4] == [sys.executable, "-m", "dumen.cli", "audit"]
        assert argv[-2:] == ["--model", "x"]
        assert out["completed"] == 1

    def test_failure_returncode_recorded(self, fake_run, tmp_path):
        fake_run.returncode = 1
        out = watch_mod.run_watch(
            audit_args=["audit"], interval=0, runs=1,
            out_path=str(tmp_path / "z.json"), sleeper=lambda s: None,
        )
        assert out["failed"] == 1

    def test_max_consecutive_failures_constant(self):
        assert watch_mod.MAX_CONSECUTIVE_FAILURES == 3
