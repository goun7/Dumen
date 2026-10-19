# PARA NASIL ALINIR? — şirket yokken, AB müşterisinden (16-Eyl-2026)

> **Başlangıç noktası (gerçek):** Türk şirketi YOK · 20/B başvurusu YOK ·
> AB/ABD'de varlık YOK · gelir 0 · müşteriler AB'de (BFL DE, Pleias FR,
> Almawave IT...). Bu doküman **gerçek duruma** göre yazıldı, idealize
> edilmedi.

## ÖNEMLİ ZAMANLAMA: 20/B'Yİ ŞİMDİ BAŞLAT

```
Müşteri "fatura gönder" der → 20/B yok → 4 hafta bekle → anlaşma ÖLÜR
```

20/B (hizmet ihracı KDV muafiyeti) başvurusu **1-4 hafta** sürer. Sen
müşteriyle konuşurken **paralel** başlatmalısın. İlk ödeme gelene kadar
hazır olur. **Beklersen kaybedersin.**

## ADIM ADIM PLAN (sıralı)

### Adım 1 — BUGÜN: e-posta + alan adı (~$12/yıl, 10 dk)
- `dumen.dev` al (Cloudflare'den ~$12/yıl — **boş, doğrulandı**)
- Cloudflare **ücretsiz** e-posta yönlendirme: `adın@dumen.dev` → gmail
- Yanıtları gmail'den atarsın, alıcı `@dumen.dev` görür
- **Neden:** `vegoko7@gmail.com` kurumsal tedarikçi sinyali vermez. Ama
  sahte şirket kurmaktan **kaçınırız** (düzenleme gelince çöker, dürüstlük
  doktrinine aykırı)

### Adım 2 — BUGÜN/BU HAFTA: Wise hesabı (ücretsiz, 1-3 gün)
- **Bireysel** Wise: AB IBAN (EUR) + TR IBAN
- Alıcı sıradan EUR transferi yapar — **kurumsal masraf yok, komisyon yok**
- İlk ödemeleri buradan al
- **Fatura sorunu** çözülmedi — Adım 3 gerekli

### Adım 3 — BU HAFTA: 20/B + serbest meslek (ZORUNlu, 1-4 hafta)
- Türk vergi dairesine: serbest meslek faaliyeti + 20/B (hizmet ihracı)
- **Ne sağlar:** KDV %20'den **muafiyet** (hizmet ihracı) + döviz alımı
  + kur farkı
- **Fatura:** "serbest meslek makbuzu" — AB alıcısı için makbuz + Wise
  dekontu yeterli (AB alıcısı KDV tevkifatı bekler, 20/B bunu çözer)
- **Bekleyemezsin** — "fatura gönder" anında hazır olmalı

### Adım 4 — İLK ÖDEME GELİNCE: sektör karar
- Gelir tekrarlanır görünüyorsa → **şahıs şirketi** (tek kişilik limited)
- Gelir büyürse → **Stripe Atlas / Estonian e-Residency** (AB içi fatura
  + kart ödemesi, ~€100-300, 1-3 hafta)

## SEÇENEK KARŞILAŞTIRMA (dürüst)

| Yol | Kurulum | Maliyet | Neden / Neden değil |
|---|---|---|---|
| **Wise bireysel + 20/B** | 1-4 hf | ~$0 | ✓ ÖNERİLEN — AB IBAN, KDV muafiyeti, kurumsal fatura |
| Stripe (TR bireysel) | imkansız | — | ❌ Türkiye'de bireysel Stripe yok, şirket gerekiyor |
| Upwork/Contra/Fiverr | 1 gün | %10-20 | ❌ **VAZGEÇ** — komisyon + platform kilidi + denetim işinde alıcı güvenini azaltır (imza zinciri ile çelişir) |
| PayPal bireysel | var | %3-5 | ⚠️ kurumsal alıcılar sevmez, ABD-merkezli |
| GitHub Sponsors | kolay | %0 | ⚠️ bağış modeli — **hizmet** faturalandırılamaz (sponsorluk "gelir" sayılmaz, vergi karmaşası) |
| Stripe Atlas / Estonian | 1-3 hf | ~€100-300 | ✓ ölçeklenince — AB içi ödeme + kart |

## NEDEN UPWORK'TEN VAZGEÇTİK (önemli)

Dümen **güven** satıyor: imza zinciri, kurcalama-reddi, "Not measured"
doktrini. Bir alıcı "ödemenizi platforma yapın" duyarsa, bu güven
**çelişir** — bağımsız denetçi nasıl bir aracının ödeme platformuna
bağımlı olur? Denetim işinde bağımsız görünmek **paranın kendisinden
değerli**. Doğrudan fatura + bağımsız imza = ürünün vaadi.

## MÜŞTERİYE "NASIL ÖDEYECEKSİNİZ" SORUSUNA CEVAP

Hazır cevap (AB kurumsal alıcıya):

> "Bank transfer (SEPA) in EUR, with an invoice from the maintainer under
> Turkey's service-export regime (KDV-exempt). A signed receipt + transfer
> confirmation is provided. For larger engagements we can invoice through
> a corporate entity if your procurement requires it."

**Yalan yok:** "maintainer" dürüst (tek kurucu), "service-export regime"
gerçek (20/B), "corporate entity if required" şartlı (henüz yok, ama
söylüyor — büyük işlerde kurarız).

## ÖZET — EN KISA CEVAP

```
E-POSTA:  dumen.dev al (10 dk, $12) → @dumen.dev imza
PARA:     Wise bireysel (EUR IBAN) + 20/B serbest meslek (1-4 hafta)
          → KDV muafiyeti + serbest meslek makbuzu
ÖLCEK:    ilk tekrarlanan gelir → şahıs şirketi → Stripe/Estonian

❌ Upwork/Fiverr: komisyon + güven çelişkisi
❌ Sahte şirket: düzenleme gelince çöker
❌ PayPal/GitHub Sponsors: hizmet faturalandırmaz
```

**En kritik:** **20/B'yi bu hafta başlat.** "Fatura gönder" anında hazır
değilse 4 hafta beklersin ve anlaşma o sırada ölür. Başvuru paralel
olmalı — müşteri arayışı ile aynı anda.
