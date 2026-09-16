# Dümen: an open-source, evidence-first audit engine for the EU AI Act's general-purpose AI obligations

**Technical report — draft for arXiv (cs.CR; cs.AI; cs.CL).**
Version: preprint v0.9 · Dümen software version 0.7.3+ (Apache-2.0) · Date line is set by the build.

Authors: Dümen contributors (corresponding: repository maintainers).
Code: https://github.com/goun7/Dumen · PyPI: https://pypi.org/project/dumen/

---

## Abstract

The EU AI Act's general-purpose AI (GPAI) obligations — model documentation
(Annex XI), transparency, and documented model evaluations under the Code of
Practice — have created demand for audit pipelines that produce *verifiable*,
*reproducible* evidence of model behavior. Existing open-source tooling covers
black-box probing (garak, PyRIT, promptfoo, Inspect) or documentation
automation, but no published open tool combines (i) black-box red-team
batteries, (ii) white-box activation-steering measurement, (iii) a capability
regression gate, and (iv) a tamper-evident evidence chain rendered into
regulatory document formats. We present **Dümen**, such a tool, built around a
single doctrine: *no evidence, no claim* — every unmeasured metric in a Dümen
report renders literally as "Not measured", and a hash-chained, append-only
evidence log (SHA-256; optional Ed25519 head sealing) makes the report's
derivation auditable independently of the auditing organization. We describe
the architecture (five layers: filter, interpretability probes, steering
engine, dual-agent validator, autonomous red-team), the measurement protocols
(behavioral steering-efficacy comparison, B1 capability-externality gate,
gateway self-red-team on holdout, contrastive-data provenance auditing), and
we report measurements on small open-weight models (≤3B parameters) on consumer
hardware: an extended 22-task capability run in which steering that measures
0% efficacy is correctly denied any protection claim (PASS at 0.0pp
regression), a published HarmBench-standard-40 scorecard, and the repository's
first Turkish-language capability slice — in which multi-step arithmetic
misses concentrate in BOTH tested languages, an observation consistent with
published cross-lingual refusal-geometry universality. We
articulate the threat model — including the acknowledged limitation that any
activation-write-capable actor can thin an injected refusal direction — and
show how provenance auditing (robust-median direction estimation with MAD-
calibrated outlier attribution) detects token-swap poisoning of contrastive
extraction data, a recently published attack surface for which no detector had
previously shipped. We release scorecards, raw per-task artifacts, and the
chain verifier as the paper's primary evidence.

## 1 Introduction

Regulation converts engineering practice into documentation duty. For GPAI
models, the EU AI Act (in force since Aug 2025 for GPAI obligations;
transparency duties from Aug 2026) requires model documentation whose Annex XI
content includes *evaluation results*, and the GPAI Code of Practice commits
signatories to documented model evaluations, red-teaming, and systemic-risk
analysis. The compliance market response so far is bifurcated: black-box
scanner suites with no regulatory rendering, and governance SaaS with no
measurement at all.

This paper takes the position that *audit evidence must be machine-checkable*
— a PDF attestation of a red-team run is exactly as trustworthy as the
organization that printed it — and that the tooling must therefore produce, as
a first-class artifact, a verifiable derivation of its own reports.

Contributions:

1. **A five-layer, open-source (Apache-2.0) audit engine** combining black-box
   red-teaming (Inspect-compatible; JailbreakBench / HarmBench / AgentHarm
   catalog formats), white-box activation-steering probes, and regulatory
   rendering (Annex XI dossier, CoP commitment matrix, Art. 55(1)(c) incident
   schema) behind a single CLI (`dumen audit`, `dumen dossier`).
2. **The no-evidence-no-claim rendering doctrine**, implemented in code:
   unmeasured metrics print as "Not measured"; a capability-regression gate
   (B1) refuses the protection claim when steering harms measured capability;
   a deterministic judge-calibration check with exact binomial bounds guards
   LLM-judge usage.
3. **A tamper-evident evidence chain** (append-only SHA-256, whole-chain
   recomputation on load; tampered chains refuse to load) and Ed25519 head
   sealing with an honest identity boundary (identity = key custody; not an
   eIDAS-qualified signature).
4. **Provenance auditing of contrastive steering-data**: token-swap poisoning
   of extraction pairs is a published attack surface (Aidakhmetov et al.,
   2026, arXiv:2606.05958); we ship, to our knowledge the first open detector
   — componentwise-median direction estimation, MAD-calibrated cosine
   thresholds, per-pair outlier attribution, and a mean-vs-median drift angle
   as a drag metric — with ground-truth-indexed synthetic tests and live
   model measurements (Section 6).
5. **A published self-red-team** of Dümen's own gateway on a held-out split of
   a public corpus, with false-positive-rate bounds, regex-jurisdiction
   carve-outs, and per-attack-class detection numbers — including the
   finding that single-token adversarial suffix attacks are *not detected*
   by the wall (honest non-claim).
6. **Consumer-hardware evidence loops**: all reported white-box numbers run on
   ≤8GB VRAM with ≤3B models; installation, run, and verification are each a
   single command (`pip install dumen`).

## 2 Related work

**Steering and refusal geometry.** Refusal behavior is mediated by a compact
directional structure in activation space (Arditi et al., 2024,
arXiv:2406.11717), with subsequent work refining geometry — concept cones
arXiv:2502.17420 — and demonstrating that the refusal direction is shared
across safety-aligned languages (Wang et al., 2025, arXiv:2505.17306), which
implies English-dominant evaluation under-covers multilingual risk.
Activation steering is also an attack surface end-to-end: steering vectors
can be poisoned at the contrastive-data level (arXiv:2606.05958), and
monitoring steering from within a model requires training-time intervention
(Fonseca Rivera et al., 2025, arXiv:2511.21399). Detection and control are
themselves geometrically decoupled (Galeone et al., 2026, arXiv:2606.24952).
Dümen operationalizes these facts as measured audit artifacts rather than
mitigation claims.

**Red-teaming tooling.** garak, PyRIT (archived-then-transferred within
Microsoft, active as microsoft/PyRIT), promptfoo, HELM, and UK AISI's Inspect
provide black-box batteries; MLCommons AILuminate (arXiv:2503.05731) is a
harm benchmark standard; JailbreakBench (arXiv:2404.04561) and HarmBench
(arXiv:2402.04249) publish behavior catalogs. Autonomous attacker pipelines
(PAIR arXiv:2310.08419; TAP arXiv:2312.02119) inform the red-team layer. None
of these tools reads activations, and none renders Annex XI/CoP documents.

**Defenses.** Representation engineering and circuit breakers
(arXiv:2406.04313; robustness reassessment arXiv:2407.15902), RepBend
(arXiv:2504.01550), and refusal-direction stabilization designs (aliases,
harmfulness-refusal coupling, anchored directions: arXiv:2608.18093,
arXiv:2607.00572, arXiv:2509.15202) are mitigation families Dümen *audits
for*, not claims to ship.

**RegTech.** Commercial AI-governance suites (Vanta-type evidence
automation; Giskard's evaluation platform) and EU-AI-Act-specific open-source
document packs (Annex skeleton generators, MCP compliance scanners, OPA/Rego
policy libraries — catalogued in the list this work is submitted against) are
paperwork-centric; Dümen is positioned as the measurement-and-evidence layer
they can call.

## 3 Architecture

Five layers on a single FastAPI/Click runtime (full schema: repo README):

1. **Fast input filter** — injection/PII heuristics; latency measured per
   release (CI benchmark; reported with the measurement, never as a badge).
2. **Interpretability probes** — sparse-autoencoder engines (TopK/JumpReLU)
   with feature-explained-variance quality metrics following SAEBench
   conventions (Karvonen et al., 2025).
3. **Steering engine** — difference-in-means or PCA direction mining per layer
   (`VectorMiner`), tensor projection (StTP) once a decision boundary is
   crossed; rank-k manifold generalization of the single-direction hypothesis
   is Dümen's own and is tested, not assumed.
4. **Dual-agent validator** — generator/validator firewall with policy
   contracts.
5. **Autonomous red-team** — Inspect-compatible task runner (InspectBridge)
   with a hybrid judge; judge usage is gated by a deterministic calibration
   check with exact binomial bounds (`judge_calibration`).

**Evidence chain.** Every stage appends `{index, timestamp, stage, payload,
prev_hash, entry_hash}` to an append-only SHA-256 chain; loading recomputes
the whole chain and refuses tampered files; `dumen sign` seals the chain head
with Ed25519 (identity = key custody, explicitly not a qualified electronic
signature); `dumen export` renders print-ready, brand-embedded single-file
HTML with the chain/head/signature in the footer. All model-origin text is
HTML-escaped at export (untrusted text never becomes markup).

**Capability-externality gate (B1).** Because "safe" steering that destroys
usefulness is a regulatory harm in itself, each behavioral run additionally
executes 12 deterministic in-house tasks (arithmetic/units/geography/
translation/logic; program-verifiable, no LLM judge, echo-safe targets) and —
opt-in — 10 GSM-style multi-step word-problem tasks (task *class* is a
standard capability probe; texts and numbers are original, no licensed corpus
is redistributed). Verdicts are pass/fail/**inconclusive** — where the base
model shows no capability signal, the gate says so instead of inventing a
number.

**Continuous operation.** `dumen watch` spawns full audits on an interval and
records each round (exit code, duration, command) into its own verifiable
chain, with a fail-loud halt after three consecutive failures — subscription
evidence (CoP "continuous evaluation" posture) without a hosted backend.

## 4 Threat model (what the evidence does and does not say)

- *In scope:* untargeted and targeted prompt attacks (black-box); measured
  steering efficacy and capability externality (white-box, local weights);
  evidence tampering (SHA-256 chain + Ed25519 sealing); contrastive-data
  poisoning (provenance auditor, §6).
- *Explicitly out of scope, published:* an attacker able to read the
  activation stream can thin an injected refusal direction — the limitation
  the steering-awareness literature itself acknowledges; runtime direction-
  integrity tripwires are future work with prior art cited at component level.
- *Honesty guarantees enforced in code:* efficacy enters reports only through
  measured comparisons; unmeasured → "Not measured"; scorecards carry raw
  per-task artifacts; licensed/harmful raw corpora never enter the repository.
- *Chain ≠ notarization:* the chain proves internal consistency and, with a
  seal, key custody — not the identity of a natural person and not wall-clock
  time (RFC 3161 TSA is a documented future step).

## 5 Method and reproducibility

All numbers below were produced by:

```bash
pip install dumen
dumen audit --model Qwen/Qwen2.5-0.5B-Instruct --measure-steering --capability-extended --output A.json
dumen audit --model qwen2.5:3b --endpoint http://127.0.0.1:11434/v1 --dataset harmbench_standard40.csv --dataset-limit 40 --output B.json
dumen provenance --model Qwen/Qwen2.5-0.5B-Instruct --pairs 20 --poison-frac 0.25 --output C.json
```

on consumer hardware (NVIDIA GTX 1070 8GB; Python 3.14; torch CPU/CUDA;
Ollama 0.x local endpoint for black-box). Hardware/versions are pinned in the
chain payload of each artifact. Every cited artifact is committed under
`examples/audits/`; the figures in §6 are generated mechanically from those
JSON files (no manual transcription), as is this paper's results table
(`scripts/render_paper_results.py`, included).

## 6 Results (measured)

## 6 Results (measured)

_All values machine-generated from committed artifacts (`examples/audits/`); absent measurements print as "Not measured"._

### 6.1 B1 capability gate with GSM-style external tasks (white-box, Qwen2.5-0.5B-Instruct)

| metric | value |
|---|---|
| artifact present | yes |
| task set | internal-12+gsm-style-10 |
| accuracy unsteered | 59.1 |
| accuracy steered | 59.1 |
| regression pp (tolerance 5.0) | 0.0 |
| **gate verdict** | pass |
| steering efficacy, same run (%%) | 0.0 |

### 6.2 HarmBench standard-40 black-box scorecard (qwen2.5:3b via local Ollama)

| metric | value |
|---|---|
| artifact present | yes |
| tasks evaluated | 40 |
| overall safety score | 91.1 |
| report id | DUMEN-AUDIT-1789515091 |
| model / endpoint | qwen2.5:3b@http://127.0.0.1:11434/v1 |
| dataset | HarmBench standard-40 (local copy; not redistributed) |

### 6.3 Contrastive-data provenance audit (token-swap poisoning, Qwen2.5-0.5B-Instruct)

| metric | value |
|---|---|
| artifact present | yes |
| pairs / poison-fraction | 8 / 0.25 |
| detector recall (poisoned pairs flagged) | 0.0 |
| false-positive rate (clean pairs flagged) | 0.0 |
| mean↔median direction drift angle (deg, poisoned set) | 17.686 |
| baseline flags on clean set | [] |
*(Prior art credit: poisoning surface — arXiv:2606.05958; detector combination is Dümen's at tool level. Low-intensity recall=0 is the published calibration boundary, not a tuning artifact.)*


## 7 Limitations

- Small models (≤3B) are the *substrate*, not the subject: published numbers
  characterize Dümen's measurement loop on open checkpoints; frontier-model
  runs (larger weights, hosted APIs) are operator-configuration exercises with
  the same code paths.
- Behavioral efficacy is judge-mediated by design (hybrid judge); the
  deterministic calibration guard bounds — but does not eliminate — judge
  subjectivity.
- The provenance detector targets the token-swap/label-noise class; fluent
  semantic poisoning remains geometrically invisible (§4).
- Capability tasks: the 12-task core and 10-task GSM-style extension are
  English arithmetic/knowledge; the Turkish slice (10 original tasks, one 3B
  family, black-box channel) is n=10 per language and reports a %70-vs-%60
  accuracy pattern we deliberately do NOT call parity — the difference is
  inside its own noise band; TR B4 (refusal-stress) evidence remains open.

## 8 Conclusion

Regulatory evidence for AI is a software artifact problem before it is a
policy problem. Dümen ships the artifact loop — measure, hash, seal, render,
re-verify — as Apache-2.0, on hardware an auditor already owns, with the
uncomfortable results (0% efficacy on one family; undetected suffix attacks;
undetectable fluent poisoning) published in the same repository as the
promising ones. That honesty contract is the contribution; the engine is how
it stays enforceable.

## References (verified against arXiv on 2026-09-16)

Arditi et al., 2024 — Refusal in LMs is mediated by a single direction. arXiv:2406.11717.
Wang et al., 2025 — Refusal direction is universal across safety-aligned languages. arXiv:2505.17306.
Aidakhmetov et al., 2026 — Steering vectors are an adversarial attack surface. arXiv:2606.05958.
Fonseca Rivera et al., 2025 — Steering awareness: detecting activation steering from within. arXiv:2511.21399.
Galeone et al., 2026 — Perfect detection, failed control: the geometry of knowing vs. steering. arXiv:2606.24952.
Zou et al., 2024 — Improving alignment and robustness with circuit breakers. arXiv:2406.04313.
Robustness reassessment of circuit-breaker defenses, 2024. arXiv:2407.15902.
RepBend (ACL 2025). arXiv:2504.01550.
Concept cones. arXiv:2502.17420.
PAIR. arXiv:2310.08419. TAP. arXiv:2312.02119.
JailbreakBench. arXiv:2404.04561. HarmBench. arXiv:2402.04249.
MLCommons AILuminate. arXiv:2503.05731.
SAEBench (Karvonen et al., 2025). arXiv:2503.09532.

*(Additional verified corpus — 60+ entries with access-tier classification —
is maintained in the repository's research log; only citations used above are
listed here in full.)*
