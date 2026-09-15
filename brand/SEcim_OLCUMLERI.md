# Aday Ölçümleri (15 Eyl — programatik, kanıtlı)

| hücre | sert-IoU (potrace turu) | 16px korunum (korel.) | halo (AA-gri) oranı | gradient-iz (ton-std) | verdigris | OCR-wordmark |
|---|---|---|---|---|---|---|
| A | 0.195 | 0.232 | 0.035 | 27 | %0 | okunamadı |
| B | **0.565** | 0.533 | **0.012** | 26 | %0 | okunamadı |
| C | 0.305 | 0.332 | 0.035 | 33 | %0 | kısmi |
| D | 0.165 | **0.899** | 0.045 | 31 | **%23.9** | okunamadı |
| E | 0.163 | 0.328 | 0.018 | 23 | %0 | "DUME" kısmi |

Notlar:
- IoU bu atölye-levhasında (215px işaret) YALNIZCA relatif sıralamadır; seçilen
  hücrenin yüksek-çözünürlük yeniden-üretimi sonrası asıl kapı IoU≥0.99'dur.
- D favicon-boyutunda yapıyı ezici biçimde koruyor (0.899) + tek verdigris
  kullanan aday — ama vektöre en zor çevrilen (%23.9 ikili-ton + ince detay?).
- B izlenebilirlik+flatness şampiyonu; 16px'te orta.
- Hiçbirinde gradient-ihlali işareti (yüksek ton-std) YOK — prompt kuralı tutmuş.
