"""
dumen.reports.veridict_bridge
=============================
Dümen → Veridict köprüsü — EU AI Act teknik dokümantasyonu için
offline-doğrulanabilir sertifika üretimi.

Dümen'in SHA-256 kanıt zinciri (EvidenceChain) "kendi-kendine tutarlılık"
kanıtlar; Veridict'in ledger + sertifikası bunun üzerine **bağlam** katar:
- append-only hash-chained ledger'a kanıt kayıtlarının özetleri yazılır
- bağımsız bir doğrulayıcı sertifikayı offline olarak yeniden oynayabilir
- Rekor transparency-log anchor'ı RFC 3161 zaman-mührü boşluğunu kapatır
  (dumen/reports/signing.py'nin belirttiği "harici TSA gerekir" notu)

Doktrin uyumu: bu modül bir İHRACAT modülüdür — Veridict ledger'ına
SADECE mevcut entry tiplerini yazar; şema değişikliği yapmaz. Dümen'in
zinciri olduğu gibi korunur (source of truth); Veridict tarafında onun
özeti ve doğrulama sonucu kanıt olarak tutulur.

Kapsam (dürüst sınır): bu modül **sertifika üretmez**. Veridict sertifikası
ancak tam bir denetim akışının (task → claims → adjudications → jury)
sonunda `CertificateIssuer.issue` tarafından imzalanabilir; köprü o
akışın yerini almaz. Köprü, ledger tarafını kurar — sertifika ve anchor
veridict CLI'sı veya audit akışıyla alınır (aşağıdaki `anchor_note`).
"""
from __future__ import annotations

import json
import os
from typing import Any, List, Optional

from pydantic import BaseModel, Field

from .evidence_chain import ChainEntry, ChainVerification, EvidenceChain

# ---------------------------------------------------------------------------
# Model: köprünün çıkış sertifikası
# ---------------------------------------------------------------------------


class BridgeReceipt(BaseModel):
    """Köprünün ürettiği fiş — hem Dümen hem Veridict tarafında okunabilir."""

    dumen_chain_head: str = Field(description="Dümen zincir başı SHA-256")
    dumen_chain_length: int = Field(ge=0)
    dumen_chain_valid: bool
    dumen_break_index: Optional[int] = None
    dumen_break_reason: Optional[str] = None
    dossier_digest: Optional[str] = Field(
        default=None,
        description="Annex XI dossier JSON özeti (dossier sağlanmışsa)",
    )
    signature_fingerprint: Optional[str] = Field(
        default=None,
        description="Ed25519 imza parmak-izi (imza sağlanmışsa)",
    )
    veridict_ledger_path: Optional[str] = None
    veridict_entry_count: int = Field(default=0, ge=0)
    veridict_head: Optional[str] = None
    anchored: bool = Field(default=False, description="Rekor anchor'ı başarılı")
    anchor_sidecar_path: Optional[str] = None
    notes: List[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Çekirdek: Dümen zincirini Veridict ledger'ına ihracat
# ---------------------------------------------------------------------------

_STAGE_TO_ENTRY_TYPE = {
    "mining": "evidence.recorded",
    "evaluation": "evidence.recorded",
    "steering": "evidence.recorded",
    "report": "evidence.recorded",
    "dossier": "evidence.recorded",
    "incident": "evidence.recorded",
}


def export_chain_to_veridict(
    chain: EvidenceChain,
    ledger_out: str,
    *,
    actor_identity: str = "dumen-evidence-bridge",
    dossier_json: Optional[str] = None,
    signature_record: Optional[Any] = None,
) -> BridgeReceipt:
    """Dümen kanıt zincirini Veridict ledger'ına yazar.

    Her Dümen ChainEntry için bir Veridict ledger girişi üretilir:
    - entry_type: stage'e göre eşlenir (hepsi mevcut 'evidence.recorded')
    - payload: {dumen_stage, dumen_index, dumen_entry_hash, dumen_payload_digest}
      — Dümen'in iç içeriğini KOPYALAMAZ, özetini bağlar

    Anchor (Rekor) bu modülün kapsamında DEĞİLDİR: anchor, Veridict
    sertifikasının checkpoint'ini bağlar ve sertifika yalnızca tam bir
    denetim akışında imzalanabilir. Köprü ledger'ı kurar; anchor için
    `anchor_note`'a ve README'deki iki adımlı akışa bakın.

    Args:
        chain: doğrulanmış Dümen kanıt zinciri
        ledger_out: çıkış ledger JSONL yolu
        actor_identity: Veridict tarafında üretici kimliği
        dossier_json: Annex XI dossier JSON metni (ek özet girişi için)
        signature_record: imza fişi (SignatureRecord veya dict)

    Returns:
        BridgeReceipt — her iki tarafın da okuyabileceği fiş
    """
    # 1. Dümen zincirinin bütünlüğünü yeniden hesapla (kendi doğrulayıcısı)
    verification: ChainVerification = chain.verify()
    entries: List[ChainEntry] = chain.get_entries()

    receipt = BridgeReceipt(
        dumen_chain_head=chain.head_hash(),
        dumen_chain_length=len(entries),
        dumen_chain_valid=verification.is_valid,
        dumen_break_index=verification.first_broken_index,
        dumen_break_reason=verification.break_reason,
    )

    # Bozuk zincir ihracat edilmez — sessiz-geçiş yasağı
    if not verification.is_valid:
        receipt.notes.append(
            "chain integrity FAILED — refused to export a broken chain "
            "(fail-closed, no silent pass)"
        )
        return receipt

    # 2. Veridict ledger'ını kur (geçici import — Dümen çekirdek bağımlılığı değil)
    from veridict.ledger import Ledger  # noqa: PLC0415  (optional bridge dep)
    from veridict.schemas import ActorRef  # noqa: PLC0415

    ledger = Ledger()
    producer = ActorRef(kind="watcher", identity=actor_identity, version="0.1.0")

    # 3. Her Dümen kaydı için bir özet-bağlama girişi
    for entry in entries:
        payload = {
            "dumen_stage": entry.stage,
            "dumen_index": entry.index,
            "dumen_entry_hash": entry.entry_hash,
            "dumen_prev_hash": entry.prev_hash,
            "dumen_payload_digest": _digest_payload(entry.payload),
        }
        entry_type = _STAGE_TO_ENTRY_TYPE.get(entry.stage, "evidence.recorded")
        ledger.append(entry_type, producer, payload)

    # 4. İmza parmak-izi varsa ek bir bağlama girişi
    if signature_record is not None:
        sig = (
            signature_record
            if isinstance(signature_record, dict)
            else signature_record.model_dump()
        )
        ledger.append(
            "evidence.recorded",
            producer,
            {
                "dumen_stage": "signature.binding",
                "dumen_index": -1,
                "dumen_entry_hash": sig.get("head_hash", ""),
                "dumen_prev_hash": "",
                "dumen_payload_digest": _digest_payload(sig),
                "dumen_signature_fingerprint": sig.get("pubkey_fingerprint", ""),
                "dumen_signer_name": sig.get("signer_name", ""),
            },
        )
        receipt.signature_fingerprint = sig.get("pubkey_fingerprint")

    # 5. Dossier özeti (opsiyonel)
    if dossier_json is not None:
        digest = _digest_json(dossier_json)
        receipt.dossier_digest = digest
        ledger.append(
            "evidence.recorded",
            producer,
            {
                "dumen_stage": "dossier.digest",
                "dumen_index": -1,
                "dumen_entry_hash": "",
                "dumen_prev_hash": "",
                "dumen_payload_digest": digest,
                "dumen_dossier": True,
            },
        )

    # 6. Ledger'ı diske yaz ve doğrula
    os.makedirs(os.path.dirname(os.path.abspath(ledger_out)) or ".", exist_ok=True)
    ledger.save(ledger_out)
    ok, reason = ledger.verify_chain()
    receipt.veridict_ledger_path = ledger_out
    receipt.veridict_entry_count = len(ledger.entries)
    receipt.veridict_head = ledger.entries[-1]["entry_hash"] if ledger.entries else None
    if not ok:
        receipt.notes.append(f"veridict chain verification failed: {reason}")
        return receipt

    receipt.notes.append(
        "ledger ready — for the offline-verifiable certificate + Rekor anchor "
        "run: veridict audit --ledger <path> (anchor requires the signed "
        "certificate; see module docstring)"
    )
    return receipt


# ---------------------------------------------------------------------------
# Yardımcılar
# ---------------------------------------------------------------------------


def _digest_payload(payload: Any) -> str:
    """Dümen payload'ının kararlı SHA-256 özeti."""
    import hashlib  # noqa: PLC0415

    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _digest_json(text: str) -> str:
    import hashlib  # noqa: PLC0415

    return hashlib.sha256(text.encode("utf-8")).hexdigest()


__all__ = ["BridgeReceipt", "export_chain_to_veridict"]
