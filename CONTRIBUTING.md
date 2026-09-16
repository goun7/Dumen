# Contributing guide

Evidence is mandatory for contributions to Dümen — code is not. The project
doctrine is: ***no evidence, no claim.*** This applies to contributions too.

## Development environment

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"            # test + lint tooling
pip install -e ".[model]"          # (opt.) transformers, for real-model integration tests
python -m pytest tests/ -q         # run the suite
ruff check dumen/ tests/ examples/ scripts/
python scripts/surface_parity.py   # README EN↔TR numeric-token parity gate
```

Python 3.10–3.14 is supported; CI runs three versions (real-model tests
included on 3.12; CI also runs the lint scope above, the parity gate, and fails under coverage %95).

## Rules

1. **No fake numbers.** An unmeasured metric stays `None`/"Not measured" in
   the report; a hard-coded success number never reaches production
   (see `steering_efficacy`).
2. **No behavior without a test.** Every new production branch is exercised
   through a real socket/CLI/file path — real mechanisms over mock servers
   (e.g. stdlib threading HTTP server, see `test_api_runner.py`).
3. **Citations verified.** arXiv ID + title + year must be confirmed against
   the primary source; a citation correction is called out separately in the PR.
4. **External data licenses.** Raw licensed/harmful corpora (deepset CC-BY-NC,
   AgentHarm "other") **never enter the repo**; only MIT/Apache distributions
   get committed (JBB MIT ✓). Loaders pin the schema; the data stays with the
   user.
5. **Scope honesty.** White-box (activation) and black-box (API) channels are
   never conflated; efficacy measurement is only possible white-box.

## PR process

- One theme, one commit (prefixes `feat|fix|docs|test|perf|security(scope)`).
- Gates: full suite green + coverage ≥ %95 + `ruff` clean + surface parity (numbers never drift between README languages).
- New CLI flag: user-facing text may mix Turkish and English; error messages
  must be **reproducible** (say what you tried).

## Report quality

Published audits under `examples/audits/` are **transparent evidence**: every
shipped artifact carries its reproduction command inside `_run.log`. If you
publish a new audit, add the command and the environment too.
