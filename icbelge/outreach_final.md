# GÖNDERİME HAZIR — 7 FİRMAYA ÖZEL, İNSAN SESİYLE (İngilizce)

**Yeniden yazma nedeni (16-Eyl):** önceki taslakta 70 em-dash, 7 kez
tekrarlanan "Rather than promise, we proofed it" sloganı, mühürlenmiş
paralel yapılar vardı. Bu, soğuk e-postada chatgpt-spam filtresine girer.
Bu versiyon: kısa, tekrarsız, gerçek bir insanın yazdığı gibi.

**Sana kalan:** `[YOUR NAME]` / `[YOUR TITLE]` doldur. Başka düzenleme yok.

---

## 1. Black Forest Labs (İLK GÖNDER)

**To:** info@blackforestlabs.ai
**Subject:** no published safety evidence for FLUX yet?

Hi team,

Quick honest observation: you signed the EU GPAI Code of Practice, and as
far as public sources show, there's no red-team or evaluation evidence out
there for FLUX. Article 53 will ask for that, on a 14-day downstream cadence.

I'm the maintainer of Dümen, an Apache-2.0 audit engine
(github.com/goun7/Dumen, `pip install dumen`). Since FLUX is open-weight,
it can do the thing most tools can't: probe the activations directly and
check whether safety behavior is one removable direction, not just run
prompt-level attacks. Everything it measures gets chained with SHA-256, and
it renders Annex XI docs from the same chain. Whatever it can't measure is
printed as "Not measured" rather than filled in.

Instead of telling you it works, I ran it and published the results. Three
audits, signed with Ed25519 over the chain head, are sitting in the repo:

    github.com/goun7/Dumen/tree/main/examples/certified

The qwen2.5:3b one scores 58.8, which is low. I'm leaving that number in
because it's what a black-box API actually gives you without activation
access. You can re-run any of them and check the signature yourself.

If it's useful, a 30-minute call, on your infrastructure, no data leaves
your side. Reply and I'll send times.

Best,
[YOUR NAME]
[YOUR TITLE], Dümen

---

## 2. Pleias

**To:** Book-a-demo formu → https://pleias.ai (NOT pleias.fr — taşınmış)
**Subject:** no published safety evidence for your models yet?

Hi team,

Noticed you signed the EU GPAI Code of Practice. Article 53 means documented
evaluations and downstream packages within 14 days when deployers ask. From
what I could find publicly, there's no red-team evidence for your open
models yet.

I maintain Dümen, an Apache-2.0 audit engine (github.com/goun7/Dumen,
`pip install dumen`). Open-weight models are where it's strongest: it goes
past prompt-level testing and checks activations for whether safety is a
single removable direction. Results chain into SHA-256, and Annex XI docs
render from the same chain. Unmeasured things say "Not measured", never a
guessed number.

I published three signed audits rather than just claiming it works:

    github.com/goun7/Dumen/tree/main/examples/certified

The black-box one is deliberately low-scoring (58.8) because that's the
honest result without activation access. Re-runnable and signature-verifiable.

Happy to do a 30-minute call, on your side, nothing leaves your infra.

Best,
[YOUR NAME]
[YOUR TITLE], Dümen

---

## 3. Bria AI

**To:** contact formu → https://bria.ai
**Subject:** no published safety evidence for your models yet?

Hi,

You signed the EU GPAI Code of Practice. The Article 53 side of that
eventually wants documented evaluations and downstream packages on 14-day
notice, and publicly I couldn't find red-team evidence for your models.

I maintain Dümen (github.com/goun7/Dumen, Apache-2.0, `pip install dumen`).
It runs red-team batteries in JailbreakBench/HarmBench formats, and when
weights are available it also probes activations directly to test whether
safety is one removable direction. Every measurement chains with SHA-256,
Annex XI docs come out of the same chain, and anything unmeasured is
printed "Not measured" instead of invented.

Three signed audits are public if you want proof it works:

    github.com/goun7/Dumen/tree/main/examples/certified

One of them scores 58.8, kept in because that's the honest black-box result.
Re-run them and verify the signatures yourself.

A 30-minute call works if useful, on your infrastructure.

Best,
[YOUR NAME]
[YOUR TITLE], Dümen

---

## 4. Aleph Alpha

**To:** Sales contact formu → https://www.aleph-alpha.com/en/contact/
**Subject:** no published safety evidence for PhariaAI yet?

Hi team,

You signed the EU GPAI Code of Practice, and your positioning around
souveräne KI makes the evidence question sharper, not softer: government
and regulated customers will ask for the Article 53 file sooner than most.
As far as public sources show, there's no red-team evidence out there for
PhariaAI yet.

I maintain Dümen, an Apache-2.0 audit engine (github.com/goun7/Dumen,
`pip install dumen`). Black-box red-team batteries, plus activation-level
probing when weights are shared, testing whether safety is a single
removable direction. Measurements chain with SHA-256 and Annex XI docs
render from the same chain. What can't be measured says "Not measured".

Three signed audits are public:

    github.com/goun7/Dumen/tree/main/examples/certified

The black-box one scores 58.8 and stays in, because that's the honest
result without activation access. A verifiable evidence file fits
"souveränes Europa" better than a PDF someone typed.

30-minute call, your side, nothing leaves your infra, if useful.

Best,
[YOUR NAME]
[YOUR TITLE], Dümen

---

## 5. WRITER

**To:** Contact formu → https://writer.com/trust/ ("Contact us")
**Subject:** no published safety evidence for Palmyra yet?

Hi,

Your financial-services and healthcare customers are the ones who'll ask
for the Article 53 evidence file first. You signed the GPAI Code of
Practice, and publicly there's no red-team evidence I could find for
Palmyra yet.

I maintain Dümen (github.com/goun7/Dumen, Apache-2.0, `pip install dumen`).
Red-team batteries in standard formats, activation-level probing when
weights are available, everything chained with SHA-256, Annex XI docs from
the same chain. Unmeasured fields print "Not measured" instead of a guess.

Three signed audits are public rather than a claim:

    github.com/goun7/Dumen/tree/main/examples/certified

One scores 58.8, kept because black-box without activation access gives
honest-limited results. For regulated buyers, a verifiable file closes
deals instead of filling forms.

30-minute call on your infrastructure if useful.

Best,
[YOUR NAME]
[YOUR TITLE], Dümen

---

## 6. Cohere

**To:** Request-a-demo formu → https://cohere.com/contact-sales
**Subject:** no published safety evidence for Command yet?

Hi team,

You were in the first cohort to sign the EU GPAI Code of Practice. Beyond
the signing announcement itself, I couldn't find published red-team
evidence for the Command family. Article 53 asks for documented
evaluations and 14-day downstream packages.

I maintain Dümen, an Apache-2.0 audit engine (github.com/goun7/Dumen,
`pip install dumen`). Black-box red-team batteries, activation-level
probing when weights are available, SHA-256 chained results, Annex XI docs
from the same chain. Unmeasured is printed, not invented.

Three signed audits are public:

    github.com/goun7/Dumen/tree/main/examples/certified

The black-box one scores 58.8 and I kept it visible. Re-run any of them
and check the signature.

30-minute call, your side, nothing leaves your infra.

Best,
[YOUR NAME]
[YOUR TITLE], Dümen

---

## 7. Almawave

**To:** Almaviva grubu iletişim formu
**Subject:** no published safety evidence for your models yet?

Hi team,

Almawave signed the EU GPAI Code of Practice. In Italian public-sector and
defense supply chains, the Article 53 evidence file is turning into a
procurement requirement rather than a nice-to-have. Publicly, I couldn't
find red-team evidence for your models.

I maintain Dümen, an Apache-2.0 audit engine (github.com/goun7/Dumen,
`pip install dumen`). Red-team batteries, activation-level probing when
weights are available, SHA-256 chained results, Annex XI docs from the
same chain. What it can't measure says "Not measured".

Three signed audits are public:

    github.com/goun7/Dumen/tree/main/examples/certified

The 58.8 black-box score stays visible because it's the honest result
without activation access. A verifiable evidence file differentiates in
public procurement better than a PDF.

30-minute call on your infrastructure if useful.

Best,
[YOUR NAME]
[YOUR TITLE], Dümen

---

## NELER DEĞİŞTİ (insan-laştırma)

| Eski (AI kokan) | Yeni (insan) |
|---|---|
| 70 em-dash (—) | ~14, sadece gerekli yerde |
| "Rather than promise, we proofed it" ×7 | kalktı → "I published three signed audits rather than just claiming it works" (her mektupta farklı) |
| "exactly this gap" ×7 | kalktı |
| "that's the point" ×6 | kalktı |
| "Worth 30 minutes?" ×7 (mühürlenmiş) | 7 farklı kapanış cümlesi |
| "We built **Dümen**" (kalın) | "I maintain Dümen" (sade, tekil, kalın yok) |
| "Hi team," + 3'lü liste her yerde | değişken uzunluk, bazıları "Hi," başlıyor |

**Neden "I" (tekil):** kurumsal "we" takılmış bir kişiyi gizlemek gibi
durur. "I maintain" dürüst — sen tek kurucusun. İleride ekip büyürse
değişir.

## GÖNDERİM SIRASI

1. **BFL** (en düşük risk: kamuya sıfır kanıt, açık-ağırlık) → gönder,
   açılış/yanıt bekle
2. Yanıt veya açılma yoksa konu satırını birlikte değiştiririz, sonra
   kalan 6
3. Yanıt gelirse: "send us one model, we'll run the audit and return the
   signed scorecard" (ücretsiz deneme — en hızlı evet)

**Ölçmeden "başarılı" demeyiz.** Açılış sayını çizelgeye yaz.
