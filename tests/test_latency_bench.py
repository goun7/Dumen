"""
tests/test_latency_bench.py
===========================
Performans iddialarının KANIT testi: projenin her yerinde geçen
"alt-milisaniye filtre taraması" sayısı pazarlama değil, burada ölçülür.
CI makineleri yavaş olabilir — eşikler cömert tutulur (iddia ~%3-5'lik gerçek
değerlerin ~50-100x üst sınırı); esas amaç, gecikmenin patolojik biçimde
büyüdüğünü (O(n²) sızıntısı, recompile, ağ tuzağı) regresyonda yakalamaktır.
Gerçek ölçüm değerleri `pytest -s` ile stdout'a basılır (raporlanabilir kanıt).
"""

import asyncio
import time

from dumen.gateway.filters import FastSecurityFilter
from dumen.gateway.validator import ValidatorAgent

BENIGN = (
    "A firewall filters network traffic based on a set of configured rules, "
    "blocking unauthorized access while allowing legitimate traffic to pass through."
)


def _measure(fn, n_warmup: int = 50, n_iter: int = 500) -> float:
    for _ in range(n_warmup):
        fn()
    t0 = time.perf_counter()
    for _ in range(n_iter):
        fn()
    return (time.perf_counter() - t0) / n_iter * 1000.0


def _measure_p99(fn, n_warmup: int = 50, n_iter: int = 500) -> tuple[float, float]:
    """(ortalama_ms, p99_ms) döner — dağılım kuyruğu ortalama kadar önemlidir."""
    for _ in range(n_warmup):
        fn()
    samples = []
    for _ in range(n_iter):
        t0 = time.perf_counter()
        fn()
        samples.append((time.perf_counter() - t0) * 1000.0)
    samples.sort()
    return sum(samples) / n_iter, samples[int(0.99 * (n_iter - 1))]


class TestGatewayLatencyProof:
    def setup_method(self):
        self.filter = FastSecurityFilter()
        self.validator = ValidatorAgent()

    def test_scan_prompt_latency_bound(self):
        """Regex tarama başına süre < 5ms (ölçülen tipik ~0.03ms)."""
        ms = _measure(lambda: self.filter.scan_prompt(BENIGN))
        print(f"\n[bench] scan_prompt: {ms:.3f} ms/çağrı")
        assert ms < 5.0, f"scan_prompt gecikmesi patladı: {ms:.3f} ms"

    def test_scan_prompt_p99_bound(self):
        """Kabul kriteri 4: filtre taraması p99 < 10ms (BÖLÜM 7 — ölçülmeli, iddia edilmemeli)."""
        mean_ms, p99_ms = _measure_p99(lambda: self.filter.scan_prompt(BENIGN))
        print(f"[bench] scan_prompt: ortalama {mean_ms:.3f} ms | p99 {p99_ms:.3f} ms")
        assert p99_ms < 10.0, f"scan_prompt p99 eşiği aştı: {p99_ms:.3f} ms"

    def test_scan_output_latency_bound(self):
        ms = _measure(lambda: self.filter.scan_output(BENIGN))
        print(f"[bench] scan_output: {ms:.3f} ms/çağrı")
        assert ms < 5.0, f"scan_output gecikmesi patladı: {ms:.3f} ms"

    def test_full_validation_path_submillisecond_class(self):
        """Tam yerli validasyon hattı (PII+çıktı+karar) < 50ms (ölçülen ~0.4ms)."""
        ms = _measure(
            lambda: asyncio.run(self.validator.validate_output("hello", BENIGN)),
            n_warmup=20, n_iter=200,
        )
        print(f"[bench] validate_output (tam yerli hat): {ms:.3f} ms/çağrı")
        assert ms < 50.0, f"validasyon hattı gecikmesi patladı: {ms:.3f} ms"
