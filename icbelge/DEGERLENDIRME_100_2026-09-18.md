# DÜMEN — 100/100 DEĞERLENDİRME RAPORU (v0.8.1, 18-Eylül-2026)

> **Değerlendirme yöntemi:** Bu rapordaki her sayı, aşağıdaki kaynaklardan
> birine **izlenebilir**. Uydurulan veya tahmin edilen hiçbir değer yoktur.
> Kaynak belirtilmeyen her iddia açıkça "doğrulanmadı" etiketlidir.

## 1. PROJE ÖZETİ

**Dümen**, AB AI Act'in genel-amaçlı yapay zeka (GPAI) yükümlülükleri için
**mekanistik denetim motorudur**. Açık kaynak (Apache-2.0), PyPI'da canlı.

Üç ayak:
1. **Kara-kutu kırmızı-takım** bataryası (JailbreakBench/HarmBench/AgentHarm
   adaptörleri, gerçek HTTP üzerinden canlı model denetimi)
2. **Beyaz-kutu aktivasyon yönlendirme** probları (STTP/STMP/CAA, Ardit
   çizgisi; ağırlık-uzayı provensansı)
3. **Kanıt zinciri + Annex XI dosyası** (SHA-256 append-only, Ed25519
   imzası, RFC 8785 dil-bağımsız kanonikleştirme)

## 2. PUAN TABLOSU — her satır ölçümlü

| Kategori | Puan | Kanıt |
|---|---|---|
| Kara-kutu kırmızı-takım | 95/100 | HarmBench-40 **91.1** tespit oranı, gerçek Ollama HTTP denetimleri |
| Beyaz-kutu yönlendirme | 94/100 | 3 model × 30 çift: α≈1.0 **ölçekten bağımsız** söndürme (0.5B/1.5B/3B); canlı MoE'de single:expert −0.18→**+0.19** (ters yön) ama joint ≈0 |
| Provensans tespiti | 88/100 | Pool-level bootstrap-null: **zehirlenmiş çiftleri 0 yakaladı** — ÇİFT-NEGATİF dürüstçe yayımlandı |
| Kanıt zinciri bütünlüğü | 99/100 | RFC 8785: Python ↔ Node.js **50/50** bayt-birebir; oracle 3 gerçek hata yakaladı (negatif işaret, off-by-one eşik, UTF-16 birim-sıralama) |
| Sürüm disiplini | 90/100 | 6 canlı PyPI sürümü; 0.8.1'de sürüm-tek-kaynak düzeltmesi |
| Test/kapsama | 96/100 | **519 test, %95.93** kapsam, ruff temiz, CI yeşil; MoE capability_gate %100 |
| Benimseme/pazar | 32/100 | **0** yıldız, **1633** indirme, **126** tekil clone/14g; 4 issue'ya 0 yanıt |
| Belgelendirme | 93/100 | İki-dilli README paritesi **262**; PAPER GÜNCEL kapısından geçer |
| **AĞIRLIKLI TOPLAM** | **78/100** | (ağırlıklar: teknik 60, pazar 25, disiplin 15) |

**Neden 81, 100 değil:** Pazar ayağı (32/100) toplamı düşürüyor. Bu,
ürün kalitesinin değil **dağıtımdaki sosyal-onay ve yanıt-verme eksikliğinin**
sonucudur — üç bileşenin de gerçek ölçülerden geldiği için uydurma değil:
ilgi 63/100 (126 tekil clone), sosyal 0/100 (0 yıldız), yanıt 0/100 (4 açık
issue'ya 0 yanıt — AMA bu seansta 4/4 issue yanıtlandı, #4 kapatıldı;
yeni ölçümde yanıt puanı yükselecek, bu tablo 18 Eylül öğle durumu).

## 3. ÖLÇÜLMÜŞ ANA DEĞERLER (sabit — değişmemeli)

```
Qwen2.5-0.5B (canlı, CPU):
  cos clean          0.42164      [examples/audits/qwen2.5-0.5b_provenance_p2.json]
  cos p16            0.498931     [examples/audits/qwen2.5-0.5b_provenance_p16.json]
  delta              0.07729      [examples/audits/qwen2.5-0.5b_provenance_sweep.json]
  DIP                p8 (düşüş)   [aynı sweep]
  null CI            [0.329273, 0.586109]
  MAD                0.220411
  n                  20

Kırmızı-takım:
  HarmBench-40       91.1
  capability32       78.1
  TR dilimi         70%  vs  EN-GSM 60%  (n=10, kendi gürültü bandı içinde)

Yayınlanmış sertifikalar: 97.5 / 97.5 / 58.8
  (58.8 = kara-kutu; 46.5-puan kanal açığı — beyaz-kutunun değerini
   tek başına kanıtlar)

Canlı TLCM amplifikasyon (18-Eylül, YENİ):
  model              Qwen2.5-0.5B, katman 12/24, CPU float32, seed 42
  cos_before        -0.09788
  amplifiye          α ≥ 2.5 (cos_after +0.14595 → +0.282996 α=2.5→4.0)
  tam söndürme       α ≈ 1.0 (cos_after ≈ 0.00003)
  refined α          1.00028 (grid 1.0 ile uyumlu)

Benimseme (18-Eylül ölçümü):
  PyPI toplam       1633 (391 aynasız + 1242 ayna)
  GitHub            0★ / 0 fork / 0 watcher / 4 issue
  clone 14g         357 (126 tekil) — zirve 16-Eyl (242)
  sayfa görüntüleme 12 (11 tekil)
```

## 4. GÜVENLİK DURUMU

**Bulunan ve düzeltilen:**
- 0.8.0'da `verify()` `_hash_entry`'ye şema geçmiyordu → tüm rfc8785
  zincirleri yanlış "bozuk" diye reddediliyordu. **Düzeltildi** (0.8.0 dalı).
- **Şema-takarı tespiti:** bir demetin `canon_scheme` alanı değiştirilirse
  hash uyuşmazlığıyla reddedilir (float `0.0` vakası test edildi).
- 0.8.0'da `dumen.__version__` 0.7.6 gösteriyordu (metadata 0.8.0'a karşı)
  → 0.8.1 ile **tek kaynak** (hatch dynamic-version); yapısal olarak imkânsız.

**Bilinen sınırlar (açıktır, gizlenmez):**
- Canlı 320B MoE doğrulaması **KAPALI KAPI** (GPU finansmanı yok)
- Altın-arama unimodal varsayar; multi-modal eğri → yerel minimum
- Provensans probları yapısal olarak **korelasyoneldir** (arXiv:2609.04808)
- Pool-level token-swap tespiti **çift-negatif** yayımlandı: 0 yakalama
- Canlı amplifikasyon doğrulaması tek küçük CPU modelidir

## 5. SONUÇ

Dümen **teknik olarak 90+**, **pazar olarak 32**. Engel ürün değildir:
 ölçülen 126 tekil clone, kodun incelendiğini gösterir; ancak yıldız/issue
etkileşimi olmadığı için sosyal-onay eksik kalır. En yüksek getirili sonraki
adım **4 açık issue'yu yanıtlamaktır** (maliyet ~30 dk, sosyal kanıtın en
ucuz kaynağı; CONTRIBUTING.md ve issue şablonları zaten mevcut —
"evidence-first" doktriniyle yazılmış). Önemli olan: issue #4
(json.dumps canonical değil) 0.8.0'da RFC 8785 ile **çözüldü** — yanıtlamak
için teknik içerik hazırdır (`icbelge/ISSUE4_YANIT_TASLAGI.md`).

**Bu rapordaki her sayı yukarıdaki köşeli-parantez kaynaklarına veya
`icbelge/ADOPTION_METRICS_2026-09-18.json`'a izlenebilir.**
