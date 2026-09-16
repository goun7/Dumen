# Dümen v0.7.5 — Tam Dürüstlük Değerlendirmesi

> Tarih: 2026-09-16 · Sürüm: v0.7.5 (PyPI'da canlı) · Kapı: 419 test, %96.82
> kapsam, ruff temiz, parite 232, paper --check ✓, CI yeşil
>
> **Doktrin:** "kanıt yoksa iddia yok" — bu rapordaki her sayı ya makine-üretimi
> ya da açıkça "ölçülmedi" olarak etiketli. Kopyala-yapıştır yapabileceğiniz
> hiçbir yerde el-le yazılmış metrik yoktur.

---

## 1. BU OTURUMDA NE KIRIKTI, NE DÜZELTİLDİ

### 🔴 K1 — README'nin yaşam-döngüsü BAŞTAN SONA KIRIKTI (en kritik)

**Durum (v0.7.4):** README'nin yazdığı `dumen audit --output karne.json` →
`dumen sign --chain karne.json` yolu **çalışmıyordu**. `audit` rapor-only JSON
yazıyordu; `sign` ise kanıt-zinciri şeması bekliyordu → "kayıt şeması bozuk"
hatası. Yani: projenin ana vaadi (imzalanabilir kanıt) README'deki talimatları
izleyen hiçbir kullanıcı tarafından **ulaşılamaz** durumdaydı. Ben bunu daha
önce sadece Python API'sinden denemiş, README'yi kelimesi kelimesine hiç
koşturmamıştım.

**Düzeltme (v0.7.5):** `audit --output` artık **kanıt-demeti (evidence bundle)**
yazıyor: raporun kök-alanları + `evidence_chain` + `chain_head` tek dosyada.
`EvidenceChain.from_json` **çelişki-kapısı** uygular: kök-alanlar mühürlü
report-kaydından farklıysa veya `chain_head` uyuşmuyorsa → `ValueError` "Kanıtdemeti
çelişkisi… Kanıt kabul edilmez."

**Temiz-oda kanıtı (PyPI 0.7.5 wheel'inden):**
```
pip install dumen==0.7.5
dumen audit --refusal-baseline --output karne.json     → rc=0
dumen keys --name auditor --dir ./keys                 → ✅
dumen sign --chain karne.json --key ... --name "..."   → ✅ DOĞRULANDI
dumen verify --chain karne.json --sig ... --pub ...    → rc=0
dumen export --input karne.json --chain ... --sig ...  → HTML INTACT mührü ✓
```
Ayrıca **kurcalama testi**: `overall_safety_score=99.9` değiştirildi →
imzalama öncesi reddedildi "kök-alanları mühürlü report-kaydıyla farklı".
**Kırılganlık kapatıldı, makineyle doğrulandı.**

### 🔴 Y1/Y2/Y4 — Gateway "çift-ajan validator" YALANIDIR

**Durum (v0.7.4):** README/CoP "dual-agent Generator-Validator güvenlik duvarı"
idi ama **hiçbir yapılandırma yolu yoktu** — bayrak mevcut değildi. Daha kötüsü:
ikincil denetçi erişilemezse **sessizce** yalnız-regex karar veriyordu ve yanıt
tam-doğrulanmış görünüyordu. SSE akışı da PII'yı **sayıp ham geçiriyordu**
(maskesiz teslim).

**Düzeltme (v0.7.5):**
- `serve --validator-url/--validator-model/--validator-key` — ikincil LLM
  denetçisi GERÇEK bağlandı (herhangi OpenAI-uyumlu uç; Ollama `127.0.0.1:11434`).
- `/health` + her `dumen_meta` **aktif savunma katmanını ifşa eder**:
  `fast_filter + dual_agent_validator` veya `fast_filter_only`.
- Denetçi çökerse: `fast_filter_validator_unavailable` damgası + gerekçe satırı
  (sessiz düşüş YOK).
- SSE: 96-karakter **gecikmeli-pencere** → PII maskeli teslim; kritik çıktıda
  `stream_cut: true` ile fail-closed kesim; ayrıştırılamaz kare akışı KESER.

**Testlerle kanıtlandı:** PII maskelenmeden teslim edilmiyor (regex ile), bozuk
kare sızdırmıyor, `def exploit` + `rm -rf /` midstream kesiliyor, sağlık uçları
katmanı söylüyor.

### 🔴 Y5 — Bootstrap güveni `n<2` için **1.0 UYDURUYORDU**

**Durum:** tek örnekle madencilik → `confidence=1.0` (mükemmel istikrar).
Bu, bir örnekle "matematiksel olarak kanıtlanmış" görünen sahte bir sayıydı.

**Düzeltme:** `SteeringVector.confidence: Optional[float]` — `n<2 → None`
("ölçülmedi"), asla 1.0. Madenci fonksiyonu da `Optional[float]` döner.

### 🔴 K2 — CoP matrisi KOŞMAMIŞ şeyleri "tamamlandı" diyordu

**Durum:** `dumen dossier` her zaman "hiyerarşik kırmızı-takım testi tamamlandı"
yazıyordu — o motor **kütüphane-API'sidir, hiçbir CLI komutu onu koşturmaz**.
IV.4 "dual-agent validator" koşulsuz; IV.3 olay-takibi her zaman `demonstrated`.

**Düzeltme (v0.7.5):**
- IV.1'in ölçü-satırı: gerçekte koşan **tek-tur adversarial batarya + JudgeEvaluator**.
- IV.3: `--incident-log` (JSON, pydantic-doğrulamalı, fail-loud) **veri-temelli**;
  kayıt yoksa `not_demonstrated` (sabit True değil).
- IV.4: validator katmanı **koşullu** + `steering_overhead=not_measured`
  (eskiden `False` "yük yok" gibi okunuyordu).
- Annex XI / scorecard / pilot dosyaları: "otonom saldırı ölçüldü" →
  "tek-tur tamamlandı; çok-tur/otonom **Ölçülmedi — iddia edilmez**."

### 🔴 O6 — `steer-test` koşulsuz "✅ BAŞARILI!" basıyordu

**Durum:** assertion yok; matematik işlese de işlemese de başarı yazıyordu.
Ayrıca `--dim 1` → ham `AssertionError` traceback.

**Düzeltme:** artık **gerçek invariant**: `|cos|` azalmalı + maske seyreltmeli;
ihlalde `SystemExit(1)` + "BAŞARISIZ" (negatif-kontrol testi eklendi: `sparsity=1.0`
→ rc=1). Kötü `--dim` → `UsageError`. **Canlı kanıt:** `+0.2781 → +0.0075` ✓

### 🔴 Y3 — README mimari diyagrami YALANIDI (5 katman)

**Durum:** gateway isteği yolunda `[2] SAE latent inspection`, `[3] StTP steering`,
`[5] Autonomous red team` çiziyordu — **gateway kodunda bunlardan hiçbiri yoktu**
(SAE motoru CLI'nin hiçbir yolunda koşmuyor). Kullanıcıyı yanlış yönlendiren
en büyük yüzey.

**Düzeltme:** diyagram **iki gerçek hat + bir kütüphane yüzeyi** olarak yeniden
yazıldı (EN + TR, parite 232 ile doğrulandı):
1. **DENETİM hattı** (`dumen audit`): tek-tur kırmızı-takım + hakem → beyaz-kutu:
   VectorMiner steering vektörleri → B1 kapasite kapısı → kanıt zinciri →
   Annex XI + CoP + HTML.
2. **GEÇİT hattı** (`dumen serve`): hızlı filtre (~0.03ms ölçülen) → upstream →
   çıktı taraması + PII maskeleme + opsiyonel ikincil denetçi → fail-closed SSE.
3. **KÜTÜPHANE yüzeyi** (Python API — gerçek ama **hiçbir CLI koşturmaz**,
   açıkça böyle etiketlendi): SAE motoru & kalite-bench, çok-turlu PAIR/HRL,
   hakem-kalibrasyon, steering-yük.

---

## 2. LİTERATÜR DOĞRULUK DÜZELTMELERİ (makale öncesi)

| Hata | Düzeltme |
|---|---|
| JailbreakBench ID `2404.04561` | → `2404.01318` (eski ID **3D-vizyon** makalesine çözümleniyordu!) |
| arXiv:2606.05958 "loss-surface dedektörü" | → **saldırı-yüzeyi** makalesi; training-time mitigasyonlar önerir, **post-hoc dedektör göndermez** |
| "intensity-monotone drift" | → **kesin-monoton DEĞİL** (8-takas noktası DÜŞER: 0.482→0.480); "her şiddette pozitif" olarak düzeltildi |
| Abstract "zehirlenmeyi TESPİT eder" | → ölçülen **çift-negatif sınır** (gerçek sonuç buysa) |
| "first open detector" | → "first OPEN per-pair geometric outlier-attribution tool" + arama sınırı (2026-09-16) |
| "ilk Türkçe B1 kanıtı" | → "aramamızda (2026-09-16'e kadar) kamuya açık Türkçe steering-capability kanıtı bulunamadı" |
| 9 eksik atıf kimliği | tamamı birincil-kaynaktan doğrulandı (SteerCheck, ObserverBench, decoy-direction, evaluator fragility ×2, aliases/HARC/DeepRefusal) |

---

## 3. KALAN TEKNİK BORÇ — GERÇEK DURUM

### Bilinçli olarak BIRAKILAN (değiştirilmez — immutable published evidence)
- **Yayınlanmış provenance artifact'ları** eski şema taşır (`swEEP_note` yanlış-büyük-harfli
  anahtar, p2/p8/p16'da pair-cosine yok). **Değiştirmek kanıt zincirini kırar.**
  Quirk'ler artık `examples/audits/README.md`'de belgeli.
- **IV.4 CoP `not_demonstrated`** — `steering_efficacy=not_measured` olduğu için
  **DOĞRU**. "Düzeltmek" = yalan üretmek olurdu.
- **GTX 1070 (sm_61) vs cu130 (sm_75+)** — CPU yayın artifact'ları; `DUMEN_DEVICE`
  ile opt-in (README'de belgelendi).

### Geri Ödeme Listesi (v0.7.6+ için, öncelik sırasıyla)
1. **Kütüphane yüzeyini CLI'ya bağla**: SAE kalite-bench, çok-turlu HRL,
   hakem-kalibrasyon — şu an README "Python API" diyor, bu dürüst ama ürün
   açısından **eksik**. En yüksek değer.
2. **Hakem-çift-etiketleme (B3)**: `examples/calibration_seed.py` tohumu var,
   insan ikinci-etiket geçişi AÇIK — κ ölçümü koşulduğunda IV.1'i güçlendirir.
3. **Çok-turlu/otonom kırmızı-takım**: şu an tek-tur. Ölçülmediğini söylemek
   doğrudur ama rakipler (garak, PyRIT) bunu sunar (bkz §5).
4. **`SteeringVector.steering_overhead` ölçümü**: kütüphane var, CoP'de
   `not_measured` — koş ve IV.4'ü kapat.
5. **ICLR 2027 zamanlaması**: abstract 18-Eyl-2026 / paper 25-Eyl-2026.
   arXiv duyurusuyla görünürlük çakışması var — **karar sizin** (bkz §7).

---

## 4. KALİTE DURUMU — "100/100 MÜ?"

**Dürüst cevap: kod ve kanıt zemininde ~90/100; pazarlama/yüzey honestly
düzeltildi; kalan 10 puan yukarıdaki geri ödeme listesinde.**

### ✅ Makineyle doğrulanmış (sayılar üretildi, elle yazılmadı)
- **419 test, hepsi yeşil**, %96.82 kapsam (≥95 kapısı)
- **ruff temiz** (dumen + tests + scripts + examples)
- **EN↔TR sayısal parite 232 token** (README'ler arasında sayı kayması yok)
- **paper --check ✓** (§6.3 tablosu artifact'lardan makine-üretiliyor)
- **PyPI 0.7.5 canlı + temiz-oda byte-özdeş wheel** + yaşam-döngüsü çalışıyor
- **CI yeşil** (v0.7.5 commit'inde 1m35s)
- **Kurcalama-tespiti** kanıtlandı (mühürlü report-kaydı + head-hash)

### ⚠️ "UI/UX" — GUI yok, kullanıcı yüzü CLI + API + HTML rapor
- **CLI (11 komut)**: `--help` hep çalışıyor; hatalar `ClickException`/`UsageError`
  (ham traceback değil — `steer-test --dim 1` düzeltildi); çıkış-kodları anlamlı
  (`verify` geçersizde 1).
- **HTML raporu**: marka SVG gömülü, print-CSS, XSS-kaçışlı, mühür ayak-bası
  (INTACT + head-hash + imzalayan). **Ama:** markdown-tablo stilleri sınırlı,
  koyu-tema yok, interaktif değil. Görsel kalite **fonksiyonel, ödünç-değil** —
  denetçi-formatı amacıyla yeterli, ama "göz kamaştırıcı" değil.
- **API gateway**: `/health` katmanı ifşa eder (Y1 düzeltmesi); SSE'de
  `dumen_meta` her yanıtta hangi katmanın karar verdiğini söyler.
- **Dürüst puan: 85/100 UI/UX** — fonksiyonel ve doğru iletişim kuran ama
  görsel cila isteyen bir denetim aracı.

---

## 5. GERÇEKÇİ RAKİP ANALİZİ (2026-09-16 itibarıyla)

| Rakip | Güçlü Yönü | Dümen'in Farkı |
|---|---|---|
| **garak v0.17** (NVIDIA) | 100+ vektörler, çok-dilli, aktif gelişim | garak **sadece saldırı/sayı üretir** — kanıt zinciri, imzalama, Annex XI, CoP matrisi **yok**. Dümen: saldırı + **mekanistik denetim + imzalanabilir kanıt**. |
| **PyRIT 1.1.0** (Microsoft) | Python framework, orkestrasyon | PyRIT **framework'tür, ürün değil** — dolum/denetim çıktısı üretmez. "undetermined" skoru PyRIT'in ölçülmemiş-sonuç için öncülüdür (bizim `not_measured` ile aynı ruh). |
| **Inspect 0.3.263** (UK AISI) | AI-safety eval platformu, ReviewEvent izleri | Inspect **değerlendirme altyapısıdır** — hukuki çıktı (Annex XI/CoP) üretmez. **Dümen Inspect'i kullanır** (köprü var), rakip değil tamamlayıcıdır. |
| **promptfoo 0.123** | CI entegrasyonu, evalOps | CI/evalOps odaklı; mekanistik yorumlanabilirlik, EU AI Act çıktısı **yok**. |
| **NeMo Guardrails** | Politika-temelli koruma | **Siyah-kutu kural motoru** — madencilik/yönlendirme/mechanistic denetim **yok**. Dümen'in gateway'i benzer ama **beyaz-kutu denetimi** ekler. |

### Dümen'in Gerçekçi Konumu
**Güçlü:** (1) imzalanabilir kanıt-demeti (başka hiçbir rakip sunmuyor — garak/PyRIT/Inspect
imzalama özelliği yok); (2) EU AI Act Annex XI + CoP matrisi (hukuki çıktı tek başına);
(3) mekanistik steering ile siyah-kutu kırmızı-takım **tek kanıt zincirinde** birleştirme;
(4) iki dilli (TR/EN) — **bulduğumuz kadarıyla kamuya açık ilk Türkçe steering-capability
kanıtı**; (5) çift-negatif yayın kültürü (araç kendi hipotezini veto etti).

**Gerçekçi zayıf:** (1) küçük modeller (≤3B) — frontier (70B+) ölçek
**ölçülmedi**; (2) çok-turlu/otonom saldırı **yok** (rakiplerde var); (3)
HuggingFace'de yıldız/indirme tabanlı topluluk-kabül kanıtı **yok** (issue #36
Giskard'dan, PR #76 GenAI-Gurus'tan — ilk işaretler); (4) insan hakem-çift
etiketleme (B3) **açık**; (5) "mükemmel UI" değil, fonksiyonel CLI.

**Dürüst sonuç: Dümen niş bir "denetim-kanıt" aracıdır — garak ile değil,
`garak + eIDAS-ruhu + makine-okuşan kanıt` ile rekabet eder. Geniş saldırı
genişliğinde kaybeder, kanıt bütünlüğünde kazanır.**

---

## 6. ÖNCELİKLİ EYLEM PLANIM (sıralı)

1. **✅ BİTTİ** v0.7.5 yayın + temiz-oda kanıtı + CI yeşil (bu oturum).
2. **Şimdi** — PR #76 (GenAI-Gurus awesome-list) + issue #36 (Giskard) takip.
3. **v0.7.6** — kütüphane yüzeyini CLI'ya bağla (SAE bench → `dumen sae-bench`;
   HRL → `audit --multi-turn`; κ → `dumen calibrate`). Bu en yüksek değerli
   geri ödemedir: README'nin "Python API" deme sebebi kalkar.
4. **B3** — hakem-çift-etiketleme tohumunu koş, κ'yı ölç, IV.1'i güçlendir.
5. **Roadmap公开** — ROADMAP.md'ye yukarıdaki listeyi koy (keşfedilebilirlik).
6. **ICLR kararı** — §7'deki zamanlama çakışması için sizin onayınızı bekliyorum.

---

## 7. SİZİN KARARINIZI BEKLEYEN (otomatik yapılmaz)

- **ICLR 2027 zamanlaması**: abstract 18-Eyl-2026 / paper 25-Eyl-2026. arXiv
  duyurusu ile çakışıyor — görünürlük mi, öncelik mi? **Karar sizin.**
- **arXiv gönderimi** (PAPER.md hazır, tüm atıflar doğrulandı)
- **HN/Reddit duyurusu**, **outreach e-postaları**, **og.png yüklemesi**

Bunlar insan-onaylı eylemlerdir — otomatik yapılmaz, yapılmadı.

---

## 8. ÖZET

**v0.7.5 öncesi:** README'nin ana vaadi çalışmıyordu (audit→sign kırık),
gateway "çift-katman" yalandı, bootstrap 1.0 uyduruyordu, mimari diyagramı
olmayan şeyler çiziyordu, JailbreakBench atfı yanlış makaleye gidiyordu.

**v0.7.5 sonrası:** her şey **makineyle doğrulandı** — kanıt-demeti + imzalama
temiz-odadan koştu, kurcalama yakalandı, gateway katmanı ifşa ediyor, sahte
metrikler `not_measured`'a döndü, atıflar birincil-kaynaktan doğrulandı,
419 test + %96.82 + ruff + parite + paper + CI hepsi yeşil, PyPI'da canlı.

**Kalan iş yukarıdaki listede — hiçbiri gizli değil.**
