"""Sürekli-denetim planlayıcısı — abonelik ürünün çekirdek halkası.

`dumen watch` her turda TAM bir `dumen audit` koşusu spawn eder (bu modülün
işi zamanlama + kanıt defteri, denetim mantığını KENDİNDE YENİDEN YAZMAZ —
anti-entropi: tek sahiplik audit'te kalır). Her tur zincire kanıt kaydı olur;
tur rc'si, süresi ve rapor-yolu append-only SHA-256 zincirinde birikir;
izleme dosyası tek başına doğrulanabilir kanıttır (imzalanabilir de — signing).

Dürüst sınırlar: planlayıcı systemd/cron'un yerini tutmaz (process ölürse
uyumaz — restart politikası operatöründe); aralık-ötesi takvim yok; çift
çalıştırmayı tek-dosya-kilidiyle değil KULLANICI bilinciyle varsayar (ileride
lockfile doğal genişlemedir — uydurulmuş sağlamlık iddiası yok).
"""
from __future__ import annotations

import shlex
import subprocess
import sys
import time
from typing import Any, Callable, Dict, List, Optional

from .reports.evidence_chain import EvidenceChain

MAX_CONSECUTIVE_FAILURES = 3


def _utc() -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())


def _default_spawn(argv: List[str]) -> int:
    proc = subprocess.run(argv, capture_output=True, text=True)  # noqa: S603
    return proc.returncode


def run_watch(
    audit_args: List[str],
    interval: float,
    runs: int,
    out_path: str,
    *,
    sleeper: Callable[[float], None] = time.sleep,
    spawn: Optional[Callable[[List[str]], int]] = None,
    clock: Callable[[], float] = time.monotonic,
) -> Dict[str, Any]:
    """`runs` tur `dumen audit <audit_args>` koşar; aralarda `interval` saniye
    uyur. Her tur + özet zincire yazılır; zincir out_path'e atomik-benzeri
    (yaz-then-rename) saklanır ve geri-yükleme-doğrulamalıdır.

    injectables (sleeper/spawn/clock) testleri deterministik yapar — üretim
    yolları default'lardır. returns: {status, completed, failed, out_path}
    """
    if runs < 1:
        raise ValueError("runs en az 1 olmalı")
    if interval < 0:
        raise ValueError("interval negatif olamaz")
    spawn = spawn or _default_spawn
    chain = EvidenceChain()
    failures = 0
    completed = 0
    failed = 0
    status = "done"

    for i in range(runs):
        started = _utc()
        t0 = clock()
        rc = spawn([sys.executable, "-m", "dumen.cli", "audit", *audit_args])
        duration = round(clock() - t0, 3)
        entry = {
            "run": i + 1,
            "started_at": started,
            "exit_code": rc,
            "duration_s": duration,
            "command": "dumen audit " + shlex.join(audit_args),
        }
        chain.append("watch-run", entry)
        if rc == 0:
            failures = 0
            completed += 1
        else:
            failed += 1
            failures += 1
            if failures >= MAX_CONSECUTIVE_FAILURES:
                status = "halted_consecutive_failures"
                chain.append("watch-halt", {
                    "reason": f"{failures} ardışık başarısız tur — fail-loud duruş",
                    "at_run": i + 1,
                })
                break
        if i < runs - 1 and status == "done":
            sleeper(interval)

    summary = {
        "status": status,
        "completed": completed,
        "failed": failed,
        "scheduled_runs": runs,
        "interval_s": interval,
        "finished_at": _utc(),
    }
    chain.append("watch-summary", summary)

    from pathlib import Path
    tmp = Path(str(out_path) + ".tmp")
    tmp.write_text(chain.to_json(), encoding="utf-8")
    # geri-yükleme kapısı: yazdığımız zincir from_json bütünlüğünden geçmeli
    EvidenceChain.from_json(tmp.read_text(encoding="utf-8"))
    tmp.rename(out_path)
    return {**summary, "out_path": str(out_path)}
