<!-- Doctrine applies to PRs as it does to reports: no evidence, no claim. -->

## What & why (one theme per PR)

- [ ] Single theme; commit prefix `feat|fix|docs|test|perf|security(scope):`
- [ ] User-visible behavior change → README/CHANGELOG lines updated in the same PR

## Evidence

- [ ] `python3 -m pytest tests/ -q --cov=dumen --cov-fail-under=95` green (paste the
      final line — test count + coverage %, measured not remembered)
- [ ] `ruff check dumen/ tests/ examples/ scripts/` clean
- [ ] New behavior tested through a real socket/CLI/file path — **no mocks**
- [ ] Claims of the "no evidence, no claim" kind: unmeasured metrics render as
      "Ölçülmedi"/None, never a placeholder number

## Published audits (if any new artifact)

- [ ] Reproduction command + environment noted inside `*_run.log`
- [ ] Raw licensed/harmful payloads stay OUT of the repo (cache-only policy)
