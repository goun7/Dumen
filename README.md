# 🛡️ Dümen (SteeringOS)

> 🌐 [Türkçe](README_TR.md) · **English** (this page)

[![CI](https://github.com/goun7/Dumen/actions/workflows/ci.yml/badge.svg)](https://github.com/goun7/Dumen/actions/workflows/ci.yml) [![License: Apache 2.0](https://img.shields.io/badge/license-Apache%202.0-blue)](LICENSE) [![Python 3.10–3.14](https://img.shields.io/badge/python-3.10_–_3.14-blue)](https://pypi.org/project/dumen/)

**Mechanistic auditing, SAE interpretability and runtime activation-steering platform
for frontier AI models**

> *"It makes the latent intent of frontier models transparent at neuron level,
> and prevents loss of control mathematically by steering at inference time —
> before the model ever emits the harmful output."*

Dümen is the **technical answer** to the need voiced by the
**International AI Safety Report** (Bengio et al., 2025; arXiv:2501.17805) —
the G7-mandated report advocating independent third-party audits, echoing calls
from frontier-lab leaders (e.g. Altman and Amodei): it unifies white-box
auditing (SAE + activation steering on open-weight models) and black-box
auditing (dual-agent firewall + autonomous red-teaming on API models) under a
single evidence chain. (This paragraph is a motivation frame, not an evidence
claim — Dümen's doctrine: nothing unmeasured ever enters a report as a number.)

## Install

```bash
pip install -e ".[dev]"
python -m pytest tests/ -q          # full suite, 100% green
```

> **PyPI note:** the `dumen` package name was **verified free** on 15-Sep-2026
> (HTTP 404). Publishing to PyPI happens in lockstep with opening the repo —
> until then install from source (`-e .`); there is no `pip install dumen`
> claim yet.
>
> **Install weight (honest note):** the core ships `torch` — a fresh virtualenv
> measured ~5GB, the first download takes minutes; but the first RUN takes
> seconds: the refusal-baseline audit measured **5.1s** on a fresh install
> (15-Sep gate measurement). White-box model downloads are a separate matter.
> Fresh-environment smoke test passed end-to-end: `dumen --version` →
> `dumen audit --refusal-baseline` → `dumen dossier`.

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
fields clearly labelled).

### 2. EU AI Office Annex XI dossier (one command)

```bash
dumen dossier --model my-gpai-model --output annex_xi.md
# → Annex XI technical documentation + Code of Practice matrix + SHA-256 evidence chain
```

### 3. Firewall proxy (in front of API models)

```bash
dumen serve --upstream https://api.openai.com --api-key $KEY --strict
# → OpenAI-compatible reverse proxy: injection filter + PII masking + dual-agent validator
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

> Raw-data licenses: JBB MIT (in the sample repo ✓); deepset/AgentHarm are
> research-licensed — **never committed**, loaders read the user's local file
> (see `examples/redteam_gateway_self.py`).

### 6. Test your own wall — gateway self-red-team

```python
from dumen.benchmarks import GatewaySelfRedTeam
m = GatewaySelfRedTeam.evaluate(samples)   # recall/FPR + raw escapes included
```

Two-layer measurement against a published corpus, on a holdout
(regex ∪ semantic judge): `examples/audits/gateway_selfredteam_qwen2.5-3b.json`.

## Architecture (5 layers)

```
Request → [1] Fast filter (injection/PII, measured ~0.03ms — see tests/test_latency_bench.py)
        → [2] SAE latent inspection (TopK/JumpReLU monosemantic features)
        → [3] StTP activation steering (tensor correction once the decision boundary is crossed)
        → [4] Dual-agent validator (Generator-Validator firewall)
        → [5] Autonomous red team (PAIR/TAP + Inspect AI + hybrid judge)
        → Evidence chain (SHA-256 hash-chain, tamper-evident)
        → Annex XI dossier + CoP matrix (AI Office submission-ready)
```

## Scientific basis

| Capability | Grounding |
|---|---|
| Single-direction refusal (DiM mining) | Arditi et al., NeurIPS 2024 (arXiv:2406.11717) |
| Rank-k manifold | Multi-directional refusal evidence: Rocchetti & Ferrara 2026, "Refusal Beyond a Single Direction" (arXiv:2606.13720); the k-dimensional SVD generalization is Dümen's own |
| SAE quality metrics (FEV, L0, sweep) | SAEBench, Karvonen et al., ICML 2025 |
| Steering-load measurement | capability-retention paradigms |
| Autonomous red teaming | PAIR (Chao et al., 2023; arXiv:2310.08419), TAP (Mehrotra et al., NeurIPS 2024; arXiv:2312.02119) |
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

## Quality evidence (v0.7.2)

- 349 unit tests, 100% green (CI: Python 3.10/3.12/3.14 matrix; real-model
  tests included on 3.12)
- Coverage %96.9+ (CI gate %95), ruff lint 0 errors
- **Zero fabricated numbers**: efficacy enters a report only via the
  `--measure-steering` behavioral comparison; every unmeasured metric renders
  as "Not measured / not claimed"
- **B1 capability-externality gate**: steering is now also measured on the
  capability-harm side — 12 deterministically-verifiable tasks,
  pass/fail/inconclusive; live publication for Qwen2.5-0.5B: efficacy %0 +
  capability **PASS** (%83.3→%83.3). If the gate fails, the protection claim
  is retracted from CLI **and** Annex XI.
- **Published audits** (comparison table: `examples/audits/README.md`):
  Qwen2.5-0.5B white-box + **three Ollama families** black-box — qwen2.5:3b
  (standard 58.8, sandbox %95 real finding · JBB-40 91.8), llama3.2:3b
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
- Judge-calibration comparison: FP/FN confusion matrix measured on a gold set;
  B3 human second-label pipeline: `examples/calibration_seed.py`
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