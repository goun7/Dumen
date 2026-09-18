# OUTREACH TRACKER

**Son güncelleme: 2026-09-18 16:05 — İLK DALGA TAMAMLANDI (GitHub kanalına geçildi)**

## GÖNDERİM SONUÇLARI — FİNAL

### Web formu kanalı (ilk deneme, 15:30)
| # | Firma | Sonuç |
|---|---|---|
| 1 | Black Forest Labs | ✅ gönderildi — AMA yanlış reply-to (noreply) |
| 2-7 | Pleias/Bria/Aleph/WRITER/Cohere/Almawave | ❌ SSL/captcha/form-yok/JS/403 |

**Web formları headless tarayıcıya kilitli. Kanal öldü.**

### GitHub kanalı (16:00 — kullanıcının talimatı) ✅
| # | Firma | Repo | Issue |
|---|---|---|---|
| 1 | Black Forest Labs | black-forest-labs/Self-Flow | [#17](https://github.com/black-forest-labs/Self-Flow/issues/17) |
| 2 | Pleias | Pleias/Pleias-RAG-Library | [#18](https://github.com/Pleias/Pleias-RAG-Library/issues/18) |
| 3 | Aleph Alpha | Aleph-Alpha/.github | [#7](https://github.com/Aleph-Alpha/.github/issues/7) |
| 4 | WRITER | writer/cerebro | [#2995](https://github.com/writer/cerebro/issues/2995) |
| 5 | Cohere | cohere-ai/cohere-security-toolkit | [#2](https://github.com/cohere-ai/cohere-security-toolkit/issues/2) |

**5/5 GitHub issue açıldı.** Hepsi bağlamsal (ilgili repo, ölçümlü içerik,
"close freely if off-topic" ile), spam değil.

### Adres düzeltmesi (16:00)
Black Forest Labs web formuna **vegoko7@gmail.com** ile düzeltme gönderildi
(önceki noreply adresi mail ALMIYORDU). Tüm GitHub issue'ları da bu adrese
yanıt için yönlendiriyor.

## ATLANAN FİRMALAR
- **Bria AI** — GitHub org'u YOK (github.com'da bulunamadı)
- **Almawave** — GitHub org'u YOK (403 web + GitHub'da yok)

## YANIT İZLEME (vegoko7@gmail.com + GitHub)

**İzlenebilir:**
- GitHub issue yanıtları → `gh issue list` ile GÖRÜNÜR
- Star/fork → `gh api repos/goun7/Dumen` ile GÖRÜNÜR
- Pricing-research issue'ları → görünür

**İZLENEMEZ (dikkat):**
- vegoko7@gmail.com'a gelen e-posta → **ben göremem, kullanıcı okumalı**
- Kullanıcı her gün bakmalı; yanıt gelirse bana ilet

## BAŞARI KRİTERİ (değişmedi)
- **5 sohbet** (10'dan 5'e düşürüldü — 5 firma ile sınırlıyız)
- **3-4 sohbet** = zayıf; mesaj/segmenti değiştir
- **0-1 sohbet** = segment yanlış; ürüne odaklan



**Son güncelleme: 2026-09-18 15:45 — İLK DALGA GÖNDERİLDİ (kısmi)**

## GÖNDERİM SONUÇLARI (18 Eylül 2026, 15:30-15:45)

| # | Firma | Kanal | Sonuç | Not |
|---|---|---|---|---|
| 1 | **Black Forest Labs** | contact formu | ✅ **GÖNDERİLDİ** | Form doldu + submit; takip: info@blackforestlabs.ai |
| 2 | **Pleias** | form | ❌ ERİŞİLEMEZ | SSL hatası (ERR_CERT_AUTHORITY_INVALID), site çökük |
| 3 | **Bria AI** | contact formu | ⚠️ **CAPTCHA ENGELİ** | Form doldu ama submit navigasyon vermedi (muhtemelen reCAPTCHA) |
| 4 | **Aleph Alpha** | sales formu | ⚠️ **CAPTCHA ENGELİ** | GDPR onayı işaretlendi, Absenden tıklandı, sayfa aynı (HubSpot captcha) |
| 5 | **WRITER** | contact page | ❌ **UYGUN DEĞİL** | Tek-alan e-posta yakalama; sohbet mesajı için form yok |
| 6 | **Cohere** | /contact | ❌ **JS ENGELİ** | Sayfa interactive eleman yüklemiyor |
| 7 | **Almawave** | ana sayfa | ❌ **403 BOT ENGELİ** | Headless tarayıcıyı reddediyor |

**Skor: 1/7 gönderildi, 2 captcha-engeli, 4 erişim-engeli.**

### ÖNEMLİ ANALİZ (18 Eylül, clone verisinden)

Önceki varsayım **YANLIŞ ÇIKTI**:
- ❌ "126 meraklı insan var, sadece yıldızlamıyorlar"
- ✅ **Gerçek: 357 clone'un çoğu OTOMATİK** — 15-16-17 Eylül'de 3 günlük
  patlama (53/242/62). Bu, PyPI yayın sonrası indeksleyici/güvenlik
  tarayıcısı imzasıdır, insan koşusu değildir
- ✅ **12 view, 11 unique** — ve populer path'lerin ÇOĞU kendi CI sayfalarımız
  (`/actions/workflows/*`). Dışarıdan gelen neredeyse YOK
- ✅ **1633 indirme'nin 1242'si ayna trafiği** — gerçek pip install: **391**
- ✅ **Tek referrer github.com** — HİÇBİR dış keşif kanalı yok (arama/blog/sosyal)

**Sonuç: kova sızdırmıyor; kovada su yok. Outreach şu an TEK keşif kanalı.**
Bu, "outreach'u bekle" gerekçesini tamamen ortadan kaldırıyor.

### ÖNERİ: 2. dalga için kanal değişikliği

Kurumsal iletişim formaları botlara karşı kilitli (captcha/403/JS). 2. dalga
için daha iyi kanallar:
1. **GitHub issue'ları doğrudan** — bu repolarda açık issue'ları varsa
   oraya ölçümlü yorum (kullanıcı bu yetkiyi verdi)
2. **LinkedIn mesajı** — founder/CTO'ya doğrudan
3. **e-posta** — info@/hello@ tahminleri yerine gerçek adres bulma
4. **Hacker News / Reddit r/MachineLearning** — kanıt-gösterili show post

# OUTREACH TAKİP ÇİZELGESİ — 1. dalga (7 firma)

**Gönderim öncesi son kontrol (18-Eyl-2026, v0.8.1 ile güncellendi):**
- [x] Tüm linkler canlı (PyPI 0.8.1 200, GitHub 200, examples/certified 30)
- [x] pip install dumen clean-room venv'de çalışıyor (v0.8.1,
      sürüm=metadata=0.8.1 çelişkisiz, şema=rfc8785)
- [x] Mektuptaki tüm iddialar koda/artifact'lara karşılık geliyor
      (RFC 8785 21/21 Node parity; canlı amplifikasyon 0.5B+3B
      tekrarı examples/audits/ altında)yor
- [x] "first" iddiası yok, uydurma isim yok, uydurma skor yok
      (18-Eyl: kalan 2 öncelik-iddiası da ölçülü dile çevrildi)
- [x] Dil İngilizce; hitap "Hi team" (imzacı kişi kamu kaynağında yok)

| # | Firma | Kanal | Gönderildi? | Açılış | Yanıt | Sonraki adım | Tarih |
|---|---|---|---|---|---|---|---|
| 1 | Black Forest Labs | info@blackforestlabs.ai | ☐ | | | | |
| 2 | Pleias | Book-a-demo formu (pleias.ai) | ☐ | | | | |
| 3 | Bria AI | contact formu | ☐ | | | | |
| 4 | Aleph Alpha | Sales contact formu | ☐ | | | | |
| 5 | WRITER | Contact us formu | ☐ | | | | |
| 6 | Cohere | Request-a-demo formu | ☐ | | | | |
| 7 | Almawave | Almaviva grubu formu | ☐ | | | | |

## Yanıt senaryoları
- **7 gün yanıt yok** → kısa takip: sertifikaya link, yeni vaat yok
- **İlgili** → "bir modelinizde ücretsiz audit koşturalım, imzalı karnesini
  gönderelim" (düşük risk = hızlı evet)
- **"erken" derse** → 2 Ağu 2026 enforcement + Appendix 3.5 dış-evaluatör
  notu; 30 gün sonra tekrar
- **Olumsuz** → 2. dalgaya taşı, neden kaydet (retrodata)

## Başarı ölçütü (doktrin: ölçülmemiş hedef yazılmaz)
- **İlk metrik:** 7 gönderim → kaç açılış/yanıt (oranı yaz)
- **İkincil:** kaç "ücretsiz audit" teklifi kabul edildi
- **Dönüşüm:** kaç ÜCRETLİ denetim/koçluk sözleşmesi
- Bu sayılar ölçülmeden "başarılı" DENMEZ.
