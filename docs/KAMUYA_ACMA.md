# Kamuya Açma Talimatı — tek oturumda 5 adımlık kontrol listesi

> Amaç: v0.7.2'yi GitHub + PyPI'ya SENİN ADINA çıkarmak. Repo tarafındaki her
> şey hazır (temiz-history üretici, numune dosya, testler yeşil). Kalan 5 adım
> hesap/otorite gerektirdiği için yalnız sende. Tahmini toplam süre: ~25 dk.

## 0) Kararlar (2 dakika, kağıt üstü)
- **Kimlik:** aile-standardı ZATEN scriptin içinde (`goun7` + GitHub-noreply,
  Sester içtihadı) — farklı istersen PUBLIC_NAME/PUBLIC_EMAIL ile geçersin.
- **Repo adresi:** `goun7/Dumen` (Sester/Veridrome deseni; `dumen-ai` org
  istenirse web'den kurulur, repo sonra transfer edilir — ikisi de 5 sn'lik iş).

## 1) Temiz kamusal-kopyayı üret — TEK komut
```bash
cd ~/projects/01_unicorn/77-Dumen
DRY_RUN=0 bash scripts/prepare_public.sh
```
v2 şunları yapar ve SONUNDA FAIL-LOUD doğrular: imza-maskesi, strateji
belgelerinin (DUMEN_MASTER_100, INSAA_SPECI, YOL_HARITASI, task_plan, bu
dosya) **geçmişten** sökülmesi, commit mesajı scrub'ı, tam-history taraması.
15-Eyl'de /tmp'de uçtan uca test edildi: 47 commit, tek imza, fsck temiz,
v0.7.0/0.7.1/0.7.2 etiketleri duruyor, yasaklı-iz 0. Orijinal klasöre dokunulmaz.

## 2) GitHub reposu + push
```bash
cd ../77-Dumen-public
git branch -m master main          # CI [main] bekliyor — push'tan ÖNCE
gh repo create goun7/Dumen --public --source . \
  --description "Open-source EU AI Act audit engine: white-box steering evidence, capability-regression gate, tamper-evident Annex XI dossiers"
git push -u origin main --follow-tags
```
Konu etiketleri: `ai-safety`, `eu-ai-act`, `red-teaming`, `interpretability`,
`llm-evaluation`, `compliance`.

## 3) PyPI adı tahsisi (bunu İLK yapmış olmak değerli — yarış yok ama sigorta)
```bash
# dağıtımları taze üret (dist/ 0.7.2 mevcut — yine de taze koş):
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

## Adım 1.5 — Yüz-dili hizası (logo ile birlikte karar)
Yeni topluluk dosyaları İngilizce yazıldı (Sester içtihadı: yayın-yüzü
İngilizce), README/CONTRIBUTING/SECURITY/CHANGELOG şimdilik Türkçe — karışık
yüz profesyonel değil. Uygulanacak desen: **README.md İngilizce-anasaha +
README_TR.md tam kardeş** (sayı-aynılık-kontrolü betiklе: her ölçülmüş sayı
iki yüzeyde birebir), TR-özet bloğu anasayfada dil-anahtarı; CONTRIBUTING/
SECURITY İngilizce'ye taşınır, CHANGELOG-ingilizce-lei geçişi ayrı tur.
İstisna yok: çeviride hiçbir sayı/yıl/atıfa dokunulmaz — diff-kontrolü şart.
