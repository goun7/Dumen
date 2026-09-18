# Security Policy

## Supported versions

| Version | Support |
|---------|---------|
| 0.7.x   | ✅ Active |
| < 0.7   | ❌ Community contributions (best-effort) |

## Reporting — local evidence first

Dümen is a **security-audit tool**; vulnerabilities in the tool itself are
taken seriously. If you find one:

1. **Report with evidence:** reproduction command, version, environment
   (Python/OS), and the `examples/audits/` output if relevant. Not "it doesn't
   work" but "this command produces this error" — the project's own doctrine:
   **no evidence, no claim**.
2. **Scoped disclosure:** *product*-security issues — gateway bypass
   (FastSecurityFilter), PII-masking leaks, evidence-chain (EvidenceChain)
   tampering, signed-report spoofing — go through private disclosure first.
   Generic model-weakness findings (jailbreak prompts) do not; they belong to
   the model, not this tracker.
3. **Channel:** GitHub → Security → **"Report a vulnerability"** (private
   reporting enabled). The e-mail channel (`dev@dumen.ai`) is a fallback only
   if the domain is confirmed; if no response arrives within 14 days, you may
   disclose publicly as a plain issue (max embargo: 14 days).

## Out of scope (known limits — see README "Quality evidence" & "Regulatory scope")

- The regex-based gateway layer missing creative/multilingual indirect
  injections is a **design-boundary statement**, not a vulnerability: our
  holdout recall is published (`examples/audits/gateway_selfredteam_*.json`)
  and is the rationale for defense-in-depth architecture.
- Pre-steering white-box activation access: any attacker with hook capability
  can thin the refusal direction — the limit acknowledged by every published
  steering-awareness attack in the field.
- Users with local filesystem access can regenerate the evidence chain; the
  chain provides **tension-resistance, not identity authentication**.
  Signing *is* implemented (`dumen sign` / `dumen verify`, Ed25519 over the
  sealed chain file), so authorship can be proven — but the chain itself
  cannot bind a private key to a legal person; that requires a
  notified-body-issued credential, which is out of scope.
