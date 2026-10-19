# Dümen — En Dürüst İş Modeli Tavsiyesi (16-Eyl-2026)

> **Gerçek başlangıç:** 0 star · 0 fork · 27 clone (hepsi açılış günü) · gelir 0
> **Bağlam:** 01_unicorn ortaklığı — unicorn hedefli ortak şirket. Açık kaynak
> kalırsa proje tamamlandığında **taşınması** gerekecek (org/şirket reposuna).

## Senin yanıtların → ne anlama geliyor

| Senin cevabın | İş çevirisi | Dürüst sorun |
|---|---|---|
| "Hem faydalı hem para" | İkili hedef — çatışmaz, ama **sıralama** şart | Fayda geliri getirir, ama fayda **kanıtlanmadan** para gelmez |
| "Herkesle çalışabiliriz, neden birini seçeyim?" | Doğru — **ama satışta değil** | Hedef kitleyi **tercih etmemek** = hiç kimseye satamamak. Ürün herkese açık olabilir, **ilk 5 müşteri** seçilmeli |
| "Mümkün olduğunca kısa sürede para" | Hız önceliği | Hızlı para = **hizmet** (senin zamanını satar). Ürün (ölçek) 6-12 ay |
| "En iyi yol hangisiyse onu yapalım" | Pragmatik | "En iyi" = **bugün için en hızlı GEÇERLİ satış** |

## EN DÜRÜST TAVSİYEM: HİZMET + AÇIK KAYNAK (Seçenek 1)

**Neden bu:** 0 star ile ürün satılmaz — hiçbir GDPR/EU AI Act alıcısı
"piyasadaki yeni aracı" satın almaz. Ama **senin** ellerinde kanıt üreten bir
araç var. **İnsanlar senin emanet ettiğin kanıtı satın alır, aracı değil.**

```
Senin zamanın     →  dumen audit koştur  →  imzalı kanıt + Annex XI  →  €
     ↑                                                            ↓
     └──── senin uzmanlığın (aracın değil) ←──────────────────────┘
```

### Somut: 3 müşteri segmenti, heyle aynı araç

| Segment | Kim | Ne alır | Fiyat | Satış süresi |
|---|---|---|---|---|
| **1. GPAI sağlayıcılar** (CoP imzacıları: Aleph Alpha, BFL, Pleias...) | Model sahipleri | Annex XI kanıtı (zorunlu) | €5-15k/model | 2-4 ay |
| **2. Denetim/danışmanlık firmaları** | KPMG, PwC, boutique AI safety | **Aracın kendisi + eğitim** — onlar müşterilerine satar | €2-8k/proje | 1-2 ay ⚡ |
| **3. Akademi/regülatör** | AB JRC, AI Office, üniversiteler | Ücretsiz kullanım → **görünürlük** (atıf, rapor) | €0 → itibar | hemen |

**"Neden birini seçeyim?" cevabı:** Ürünü **herkese** açık tut (Apache-2.0), ama
**ilk satışların için segment 2'yi seç** — çünkü:
- GPAI sağlayıcılar (segment 1) yavaş, kurumsal süreç, 2-4 ay
- **Danışmanlık firmaları (segment 2) hızlı** — onların zaten müşterisi var,
  onlara "araç + senin koçluğun" satıyorsun, **onların müşterisi sana gerek yok**
- Akademi (segment 3) parayı değil, **itibarı** getirir → segment 1'i açar

**Bu "herkesle çalışmak" ile çelişmez** — herkes kullanabilir, **ilk aya
odaklanmak** başarısızlığın önüne geçer.

## 01_UNİCORN ORTAKLIĞI İÇİN KRİTİK KARAR

Açık kaynak + unicorn şirket bir arada olabilir, ama **belirsizlik öldürücü**:

| Senaryo | Ne olur | Ne yapılır |
|---|---|---|
| **A. Açık kalır** (önerim) | Dümen açık, **şirket kapalı katman** satar (open-core) | Şirket reposu = ayrı private repo; bu repo goun7/Dumen kalır, **contributor agreement (CLA) şart** |
| **B. Kapalıya döner** | Lisans değişimi — geçmiş kullanıcıları kızdırır, itibar kaybı | Apache-2.0'dan dönülür ama **çirkin**; fork'lar zaten yapılamadı (0 fork) |
| **C. Şirkete taşınır** | goun7/Dumen → unicorn-org/Dumen, redirect | **Taşınabilir** — GitHub transfer repo'yu ve star'ları korur |

**Benim önerim: A + C karması:**
1. **Şimdi:** repo `goun7/Dumen`'de açık kalır, **CLA ekle** (contributor
   license agreement — gelecek katkıları şirket kullanabilsin)
2. **Unicorn kurulduğunda:** GitHub transfer → `unicorn-org/Dumen` (star'lar
   korunur, redirect otomatik), **core açık kalır**
3. **Şirketin sattığı:** açık-core'un **kapalı enterprise katmanı** (takım,
   yönetilen watch, insan-ikinci-etiket B3) — **aynı kod tabanında değil,
   ayrı private repo'da**

**Kaçınılmaz gerçek:** Yatırımcıya "açık kaynak unicorn" sunuyorsan,
**open-core şart** — sadece Apache-2.0 + hizmet ile unicorn olmaz ( hizmet
= senin zamanın, ölçeklenmez). Ama **bugün kapalıya dönemeyiz** (0 star).

## HIZLI PARA İÇİN 30 GÜNLÜK PLAN (en dürüst sıralama)

### Hafta 1-2: "Satılabilir kanıt" (gelir 0, ama teklif edilebilir)
1. **3 kamuya açık sertifika koştur** (0.5B/1.5B/3B modeller) — imzala,
   README'ye koy → "referans denetimler" (examples/audits/ zaten 20+ artifact)
2. **B3 hakem-çift-etiket** tohumunu koştur → κ ölçümü yayınla
   (hakem kalitesi = güven = satış)
3. **1 sayfa PDF**: "Dümen ile Annex XI 2 haftada" (PAPER.md'den brew)

### Hafta 2-3: İlk 5 görüşme (segment 2: danışmanlık firmaları)
4. Outreach: **10 boutique AI safety/danışmanlık firması** (hızlı karar)
   "Aracı + 2 saat koçluk" → €2-5k/proje
5. **Ücretsiz deneme sun**: bir modelde audit koştur, sonucu gönder
   (düşük risk = hızlı evet)

### Hafta 4: İlk teklif
6. Fiyatlandırma kanıtı alındıktan sonra: **segment 1'e** (GPAI) geç
7. **FUNDING.yml** + GitHub Sponsors (sembolik, ama yatırımcı görür)

## KESİNLİKLE YAPMA ❌

- **Core'u kapatma** — 0 star iken kapalı = ölü
- **Önceden fiyat listesi yayınlama** — talep kanıtı olmadan
- **"Enterprise edition" ilan etme** müşteri yokken
- **Hibe vaadi etme** (NLnet reddi yüksek olasılık)
- **Hizmetten ürüne atlamayı bekleme** — önce hizmet ile para + kanıt, sonra ürün

## ÖZET — EN KISA CEVAP

**"En hızlı para + en iyi yol" = HİZMET, açık kaynak core ile.**

```
Bugün          →  30 gün              →  90 gün
0 star            3 kamuya açık         İlk 2-3 danışmanlık
                  sertifika + B3        müşteri (€2-8k/proje)
0 gelir           10 outreach           → unicorn kurulduğunda:
                                        open-core kapalı katman
```

**Neden bu en dürüst:** 0 star ile ürün satışı **impossible** — hiçbir
kurumsal alıcı yeni aracı önceden satın almaz. Ama **senin ellerinde imzalı
kanıt** var. **İnsanlar güveni satın alır, kodu değil.** Hizmet = güveni
satan en hızlı yol. Ürün (ölçek) geliyor — ama **kanıt birikmeden değil.**

## SANA SORU

1. **İlk segment 2 (danışmanlık firmaları) kabul mü?** yoksa direkt GPAI'ye
   mi (yavaş ama büyük)?
2. **CLA ekleyeyim mi?** (unicorn ortaklığı için — gelecek katkıları
   şirket kullanabilsin)
3. **3 kamuya açık sertifika koşturmaya başlayayım mı?** (ben yaparım,
   CPU'da küçük modellerle, imzalarım)
