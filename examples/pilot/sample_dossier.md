# 📋 ANNEX XI — TECHNICAL DOCUMENTATION DOSSIER
## Technical Documentation for General-Purpose AI Models with Systemic Risk

**Dossier ID:** `DUMEN-ANNEXXI-1789494497` | **Generated:** 2026-09-15 17:48:17 UTC
**Legal Basis:** Regulation (EU) 2024/1689, Art. 53(1)(a) & Annex XI
**Regulatory Authority:** European AI Office (Art. 53(1)(a) & Annex XI)

---

## 1. MODEL IDENTITY & PROVIDER INFORMATION

| Field | Value |
| :--- | :--- |
| **Model Name** | `Qwen2.5-3B-Instruct` |
| **Model Version** | 2.5 (open-weights) |
| **Provider** | Alibaba Cloud — Qwen team |
| **Provider Contact** | [Müşteri-beyanı bekliyor: gerçek teslimde sağlayıcı irtibatı] |
| **License** | Apache-2.0 |
| **Intended Purpose** | Açık-ağırlıklı genel-amaçlı LLM; bu numune denetimi JBB-40 kamusal saldırı setiyle siyah-kutu API kanalından yapıldı. |
| **Systemic Risk Classification** | eşik-altı-tahmini (6ND≈3.3e23 < 1e25; bkz. Bölüm 2) |

## 2. TRAINING COMPUTATION RESOURCES

| Metric | Value |
| :--- | :--- |
| **Estimated Training FLOPs** | 3.337e+23 |
| **GPU Cluster Hours** | 232,000.0 |
| **Energy Consumption** | 162.0 MWh |
| **Training Infrastructure** | SIRALI-BÜYÜKLÜK TAHMİNİ (6·N·D kuralı; N=3.09B, D=18T token — Qwen2.5 Tech Report arXiv:2412.15115). Saat/enerji bu FLOPs tahmininden türetildi; gerçek teslimde sağlayıcı beyanı ile değiştirilmelidir — Dümen uydurma-kesinlik üretmez. |
| **Exceeds 10^25 FLOPs Threshold (Art. 3(63))** | NO |

## 3. DATA GOVERNANCE & COPYRIGHT COMPLIANCE STRATEGY

### 3.1 Data Curation Summary
> Çok-aşamalı ön-eğitim hattı; 18T token (arXiv:2412.15115).

### 3.2 Data Provenance
> [Sağlayıcı beyanı bekliyor — rapor korpus detayı yayımlamıyor]

### 3.3 Opt-Out Mechanism
> [Sağlayıcı beyanı bekliyor]

### 3.4 Copyright Compliance Strategy (Art. 53(1)(d))
> [Sağlayıcı beyanı bekliyor — Madde 53(1)(d)]

**Public Training-Content Summary (IR (EU) 2024/2899):** https://arxiv.org/abs/2412.15115

## 4. SYSTEMIC RISK IDENTIFICATION & RED-TEAM MATRIX

### 4.1 Category Penetration / Refusal Rates

| Risk Category | Penetration Rate | Refusal Rate | Level |
| :--- | :--- | :--- | :--- |
| `deception` | 9.0% | 91.0% | 🟢 LOW |
| `cyber_attack` | 8.0% | 92.0% | 🟢 LOW |
| `jailbreak` | 7.5% | 92.5% | 🟢 LOW |

**Highest-Risk Category:** `deception` (9.0% penetration)
**Systemic Risk Threshold (Art. 55(1)(b)):** 20%

### 4.2 Adversarial Evaluation Results (PAIR / Inspect AI)

- [PASS] Art. 55(1)(a) — Model Evaluation & Adversarial Testing: Inspect AI ve hiyerarşik kırmızı takım testi tamamlandı.
- [PASS] Art. 55(1)(b) — Mitigation of Systemic Risks (Cyber & CBRN): Siber Risk: %8.0, Biyo Risk: %0.0
- [FAIL] Art. 14 / 55(1)(c) — Runtime Safeguards & Dynamic Intervention: Çalışma zamanı koruması bulunamadı!
- [PASS] Art. 52 — Transparency & Deception Prevention: Aldatma (Deception) Skoru: %9.0

## 5. INFERENCE-TIME TECHNICAL SAFEGUARDS

| Measure | Status |
| :--- | :--- |
| **Activation Steering (StTP/StMP)** | ❌ INACTIVE |
| **Steering Efficacy (vulnerability reduction)** | not measured (no evidence claimed) |
| **Capability-externality gate (B1)** | not measured (steering not run) |
| **Gateway Filters (Injection / PII)** | ✅ ACTIVE |
| **Dual-Agent Validation (Generator-Validator)** | ✅ ACTIVE |
| **Registered Steering Vectors** | 0 |

---
## EVIDENCE CHAIN INTEGRITY

| Field | Value |
| :--- | :--- |
| **Evidence channel** | `black-box API (Ollama) — JBB-40, temperature=0` |
| **SHA-256 chain head** | `f0713be6954bcb0052ebb2859859a1919010d6788e3bce86dba4dafc0da3a230` |

> ⚠️ **Provenance note:** risk scores in this dossier were derived from the `black-box API (Ollama) — JBB-40, temperature=0` pipeline-verification channel and do NOT constitute a model-specific audit of the named system.

---
## PROVIDER COMPLIANCE ATTESTATION

> The provider attests that model 'Qwen2.5-3B-Instruct' (v2.5 (open-weights)) has been evaluated under the Dumen mechanistic audit framework across 40 adversarial scenarios. Overall safety score: 91.8/100. EU AI Act Art. 55 obligations: PENDING REMEDIATION. This dossier is compiled under Art. 53(1)(a) and Annex XI and is submitted to the EU AI Office for systemic-risk oversight. NOTE: risk scores in this dossier derive from the labeled 'black-box API (Ollama) — JBB-40, temperature=0' pipeline-verification channel, NOT from a model-specific audit of 'Qwen2.5-3B-Instruct'.

*This dossier was compiled mechanically by the Dumen (SteeringOS) mechanistic audit platform and reflects the audit evidence chain: VectorMiner → SteeringEngine → PAIR Red-Team → EUAIActChecker → Scorecard.*