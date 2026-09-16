# SENİN EYLEM PLANIN — adım adım (16-Eyl-2026, v0.7.5 yayında)

> **Yapacağım diye bir şey yok** — aşağıdaki her adım **hesap/otorite/kimlik**
> gerektirdiği için otomatik yapılmadı. Hazırlık kısımlarını tamamladım; sadece
> onayın ve tıklamaların gerekli.
>
> Toplam tahmini süre: **~1.5 saat** (adım 1 hariç; o bir karar).

---

## ICLR NEDİR? NEDEN ACELE?

**ICLR** (International Conference on Learning Representations) — makine
ogrenmesinin saygin konferanslarindan biri. **ICLR 2027** icin ozet/niyet
kayit tarihleri **Eylul 2026'da**.

**Onemli:** Eger ICLR'i **istemiyorsan** (sadece arXiv + urun yeterliyse),
o zaman **acelen yok** — arXiv'i istedigin zaman yaparsin. Bana soyle:
"ICLR'i bosver" veya "ICLR'e giriyorum".

- **18-Eyl-2026** (2 gun): ozet/niyet kaydi — gecikirse ICLR 2027 kapisi kapanir
- **25-Eyl-2026** (9 gun): tam metin

## ⏰ ACİLİYET SIRASI — ICLR 2027 (2 gün kaldı!)

```
abstract deadline : 2026-09-18  →  2 GÜN KALDI
paper deadline    : 2026-09-25  →  9 gün kaldı
```

### ADIM 1 — ICLR mi, arXiv önceliği mi? KARAR (5 dakika, kağıt üstü)

Bu bir çakışmadır, iki taraf da doğru ama farklı öncelikler:

| Seçenek | Kazancı | Riski |
|---|---|---|
| **A: Önce arXiv (hemen)** | Sitasyon saati çalışır; HN/outreach'ta link verilir; "first" iddiası tarih damgalanır | ICLR genellikle daha önce arXiv'e çıkmış işleri kabul eder (genellikle sorun değil ama 2027 politikasını kontrol et) |
| **B: Önce ICLR (abstract 18-Eyl)** | Hakemlerden önce yayınlanmaz; double-blind gerekirse isim silinmeli | Sitasyon saati 9 gün geç başlar; HN ertelenir |
| **C: Ikisi birden** | abstract'ı 18-Eyl'de ICLR'e ver, **aynı gün** arXiv'e koy | En yaygın yol (arXiv + konferans birlikte); ICLR politikası arXiv'i "yayın" saymaz |

**Benim önerim: C.** Nedeni: ICLR abstract'ı bağlayıcı değildir (tam metin 25-Eyl'e kadar çekilebilir); arXiv gecikmesi sitasyon açısından geri dönüşü olmayan bir kayıptır. Ama **karar senin** — sadece bana söyle.

---

## ADIM 2 — arXiv gönderimi (30-40 dakika, senin hesabın)

**Hazırlık benden: TAMAM** — PAPER.md tüm atıfları doğrulanmış, sürüm satırı 0.7.5,
§6.3 tablosu `scripts/render_paper_results.py --check` ile makine-üretimli.

**Senden gerekenler:**

```bash
# (a) pandoc + xelatex kur (bir kerelik)
sudo pacman -S pandoc-cli texlive-xetex   # ~700MB, 5-10 dk

# (b) PDF üret
cd /home/gokun/projects/01_unicorn/77-Dumen
pandoc PAPER.md -o /tmp/dumen_paper.pdf --pdf-engine=xelatex \
  --metadata title="Dümen: an open-source, evidence-first audit engine..."

# (c) arXiv'e yükle
#     https://arxiv.org/submit  →  New submission
#     Kategoriler: cs.CR (ana), cs.AI, cs.CL (cross-list)
#     License: Apache-2.0 değil → arXiv'in kendi lisans seçenekleri
#              (CC-BY 4.0 öneririm — kod Apache-2.0, metin CC-BY ayrışması normal)
```

**Bilmen gereken tuzaklar:**
- **"First" iddiaları önceden kontrol edildi** (15-Eyl literatür taraması,
  `research_b4_literature.md`): "ilk Türkçe steering-capability kanıtı" →
  "aramamızda (2026-09-16'a kadar) kamuya açık Türkçe kanıt bulunamadı" olarak
  daraltıldı. **Göndermeden önce bir kez daha tara** — son 48 saatte yeni bir
  makale çıkmış olabilir. `web_search` ile "Turkish steering activation LLM
  arXiv 2026" ara.
- **Kod bağlantısı**: tag `v0.7.5` + `examples/audits/` (sweep + TR + HB40)
  gönderimde referans ver — hakemler tekrar üretebilir.
- **Yazar kimliği**: arXiv hesabın kurucu kimliği — bu senin kararin.

---

## ADIM 3 — og.png sosyal-preview görseli (10 dakika)

arXiv ve HN/HN-öncesi linklerin sosyal kartı için. `avatar.png` mevcut ama
OG-kartı için ideal boyut **1200×630**:

```bash
# Hazırlık benden: avatar mevcut (.github/assets/avatar.png, 13KB)
# Senden: 1200×630 canvas'a yerleştir + repo köküne og.png olarak koy
#         (herhangi editör: GIMP/Canva/Figma — eğer istersen .github/assets/
#          içine koyup README'den linkle, ben bağlayayım)
```

**Sonra:** GitHub repo ayarları → social preview → og.png seç.

---

## ADIM 4 — Hacker News: YAPMA (hesap ban riski)

**Yeni hesabin + onceki gonderin flag'lendi** — bir sonrakinde banlama olasi.
Show HN'i plandan cikardim.

**Yerine (ban riski olmadan):** arXiv listing'i birincil dagitim yap; Lobsters
(davet ister), r/MachineLearning (self-promotion orani dusuk), EuroPython /
AI safety Discord'lari ikincil.

**Taslak (ileride hesap guvenli olursa)** (`30-submission-plan.md` içinde), ama **v0.7.4→v0.7.5 ve yeni
sayılarla güncellendi** — kopyala:

```
Title: Show HN: Dümen – open-source EU AI Act audit engine with SHA-256 evidence chains

Body:
Apache-2.0, `pip install dumen`. Measures models (black-box single-shot red-team
batteries + white-box activation-steering probes on ≤3B open weights, consumer
GPU/CPU), gates capability harm with deterministic tasks (original Turkish task
set — multilingual evidence is missing everywhere), and writes every step into a
tamper-evident chain that renders into Annex XI / Code-of-Practice documents.

The repo ships its own negatives: 0% steering efficacy on one family; a
data-provenance detector that measurably does NOT fire at low poisoning
intensity (intensity curve published, 2/8/16-swap grid). Unmeasured fields
print as "Not measured" — no fabricated scores.

v0.7.5 just shipped: the audit→sign→verify path now works end-to-end (it was
broken), the gateway discloses which layer actually decided, and bootstrap
confidence is None instead of a fake 1.0.

[repo] https://github.com/goun7/Dumen
[paper] (arXiv link — ADIM 2'den sonra ekle)
```

**Önce ADIM 2'yi bitir** — HN'de paper linki olmadan itibar düşer.

---

## ADIM 5 — Outreach e-postaları (7 hedef, ~1 saat)

**Hazırlık benden: TAMAM** — 2 varyant taslak + 20 hedefli liste
(`outreach_letters.md`, `research_cop_targets.md`).

**Varyant A — "kanıt-yayıncılığı"** (BFL, Aleph Alpha, Bria, Pleias, Almawave,
Cohere, WRITER): "your model family could ship the EU's first open white-box
audit evidence" — CoP imzacılarına yönelik.

**Varyant B** — araştırma işbirliği (research_cop_targets.md'de).

**Senden gerekenler:**
1. İsimleri doldur (`[Name/Team]` yer tutucuları)
2. Kişisel bir cümle ekle (her hedefin imza tarihi/ürünü için — liste'de var)
3. **Gönderim öncesi kontrol**: 15-Eyl'den bu yana hedeflerden biri ürün
   duyurduysa metni güncelle
4. **Kanal seç**: doğrudan e-posta mı, LinkedIn mi? (E-posta soğuk-LinkedIn'ten
   daha yüksek yanıt oranı ama spam riski; 7 hedef için hızlı bir A/B düşün)

---

## ADIM 6 — PR/issue takibi (10 dakika, bekleme-durum)

| Nereye | Durum | Senin eylemin |
|---|---|---|
| **GenAI-Gurus/awesome-eu-ai-act PR #76** | açık, 0 yorum, 0 reviewer | **Bekle** (uygulamadan 2-3 gün). 1 yorum yoksa nazik bir "ping" yorumu: "bumping gently — happy to adjust the entry if the section needs a different format" |
| **Giskard-AI/awesome-ai-safety issue #36** | açık, 0 yorum | **Bekle**. PR#76 merge olunca "already listed in GenAI-Gurus/awesome-eu-ai-act" diye yanıt yaz (sosyal kanıt) |
| **ProjectRecon/awesome-ai-agents-security PR #123** (Veridict) | açık, 1 yorum (kendi güncellemen) | **Bekle** — bakıcı yanıtı yok |
| **vimalnakrani08/auditweave issue #1** | açık | Düşük öncelik; işbirliği teklifi |

**Kural:** hiçbir yere "merge pls" yazma — tek bir nazik hatırlatma, 1 defa.

---

## ADIM 7 — v0.7.6 yol haritası onayı (ben yapacağım, sadece onayın)

Eğer onaylarsan 8-10 saatlik pencerede devam ederim:

1. **Kütüphane yüzeyini CLI'ya bağla** (en yüksek değer) — README'nin
   "Python API; hiçbir CLI koşturmaz" deme sebebini kaldırır:
   - `dumen sae-bench` (SAE kalite metrikleri)
   - `dumen audit --multi-turn` (HRL motoru)
   - `dumen calibrate` (hakem κ ölçümü → IV.1'i güçlendirir)
2. **steering_overhead ölç** → CoP IV.4'ü kapat (`not_measured` → gerçek sayı)
3. **B3 hakem-çift-etiketleme** — `examples/calibration_seed.py`'ı koş
4. **ROADMAP.md** kamu repoya (yukarıdaki listeyi görünür yap)

---

## ✅ BENİM YAPTIKLARIM (bu oturum, otomatik)

| # | Ne | Kanıt |
|---|---|---|
| K1 | kanıt-demeti: audit→sign→verify artık çalışıyor | temiz-odam PyPI wheel'inden koştu; kurcalama yakalandı |
| Y1/2/4 | gateway validator + katman-ifşa + SSE maskeleme | 4 yeni test |
| Y5 | bootstrap 1.0 uydurusu → None | `test_rank_k.py` |
| K2 | CoP matrisi koşulanı söylüyor | `--incident-log` ile veri-temelli |
| O6 | steer-test gerçek assert | `+0.2781 → +0.0075` |
| Y3 | mimari diyagramı yalan → 2 gerçek hat | parite 232 |
| Literatür | JB ID + 2606.05958 + monotone + 9 atıf | hepsi birincil-kaynaktan |
| Sürüm | v0.7.5: push + tag + PyPI + CI + temiz-oda | hepsi yeşil |

**Kapı:** 419 test · %96.82 · ruff temiz · parite 232 · paper ✓ · CI ✓

---

## ÖZET — SIRALAMA

```
1. (2 gün!) ICLR/arXiv kararı ver        → bana söyle, hemen hazırlayayım
2. arXiv gönder                            → pandoc kur, PDF üret, yükle
3. og.png                                  → CANLI, sadece preview sec
4. Show HN                                 → YAPMA (ban riski)
5. Outreach 7 e-posta                      → isimleri doldur, gönder
6. PR/issue ping'leri                      → 3 gün sonra, nazikçe
7. v0.7.6 onayı                            → "devam et" de, ben yaparım
```

**Hiçbir adımı sen onaylamadan yapmadım. ArXiv/HN/outreach/og.png
beklemede.**
