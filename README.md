<p align="center"><img src="https://raw.githubusercontent.com/goun7/Dumen/main/.github/assets/banner.svg" alt="Dümen — helm-mark banner"/></p>

# Dümen

> [Türkçe](README_TR.md) · **English** (this page)

[![CI](https://github.com/goun7/Dumen/actions/workflows/build.yml/badge.svg)](https://github.com/goun7/Dumen/actions/workflows/build.yml) [![License: Apache 2.0](https://img.shields.io/badge/license-Apache%202.0-blue)](LICENSE) [![Python 3.10–3.14](https://img.shields.io/badge/python-3.10_–_3.14-blue)](https://pypi.org/project/dumen/)

**Mechanistic auditing, SAE interpretability and runtime activation-steering platform
for frontier AI models**

> *"It makes the latent intent of frontier models transparent at neuron level,
> and prevents loss of control mathematically by steering at inference time —
> before the model ever emits the harmful output."*

Dümen is the **technical answer** to the need voiced by the
**International AI Safety Report** (Bengio et al., 2025; arXiv:2501.17805) —
the G7-mandated report advocating independent third-party audits: it unifies
white-box auditing (activation steering on open-weight models; SAE inspection
ships as a library API) and black-box auditing (configurable dual-layer
firewall + adversarial red-teaming battery on API models) under a single
evidence chain. (This paragraph is a motivation frame, not an evidence
claim — Dümen's doctrine: nothing unmeasured ever enters a report as a number.)

## Why Dümen (measured, not claimed)

Behavioral red-teaming alone no longer distinguishes a tool — the 2026 OSS
landscape has several capable black-box batteries. What is missing in every
one we verified is **weight-space access turned into regulatory evidence**:

| Capability | Dümen (measured here) | Black-box-only tools |
|---|---|---|
| Activation-steering efficacy, measured | **0.077 median cos shift**, non-monotone by design (§6.2) | structurally impossible |
| Weight-space provenance detection | pool=20, poison-frac 0.5, null CI [0.329, 0.586] | structurally impossible |
| Annex XI + Code-of-Practice dossier, machine-generated | one command, chain-anchored | not produced |
| Tamper-evident evidence chain + Ed25519 sealing | SHA-256 append-only; tampering exits non-zero | rarely present |

This is the honest position: red-team-plus-audit is no longer a differentiator
(the gap closed in 2026), so Dümen's claim is narrower and verifiable —
**white-box steering + weight-space provenance + Annex XI**, on open-weight
models, with every number in this README reproducible by the commands above.

**Limitation stated plainly:** steering on mixture-of-experts checkpoints is
diagnostic-only (`moe-joint-test`); the provenance detector covers the
token-swap/label-noise class only, and at tested intensities even that class
is invisible to post-hoc pool geometry (the honest double-negative result is
published, not hidden). See PAPER.md §7.

## Install

```bash
pip install -e ".[dev]"
python -m pytest tests/ -q          # full suite, 100% green
```

> **PyPI:** `pip install dumen` — published same-day with the repo opening
> (15-Sep-2026). Source install also works: `pip install -e ".[dev]"`.
>
> **Device note (honest):** all published artifacts run on CPU. `torch.cuda.is_available()`
> can report True on a Pascal-class GPU (sm_61) while cu130 wheels require sm_75+,
> so forwards raise `AcceleratorError`. CPU is the default; opt into a specific
> device with `DUMEN_DEVICE=cuda` (or any torch device string) if your card matches
> the wheel's compute capability.
>
> **Install weight (honest note):** the core ships `torch` — a fresh virtualenv
> measured ~5GB, the first download takes minutes; but the first RUN takes
> seconds: the refusal-baseline audit measured **5.1s** on a fresh install
> (15-Sep gate measurement). White-box model downloads are a separate matter.
> Fresh-environment smoke test passed end-to-end: `dumen --version` →
> `dumen audit --refusal-baseline --output k.json` → `dumen dossier --model X`
> → `dumen sign` → `dumen verify` (exit 0).

For real-model auditing (optional):

```bash
pip install transformers
python -m pytest tests/test_real_model_integration.py -v   # real GPT-2 proof
```

## Quickstart

### 1. Model audit (three evidence channels)

```bash
# (a) Refusal-baseline: pipeline verification, no model required
dumen audit --refusal-baseline --output karne.json

# (b) White-box (local HF): activation access → steering efficacy measurable
dumen audit --model Qwen/Qwen2.5-0.5B-Instruct
dumen audit --model Qwen/Qwen2.5-0.5B-Instruct --measure-steering

# (c) Black-box (API endpoint): Ollama / vLLM / LM Studio / OpenAI-compatible
dumen audit --model qwen2.5:3b --endpoint http://127.0.0.1:11434/v1
# single-VRAM machines with cold model loads / slow generation: --request-timeout 300 (seconds)
# widen with a published attack set (JBB/HarmBench/AgentHarm/AILuminate — schema auto-detected):
dumen audit --model qwen2.5:3b --endpoint http://127.0.0.1:11434/v1 \
    --dataset examples/datasets/jbb_harmful_behaviors.csv --dataset-limit 40
```

Risk scores are **never hand-entered** — they are derived from the harm_score
of the red-team samples actually run. Efficacy becomes a number **only if
`--measure-steering` measures it**; on the API-endpoint channel activations
cannot be read, so efficacy is unmeasurable and the report prints "Not
measured" (the era of a fabricated %96 is over). Published evidence:
Qwen2.5-0.5B (white-box, B1-gated) + **three Ollama families** (qwen2.5:3b,
llama3.2:3b — std+JBB-40; phi3:mini — std+JBB-10) — comparison table in
`examples/audits/README.md`. A **sales-grade sample dossier** generated from
these real scorecards lives in `examples/pilot/` (real scores + declared-pending
fields clearly labelled). **Certified audits** (imzalanmış, tekrar üretilebilir)
in `examples/certified/` — 0.5B/1.5B beyaz-kutu (97.5) + 3B siyah-kutu API (58.8):
kanal farkının sonucu nasıl değiştirdiğini gösterir.

### 2. EU AI Office Annex XI dossier (one command)

```bash
dumen dossier --model my-gpai-model --output annex_xi.md
# → Annex XI technical documentation + Code of Practice matrix + SHA-256 evidence chain
```

### 3. Firewall proxy (in front of API models)

```bash
# single layer: fast filter only — /health and dumen_meta SAY SO
dumen serve --upstream https://api.openai.com --api-key $KEY --strict
# dual layer: add the secondary LLM validator (any OpenAI-compatible endpoint)
dumen serve --upstream https://api.openai.com --api-key $KEY --strict \
  --validator-url http://127.0.0.1:11434/v1 \
  --validator-model qwen2.5:3b \
  --validator-key $VAL_KEY   # omit for local Ollama
# → OpenAI-compatible reverse proxy: injection filter + PII masking;
#   the validator tier is OPT-IN and every response discloses which layer decided
```

### 4. Python API — contrastive vector mining

```python
from dumen import ContrastiveBenchmarkSuite, VectorMiner, RiskCategory, SteeringEngine

# Built-in literature-based seeds (MACHIAVELLIANISM, TruthfulQA, CyberSecEval, ...)
suite = ContrastiveBenchmarkSuite()
pairs = suite.get_contrastive_pairs(RiskCategory.DECEPTION)

# Mine vectors from real model forward-hook activations
vectors = VectorMiner.mine_from_prompts(
    prompt_pairs=pairs,
    forward_hook_extractor=my_hook_extractor,   # a transformers hook
    target_risk=RiskCategory.DECEPTION,
    target_layers=[12, 16],
    rank=4,          # rank-k refusal manifold (post-Arditi literature)
    n_bootstrap=50,  # direction confidence interval
)

# Runtime intervention
engine = SteeringEngine()
engine.register_vector(vectors[12])
steered, intervened, scores = engine.apply_steering(hidden_state, layer_idx=12)
```

### 5. Real datasets — external catalog bridges

Four published sets translate into one common `BenchmarkSeed` contract (schema
auto-detected):

```python
from dumen import JailbreakBenchLoader, HarmBenchLoader, AgentHarmLoader, AILuminateLoader

seeds = HarmBenchLoader.load_from_file("harmbench_behaviors_text_all.csv")   # 400 behaviors
seeds = AgentHarmLoader.load_from_file("harmful_behaviors_test_public.json") # 176 agentic tasks
pairs = [(s.harmful_prompt, s.safe_prompt) for s in seeds]                   # mining-ready
```

> Raw-data licenses: JBB MIT (in the sample repo OK); deepset/AgentHarm are
> research-licensed — **never committed**, loaders read the user's local file
> (see `examples/redteam_gateway_self.py`).

### 6. Test your own wall — gateway self-red-team

```python
from dumen.benchmarks import GatewaySelfRedTeam
m = GatewaySelfRedTeam.evaluate(samples)   # recall/FPR + raw escapes included
```

Two-layer measurement against a published corpus, on a holdout
(regex ∪ semantic judge): `examples/audits/gateway_selfredteam_qwen2.5-3b.json`.

### 7. Seal it, ship it, keep watching — evidence lifecycle

```bash
dumen keys --name auditor --dir ./keys                 # Ed25519 pair (private 0600)
dumen sign --chain karne.json --key ./keys/auditor.key --name "Acme Audit Ltd"
dumen verify --chain karne.json --sig karne.json.sig --pub ./keys/auditor.pub
dumen export --input dossier.md --chain karne.json --sig karne.json.sig
dumen watch --runs 4 --interval 3600 \
  --audit-arg --refusal-baseline --audit-arg --output --audit-arg run.json
dumen capability --model qwen2.5:3b --endpoint http://127.0.0.1:11434/v1 \
  --task-set all      # 32-task B1 battery, any OpenAI-compatible endpoint
dumen provenance --model Qwen/Qwen2.5-0.5B-Instruct --sweep \
  --poison-frac 0.3   # contrastive-data poisoning intensity curve
```

`capability` runs the B1 battery standalone — including 10 ORIGINAL Turkish
tasks (first multilingual slice; on qwen2.5:3b TR 70% vs EN-GSM 60% with the
internal-12 at 12/12 — misses concentrate on multi-step arithmetic in BOTH
languages; the n=10 gap is inside its own noise band, so we deliberately do
NOT call it parity). `provenance` audits the very data steering vectors are
mined from: token-swap poisoning (attack surface credited to arXiv:2606.05958).
Published as a DOUBLE NEGATIVE: per-pair outlier flags recalled 0 poisoned
pairs at 2/8/16 swaps, and the pool-level drift — monotone with intensity —
stays inside its bootstrap null (a seed-fixed significance test vetoed the
plausible-looking signal). At tested intensities and pool sizes, token-swap
poisoning is invisible to post-hoc pool geometry; the boundary is measured,
not tuned away.

`sign` seals the chain HEAD (a broken chain cannot be signed — integrity gate
runs at load); `verify` independently recomputes chain + signature + head and
exits non-zero on any mismatch. Identity = key custody: cryptographic
provenance, **not** an eIDAS qualified signature. `export` renders a
single-file, print-ready HTML with the embedded mark and a chain-seal footer
(model output is HTML-escaped — untrusted text never becomes markup). `watch`
spawns a full `dumen audit` per round and records every round into its own
append-only chain; 3 consecutive failures halt loudly (exit 2). The B1
capability gate additionally supports `--capability-extended`: 12 in-house
tasks plus 10 GSM-style multi-step word problems, all program-verifiable.

## Architecture (two shipped pipelines + one library surface)

```
AUDIT pipeline (dumen audit / dossier — what produces the published evidence):
  task suite → [1] adversarial red-team battery (InspectBridge, single-shot;
                    hybrid judge: regex fast-path + optional LLM, `evaluated_by`-tagged)
             → [2] white-box only: VectorMiner mines steering vectors from real
                    activations → measured steering efficacy + B1 capability gate
             → [3] evidence chain (SHA-256 append-only; optional Ed25519 head seal)
             → [4] scorecard · Annex XI dossier · CoP matrix · print-ready HTML

GATEWAY pipeline (dumen serve — the black-box firewall):
  request → [1] fast filter (injection/PII, measured ~0.03ms — tests/test_latency_bench.py)
          → upstream call
          → [2] output scan + PII redaction; the SECONDARY LLM validator runs only
                 when configured (--validator-url); otherwise the response's
                 dumen_meta discloses `fast_filter` as the deciding layer
          → SSE streaming: delayed-window masking, fail-closed cut on violation
          → [3] every audited decision carries its layer identity

LIBRARY surface (Python API — genuinely implemented + unit-tested, but no CLI
command runs them today; we say so instead of implying otherwise):
  SAE engine & quality bench (FEV/L0/sweep) · multi-turn PAIR/HRL red-team
  engine · judge-calibration harness · steering-overhead bench
```

## Scientific basis

| Capability | Grounding |
|---|---|
| Single-direction refusal (DiM mining) | Arditi et al., NeurIPS 2024 (arXiv:2406.11717) |
| Rank-k manifold | Multi-directional refusal evidence: Rocchetti & Ferrara 2026, "Refusal Beyond a Single Direction" (arXiv:2606.13720); the k-dimensional SVD generalization is Dümen's own |
| SAE quality metrics (FEV, L0, sweep) — *library API; no CLI command runs it yet* | SAEBench, Karvonen et al., ICML 2025 |
| Steering-load measurement — *library API; not wired into `dumen audit`* | capability-retention paradigms |
| Multi-turn red teaming (PAIR/HRL) — *library API; the shipped CLI battery is single-shot* | PAIR (Chao et al., 2023; arXiv:2310.08419), TAP (Mehrotra et al., NeurIPS 2024; arXiv:2312.02119) |
| External dataset bridges | JAILBREAKBENCH (dormant since Apr 2025) + **MLCommons AILuminate** format bridge (2026 standard; arXiv:2503.05731) |
| Behavioral steering efficacy | pre/post-steering weakness comparison on the same attack prompts — "Not measured" unless actually measured |
| Regulatory alignment | EU AI Act Art. 53/55, Annex XI, GPAI Code of Practice (10-Jul-2025) |

## Regulatory scope

- **Annex XI technical documentation** — Art. 53(1)(a): model identity, training
  computation resources, data governance, systemic-risk matrix, runtime measures
- **Code of Practice matrix** — 8 commitments with honest `partial`/`not_demonstrated` states
- **Art. 55(1)(c) serious-incident reporting** — AI Office format gated on HIGH+ severity
- **Evidence chain** — append-only SHA-256; a tampered chain refuses to load

**Enforcement timeline (European Commission official page, accessed Sep 2026):**
prohibitions entered force 2-Feb-2025; GPAI obligations + governance
2-Aug-2025; **Art. 50 transparency rules 2-Aug-2026** (the nearest obligation —
Dümen is ready for content-labeling/concealment auditing); prohibition #9
(non-consensual image manipulation) moved to **Dec 2026** via the AI Omnibus
added Aug 2025; **strict obligations for Annex-III high-risk systems were
postponed to 2-Dec-2027** after the Omnibus. Dümen's high-risk GPAI dossier
generation is in time for that 2027 window; the transparency obligation is
covered today.

## Quality evidence (v0.7.4)

- 406 unit tests, 100% green (CI: Python 3.10/3.12/3.14 matrix; real-model
  tests included on 3.12)
- Coverage %96.9+ (CI gate %95), ruff lint 0 errors
- **Zero fabricated numbers**: efficacy enters a report only via the
  `--measure-steering` behavioral comparison; every unmeasured metric renders
  as "Not measured / not claimed"
- **B1 capability-externality gate**: steering is measured on the
  capability-harm side too — 12 core + 10 GSM-style + 10 Turkish
  deterministically-verifiable tasks (pass/fail/inconclusive, no judge).
  Live: Qwen2.5-0.5B extended-22 → **PASS, 0.0pp** (%59.1→%59.1) alongside
  efficacy %0 on the same run — the gate refuses protection claims where
  steering is inert. qwen2.5:3b black-box 32-task run: TR %70 (7/10) vs EN-GSM %60 (6/10), internal-12 12/12 — misses concentrate on multi-step arithmetic in BOTH languages (the n=10 gap is noise-banded); multilingual evidence the field lacks. If the
  gate fails, the protection claim is retracted from CLI **and** Annex XI.
- **Published audits** (comparison table: `examples/audits/README.md`):
  Qwen2.5-0.5B white-box + **three Ollama families** black-box — qwen2.5:3b
  (standard 58.8, sandbox %95 real finding · JBB-40 91.8 · **HarmBench
  standard-40 91.1**, hallucination %9.2 top risk), llama3.2:3b
  (standard 77.5, cyber %60 · JBB-40 **91.3** — inter-family consistency
  measured), phi3:mini (standard 95.0 · JBB-10 97.0 — n difference flagged in
  the table)
- **Red-teaming our own firewall, on a holdout, raw numbers published**: regex
  layer FPR %0 / recall %20 → combined with the semantic layer: %78.3 recall /
  **%16.1 FPR** (the 3B judge's false-accepts are UNSAFE — threshold sweeping
  does not lower FPR; known limitation, `gateway_selfredteam_qwen2.5-3b.json`)
- Real-model integration tests (tiny GPT-2: hook → mining → steering → generation
  + efficacy comparison + B1 gate)
- Permutation significance test: mined directions carry statistically-evidenced
  p-values
- External attack catalogs: JAILBREAKBENCH (MIT, in-repo) + **HarmBench 400** +
  **AgentHarm 176** + AILuminate bridge — schema auto-detected via `--dataset`
- Judge-calibration comparison: FP/FN confusion matrix measured on the
  adversarially-labeled HOLDOUT of the gateway self-red-team run (artifact
  above); a standalone JudgeCalibrationHarness (κ, dual-labeler) ships as a
  Python API — its human second-label pass is open (B3): `examples/calibration_seed.py`
- `dumen steer-test`: offline deterministic self-check of steering math
  (|cos| reduction + OV thinning are ASSERTED; non-zero exit on regression)
- `dumen moe-joint-test`: Mixture-of-Experts joint-intervention diagnostic —
  flags the silent-failure regime where single-component steering reports a
  reduction that joint intervention recovers ~4x better (arXiv:2609.09793).
  Detects it from measured cross-component subspace overlap; live-320B
  validation is open work, the module docstring states the boundary
- `dumen amplification-scan`: TLCM amplification-regime detector — sweeps α
  and flags the first α where |cos_after| > |cos_before| (the
  low-confidence-direction regime from arXiv:2609.07876), returning a
  safe-α boundary. Detection, not prevention; synthetic-vector validation
- Latency gates enforced in tests: regex ~0.03ms, p99 < 10ms, full validation ~0.4ms
- Real HTTP test of the API-endpoint black-box channel + live Ollama audits
  published (`--request-timeout`: field fix for single-VRAM cold loads)
- Citation audit (Sep 2026): 12 of 12 arXiv IDs verified against primary
  sources; 3 wrong citations corrected, 2 unverifiable claims removed

## License

Apache-2.0 — see [LICENSE](LICENSE).

## Documentation

- [examples/](examples/) — runnable examples (index in `examples/README.md`)
- [examples/audits/](examples/audits/README.md) — published scorecards + family comparison table
- [examples/pilot/](examples/pilot/README.md) — sample compliance dossier generated from real data
- [CHANGELOG.md](CHANGELOG.md) · [SECURITY.md](SECURITY.md) · [CONTRIBUTING.md](CONTRIBUTING.md)