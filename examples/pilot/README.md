# Örnek Uyumluluk Dosyası (satış numunesi)

Bu klasördeki dosyalar, Dümen'in **parayla satacağı şeyin gerçeğe en yakın
örneğidir**: bir yapay-zeka sağlayıcısının AB yapay-zeka-yasası kapsamında
regülatöre sunmak zorunda olduğu teknik dosya.

## Ne okuyacaksınız?

| Dosya | İçerik |
|---|---|
| `sample_dossier.md` | Annex XI teknik dosyası — model kimliği, hesaplama, veri, kırmızı-takım sonuçları, eşik-değerlendirmesi |
| `sample_cop.md` | GPAI Uygulama Yönetmeliği (CoP) taahhüt matrisi — hangi madde kanıtlandı, hangisi eksik |
| `evidence_chain.json` | SHA-256 zinciri — dosyadaki her sayının hangi denetim kaydından geldiği; tek rakam değişse zincir kırılır |
| `sample_dossier.json` | Aynı dosyanın makine-okur hâli |

## Bu numunideki sayılar gerçek mi?

**Evet.** Skorlar bu depoda yayımlanmış gerçek bir denetimden geldi:
qwen2.5:3b modeline, kamuya açık JBB saldırı setinden 40 görev, sıcaklık=0,
15-Eyl-2026, bu makinede. Karnenin dosya-hash'i (SHA-256) kanıt zincirine
mühürlü — `evidence_chain.json` içindeki `d49a2041…` öneki
`examples/audits/qwen2.5-3b_ollama_jbb40.json` dosyasının başıdır.

## Neden bazı alanlarda "[Sağlayıcı beyanı bekliyor]" yazıyor?

Çünkü o bilgiler model sahibinde olur (irtibat, veri kökeni, opt-out, telif
politikası) ve Dümen **olmayan bilgiyi uydurmaz**. Gerçek teslimatta bu
köşeli-parantez alanlar müşteri beyanıyla dolar; kalan her satır denetimden
otomatik gelir. Numune, sınırın nerede olduğunu bilerek gösterir.

Hesaplama alanı da aynı dürüstlükle etiketli: FLOPs değeri, yayımlanmış
N (3.09B parametre) ve D (18T token, arXiv:2412.15115) ile 6·N·D kuralından
türetilmiş **sıra-tahminidir** ve dosyada böyle yazar; sonuç Madde 3(63)
eşiğinin (10²⁵) altında → araç, eşik mantığını beyandan kendisi hesaplar.

## Bunu kim, neden satın alır?

Yükümlülük haritası (dürüst sınırlarıyla):

- **Sistemik-risk GPAI sağlayıcıları** (eğitim ~10²⁵ FLOPs üstü ya da
  AB Komisyonu listesinde): tam olarak bu dosya — Ek-XI — **zorunlu**
  (Madde 55/53). Piyasadaki sayılı oyuncu, ama birim değer en yüksek.
- **Kapalı/kommerşyel GPAI sağlayıcıları**: Madde 53(1)(b) + Ek-XII
  dokümantasyonu zorunlu; araç oradaki "model değerlendirme" satırlarını
  aynı kanıt-zinciriyle besler.
- **Açık-ağırlık sağlayıcıları** (numunemizdeki Qwen gibi): birçok yükümlülükten
  muaf — AMA kendi müşterileri onları durdurur: bankalar/hastaneler/uluslararası
  ihaleler tedarikçi-due-diligence'ında kırmızı-takım kanıtı istiyor. Numune
  tam bu vaka: "muafsın ama müşterin bu sayfaları görecek" — satılan hizmet
  o masaya koyulabilir kanıt.
- **Yüksek-risk alan kullanıcıları** (Madde 6 sınıflı ürünler): Annex IV
  teknik dosyasının model-bölümü aynı kanıtlardan beslenir.
- 2 Ağu 2026'dan beri yürürlüklü Madde 50 şeffaflık kuralları tüm sağlayıcılara
  değiyor; denetim-kanıtı üretmenin en ucuz yolu bu hat.

Numunedeki CoP kapsamı bilerek **%62** ve dosya "sunuma hazır: HAYIR" damgası
taşıyor: eksik iki satırın kendisi hizmetin tarifidir — (1) olay-takip süreci
müşterinin kendi hattıdır, (2) çıkarım-zamanı önlemleri siyah-kutu kanalından
doğrulanamaz (ölçülenden fazlası asla yazılmaz). Satın alınan şey %100 yeşil
broşür değil, **gerçek durumu gösteren kırılmaz dosyadır.**

## Bu numuneyi kendi modelinizle üretin

```bash
# 1) denetim (yerel Ollama/vLLM/OpenAI-uyumlu uç ya da HF beyaz-kutu)
dumen audit --model <sizin-model> --endpoint <uç> --output denetim.json
# 2) dosya + CoP + zincir
python3 examples/pilot_dossier.py   # numune; kendi veriniz için bu betiği
                                    # denetim.json'unuzu okuyacak şekilde değiştirin
```
