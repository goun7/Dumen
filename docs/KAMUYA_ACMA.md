# Kamuya Açma Talimatı — tek oturumda 5 adımlık kontrol listesi

> Amaç: v0.7.2'yi GitHub + PyPI'ya SENİN ADINA çıkarmak. Repo tarafındaki her
> şey hazır (temiz-history üretici, numune dosya, testler yeşil). Kalan 5 adım
> hesap/otorite gerektirdiği için yalnız sende. Tahmini toplam süre: ~25 dk.

## 0) Kararlar (2 dakika, kağıt üstü)
- **Kimlik maskesi:** public commitlerde hangi isim/e-posta görünecek?
  (Sester'de kullanılan desen: `Gokun <dev@dumen.ai>` gibi noreply-türevi.)
- **Organizasyon/ad:** `github.com/dumen-ai/dumen` önerim (PyPI adı ile aynı
  kök; org daha alınmadı — almak için şu an engel yok).

## 1) Temiz kamusal-kopyayı üret
```bash
cd ~/projects/01_unicorn/77-Dumen
DRY_RUN=0 PUBLIC_NAME="SEÇTİĞİN_AD" PUBLIC_EMAIL="SEÇTİĞİN_MAIL" bash scripts/prepare_public.sh
```
Çıktı: `../77-Dumen-public/` — tüm commit imzaları maskeli, sızma taraması
geçmiş, ORİJİNAL klasöre dokunulmaz. (Kopyayı patlatmazsan geri-alış yok;
push'tan önce bir kez göz gezdir: `git -C ../77-Dumen-public log --format='%an <%ae>' | sort -u` tek satır olmalı.)

## 2) GitHub reposu
```bash
gh repo create dumen-ai/dumen --public --source ../77-Dumen-public \
  --description "Open-source EU AI Act audit engine: white-box steering evidence, capability-regression gate, tamper-evident Annex XI dossiers"
cd ../77-Dumen-public && git push -u origin master --follow-tags
```
Not: CI tanımı `main` dalına push bekler — istersen `git branch -m master main`
önce. Konu etiketleri: `ai-safety`, `eu-ai-act`, `red-teaming`, `interpretability`,
`llm-evaluation`, `compliance`.

## 3) PyPI adı tahsisi (bunu İLK yapmış olmak değerli — yarış yok ama sigorta)
```bash
# 0.7.2 dağıtımlarını yeniden üret (dist/ şu an 0.7.1):
python3 -m build --sdist --wheel
python3 -m pip install --upgrade twine
# pypi.org/account/register/ (varsa atla) → sonra:
python3 -m twine upload --repository-url https://upload.pypi.org/legacy/ dist/dumen-0.7.2*
```
`dumen` adı 15-Eyl'de boşta DOĞRULANDI (HTTP 404). `pip index` yerine gerçek
kurulumla teyit: `pip install dumen` temiz venv'de.

## 4) GitHub Release (v0.7.2)
`gh release create v0.7.2 --generate-notes` — gövdeye şunu yapıştır:

> Audit-grade evidence for the EU AI Act, from your own GPU. 7 published
> scorecards across 3 model families (qwen2.5/llama3.2/phi3 via Ollama), a
> capability-regression gate (B1) that vetoes "protection" claims when
> steering breaks the model, and SHA-256-sealed Annex XI dossiers. 349 tests,
> %97 coverage. Sample compliance file: examples/pilot/.

## 5) Yayın-günü README kontrolü (otomatik kapı yok — göz)
- [ ] `pip install dumen` README'nin üstinde ARTIK doğru (3. adım bittiyse)
- [ ] "repo-açma kararı sende" notları kaldırıldı mı → kaldır (artık açıldı)
- [ ] `dumen --version` → 0.7.2; `dumen audit --refusal-baseline` canlıda 10sn altında

## Bu liste bittikten SONRA (ilk iş-geliştirme, bana devret)
C2'deki 10 aday-müşteri listesine numune dosyayla (`examples/pilot/`) ilk
e-posta turu atılır; GitHub yıldız/trafik verisi 90-gün ölçümünün (klasör
kararı) gerçek-üst-verisi olur.
