# Dümen — Rakip & Akademik Literatür Taraması (2026-09-16)

**Doğrulama yöntemi:** Tüm araç verileri canlı olarak PyPI JSON API, npm registry ve GitHub REST API'den 16 Eylül 2026 tarihinde çekildi. `web_search` çalışmıyor (HTTP 401); keşif arXiv API + GitHub topic/arama API ile yapıldı. **Hiçbir isim/sürüm/tarih uydurulmadı.**

---

## A) RAKİP ARAÇLAR

### A.1 Anahtar rakipler (hepsi canlı, açık kaynak, izinli lisanslı — 2026-09-16)

| Araç | Repo | Lisans | Canlı | Son sürüm | Beyaz-kutu (steering) | Annex XI/CoP |
|---|---|---|---|---|---|---|
| **garak** (NVIDIA) | [NVIDIA/garak](https://github.com/NVIDIA/garak) | Apache-2.0 | EVET (push 09-16, 9.3k★) | PyPI **0.17.0** (09-09) | **YOK** — prompt tabanlı probe | **HAYIR** |
| **PyRIT** (Microsoft) | [Azure/PyRIT](https://github.com/Azure/PyRIT) | MIT | EVET (push 09-16, 4.4k★) | PyPI **1.1.0** (09-04) | **YOK** | **HAYIR** |
| **promptfoo** | [promptfoo/promptfoo](https://github.com/promptfoo/promptfoo) | MIT | EVET (push 09-16, 25.2k★) | npm **0.123.0** (PyPI wrapper 0.1.4) | **YOK** | **HAYIR** — red-team *vulnerability* raporu |
| **inspect-ai** (UK AISI) | [UKGovernmentBEIS/inspect_ai](https://github.com/UKGovernmentBEIS/inspect_ai) | MIT | EVET (push 09-16, 2.8k★) | PyPI **v0.3.263** | **YOK** | **HAYIR** |
| **Giskard** | [Giskard-AI/giskard-oss](https://github.com/Giskard-AI/giskard-oss) (`giskard`'dan rename) | Apache-2.0 | EVET (push 09-16, 5.8k★) | PyPI **giskard 3.0.0** — v3 tam yeniden yazım, **v2 bakımsız** | **YOK** — v3 kara-kutu agent + LLM-judge | **HAYIR** — v3 README'de "AI Act"/"Annex"/"European" **sıfır** (grep doğrulandı) |
| **lm-evaluation-harness** | [EleutherAI/lm-evaluation-harness](https://github.com/EleutherAI/lm-evaluation-harness) | MIT | EVET (push 09-14, 14.0k★) | — | **YOK** | **HAYIR** |
| **HELM** | [stanford-crfm/helm](https://github.com/stanford-crfm/helm) | Apache-2.0 | EVET (push 09-01, 2.9k★) | — | **YOK** | **HAYIR** |

**Sonuç:** 7/7 rakip tamamen kara-kutu. **Hiçbiri activation steering / ağırlık-space analizi yapmıyor; hiçbiri Annex XI / GPAI CoP formatında teknik doküman üretmiyor.**

### A.2 2026 "EU AI Act compliance open source" çıkışları (GitHub `topic:eu-ai-act`, yıldıza göre)

Toplam 1.088 etiketli repo; ilk sıralar **çoğunlukla alakasız/aşırı etiketlenmiş**: Bindu (9.8k★ = agent kimlik/ödeme katmanı), Sandcastle (88★ = iş-akış orkestratörü), Claude-Skills-GRC (903★ = prompt/skill paketi), eullm (56★, AGPL-3.0 = AB-yerel LLM *üretim* platformu, "AI Act ready" ama audit değil).

| Araç | Repo | Lisans | Canlı | Beyaz-kutu | Annex XI/CoP |
|---|---|---|---|---|---|
| **iFixAi** (Nisan 2026) | [ifixai-ai/iFixAi](https://github.com/ifixai-ai/iFixAi) | Apache-2.0 | EVET (15.2k★, push 09-16) — 5 aylık repo için aşırı yüksek, şüpheli | **YOK** — README resmen *"treats it as a black box reached through a thin adapter"* | **HAYIR** — A–F scorecard + JSON/MD; `eu-ai-act` sadece topic |
| **aisbom** | [Lab700xOrg/aisbom](https://github.com/Lab700xOrg/aisbom) | Apache-2.0 | EVET (79★, push 09-15) | **YOK** — statik dosya taraması (pickle bomb, Keras Lambda RCE, GGUF template injection) | **KISMEN** — CycloneDX/SPDX AI-BOM ("EU AI Act, CRA, FDA §524B evidence"), tedarik-zinciri kanıtı, Annex XI teknik dokümanı değil |

iFixAi: 60 inspection, 5 sütun (Fabrication/Manipulation/Deception/Unpredictability/Opacity), iki-sağlayıcılı LLM-judge. Premium kategoride *"training disposition provenance"* vardır ama **davranışsaldır**, ağırlık-space provenance değildir. Geniş `eu ai act audit` araması (13.6k sonuç) adanmış AI Act denetim aracı göstermedi.

---

## B) AKADEMİK LİTERATÜR (arXiv API, 2025–2026)

**B.1 Activation steering / refusal direction**
1. **"How Fragile Is Safety Alignment at Frontier Scale? A Single-Direction Attack on a 320B MoE"** (2609.09793, 2026-09) — GLM-5.3-Flash 320B MoE'de etki ancak attention+dense+routed-expert yazarları **birlikte** düzenlenince ortaya çıkıyor (%74'ü joint intervention'da); geleneksel modül-adı tarifi **sessizce başarısız**. → **Zorlar.**
2. **"Decoy Direction Optimization"** (2609.16204) — Kontrastif estimatör'ü bozan decoy savunması, RFA ASR <%10. → **Tarafsız** (steering hem saldırı hem savunma merkezi).
3. **"Bait-and-Recover"** (2609.05794) — Gözlem yolunu zehirleyerek edit aramasını bozar. → **Tarafsız.**
4. **"A Unified Mechanistic Analysis of Knowledge-/Safety-Based Refusals"** (2609.00760, EMNLP 2026) — Ret *"commit-then-specify"*; paylaşılan yön + üst katman tip-özelleşme. → **Destekler.**
5. **"Refusal geometry reflects refusal training"** (2608.25390) — Çeşitli ret önekleri stable rank'i yükseltip ablation'ı zayıflatır. → **Zorlar.**
6. **"Detecting Safety Training Modification via Activation Analysis"** (2608.05578, IEEE Access 2026) — **AMS**: activation geometrisiyle abliterated/uncensored tespit; σ güvenlik-uyumunu öngörür (r=−0.546). → **GÜÇLÜ DESTEK** (en doğrudan akademik dayanak).

**B.2 SAE + steering kalitesi**
7. **"Key Path Identification" (KPI)** (2609.08173) — Nedensel anahtar-yol seçimi, mass steering yerine +%18. → **Destekler** (kalite > miktar).
8. **"Disentangling Steering Vectors"** (2609.07037) — Fark vektörlerinde SAE → ayrılabilir anlamsal basis. → **Destekler.**
9. **"Fixed-SAE Track"** (2609.15064) — SAE özellik steering'i RL kazançlarının ~%80'ini geri verir. → **Destekler.**
10. **"LLM Layers Immediately Correct Each Other" (TLCM)** (2609.07876, NeurIPS 2025) — *"effective steering requires extreme feature amplification."* → **Zorlar.**
11. **"Recurrence Is Not Enough"** (2609.04808, BlackboxNLP 2026) — 20+ tekrarlı özellikten nedensel olarak **1**'i geçerli. → **Zorlar** (nedensel doğrulama zorunlu).
12. **"SAEScientist-Bench"** (2609.09113) — Otonom ajanlar causal steering'de uzmanı geride. → **Destekler** (insan-denetçi konumu).

**B.3 EU AI Act + GPAI**
13. **"Bench-2-CoP: Can We Trust Benchmarking for EU AI Compliance?"** (2508.05464, 2025-08) — 194.955 soru: %61.6 halüsinasyon, %31.2 performans; **insan gözetiminden kaçma/kendi-kopyalama/otonom AI geliştirme = sıfır kapsama**. → **GÜÇLÜ DESTEK.**
14. **"Boiling the Frog"** (2605.22643, 2026-05) — **Annex I/III + GPAI CoP'ye grounded ilk çok-turlu benchmark**; toplam ASR %44.4, CoP loss-of-control %93.3. → **Destekler + tekdir** (CoP-hizalı benchmark kategorisi doldu).
15. **"Proportionality in AI risk evaluations"** (2603.10017, *Science* 391, 2026). → **Yönlendirici.**
16. **"Quality Assessment of Public Summary of Training Content, Art. 53(1)(d)"** (2603.13270) — 5 genel-özet değerlendirmesi. → **Destekler.**
17. **"When Do Data-Driven Systems Exhibit the Capability to Infer?"** (2606.11769, Fraunhofer) — Annex III kredi skorlama. → **Tarafsız.**

**B.4 Kontrastif/zehirli veri provenance**
18. **"Pretraining Data Can Be Poisoned through Computational Propaganda"** (2607.15267) — **HalfLife**: web-crawl verisine zehir dahil olma; kamu tartışma arayüzleri vektör. → **Destekler.**
19. **"!Imperio, smolVLA"** (2607.04146, KI2026) — 320 temiz bölümde **3 zehirli** = tam hizmet-dışı; *"dataset provenance as a first-class concern."* → **GÜÇLÜ DESTEK.**
20. **"Inference-Time Consensus"** (2607.23394) — Poisloned ince-ayarı consensus decoding; veri filtreleme yetersiz. → **Destekler.**

**B.5 Red-teaming otomasyonu (PAIR/HRL)**
21. **"PsychJail"** (2608.23028) — Çok-turlu ikna, %87.3 ASR. → **Tehdit** (kara-kutu otomasyon güçlendi).
22. **"PIMiner"** (2608.05108) — RL saldırganı genelleşemiyor → agentic strateji kütüphanesi (Gemini-2.5-Pro %76.2 ASR, eğitim dışı transfer). → **Zorlayıcı.**
23. **"GFlowRL"** (2607.13394, Microsoft) — AdvBench/HarmBench'te en yüksek ASR@1, 235B MoE. → **Zorlayıcı.**
24. **"RL-ADA"** (2609.02902) — DA/CA eş-evrimli arena, *"Contextual Camouflage."* → **Zorlayıcı.**

---

## C) BOŞLUK ANALİZİ — hala doğrulanmış bir boşluk, ama daraldı

- **(A) İç-veri-aktarımlı ince-ayarı denetleme:** **Boşluk açık.** Garak/PyRIT/promptfoo/inspect-ai/HELM/lm-eval prompt-veya-çıktı tabanlı; Giskard v3 ve iFixAi **açıkça kara-kutu**. Akademide B.4 tehdidi kantifiyor ama OSS aracı yok.
- **(B) Ağırlık-space provenance:** **En net, en dokunulmamış boşluk.** 7/7 ana rakip + iFixAi + aisbom: hiçbiri ağırlık/activation-space provenance üretmez. AMS (2608.05578) yöntemin *yayınlanmış akademik temeli olduğunu* kanıtlıyor → Dümen bilimsel olarak temelli, **ürün olarak tektir**.
- **(C) Mech-interp tabanlı uyum eşleştirme:** **Boşluk açık**; Bench-2-CoP + Boiling the Frog regülatör tezle uyumu kanıtlıyor. **İki uyarı:** (i) **iFixAi** Nisan 2026'da *davranışsal* denetimi doldurdu → "red-team + audit" argümanı zayıfladı; farklılaştırma tamamen **beyaz-kutu + ağırlık-space provenance + Annex XI/CoP** üzerine kalmalı. (ii) Literatür beyaz-kutu iddialarına **sınır** çiziyor (MoE joint-intervention, TLCM amplifikasyon, tekrar ≠ nedesel) → Dümen bu bulgularla uyumlu (multi-writer tespiti, zorunlu nedensel doğrulama) iddia koymalı.

**Özet:** Apache-2.0 + beyaz-kutu steering + red-team + SHA-256 zinciri + Annex XI/CoP kombinasyonu **2026-09-16 itibarıyla doğrulanmış bir boşluk**. En yakın komşular iFixAi (kara-kutu davranışsal denetim) ve aisbom (statik AI-BOM). Gerçek tek-start avantajı **(B) ağırlık-space provenance**'dir.

---

## Kürateli Açık-Kaynak EU AI Act Denetim/Compliance Araç Listesi

| Araç | Repo | Lisans | Son sürüm (2026-09-16) | Not |
|---|---|---|---|---|
| Giskard | [Giskard-AI/giskard-oss](https://github.com/Giskard-AI/giskard-oss) | Apache-2.0 | PyPI `giskard` **3.0.0** | v2 bakımsız; v3 = agent red-team + eval |
| iFixAi | [ifixai-ai/iFixAi](https://github.com/ifixai-ai/iFixAi) | Apache-2.0 | oluşturuldu 2026-04-27 | 60 inspection, A–F, kara-kutu |
| garak | [NVIDIA/garak](https://github.com/NVIDIA/garak) | Apache-2.0 | PyPI **0.17.0** | LLM vulnerability tarayıcı |
| PyRIT | [Azure/PyRIT](https://github.com/Azure/PyRIT) | MIT | PyPI **1.1.0** | Python risk izleme |
| inspect-ai | [UKGovernmentBEIS/inspect_ai](https://github.com/UKGovernmentBEIS/inspect_ai) | MIT | PyPI **v0.3.263** | UK AISI eval çerçevesi |
| promptfoo | [promptfoo/promptfoo](https://github.com/promptfoo/promptfoo) | MIT | npm **0.123.0** | red-team/pentest + CI |
| aisbom | [Lab700xOrg/aisbom](https://github.com/Lab700xOrg/aisbom) | Apache-2.0 | — | AI-BOM (CycloneDX/SPDX) kanıtı |
| Claude-Skills GRC | [Sushegaad/...Compliance](https://github.com/Sushegaad/Claude-Skills-Governance-Risk-and-Compliance) | MIT | — | GRC *prompt* paketi, motor değil |

*Doğrulanamayanlar:* HELM ve lm-evaluation-harness için sürüm tarihi; "annex xi" / "gpai code of practice tool" GitHub aramaları özel bir araç döndürmedi.
