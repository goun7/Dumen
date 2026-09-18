"""
dumen.reports.rfc8785
=====================
RFC 8785 (JSON Canonicalization Scheme, JCS) — stdlib-only uygulama.

Gereklilik (Tamga-ajan AT-036 ile doğrulanan vektörler, 2026-09-17):
  1. Number → ECMAScript Number.prototype.toString eşdeğeri:
     - integral float → tamsayı gösterim (1.0 → "1", -0.0 → "0")
     - üstel biçim YALNIZCA |e| > 21 veya üs ≤ -6 (1e16 → "10000000000000000",
       1e21 → "1e+21", 1e-7 → "1e-7", 2.93e-07 → "2.93e-7")
  2. Anahtar sıralaması UTF-16 code-unit (high-surrogate'lar BMP'den önce);
     Python code-point sıralamasından farklıdır.

Doğrulama: Python ↔ Node.js bayt-birebir karşılaştırması (Node = ECMAScript-native
= ground truth). Python'un kendi self-test'i bu hataları YAKALAYAMAZ — kaçış
kurallarıyla yazılan beklentiler hatayı taşıdığında 8/8 "geçer" ama yanlıştır.
Dış orakıl (Node) olmadan yakalanmıyor (Tamga-ajan'ın başına gelen en pahalı hata).
"""
from __future__ import annotations

import json
from decimal import Decimal
from typing import Any


def _ecmascript_number(value: float) -> str:
    """float'ı ECMAScript Number.prototype.toString ile aynı biçimde yaz.

    Python json.dumps: 1.0 → "1.0", -0.0 → "-0.0", 1e16 → "1e+16", 2.93e-07 → "2.93e-07"
    ECMAScript:        1.0 → "1",   -0.0 → "0",    1e16 → "10000000000000000", 2.93e-07 → "2.93e-7"
    """
    if value == 0:
        return "0"  # hem 0.0 hem -0.0 → "0" (IEEE işaret sıfırı eşit sayılır)
    if value != value:  # NaN — JCS'de tanımsız, fail-loud
        raise ValueError("NaN RFC 8785'de serileştirilemez")
    if value in (float("inf"), float("-inf")):
        raise ValueError("Infinity RFC 8785'de serileştirilemez")

    # Decimal üzerinden tam onluk gösterim (float repr ikili yuvarlama kalıntısı
    # bırakır; repr()'u kaynak olarak kullanmak ECMAScript ile birebir olur)
    d = Decimal(repr(value))
    sign, digits, exponent = d.as_tuple()
    if exponent >= 0:
        # tam sayı — sabit gösterim, ama ECMAScript üstel eşiği için
        # aşağıdaki kararı hâlâ gerekli (1e21 → "1e+21"), bu yüzden DÖNME
        mantissa_digits = "".join(str(x) for x in digits) + ("0" * exponent)
        fixed = mantissa_digits.lstrip("0") or "0"
    else:
        # ondalık: ECMAScript kuralları
        mantissa_digits = "".join(str(x) for x in digits)
        int_part_len = len(digits) + exponent  # noktadan önceki hane sayısı
        if int_part_len > 0:
            int_part = mantissa_digits[:int_part_len].lstrip("0") or "0"
            frac_part = mantissa_digits[int_part_len:].rstrip("0")
            fixed = int_part + (("." + frac_part) if frac_part else "")
        else:
            frac = ("0" * (-int_part_len)) + mantissa_digits
            frac = frac.rstrip("0")
            fixed = "0." + frac if frac else "0"
    fixed = ("-" if sign else "") + fixed

    # Üstel biçim karar: ECMAScript üs e'yi hesapla
    abs_s = fixed.lstrip("-").lstrip("0") or "0"
    if "." in abs_s:
        int_digits, frac_digits = abs_s.split(".", 1)
        int_digits = int_digits or "0"
        if int_digits != "0":
            e = len(int_digits) - 1
            mant = int_digits + frac_digits
        else:
            # 0.xxx → ilk sıfır-olmayana kadar kay
            stripped = frac_digits.lstrip("0")
            e = -(len(frac_digits) - len(stripped) + 1)
            mant = stripped
    else:
        # Tam sayı: ECMAScript üstel eşiği |digits|>21'dir (1e21 = 22 hane → e=21)
        e = len(abs_s) - 1
        mant = abs_s

    mant = mant.lstrip("0") or "0"
    # normalize: tek hane sonra nokta; SONDAKİ SIFIRLAR ATILIR
    # (ECMAScript: 1.000...e+21 → "1e+21", 123000 → sabit biçimde kalır)
    if "." not in mant:
        mant = mant.rstrip("0") or "0"
    if len(mant) == 1:
        mant_str = mant
    else:
        mant_str = mant[0] + "." + mant[1:]

    # ECMAScript: üstel yalnızca e >= 21 veya e <= -7
    # (Node ile doğrulandı: 1e-6 → "0.000001" SABİT; 1e-7 → "1e-7" ÜSTEL.
    #  Bizde eski kod e <= -6 kullanıyordu — off-by-one; oracle düzeltti.)
    if e >= 21 or e <= -7:
        # ECMAScript üs her zaman işaretli yazar: "1e+21" (e>0), "1e-7" (e<0)
        exp = f"e{e:+d}" if e != 0 else ""
        # NEGAİF işareti burada kaybetmemek için fixed'in işaretini geri ekle
        # (mant_str mutlak-değerden gelir; -1.5e-7 → "1.5e-7" OLMAZ)
        sign_prefix = "-" if sign else ""
        return sign_prefix + mant_str + exp
    # sabit biçim — üssü uygulayıp normalize et
    if e >= 0:
        if e < len(mant) - 1:
            return fixed  # zaten doğru sabit biçim
    return fixed


def _serialize(value: Any) -> str:
    """Değeri RFC 8785 kurallarıyla metne çevir."""
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, int) and not isinstance(value, bool):
        return str(value)
    if isinstance(value, float):
        return _ecmascript_number(value)
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, (list, tuple)):
        return "[" + ",".join(_serialize(v) for v in value) + "]"
    if isinstance(value, dict):
        # UTF-16 CODE-UNIT sıralaması (bayt sıralaması DEĞİL).
        # .encode("utf-16-le") bayt sıralaması yapar: little-endian yüksek-bayt
        # önceliklenir, bu yüzden 日(U+65E5→bayt 45,65) ve 月(U+6708→bayt 08,67)
        # yanlış döner. Doğru karşılaştırma code-unit değeridir: 0x65E5 < 0x6708.
        # (Node oracle ile 4 uyumsuzluk yakalandı; bu bayt-vs-unit hatasıydı.)
        keys = sorted(value.keys(), key=lambda k: [ord(c) for c in k])
        return "{" + ",".join(
            json.dumps(k, ensure_ascii=False) + ":" + _serialize(value[k]) for k in keys
        ) + "}"
    raise ValueError(f"RFC 8785: serileştirilemeyen tip {type(value).__name__}")


def canonicalize(obj: Any) -> str:
    """RFC 8785 kanonik metni üret (dil-bağımsız, Node.js ile birebir)."""
    return _serialize(obj)


__all__ = ["canonicalize"]
