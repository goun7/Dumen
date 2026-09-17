# Changelog

Format: Keep a Changelog · This project uses SemVer. The *evidence* for each
release lives in `examples/audits/` as reproducible artifacts.

## [Unreleased]

## [0.7.6] - 2026-09-17

### Added

- **RFC 8785 (JCS) canonicalization** — `dumen.reports.rfc8785`. The evidence
  chain previously serialized with `json.dumps(sort_keys=True)`, which is
  NOT JSON Canonicalization Scheme: three ECMAScript deviations were
  reproduced (`1.0`→`1.0` vs `1`, `-0.0`→`-0.0` vs `0`, `2.93e-07` vs
  `2.93e-7`). The new module implements ECMAScript `Number.prototype.toString`
  and UTF-16 code-unit key ordering (language-independent canonicalization).
  Verified byte-identical against a Node.js oracle on 21 vectors
  (Node = ECMAScript-native ground truth). Python self-tests alone cannot
  catch this class of bug — escape-table expectations written with the same
  buggy rules pass while being wrong.
- **Versioned canonicalization scheme** — `EvidenceChain(canon_scheme=...)`
  and the `canon_scheme` bundle field. The three published example
  certificates carry float `risk_scores` (`0.0`), so recomputing them under
  RFC 8785 would change their chain heads (e.g. `c56901ca...` →
  `12a91458...`), which reads as evidence tampering. Old bundles stay
  `jcs_python` and their hashes are preserved byte-for-byte; new chains
  default to the legacy scheme until the field is explicitly set.
- **MoE joint-intervention diagnostic** — `dumen.core.moe_joint` +
  `dumen moe-joint-test`. On a 320B mixture-of-experts model,
  single-component steering fails *silently*: attention, dense FFN and
  expert subspaces must be steered jointly, and joint intervention recovers
  ~4× what single-component edits do (arXiv:2609.09793). The module computes
  per-component rank-k bases, measures cross-component subspace overlap, and
  flags the silent-failure regime when a single component is applied under
  low overlap. Geometry validated on synthetic vectors; live-320B
  validation is open work and stated in the module docstring.
- **TLCM amplification detector** — `dumen.core.amplification` +
  `dumen amplification-scan`. The target-layer contrastive method is not
  monotone in α; in the extreme regime it *amplifies* the behavior it means
  to reduce (arXiv:2609.07876). The detector sweeps α and flags the first α
  where |cos_after| exceeds |cos_before|, returning a safe-α boundary.
  Detection, not prevention; loop-closing (choosing α from the measured
  curve inside an audit run) is open.
- **Veridict ledger bridge** — `dumen.reports.veridict_bridge` +
  `dumen veridict-export`. Exports a Dümen evidence chain into an
  append-only hash-chained Veridict ledger. Fail-closed: a broken chain
  raises and no ledger is produced. The bridge writes ledgers only — it
  does not issue certificates; a `veridict audit --ledger` pass does.

### Changed

- `EvidenceChain.from_json` now reads the `canon_scheme` field
  (backwards-compatible: missing → `jcs_python`).
- PAPER.md §7 Limitations expanded with four verified literature gaps
  (arXiv:2609.09793, 2609.07876, 2609.04808, 2609.09113); the MoE and TLCM
  entries now reflect the shipped diagnostics.
- README/README_TR: added a measured "Why Dümen" section (capability table
  with the reproducible numbers) and documented the two new commands.
  Removed residual name-dropping and an overclaiming epigraph.

## [0.7.5] - 2026-09-16

Honesty sweep: every claim that had no machine behind it, either got the
machine or lost the claim. No new measurement was fabricated to fill a gap.

- **`dumen audit --output x.json` is now SEALABLE** (evidence bundle): the
  report and its chain ship in one file; root fields must match the sealed
  report-record or the bundle is rejected as tampered. The README's
  `audit → sign → verify → export` path now works as documented (it didn't).
  Tested round-trip + report-only tamper (caught, exit 1).
- **Gateway honesty package**:
  - `serve --validator-url/--validator-model/--validator-key` — the dual-agent
    validator was advertised but had NO configuration path; it now runs when
    configured, and `/health` + `dumen_meta` disclose the ACTUAL deciding
    layer (`fast_filter` vs `fast_filter + dual_agent_validator`).
  - validator failure is no longer silent: a crashed/timed-out second agent
    stamps `fast_filter_validator_unavailable` + a reason line (was: looked
    fully validated while only regex ran).
  - SSE streaming now MASKS PII before delivery (delayed 96-char window; the
    old path counted PII and shipped it raw), CUTS the stream on critical
    output patterns, and refuses to forward unparseable chunks (fail-closed).
- **CoP matrix stops claiming what didn't run**: `dumen dossier` no longer
  prints "hierarchical red-team test completed" (that engine is library-only);
  the red-team row now names the single-shot battery that actually ran.
  `--incident-log` gates the Art. 55(1)(c) row: no validated incident records,
  no "demonstrated" (was a hardcoded True).
- **No more fake-perfect metrics**: `SteeringVector.confidence` is
  `Optional[float]` — bootstrap stability is `None` when not measured, never
  1.0 (the old `n<2 → 1.0` invented perfect stability from one sample).
- **`dumen steer-test` asserts for real**: |cos| must decrease and the OV mask
  must thin; non-zero exit on regression (was unconditional "SUCCESS"). Bad
  `--dim` now gives a UsageError, not a raw traceback.
- **Every evaluation row carries `evaluated_by`** (regex-fastpath / heuristic /
  llm-judge) — the scorecard's judge provenance is now inspectable.
- **Paper correctness** (pre-submission): JailbreakBench ID fixed
  (2404.04561 → 2404.01318 — the old ID resolved to a 3D-vision paper);
  arXiv:2606.05958 re-characterized (it is an attack-surface paper with
  training-time mitigations, NOT a loss-surface detector — we had credited it
  with a detector it does not ship); the "intensity-monotone" drift adjective
  corrected (the 8-swap point DIPS: 0.482→0.480); abstract's "detects
  token-swap poisoning" replaced with the measured double-negative boundary.
  9 new verified citations (SteerCheck, side-effect forecasting, ObserverBench,
  decoy-direction, evaluator fragility ×2, aliases/HARC/DeepRefusal).
- **README architecture rewritten as two real pipelines + one library
  surface**: SAE inspection, multi-turn HRL and judge-calibration harness are
  now labelled Python-API (no CLI runs them) instead of being drawn inside the
  gateway request path where they never existed.
- 419 tests (was 402), coverage ≥95% gate held.
- **Gateway UX**: `serve` help now shows the dual-layer invocation; bad
  `--dim` on `steer-test` yields a UsageError; `export` HTML carries the
  0.7.5 stamp by default.


**Known unchanged (deliberate):** published provenance artifacts stay
schema-legacy (`swEEP_note` key, no pair-cosines in the p2/p8/p16 files) —
immutability beats cosmetics; the quirks are now documented in
`examples/audits/README.md`.

## [0.7.4] - 2026-09-16

Evidence lifecycle + external validity + multilingual slice.

- **Ed25519 chain sealing** (`dumen keys|sign|verify`): signs the chain head
  after full integrity verification; honest identity boundary (key custody,
  explicitly *not* an eIDAS-qualified signature); silent key rotation banned
  (FileExistsError without --overwrite); wrong-key-type and corrupt-
  signature paths tested.
- **Auditor HTML export** (`dumen export`): single-file printable report with
  inline brand mark, seal footer (chain state + head + signer fingerprint),
  XSS-escaped model text, print CSS.
- **`dumen watch`**: continuous re-audit rounds recorded into their own
  verifiable chain (fail-loud halt after 3 consecutive failures); injectable
  scheduler keeps it deterministic in CI.
- **B1 external-task extension**: 10 original GSM-style multi-step word
  problems (`--capability-extended`); published 12-task scorecards stay
  comparable (default unchanged, task_set stamped).
- **Turkish capability slice (first multilingual B1 evidence)**: 10 original
  TR tasks + standalone `dumen capability` command (black-box API or local).
  Found & fixed a live landmine: the yes/no verifier only spoke English —
  correct TR answers would have scored as capability *failures*.
- **Steering-data provenance auditor** (`dumen provenance`, `--sweep`):
  robust-median direction + MAD-calibrated outlier flags against contrastive
  token-swap poisoning (surface credited to arXiv:2606.05958; detector is
  Dumen's at tool level). LIVE outcome, published as a method-level NEGATIVE:
  per-pair attribution recalled 0/10 poisoned pairs at 2/8/16 swaps — its one
  high-intensity flag was a false positive. The pool-level answer
  (`drift_verdict`, seed-fixed bootstrap-null, n=1000, alpha=0.05) was then
  measured on live and is ALSO negative: the median drift (positive at every
  tested intensity, delta up to +0.077 — note: NOT strictly monotone, the
  8-swap point dips; corrected post-audit 16-Sep) sits inside the wide
  resampling null of an n=20 pool
  (MAD 0.22). Published conclusion, bounded: token-swap poisoning is invisible
  to post-hoc pool geometry at tested intensities/sizes — the null test earned
  its place by vetoing a plausible-looking drift. `--sweep` uses a fixed 2/8/16
  grid after an open-ended scan overran 70 min and was killed.
- **Integrity hardening**: schema-corrupt chains now hit the same
  "evidence not accepted" gate as hash-tampered ones (single message).
- **Honest surfaces**: `dumen dossier --provider/--contact` — unset identity
  fields print as `[FIELD NOT SET]` instead of a silent fake lab name.
- **PAPER.md**: technical report skeleton with machine-rendered results
  (numbers generated from committed artifacts only; absent = "Not measured").
- **Hardware lesson documented**: GPU acceleration is opt-in
  (`DUMEN_DEVICE`) because `torch.cuda.is_available()` lying (sm_61 Pascal +
  cu130 wheels) produced a *crash*, not a fallback — CPU remains the
  verified default for all published artifacts.
- 406 unit tests / coverage gate 95% / real-model CI job on Python 3.12.


## [0.7.3] - 2026-09-15

Brand identity + public surface + release hygiene.

- **Brand mark (helm-"D")**: hi-res generated mark → potrace single-path SVG
  (IoU 0.994 ≥ 0.99 gate); og.png/avatar/favicon family generated by
  `scripts/make_brand_assets.py`; mark embedded in both README surfaces.
- **Surface language alignment**: English-primary README + full Turkish sibling
  with a numeric-parity CI gate (`scripts/surface_parity.py`); CONTRIBUTING/
  SECURITY/CHANGELOG migrated to English (zero numeric drift, multiset-diff).
- **Community kit**: issue/PR templates, CODE_OF_CONDUCT, CITATION.cff.
- **Release hygiene gates**: sdist whitelist + `scripts/dist_hygiene.py`
  (8 internal docs were entering the tarball — caught pre-upload); public-clone
  masker v4 revived and proof-fired (liveness 146→0 / path-sweep 9→0); full
  sdist rehearsal: fresh venv install → CLI trio → 24 bundled tests green.
- No functional API changes; CLI flags, report schema untouched.

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
