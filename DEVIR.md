# DEVIR — Dümen v0.7.6 (2026-09-17, akşam)

## CANLI DURUM

- **PyPI 0.7.6 YAYIMLANDI** — `https://pypi.org/project/dumen/0.7.6/`
  clean-room install doğrulandı, yeni komutlar wheel'da.
- **Hub** `/home/gokun/projects/01_unicorn/77-Dumen` master @ `f7ba617` (remote YOK)
- **Public** `77-Dumen-public` main @ `3295798`, github.com/goun7/Dumen.git, CI YEŞİL
- **Tam kapı:** 471 test · %95.71 kapsam · parite 253 · PAPER GÜNCEL · ruff temiz
- **0 emoji / 0 SteeringOS / 0 isim-drop (Altman/Amodei) / 0 abartı** — README+TR'de temizlendi

## BU SEANSTA YAPILAN (kanıt sırasıyla)

### 1. RFC 8785 (Tamga-ajan'ın ihbarı — doğrulandı)
- `dumen/reports/rfc8785.py` — ECMAScript Number.toString + UTF-16-le anahtar sıralama
- **Python ↔ Node.js 21/21 bayt-birebir** (Node = ECMAScript-native ground truth)
- 3 sapma üretildi: `1.0`→`1.0`(olmalı `1`), `-0.0`→`-0.0`(olmalı `0`), `2.93e-07`(olmalı `2.93e-7`)
- **Geri uyumluluk:** yayınlanmış 3 sertifika float `risk_scores: 0.0` içeriyor →
  yeniden hash'lemek kanıt-takarı taklididir. **Sürüme bağlı şema:**
  `canon_scheme` alanı eksik → `jcs_python` (hash KORUNDU, `c56901ca…` birebir)
- Tamga'nın uyarıları canlı kanıtlandı: (a) Node `JSON.stringify` insertion-order'dır,
  UTF-16-sıralı oracle olmadan sahte "nested" farkı görüldü; (b) escape-tablosu
  tuzağı → quote+backslash vektörleri; (c) `1e+21` bizde de `1.e+21` üretiyordu
- **Tamga'nın bir varsayımı yanlıştı:** "RFC 8785 diye-yazdığınız her yer" —
  grep 0 eşleşme; ihlal yanlış iddia değil **eksik doğruluk**'tü. Yanıt arşivlendi:
  `icbelge/TAMGA_RFC8785_YANIT_2026-09-17.md`

### 2. Veridict bridge (ajanın commit'i 46d0277 — review + push edildi)
- `dumen/reports/veridict_bridge.py` — zincir → append-only ledger, fail-closed
- **ÖNEMLİ DÜZELTME:** ajanın commit'i hub `cli.py`'ye **72 emoji + SteeringOS
  + "Frontier AI" başlığını** geri koymuştu. Köprüyü kaybetmeden temizlendi.
- **Ajanın uyarısı doğru:** modül sertifika ÜRETMEZ, sadece ledger kurar
  (`veridict audit --ledger` ayrı). Docstring + fiş notu yazar.
- İki kullanılmayan import (Dict, tempfile) temizlendi → ruff temiz.

### 3. MoE joint-intervention (arXiv:2609.09793) — YOL HARİTASI #1 KAPANDI
- `dumen/core/moe_joint.py` + CLI `moe-joint-test` + 12 test
- Bulguya göre: 320B MoE'de tek-bileşen müdahale **SİLİCE** başarısız;
  attention+dense+expert **birlikte** düzenlenmeli (~4 kat geri kazanç)
- `component_overlap` altuzay örtüşmesi ölçer; düşük örtüşme + tek-bileşken =
  sessiz-başarısızlık bayrağı. Sentetik vektörlerle **%100 kapsam**

### 4. TLCM amplification (arXiv:2609.07876) — YOL HARİTASI #2 KAPANDI
- `dumen/core/amplification.py` + CLI `amplification-scan` + 11 test
- `compute_adaptive_alpha` **monoton-artan sigmoid** → amplifikasyon rejimini
  GÖREMEZDI. `scan_amplification` α taraması → `|cos_after| > |cos_before|`
  ilk α + güvenli-α sınırı. Ölçülen: α=2.25'te amplifiye, güvenli sınır 2.0

### 5. iFixAi konumlanması — YOL HARİTASI #3 KAPANDI
- README'ye **ölçümlü "Why Dümen" bölümü** (capability table, tüm sayılar
  yeniden-üretilebilir: 0.077 ortanca cos, CI [0.329, 0.586], pool=20)
- **"first red-team+audit OSS" iddiası zaten ölü** — 2026'da boşluk kapandı;
  artık dar ve doğrulanabilir iddia: **beyaz-kutu + provensans + Annex XI**
- **Araştırma sırasında bulunan tekrarlayan sorun:** özet "isim-drop ve abartı
  temizlendi" diyordu ama **gerçekte duruyordu** (Altman/Amodei L19'da, TR
  epigraf "matematiksel olarak önler"). Kanıt-öncesi varsayım hatası.
- **Ders:** özet iddialarını grep ile DOĞRULA, kabul etme.

### 6. PAPER §7 — 4 akademik sınır EKLENDİ (önceden YOKTU)
- Özet "eklendi" yazıyordu ama **4'ü de yoktu** (grep 0/4). Eklendi:
  2609.09793 (MoE), 2609.07876 (TLCM), 2609.04808 (sıklık≠nedensellik),
  2609.09113 (SAEScientist-Bench — yorumlanabilirlik penceresi, hendeği değil)

### 7. PyPI 0.7.6 + portföy
- `python3 -m build` → clean-room venv → `twine upload` (rc=0)
- **Disk dolmuştu** (16G tmpfs'de 2.9G) → `/tmp/v076` 5.5G eski venv silindi
- `docs/RELEASE_INDEKSI.md` → **R21** olarak eklendi (05_acik_kaynak kanalında,
  R06/Veridict ile birlikte). **Vergi: GVK 89/13** (%0 KDV + MoR) — önceki
  20/B varsayımı Dümen için YANLIŞTI (VERGI_KANAL_CERCEVESI.md'ye göre)
- `docs/PORTFOY_OZETI.md` → "Kağıt (100/100)" → "**PyPI 0.7.6 canlı (R21)**"

## ÖLÇÜLEN (immutable, değiştirme)

- Qwen2.5-0.5B cos: temiz 0.42164 → p16 0.498931 (Δ0.07729, p8'de DIP)
- null CI [0.329273, 0.586109] · MAD 0.220411 · n=20 · seed-sabit n=1000
- HarmBench-40 91.1 · capability32 78.1 · TR 70% vs EN-GSM 60% (n=10, parite DEĞİL)
- Sertifikalar: 97.5 / 97.5 / 58.8 (58.8 = siyah-kutu, 46.5-puan kanal açığı)
- PyPI: 0.7.6 canlı · ilk ay ~299 indirme · 0 yıldız/çatal/alıntı (abartısız)

## KALAN YOL HARİTASI (öncelik sırasıyla)

1. **SAEScientist-Bench (stratejik, 1-2 yıl penceresi)** — yorumlanabilirlik
   ajanları mekanistik-bench'lerde insan-uzman seviyesine çıktı (2609.09113).
   Beyaz-kutu farklılaştırıcımız bir **pencere**, hendek değil. Şimdi değil.
2. **MoE joint-intervention CANLI doğrulama** — şu an sentetik vektörlerle
   %100. Gerçek 320B MoE kontrol noktası (örn. Mixtral) + joint vs single
   karşılaştırma. Bütçe: model indirme + GPU-saat.
3. **TLCM döngü-kapatma** — `amplification-scan` TESPİT eder ama α'yı otomatik
   seçmez. Denetim koşusu içinde ölçülen eğriden α seçme = açık iş.
4. **RFC 8785 varsayılan yap** — şu an yeni zincirler hâlâ `jcs_python`
   (yayınlanmış 3 sertifika yüzünden). 0.8.0'da varsayılan değişebilir.
5. **Dış-yayın (HUMAN-GATED)** — Variant C segment-2 danışmanlık firmaları.
   Hiçbir şey gönderilmedi. Kullanıcı onayı olmadan atılmaz.

## TEKNİK NOTLAR (bir sonraki seans için)

- **pytest + `--source=X` + torch SEGFAULT ediyor** (Python 3.14). Çözüm:
  `python3 -m coverage run -m pytest tests/... ` (source bayrağı olmadan)
  veya `coverage run` + `report --include`. `--forked` plugin YOK, sessizce
  yok sayılıyor. **Bu kod hatası değildir** — modüller %100 kapsamda.
- Edit tool **file-since-read** hatası: her zaman aynı offset'ten yeniden oku.
- `git add -A` DOKTRİN İHLALİDİR — bu seanslık bir kez oldu, hemen `git reset`
  ile geri alındı. Her zaman **seçici add** kullan.
- rsync: `--exclude='DEVIR.md' --exclude='icbelge' --exclude='.coverage'`
  + public'te `git checkout -- .gitignore`
- Kök `RAKIP_VE_LITERATUR_TARAMASI_2026-09-16.md` hub'da çöp — `icbelge/`
  versiyonu farklı/kamuya-uygun olduğu için public'e ZATEN gitti (kasıtlı).

## KULLANICI TESLİMLERİ (bekleyen)

- 100/100 değerlendirme ✓ · rakip analizi ✓ · adım-adım eylem planı ✓
- Tüm yol haritası maddeleri kapatıldı veya kanıtla ertelendi.
- **"Proje tamamlandı, geliştirecek bir şeyimiz kalmadı" diyebilir miyiz?**
  HAYIR — ama artık gap'ler **kanıtlanmış ve tarihlenmiş**, varsayımsal değil.
