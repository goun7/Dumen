# Issue #4 — yanıt taslağı (GÖNDERİLMEDİ, onay bekliyor)

**Hedef:** goun7/Dumen issue #4
**Başlık:** evidence_chain.py: json.dumps is not a canonical form

## Taslak yanıt

---

Marcus — teşekkürler, bu rapor tam olarak doğruydu ve 0.8.0'da çözüldü.

**Sizin örneğinizle ölçtüm** (Python 3.14 + Node.js, bugün):

```
{"refusal_rate": 1.0, "n": 3}
  json.dumps : {"n":3,"refusal_rate":1.0} → ee37d9fe… (Python-only)
  RFC 8785   : {"n":3,"refusal_rate":1}   → 032dfef1…
  Node JCS   : {"n":3,"refusal_rate":1}   → 032dfef1…  ← birebir
```

Tam olarak öngördüğünüz gibi: `1.0` → `1` dönüşümü ve farklı hash.
Python ↔ Node bayt-birebir (21/21 vektörde, sadece bu örnek değil).

**Ne değişti (0.8.0):**
- `dumen/reports/rfc8785.py` — ECMAScript Number canonicalization + UTF-16
  code-unit key sort, NaN/Infinity reddeder
- `EvidenceChain` artık `canon_scheme` alanı taşır; **≥0.8.0'da varsayılan
  `rfc8785`** — bildirilen kurum Python kurmadan doğrulayabilir
- `dumen amplification-scan` komutu ve `ChainEntry` şema-bilgili

**Geri uyumluluk (önemli):** yayınlanmış sertifikaların hash'lerini
değiştirmedik. Eski demetler `canon_scheme: "jcs_python"` ile yüklenir ve
hash'leri birebir korunur; **yeni** üretim rfc8785'dir. Bu, kanıt-takarını
taklit etmenin yoludur: eski sertifikaları yeniden-hash'lemek yerine
sürüme bağlı şema seçtik.

**Sort_keys konusu:** haklısınız, RFC 8785 UTF-16 code-unit sıralar;
bizde `_serialize` UTF-16-le karşılaştırması yapıyor. ASCII anahtarlar için
sonuç aynı, ama UTF-16 farkı astral/emoji anahtarlarında gerçek — bunu
da vektör setimizde kapsıyoruz.

**Tekrar üretim:**
```bash
pip install dumen==0.8.1
python -c "from dumen.reports.rfc8785 import canonicalize; print(canonicalize({'refusal_rate':1.0,'n':3}))"
# {"n":3,"refusal_rate":1}
```

Tamamlandı diye kapatmıyorum — siz "çözüldü" onaylarsanız kapatırım.
Tekrar-üretim için vektör setini de public repo'da `tests/test_rfc8785.py`
altında bulabilirsiniz (15 vektör, Node ile çapraz-doğrulanmış).

---

## Notlar (gönderim öncesi)

- **Doğruluk kontrolü:** yukarıdaki tüm sayılar bu seansta canlı ölçüldü
- **Gönderim kapısı:** kullanıcı onayı olmadan gönderilmez
- **Risk:** düşük — tamamen teknik, kaynaklı, kendi ölçümümüzle destekli
