"""test_veridict_bridge — Dümen kanıt zincirinin Veridict ledger'ına
ihracatının doğruluk testleri.

Kapsam:
- sağlıklı zincir → doğru sayıda giriş + geçerli Veridict zinciri
- imza bağlaması → parmak-izi fişe yazılır
- dossier özeti → ek giriş
- KURCALANMIŞ zincir → ihracat reddedilir (fail-closed, sessiz-geçiş yok)
"""
from __future__ import annotations

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dumen.reports.evidence_chain import EvidenceChain  # noqa: E402
from dumen.reports.veridict_bridge import (  # noqa: E402
    BridgeReceipt,
    export_chain_to_veridict,
)

try:
    import veridict  # noqa: F401
except ImportError:
    pytest.skip("veridict-standard not installed — bridge tests skipped",
                allow_module_level=True)


def _sample_chain() -> EvidenceChain:
    chain = EvidenceChain()
    chain.append("mining", {"features_found": 42, "model": "llama-3-8b"})
    chain.append("evaluation", {"bench": "SteeringOverheadBench", "overhead_ms": 4.2})
    chain.append("steering", {"direction": "refusal", "cosine": 0.71})
    chain.append("report", {"scorecard": "v0.7.5", "risk": "low"})
    return chain


def test_healthy_chain_exports_all_entries(tmp_path):
    ledger = str(tmp_path / "ledger.jsonl")
    receipt = export_chain_to_veridict(_sample_chain(), ledger)

    assert isinstance(receipt, BridgeReceipt)
    assert receipt.dumen_chain_valid is True
    assert receipt.dumen_chain_length == 4
    # 4 chain entries + 1 signature binding (passed below)
    assert receipt.veridict_entry_count == 4
    assert receipt.veridict_head is not None
    assert os.path.exists(ledger)
    assert receipt.notes  # guidance note about certificate/anchor


def test_veridict_ledger_verifies_independently(tmp_path):
    """Üretilen ledger bağımsız olarak verify_chain'den geçmeli."""
    from veridict.ledger import Ledger

    ledger_path = str(tmp_path / "ledger.jsonl")
    export_chain_to_veridict(_sample_chain(), ledger_path)

    loaded = Ledger.load(ledger_path)
    ok, reason = loaded.verify_chain()
    assert ok, f"veridict chain broken: {reason}"
    # tüm girişler evidence.recorded (mevcut şema — yeni tip yok)
    assert all(e["entry_type"] == "evidence.recorded" for e in loaded.entries)


def test_signature_binding_is_recorded(tmp_path):
    ledger = str(tmp_path / "ledger.jsonl")
    chain = _sample_chain()
    receipt = export_chain_to_veridict(
        chain, ledger,
        signature_record={
            "head_hash": chain.head_hash(),
            "pubkey_fingerprint": "ed25519:deadbeef",
            "signer_name": "dumen-test",
        },
    )
    assert receipt.signature_fingerprint == "ed25519:deadbeef"
    assert receipt.veridict_entry_count == 5  # 4 chain + 1 signature


def test_dossier_digest_is_recorded(tmp_path):
    ledger = str(tmp_path / "ledger.jsonl")
    dossier = json.dumps({"model_name": "llama-3-8b", "provider": "test"})
    receipt = export_chain_to_veridict(_sample_chain(), ledger,
                                       dossier_json=dossier)
    assert receipt.dossier_digest is not None
    assert len(receipt.dossier_digest) == 64
    assert receipt.veridict_entry_count == 5  # 4 chain + 1 dossier


def test_tampered_chain_is_refused(tmp_path):
    """Fail-closed: kurcalanmış zincir ihracat edilmez, dosya oluşmaz."""
    ledger = str(tmp_path / "ledger.jsonl")
    chain = _sample_chain()
    entries = chain.get_entries()
    entries[0].payload["features_found"] = 999        # TAMPER
    chain._entries = entries

    receipt = export_chain_to_veridict(chain, ledger)

    assert receipt.dumen_chain_valid is False
    assert receipt.dumen_break_index == 0
    assert receipt.veridict_entry_count == 0
    assert not os.path.exists(ledger)
    assert any("fail-closed" in n for n in receipt.notes)


def test_payloads_link_by_hash_not_copy(tmp_path):
    """Dümen içeriği KOPYALANMAZ — sadece özeti bağlanır (doktrin)."""
    from veridict.ledger import Ledger

    ledger_path = str(tmp_path / "ledger.jsonl")
    export_chain_to_veridict(_sample_chain(), ledger_path)
    loaded = Ledger.load(ledger_path)

    for e in loaded.entries:
        p = e["payload"]
        assert "dumen_entry_hash" in p
        assert "dumen_payload_digest" in p
        # orijinal Dümen içeriği kopyalanmamış
        assert "model" not in p
        assert "bench" not in p
