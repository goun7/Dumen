# Katkı Rehberi (Contributing)

Dümen'e katkı için kod zorunlu değil — **kanıt** zorunludur. Proje doktrini:
*kanıt yoksa iddia yok.* Bu, katkılarda da geçerlidir.

## Geliştirme Ortamı

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"          # test + lint araçları
pip install -e ".[model]"        # (ops.) gerçek-model entegrasyon testleri için transformers
python -m pytest tests/ -q       # süiti koş
ruff check dumen/ tests/ examples/
```

Python 3.10–3.14 desteklenir; CI üç sürümde koşar (3.12 gerçek-model dahil).

## Kurallar

1. **Sahte sayı yok.** Ölçülmeyen metrik raporda `None`/“Ölçülmedi” olur;
   sabit kodlanmış başarı sayısı üretime giremez (bkz. `steering_efficacy`).
2. **Test'isiz davranış yok.** Her yeni üretim dalı gerçek bir soket/CLI/
   dosya yoluyla test edilir — mock sunucu yerine stdlib threading HTTP
   sunucusu gibi GERÇEK mekanizmalar tercih edilir (bkz. `test_api_runner.py`).
3. **Atıf doğrulanır.** arXiv ID + başlık + yıl, birincil kaynaktan teyitli
   olmalı; yanlış-atıf düzeltmesi PR'da ayrıca belirtilir.
4. **Harici veri lisansı.** Ham lisanslı-veri (deepset CC-BY-NC, AgentHarm
   "other") depoya GİRMEZ; yalnız MIT/Apache dağıtımlar commit edilir
   (JBB MIT ✓). Yükleyiciler şemayı sabitler, veri kullanıcıda kalır.
5. **Kapsam dürüstlüğü.** Beyaz-kutu (aktivasyon) kanalı ile siyah-kutu (API)
   kanalı karıştırılmaz; etkinlik ölçümü yalnız beyaz-kutuda mümkündür.

## PR Süreci

- Tek tema, tek commit (`feat(...)`, `fix(...)`, `docs(...)` önekleri).
- Kapılar: tam süit yeşil + coverage ≥ %95 + `ruff` temiz.
- Yeni CLI bayrağıysa: `--help` çıktısı Türkçe+İngilizce karışık olabilir;
  hata mesajları YENİDEN ÜRETİLEBİLİR olmalı (ne denediğinizi yazın).

## Rapor Kalitesi

`examples/audits/` altındaki yayımlanmış denetimler ŞEFFAF kanıttır:
koşturulan her artifact yeniden üretilebilir komutuyla birlikte `_run.log`
içinde taşır. Yeni denetim yayımlayacaksanız komutu ve ortamı da ekleyin.
