# Dumen MCP server — mekanistik-denetim araçları AI ajanları için

`mcp/server.py`, Model Context Protocol 2025-06-18'ü stdio üzerinden
konuşur ( JSON-RPC 2.0, modul-tepesi saf-stdlib) ve 6 araci sunar.

## Araçlar

| Araç | Ne yanıtlar |
|---|---|
| `version` | `dumen --version` karşılığı + torch-yer-tespiti |
| `amplification_scan` | TLCM amplifikasyon-rejim tespiti ( arXiv:2609.07876) |
| `sae_summary` | SAE ileri-geçiş + yeniden-inşa kalitesi |
| `steering_status` | Kayıtlı steering-vektör durumu + StTP geometrisi |
| `kv_drift` | Birikimli KV-sapma metrikleri |
| `archive` | zlib-sıkıştırılmış JSON kanıt-arsivi ( `output_path` ZORUNLU) |

Her araç bir JSON kanıtı döndürür — asla exception fırlatmaz (
tamga AT-192 message-RED disiplini). Ağır-bağımlılık ( torch) opsiyoneldir:
sunucu torch'suz da ayağa kalkar ve eksik-bağımlılık bir RED-nedeni olarak
döner, çöküş değil.

## Çalıştırma

```bash
python3 mcp/server.py                              # stdio JSON-RPC
DUMEN_MCP_ARCHIVE_DIR=/tmp/kanitler python3 mcp/server.py
```

İstemci tarafı:

```json
{ "command": "python", "args": ["<repo>/mcp/server.py"],
  "env": { "DUMEN_MCP_ARCHIVE_DIR": "/tmp/kanitler" } }
```

## İzolasyon-ilkesi

HICBIR araç repo-altı varsayılan yere YAZMAZ. Yazan tek araç olan
`archive` yalnızca çağıranın verdiği acık yolu ( `output_path` argümanı
veya `DUMEN_MCP_ARCHIVE_DIR` env'i) yazar; ikisi de yoksa RED — sessizce
repo-altı bir dosya ÜRETMEZ. Testlerde daima `tmp_path` (
`docs/MCP_WORKSPACE_IZOLASYON_DERSI.md`, veridict 2026-10-19).

## Registry

Smithery yapılandırması: [`smithery.yaml`](smithery.yaml). Araç-kataloğu:
[`mcp.json`](mcp.json).

**Yayın-durumu: HAZIRDEĞİL.** Smithery publish OAuth-login gerektirir ve
kullanıcının-eliyle yapılır. Bu dosyalar registry-yapılandırma
hazırlığıdır — varlıkları yayın-yapıldığı anlamına gelmez. Yerel deneme:

```bash
smithery mcp add ./mcp/server.py --id dumen   # registry olmadan
smithery tool list dumen
smithery tool call dumen version '{}'
```

## Testler

`tests/test_mcp_server.py` subprocess üzerinden uçtan-uca pinned:
el-sıkışma, araç-listesi, 6 aracın GREEN çıktıları, bilinmeyen-arac -32601,
izolasyon ( çağrı-sonrası repo-kökünde yeni-dosya-yok).
