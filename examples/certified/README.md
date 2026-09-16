# Certified audits — referans denetimler

> Her sertifika: `dumen audit` → `dumen sign` → `dumen verify` (exit 0)
> ile üretilir, Ed25519 imzası kanıt-zinciri HEAD'ine mühürlenir.
> **Kopyala-yapıştır yapılabilir** — aynı modelde aynı komutla tekrar üretilebilir.

## Sertifikalar

| Model | Kanal | Güvenlik skoru | Değerlendirme | Tarih |
|---|---|---|---|---|
| Qwen/Qwen2.5-0.5B-Instruct | beyaz-kutu (CPU) | **97.5** | 4 | 2026-09-16 |
| Qwen/Qwen2.5-1.5B-Instruct | beyaz-kutu (CPU) | **97.5** | 4 | 2026-09-16 |
| qwen2.5:3b (Ollama) | siyah-kutu API | **58.8** | 4 | 2026-09-16 |

**Not:** 3B'nin düşük skoru dürüst bir sonuçtur — siyah-kutu API kanalında
aktivasyon erişimi yoktur; bu zayıflık **gizlenmedi**. İkisi arasındaki
46.5 puanlık fark, denetim kanalının (beyaz-kutu vs siyah-kutu) sonucu
nasıl değiştirdiğini gösterir — bu tam olarak Dümen'in ölçtüğü şeydir.

## Doğrulama (senden)

```bash
# 1) imzayı doğrula (imza + head eşleşmesi + zincir bütünlüğü)
dumen verify --chain qwen2.5-0.5b_cert1.json \
  --sig qwen2.5-0.5b_cert1.json.sig --pub <auditör-pub>

# 2) kurcalama testi: herhangi bir kök-alanı değiştir → REDDEDİLİR
#    (örn. overall_safety_score=99.9 → 'kanıtdemeti çelişkisi')
```

## Doktrin notu

Skorlar yalnızca **koşturulan örneklerden** türetilir — elle girilmez.
Ölçülmemiş alanlar `not_measured` / `None` olarak görünür
(bu dosyalarda `steering_efficacy=None`: beyaz-kutu steering kanalında
etkinlik ölçülmedi, iddia edilmedi). Bu bir **araç çıktısıdır**;
uyumluluk kararı denetçiye aittir (bkz. README "What it does not do").
