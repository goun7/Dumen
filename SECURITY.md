# Security Policy

## Destlenen Sürümler

| Sürüm | Destek |
|-------|--------|
| 0.7.x | ✅ Aktif |
| < 0.7 | ❌ Topluluk katkılarıyla (best-effort) |

## Raporlama — Önce Yerel Kanıtlar

Dümen bir **güvenlik denetim aracıdır**; bizzat aracın güvenlik açıkları
ciddiye alınır. Bir açık bulduğunuzda:

1. **Kanıtlı raporlayın:** yeniden-üretim komutu, sürüm, ortam (Python/OS),
   varsa `examples/audits/` çıktısı. "Çalışmıyor" yerine "şu komut şu hatayı
   veriyor" — projenin kendi doktrini: **kanıt yoksa iddia yok**.
2. **Etikli açıklama:** gateway bypass (FastSecurityFilter), PII maskeleme
   sızıntısı, kanıt zinciri (EvidenceChain) tahrifi, imzalı rapor spoofing'i
   gibi *product*-security konularını önce özel olarak raporlayın; genel
   model-zafiyeti bulguları (jailbreak prompt'ları) için değil.
3. **Yol:** GitHub → Security → **"Report a vulnerability"** (özel bildirime
   açık). E-posta kanalı (`dev@dumen.ai`) alan-adı doğrulandıysa ikincil
   seçenektir; yanıt gelmezse 14 gün sonra düz Issue olarak kamuyla paylaşın
   (embargo süresi maksimum 14 gün).

## Kapsam Dışı (bilinen sınırlar — README "Kalite Kanıtları" ve "Mevzuat Kapsamı" bölümleri)

- Regextabanlı gateway katmanının yaratıcı/çokdilli dolaylı enjeksiyonları
  kaçırması **tasarım sınırının** ifadesidir (holdout recall raporlu —
  `examples/audits/gateway_selfredteam_*.json`); güvenlik açığı değil,
  savunma-derinliği mimarisinin gerekçesidir.
- Yönlendirme-öncesi (pre-steering) beyaz-kutu aktivasyon erişimi: hook
  yeteneği olan her saldırgan refüs yönünü seyrekleştirebilir — bu, alandaki
  tüm yayınlanmış saldırıların (steering-awareness) kabul edildiği sınırdır.
- Yerel dosya sistemi erişimi olan kullanıcılar kanıt zincirini
  yeniden-üretebilir; zincir *kasılma-direnci* sağlar, *kimlik-doğrulaması*
  sağlamaz (imzalama roadmap'te).
