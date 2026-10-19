# Dümen — İş Modeli ve Para Kazanma (dürüst analiz, 16-Eyl-2026)

> **Önce gerçek:** 0 star · 27 benzersiz clone (tamamı açılış günü 15-Eyl'de) ·
> PyPI indirme sayısı henüz ölçülemedi (rate-limit) · **gelir: 0 ₺/ay**.
>
> Bu doküman vaat değil — seçeneklerin dürüst değerlendirmesidir.

## Mevcut durum: her şey Apache-2.0 (core açık kaynak)

```
pip install dumen          ← ücretsiz, tüm özellikler
dumen audit / serve / ...  ← tüm komutlar ücretsiz
Ed25519 imzalama           ← ücretsiz
```

**Core = açık kaynak, kapalı kaynak parça YOK.** Şu an "core açık / asıl iş
kapalı" diye bir ikilik yok; her şey açık. Bu bir seçim değil, **başlangıç
durumu** — iş modeli henüz seçilmedi.

---

## Seçenek 1: Saf açık kaynak + hizmet (en olası, en düşük risk)

| Akış | Ne satılır | Tahmini fiyat |
|---|---|---|
| **Denetim hizmeti** | Sen koşutursun `dumen audit`'i, kanıt zinciri + Annex XI teslim edersin | model başına €2-8k |
| **Eğitim / danışmanlık** | GPAI sağlayıcılarına "kendi kendine denetim" eğitimi | €5-15k/proje |
| **İmza otoritesi** | Senin Ed25519 anahtarınla üçüncü-taraf imzalama (zaten `dumen sign` var) | imza başına €200-500 |

**Neden işe yarar:** EU AI Act'te kanıt **insan onaylı** olmalı — araç ücretsiz
olsa bile "bunu profesyonel koşturup imzalayacak biri" arzusu kalıcı.
**Talep kanıtı yok** (0 star).

## Seçenek 2: Open-core (kapalı enterprise katman)

Açık kalsın: CLI, zincir, imzalama, Annex XI, CoP matrisi.
**Kapalıya al (gerçek eksiklik — şu an hiçbiri yok):**

- **Ekip/çoklu-ortam**: ortak kanıt deposu, rol-bazlı imzalama (bireysel değil)
- **Süreklilik**: `dumen watch`'ın yönetilen bulut sürümü (CI/CD değil, sürekli denetim)
- **İnsan-ikinci-etiket (B3)**: şu an AÇIK — hakem κ kalibrasyonu enterprise'a
  uygun (yazılım değil, insan süreci)
- **Uyumluluk panosu**: çoklu model, zaman içinde drift takibi

**Fiyat:** €500-3k/ay/model ailesi.
**Risk:** "Açık araçları kapatma" algısı. **Apache-2.0 core'u koruyarak** sadece
*enterprise eklemelerini* kapatmak (GPL değil) itiraz azaltır.

## Seçenek 3: Sertifika / "Dümen Certified" (en yüksek değer, en uzun yol)

Model sağlayıcı **kendisi** koşturur, sen **denetler ve mühürler**:
`dumen audit --output x.json` → `dumen verify` → senin imzan →
"Dümen-Certified (tarih, model, sha256)" rozeti.

- **Müşteri:** GPAI sağlayıcılar (CoP imzacıları: Aleph Alpha, BFL, Cohere...)
- **Değer:** Annex XI'yi sıfırdan kurmak aylar — sen haftalar.
- **Fiyat:** €10-25k/sertifika + yıllık yenileme
- **Ön şart:** itibar — 0 star ile satılmaz. Önce 2-3 **kamuya açık** sertifika
  (küçük modeller, ücretsiz) gerekir. **Ben yapabilirim** (araç hazır).

## Seçenek 4: Sponsorluk / foundation (gelir değil, hayatta kalma)

- **NLnet / NGI0** (AB fonu, açık-kaynak AI safety) — €50-100k hibe
- **Apache Software Foundation kuluçka** — 2-3 yıl sonra
- **GitHub Sponsors / Open Collective** — sembolik
- **Kullanım:** zaman kazandırır, doğrudan gelir değil

---

## BENİM ÖNERİM (sıralı, ölçülebilir)

### Aşama 1 — Kanıt birikimi (0-3 ay, GELİR YOK)
1. **3 kamuya açık sertifika** koştur: 0.5B/1.5B/3B küçük modeller, imzala,
   README'ye koy ("referans denetimler" — mevcut `examples/audits/` genişlet)
2. **B3 hakem-çift-etiket** tohumunu koştur → κ ölçümü yayınla (şu an AÇIK,
   bu "insan süreci" parçası — sertifika inandırıcılığı için gerekli)
3. **Yıldız/topluluk**: awesome-list PR'ları (beklemede), arXiv, ICLR
4. **Hedef:** 50+ star, 2 kurumsal "ilgi" sinyali (outreach yanıtı)

### Aşama 2 — İlk gelir (3-9 ay)
5. **Denetim hizmeti** (Seçenek 1) — 1-2 küçük müşteri, **fiyatlandırma
   kanıtı**. Buradan öğrenileni enterprise katmanına (Seçenek 2) besle.
6. **FUNDING.yml** ekle (GitHub Sponsors + NLnet başvuru linki)

### Aşama 3 — Ölçek (9-18 ay)
7. Open-core: **kapalı parça = takım/çoklu-ortam + yönetilen watch**
   (core Apache-2.0 kalır)
8. Sertifika programı (Seçenek 3) — ancak 3+ kamuya açık sertifikadan sonra

---

## KESİNLİKLE YAPMAMAK GEREKENLER

- ❌ **Core'u kapatmak** — itibar yokken (0 star) kapalı kaynak = ölü proje
- ❌ **"Enterprise edition" ilan etmek** müşteri yokken — sahte ürün
- ❌ **Önceden fiyat listesi** — talep kanıtı olmadan fiyat koymak
- ❌ **AB hibe vaadi** — NLnet reddi olasılığı yüksek; plana Dahil etme
- ❌ **Kripto/token** — bu bir denetim aracı, finansal araç değil

---

## Karar Verilmesi Gereken (sana soruyorum)

1. **Hizmet mi, ürün mü?** Sen denetim mi yapacaksın (hizmet), yoksa araç mı
   satacaksın (ürün)? Hizmet = senin zamanın, ürün = ölçek.
2. **Kim?** GPAI sağlayıcılar (B2B, yavaş, kurumsal) mi, yoksa denetim
   şirketleri/akademisyenler (daha hızlı, daha küçük ödeme) mi?
3. **Zaman çizelgesi:** 3 ay içinde ilk gelir hedefli misin, yoksa 12 ay
   "kanıt biriktirme"ni kabul mü ediyorsun?

**En dürüst tavsiyem:** Aşama 1'i (kamuya açık sertifikalar + B3) **hemen**
yapalım — gelir getirmez ama **hiçbir şey satmaya çalışmadan önce** elimizde
satılacak bir "kanıt" olur. 0 star ile satış görüşmesi = zaman kaybı.

Bu aşamada hiçbir ödeme altyapısı, fiyatlandırma veya kapalı kod **yok** —
kararın ardından eklerim.
