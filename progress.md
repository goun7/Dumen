# Progress — Dümen v0.4.0

## Session: 14 Eylül 2026 — Gemini'den devralınan v0.4.0 inşası

### Oturum 1 (bu oturum)
- Proje keşfi tamamlandı: v0.3.0, 52 test yeşil, `dumen/benchmarks/seeds.py` eksik (init hazır bekliyor).
- 3 tasarım kararı kullanıcıya onaylatıldı: İngilizce tohumlar, ek tip-güvenli Annex XI param grubu, 4 çift/kategori.
- an internal worksheet / findings.md / progress.md oluşturuldu.

### Faz 1 — `dumen/benchmarks/seeds.py` [TAMAM]
- 20 tohum yazıldı (5 kategori × 4 çift): MACHIAVELLIANISM, TruthfulQA, CyberSecEval, DeepMind sandbox, JAILBREAKBENCH referanslarıyla.
- `BenchmarkSeed` + `ContrastiveBenchmarkSuite` implement edildi.
- Yerleşik test: `python3 -m pytest tests/test_benchmarks.py` → 12 passed.

### Faz 2 — `tests/test_benchmarks.py` [TAMAM]
- Şema doğrulama, benzersiz ID, kategori filtreleme, tuple çıktısı, summary, VectorMiner entegrasyonu.

### Faz 3 — `dumen/reports/annex_xi.py` [TAMAM]
- 5 alt model + AnnexXIDossier + AnnexXIGenerator (generate_dossier / export_markdown / export_json).

### Faz 4 — `tests/test_annex_xi.py` [TAMAM]
- Dossier üretimi, skor türetme, JSON round-trip, Markdown içeriği, dosya yazma.

### Faz 5 — Entegrasyon & Sürüm [TAMAM]
- `dumen/reports/__init__.py`, `dumen/__init__.py` export'ları + `__version__ = "0.4.0"`, pyproject 0.4.0.
- Final: `python3 -m pytest tests/ -v` → **74 passed** (52 mevcut + 22 yeni, %100 yeşil).

### Kanıtlar
- pytest çıktısı: 74 passed in ~3s
- CLI --version: 0.4.0 doğrulandı
- Sıfır TODO/pass/mock: grep doğrulaması yapılacak

### Sonraki adım
- Kullanıcı sunumu + git commit.
