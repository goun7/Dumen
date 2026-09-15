# Changelog

Format: Keep a Changelog · This project uses SemVer. The *evidence* for each
release lives in `examples/audits/` as reproducible artifacts.

## [Unreleased]

## [0.7.2] - 2026-09-15

Fresh-environment verification and the first sales-grade sample, pre-publication.

- **Packaging fix (fresh-venv smoke-test finding):** `numpy` is now declared as
  a direct (not transitive) dependency — the torch "Failed to initialize NumPy"
  first-run warning on new installs is gone (measured: fresh env 5.4GB,
  refusal-baseline audit **5.1s**, CLI trio smoke clean). Honest
  "install weight" note added to the README.
- **Sales sample (`examples/pilot_dossier.py` + `examples/pilot/`):** a full
  Annex XI dossier + CoP matrix (62% — the two missing rows are deliberate:
  customer declaration + incident pipeline) + SHA-256 evidence chain sealing
  the source scorecard's hash, generated from a REAL PUBLISHED scorecard
  (qwen2.5:3b JBB-40, safety 91.8). The compute field is LABELLED as a
  6·N·D order-of-magnitude estimate (3.34e23 < 1e25 → below the Art. 3(63)
  threshold; D=18T verified live from arXiv:2412.15115); every unverifiable
  field stays a bracketed [pending declaration].
- No API/schema changes — the sole SemVer reason is the packaging finding.

## [0.7.1] - 2026-09-15 — B1 capability-externality gate + B5 multi-family publications

### Added
- **B1 `CapabilityGate`**: steering damage to model CAPABILITY is now measured —
  12 deterministically-verifiable tasks (no LLM judge, no circular evidence;
  echo-safety test-enforced). pass/fail/inconclusive; **a fail retracts the
  protection claim from CLI and Annex XI** (an intervention that harms is not
  an intervention). First live pair: Qwen2.5-0.5B efficacy %0 + capability
  PASS (%83.3→%83.3).
- `--request-timeout` (audit; default 300s) — field finding: on single-VRAM
  machines, cold model load + slow generation blew the 180s budget
  (phi3:mini/GTX-1070, ~1s/token). Timeouts still raise a clean
  `EndpointError`; no fake refusals are produced.
- **B5 multi-family publications** (`examples/audits/` + comparison table):
  llama3.2:3b (std 77.5 · JBB-40 **91.3**) and phi3:mini (std 95.0 · JBB-10
  97.0 — n difference flagged in the table) — with qwen2.5:3b JBB-40 91.8,
  same-depth inter-family consistency was MEASURED; llama std surfaced a
  cyber %60 REAL weakness finding.
- **B3 process tool**: `examples/calibration_seed.py` — generates a human
  second-label B3 worksheet from real (prompt, response) pairs; first live
  output: llama3.2:3b × 20 pairs (3 refusal / 17 mixed — the hard zone for
  the fastpath). Raw pairs stay out of the repo (dual-use policy); only the
  distribution is published.
### Unchanged
- Black-box/refusal-baseline channels, API surface, report schema (only the
  `capability_regression` field was added — old artifacts stay schema-safe).

## [0.7.0] - 2026-09-15 — API-endpoint auditing + real-catalog red-teaming

### Added
- **Black-box API audit channel** (`dumen audit --endpoint`): audit any
  Ollama / vLLM / LM Studio / OpenAI-compatible server; deterministic
  temperature=0; HTTP errors never become FAKE REFUSALS (EndpointError raises).
- **First local-real-model audit published**: Ollama qwen2.5:3b — standard-suite
  scorecard (`safety 58.8`, sandbox %95) + 40-task JBB wide audit (`safety
  91.8`, %0 jailbreak) — `examples/audits/qwen2.5-3b_ollama_*.json`.
- **Gateway self-red-team comparison** (`GatewaySelfRedTeam`): two-layer
  (regex ∪ semantic LLM-judge) recall/FPR matrices on the published
  deepset/prompt-injections corpus; regex patterns hardened with EN+DE
  families (holdout FPR %0, precision %100); `JudgeEvaluator.classify_injection`.
- **External attack-catalog bridges**: HarmBenchLoader (400 real behaviors) +
  AgentHarmLoader (176 agentic tasks) + `--dataset` CLI with automatic schema
  detection (JBB CSV · HarmBench CSV · AgentHarm JSON · AILuminate JSON/JSONL).
### Fixed
- JBB/AILuminate `CATEGORY_MAP` calibrated to real distribution labels
  (Malware/Hacking→cyber_attack, Disinformation→hallucination, Privacy→pii_leak).

## [0.6.1] - 2026-09-15 — evidence-integrity release

### Fixed (deep-audit findings)
- Fabricated success numbers purged: "%96.2 Active Protection" → three-state
  measured efficacy (Not measured ⚪ / %0 🟠 / +%X 🟢) via behavioral
  `SteeringEfficacyBench` (before/after judge comparison; cosmetic cosine
  rejected).
- `--measure-steering` became a real measurement pipeline (mining + live hook +
  steered generation).
- vLLM/sub-1ms/Anthropic-native/JBB-live claims → verified text only; SLA claim
  replaced by a MEASURED latency bench (`test_latency_bench.py`).
- 3 wrong academic citations corrected (PAIR/TAP; RepE↔StMP; 2606.13720 title);
  unverifiable quotes softened; EU timeline updated with EC-sourced dates.
- dossier/serve channels: refusal-baseline stamp + `evidence_channel` + chain
  head rendered inside Annex XI; context note for Art.14 ❌.
### Infrastructure
- CI coverage gate made actually effective (pytest-cov was missing); 3.12 job
  runs real-model tests; unused dependencies deleted; AILuminate format bridge;
  threat-model & limitations section (§6.5).

## [0.6.0] - 2026-09-14 — Evidence-gap closure
- rank-k subspace mining + bootstrap confidence + permutation p; joint-nullspace
  steering; InspectBridge red-team; evidence-chain reports.

## [0.5.0] - 2026-09-13 — mechanistic-core verification
- OV-circuit mask, output-filter critical bug fix, unified StTP/StMP pipeline.

## [0.4.0] and earlier — prototype
- basic mining/hook/report pipeline; test count between 52–173.
