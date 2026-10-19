"""dumen.receipt — KOK compute-work proof receipts for dumen's own analysis work.

K1'in-açık-yarısını kapatir (2026-10-19): tamga'nin compute-anchor op'u
( `tools/compute_anchor.py`, RFC-011) bir mesh projesinde KOD-KANITI ile
tuketilir. hedef: dumen'in SAE-encode MatMul'i ( W_enc @ (x - b_dec) + b_enc)
kok'un G-layer mining-proof formatina tasiyip tamga ledger'ina baglamak.

Tasarim ( kok/receipt/kok_receipt_verify_en.py'nin sozlesmesine birebir):
  - matrix_a/matrix_b  dumen'in kendi isinden turetilen tamsayi matrisler
    ( aktivasyon ve agirliklarin q=97'ye modulo-legitim cevirimi)
  - task_program        "dumen/sae-pre-acts-matmul" (Gerçek dumen isinin adi)
  - program/input commit  kok'un commitment fonksiyonlari ( ayni formuller)
  - tile certificate     ( i, j, value, m) — nonce altinda target'i gecer
  - receipt_hash         sha256( work_canonical envelope)
  - signature            Ed25519 ( PyNaCl) — SIG_DOMAIN ile

Dizgi-uyumu: bu modul kok'un verifier'ini IMPORT ETMEZ; sadece ayni
formulleri uygular ( bagimsiz-uretici = bagimsiz-verifier ile ayni sonuc).
"""
