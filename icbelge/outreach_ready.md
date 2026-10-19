# OUTREACH — ARAŞTIRMA ÇERÇEVESİ (v2, 18-Eyl-2026)

## ÖNEMLİ KARAR DEĞİŞİKLİĞİ

**Eski (v1):** satış çerçevesi — "book a call, let's fix your missing evidence".
**Yeni (v2):** ARAŞTIRMA çerçevesi. Hedef **10 sohbet**, 0 satış.

**Neden değişti (ölçümlü):**
- 126 tekil clone → **0 yıldız**. Dönüşüm hunisi delik: daha fazla erişim
  daha fazla sızdırmadan önce deliği kapatmak gerekir
- 0 yıldız + 0 watcher = henüz ürün-pazar uyumu kanıtı yok. Bu aşamada
  fiyat/mo.del **tahmin** olur; sohbet olmadan tasarımlanamaz
- v1'in "one call" dili, daha hiç kimse değer ifadesi yapmamışken
  aşırı-söz veriyor

**Yeni mantık:** her yanıt aynı anda (a) yıldız/visibility sinyali, (b) para
modeli kanıtı, (c) ürün geri-beslemesi verir. **Satış kapanışı hiç yok.**

## GÖNDERİM KURALLARI (değişmedi)

- **Kanıt yoksa iddia yok**: her sayı ölçülmüş olmalı
- Uydurma isim YOK (imzacı kişi kamu kaynaklarında doğrulanamadı → "Hi team")
- Her mesajda **fiyatlandırma sorusu** var (issue şablonuna yönlendirme)
- GitHub issue/PR üzerinden *değil*, kurumsal kanaldan (form/e-posta)
- İlk dalga **7**; yanıtları topla, 2. dalgayı kanıta göre planla

---

## Doğrulanmış iletişim kanalları (16-Eyl-2026 canlı)

| # | Firma | Kanıt-zorluk | Kanal (canlı doğrulandı) | Adres |
|---|---|---|---|---|
| 1 | **Black Forest Labs** | KOLAY | contact formu + genel e-posta | info@blackforestlabs.ai |
| 2 | **Pleias** | KOLAY | "Book a demo" formu (pleias.ai) | form |
| 3 | **Bria AI** | KOLAY | contact formu (bria.ai) | form |
| 4 | **Aleph Alpha** | KOLAY-ORTA | Sales contact formu | form |
| 5 | **WRITER** | ORTA | "Contact us" / Trust Center formu | form |
| 6 | **Cohere** | ORTA | "Request a demo" formu | form |
| 7 | **Almawave** | KOLAY | Almaviva grubu üzerinden form | form |

**İmzacı kişi:** kamu kaynaklarında doğrulanamadı → "Team"/"Hi there".
**Uydurma isim yok.**

---

## VARYANT A — araştırma çerçevesi (KÜÇÜK AB GPAI lab'ları)

**Konu satırı (A/B için 2):**

- **A1:** a research question about your GPAI evidence practice (2 min, no pitch)
- **A2:** open-source audit engine — would this be worth anything to you?

**Gövde:**

Hi team,

You signed the EU GPAI Code of Practice. Article 53 commitments mean
documented evaluations and downstream evidence packages on a 14-day cadence.
We're building an open-source tool for exactly that gap, and before we
decide what it should become, we'd rather ask the people it's for.

We built **Dümen** — Apache-2.0, `pip install dumen` (PyPI v0.8.1). It runs
black-box red-team batteries (JailbreakBench/HarmBench/AgentHarm formats)
and white-box activation-steering probes that test whether safety behavior
is a single removable direction. Every step goes into a tamper-evident
SHA-256 chain; `dumen dossier` renders Annex XI / CoP-format documents from
the same chain. Anything unmeasured prints **"Not measured"** — no
fabricated scores.

A few things we've measured rather than claimed: our evidence chains
canonicalise under RFC 8785 (JSON Canonicalization Scheme), verified
byte-identical against Node.js on 50/50 vectors — so a non-Python auditor
(a notified body, a legal team, any JavaScript toolchain) can recompute
every hash. We measured the steering amplification regime live in three
model scales (0.5B / 1.5B / 3B): over-steering *increases* the very harm
you meant to reduce, and the safe cancellation point is scale-invariant.
On a live MoE model we observed that single-component steering silently
steers the wrong way while looking like a reduction — joint intervention
fixes it.

**We have not chosen a funding model, and we'd rather decide from demand
than assumption.** If any of these would be worth money to you, tell us
which:

- **Managed audits** — you give us an endpoint, we return a sealed Annex XI
  dossier you can attach to a conformity file (engine stays free; you pay
  for the run and the seal)
- **Sealed certification issuance** — Ed25519-signed certificates
  countersigned by a party other than yourself
- **Compliance integration** — CI/HF Spaces adapter, gateway-as-a-service,
  or a localized report surface for a specific notified body

If the honest answer is "none of these, I'd pay for X" — that's the most
valuable reply we can get, because it's the only one we can't guess.

Two minutes is enough. If a star is all you can spare, that's genuinely
useful too: it's the only public signal we get, and zero stars currently
hides us from everyone who searches by popularity.

Repository: https://github.com/goun7/Dumen

Thanks for the time,
Team Dümen

---

## GÖNDERİM SONRASI — ölçülecek metrikler

Her mesajdan sonra bu üçünü takip et (yanıt geldiğinde güncelle):

1. **Açılma oranı** (form/e-posta ulaştı mı)
2. **Sohbet oranı** (kaç firma 2+ mesaj)
3. **Para-modeli sinyali** (hangi seçenek en çok geçti; "hiçbiri, X" var mı)

**Başarı kriteri (ilk dalga için):**
- **10 sohbet** = güçlü sinyal; 2. dalga aynı çerçevede
- **3-9 sohbet** = zayıf; mesajı/segmenti değiştir
- **0-2 sohbet** = segment yanlış veya değer teklifi belirsiz;
  satışı bırakıp ürüne odaklan (delik kovada)

**Asla ölçmeyeceğimiz şey:** satış. Bu dalga için kastedilen hiçbir
gelir hedefi yoktur.

## ÖZET: ESKİ vs YENİ

| | v1 (satış) | v2 (araştırma) |
|---|---|---|
| Hedef | demo randevusu | 10 sohbet |
| Dil | "let's fix that in one call" | "2 min, no pitch" |
| Para | ima edilmedi | **açık 3 seçenek + "hiçbiri, X"** |
| Kapanış | call isteği | star veya cevap, ikisi de değerli |
| Başarısızlık | satış yok | öğrenme yok (çok daha aydınlatıcı) |
