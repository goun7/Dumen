# DEVIR — Dümen v0.8.1+ (2026-09-18, öğleden sonra, GÜNCELLEME 2)

## CANLI DURUM

- **PyPI 0.8.1 CANLI**
- **Hub** master @ `ceb885a` (remote YOK)
- **Public** main @ `a1ca643`, github.com/goun7/Dumen.git — **tüm CI yeşil**
- **Tam kapı:** 519 test · %95.93 · parite 270 · PAPER GÜNCEL · ruff temiz

## BU GÜN YAPILAN (tüm liste)

### Seans 1 (öğleden önce)
1. RFC 8785 21→50: Node oracle **3 gerçek hata** (negatif üstel, off-by-one,
   UTF-16 birim-vs-bayt). 50/50 bayt-birebir. `scripts/oracle/`
2. Amplifikasyon 3 model × 30 çift: **α≈1.0 ölçekten bağımsız**
3. **Canlı MoE sessiz-başarısızlık** ★: örtüşme 0.035, single:expert
   **−0.18→+0.19** (ters yön), joint ≈0. Teori canlıda doğrulandı
4. GitHub issue'lar: #4 KAPATILDI (kanıtlı yanıt), #1/#2/#3'e ölçülmüş notlar

### Seans 2 (öğleden sonra — bu seans)
5. **Emoji temizliği**: scorecard + audit artifact'lerinden 🛡️📊🟢🔴✅❌⚠️
   kaldırıldı (kullanıcı doktrini: professional yüzeyde emoji yok)
6. **REKIP_ANALIZI_2026-09.md git'ten silindi** + `.gitignore`'a
   `REKIP_ANALIZI*` ve `RAKIP_VE_LITERATUR*` eklendi (iki katmanlı koruma)
7. **Harici suite yükleyici (issue #2)** ★: `load_jsonl_suite` +
   `register_external_suite` — GSM8K/MMLU JSONL, **LLM-hakem YOK**,
   echo-safe (hedef istemde varsa ATLA + log'la), bozuk satıra dayanıklı
   (int/None/bool answer, geçersiz JSON, aralık-dışı MMLU indeksi).
   **%100 modül kapsama** (46 test). Issue #2'ye yanıt **GÖNDERİLDİ**
8. **Değerlendirme 81 → 78/100** (dürüst yeniden hesap: teknik 94,
   pazar 32 — teknik arttı ama pazar sabit, o yüzden toplam DÜŞTÜ)

## SABİT ÖLÇÜMLER
Qwen2.5-0.5B cos 0.42164→0.498931 (Δ0.07729, DIP p8/p16); null CI
[0.329273, 0.586109]; MAD 0.220411; n=20; HarmBench-40 91.1;
capability32 78.1; TR 70% vs EN-GSM 60%; sertifikalar 97.5/97.5/58.8.
Canlı amplifikasyon: 0.5B/1.5B/3B α 2.0-2.5 amplifiye, α≈1.0 söndürme
(grid 1.0, refined 0.9997-1.0003), cos_before −0.183/−0.274/−0.282.
Canlı MoE: örtüşme 0.035, single:expert −0.18→+0.19, joint ≈0.0000.
RFC 8785: 50/50 Node bayt-birebir.

## KALAN AÇIK İŞ (ÖNCELİK SIRASI)

1. **[KULLANICI] Outreach "gönder"** — `icbelge/outreach_ready.md` v2
   ARAŞTIRMA çerçevesinde hazır (10 sohbet hedefi, 3 para seçeneği).
   Kova artık delik değil: star nudge + pricing issue şablonu yayında.
   **"Gönder" dersen 7 firmaya gider.**
2. **[KULLANICI] Para modeli kararı** — öneri: **mühürlü sertifika**
   (kod zaten ölçüldü, GPU gerektirmez, doğal tekel). AMA önce
   outreach'in 10 sohbeti hangi seçeneği seçtiğine bakın; veri seçsin.
3. **[BEN] Benimseme ölçümü** — clone verisini BEN çekebiliyorum
   (`gh api .../traffic/clones` → 357/126). Kullanıcıyı bekletmeye gerek
   yok; istenildiği an ölçülür
4. **[BEN] arXiv/ICLR kararı** — PAPER hazır; kullanıcı kararı bekleniyor
5. **[BEN] 3. parti TR capability suite** — yükleyici var; TR destekli
   set henüz koşturulmadı

## ÇALIŞMA NOTLARI
- **coverage run -m pytest --cov=dumen** py3.14'te bazen boş data verir;
  `coverage.Coverage()` API'si ile çalışınca doğru (%100 ölçüldü)
- **Edit aracı "file changed since read"** derse `python3 - <<PYEOF` ile
  değiştir; tek satır offset'lerden oku
- `git add -A` ÖZEL BELGE SIZDIRIR — seçici yol + sızma grep'i
- **ruff fix** import sıralaması yapar ama bazen kodu bozar — kontrol et
- Edit tool'da `old_string` içinde `\n` literal ise `json.dumps` ile üretilen
  kaçışı kullan (manuel kaçış hataya açık)

## KAPILAR
- **GPU KAPALI** — 320B canlı doğrulama BİR DAHA ÖNERİLMEZ
- **Kanıt yoksa iddia yok; her kapı yeşilsiz public push yok**
- **Outreach KAPALI** — kullanıcı "gönder" demedi; issue'lara farklı
  (kullanıcı GitHub yetkisi verdi)
