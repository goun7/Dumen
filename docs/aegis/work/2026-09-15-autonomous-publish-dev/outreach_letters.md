# OUTREACH — iki varyant (İÇ TASLAK; gönderim kurucunun onayına bağlı)
Kaynak: research_cop_targets.md (20 hedef, 15-Eyl-2026 doğrulamalı).

## Varyant A — "kanıt-yayıncılığı" (BFL, Aleph Alpha, Bria, Pleias, Almawave, Cohere, WRITER)
Subject: your model family could ship the EU's first open white-box audit evidence

Hi [Name/Team],

The GPAI Code of Practice you signed asks for documented model evaluations and
transparency evidence — but for most labs outside the top three, that evidence
does not exist publicly yet, and building an in-house audit pipeline is months
of work.

Dümen (Apache-2.0, github.com/goun7/Dumen, `pip install dumen`) is an open
audit engine built for exactly this gap: it runs black-box red-team batteries
(JailbreakBench/HarmBench/AgentHarm formats) and, when you can give it local
weights, white-box activation-steering probes that measure whether your safety
behavior is a single removable direction — then writes every step into a
tamper-evident SHA-256 chain and renders Annex XI / CoP-format documents.
Everything unmeasured is printed as "Not measured" — no fabricated scores.

Two things we can do in one call, self-hosted, no data leaves your infra:
1) `dumen audit` on one of your models → publishable scorecard (we can run a
   sample family first: 3 model families already have public scorecards in
   the repo);
2) `dumen dossier` → draft Annex XI technical documentation with the chain
   attached.

If a third party should sign the evidence, `dumen sign` seals the chain head
with your Ed25519 key — provenance without promising eIDAS magic.

Worth 30 minutes? [calendly/reply]
— [Founder], Dümen maintainers

## Varyant B — "downstream paket" (Microsoft, Amazon, ServiceNow, IBM, Google)
Subject: Annex XII packages for your downstream deployers, machine-generated

Hi [Team],

Article 53(1)(b)/Annex XII obligations flow to the hundreds of deployers on
[your platform]. They are asking you for evidence packages on a 14-day
cadence (CoP Transparency downstream rule). Paper won't scale; hash-chains
will.

Dümen is an Apache-2.0 audit engine that turns evaluation runs into
tamper-evident evidence chains and Annex XI/CoP-format documents
machine-generated per model-version — designed so your platform can offer
deployers a reproducible artifact instead of a PDF attestation. White-box
steering probes included when weights are available (your own or open ones).

Happy to demo against a Bedrock/Azure/watsonx-hosted open-weight model and
publish the run — repo: github.com/goun7/Dumen · PyPI: dumen.

— [Founder]

## Kurallar
- Gövdede hiçbir ölçüm-vaadi yok; repo'daki gerçek karnelere link.
- "first/only" iddiası yalnız doğrulanmış-ara-boşluk cümlesiyle (rakip
  manzarası Bölüm 3: beyaz-kutu+AnnexXI kombinasyonu doğrulanmış boşluk).
- xAI: gönderilmez (toksik-bağ notu) — pasif okuyucu.
- Imzacı-kişi bilgisi resmen yok → hitap "Team"/genel adres.
