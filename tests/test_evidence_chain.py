"""
tests/test_evidence_chain.py
============================
Hash-chain kanıt zinciri testleri: bütünlük, takma tespiti, serileştirme.
"""

import json

import pytest

from dumen.reports.evidence_chain import ChainVerification, EvidenceChain


class TestChainOperations:
    def test_append_and_length(self):
        chain = EvidenceChain()
        assert len(chain) == 0
        e1 = chain.append("mining", {"vector_name": "deception_layer_12", "confidence": 0.93})
        assert e1.index == 0
        e2 = chain.append("evaluation", {"harm_score": 0.12})
        assert e2.index == 1
        assert len(chain) == 2

    def test_genesis_prev_hash(self):
        chain = EvidenceChain()
        e = chain.append("mining", {"x": 1})
        assert e.prev_hash == "0" * 64

    def test_linkage(self):
        """Her kayıt öncekinin özetini taşımali."""
        chain = EvidenceChain()
        e1 = chain.append("mining", {"a": 1})
        e2 = chain.append("evaluation", {"b": 2})
        e3 = chain.append("report", {"c": 3})
        assert e2.prev_hash == e1.entry_hash
        assert e3.prev_hash == e2.entry_hash

    def test_valid_chain_verifies(self):
        chain = EvidenceChain()
        chain.append("mining", {"n": 1})
        chain.append("evaluation", {"harm": 0.4})
        chain.append("steering", {"intervened": True})
        v = chain.verify()
        assert isinstance(v, ChainVerification)
        assert v.is_valid is True
        assert v.length == 3
        assert v.first_broken_index is None
        assert v.genesis_present is True
        assert len(v.head_hash) == 64

    def test_empty_chain_verifies_neutral(self):
        chain = EvidenceChain()
        v = chain.verify()
        assert v.is_valid is True
        assert v.length == 0
        assert v.genesis_present is False
        assert v.head_hash == "0" * 64

    def test_rejects_non_serializable_payload(self):
        chain = EvidenceChain()
        with pytest.raises(ValueError):
            chain.append("mining", {"tensor": object()})  # JSON'a çevrilemez

    def test_rejects_empty_stage(self):
        chain = EvidenceChain()
        with pytest.raises(ValueError):
            chain.append("", {"x": 1})


class TestTamperDetection:
    def test_payload_mutation_detected(self):
        """Kayıt içeriği sonradan değiştirilirse doğrulama kırılmalı."""
        chain = EvidenceChain()
        chain.append("mining", {"confidence": 0.9})
        chain.append("evaluation", {"harm_score": 0.1})

        # Doğrudan iç kaydı kurcalayıyoruz (saldırgan simülasyonu)
        chain._entries[0].payload["confidence"] = 0.1  # kanıt takma!

        v = chain.verify()
        assert v.is_valid is False
        assert v.first_broken_index == 0
        assert "yeniden hesaplanamıyor" in v.break_reason

    def test_reordering_detected(self):
        """Kayıtların yer değişmesi zinciri koparmalı."""
        chain = EvidenceChain()
        chain.append("mining", {"a": 1})
        chain.append("evaluation", {"b": 2})
        chain.append("report", {"c": 3})
        chain._entries[1], chain._entries[2] = chain._entries[2], chain._entries[1]
        v = chain.verify()
        assert v.is_valid is False

    def test_truncation_of_head_keeps_prefix_valid(self):
        """
        SON kayıt silinirse: kalan önek kendi içinde tutarlı kalır
        (hash-chain'in doğası). Bunu dürüstçe raporla: önek geçerli ama
        uzunluk değişmiştir — head_hash değişir, dış referans tutmaz.
        """
        chain = EvidenceChain()
        chain.append("mining", {"a": 1})
        chain.append("evaluation", {"b": 2})
        head_before = chain.head_hash()
        chain._entries.pop()  # son kayıt silinir
        v = chain.verify()
        assert v.is_valid is True  # önek kendi içinde sağlam
        assert chain.head_hash() != head_before  # ama dış baş referansı artık tutmaz


class TestSerialization:
    def test_json_roundtrip_valid(self):
        chain = EvidenceChain()
        chain.append("mining", {"name": "v1", "dim": 16})
        chain.append("dossier", {"id": "DUMEN-ANNEXXI-1"})
        raw = chain.to_json()
        restored = EvidenceChain.from_json(raw)
        assert len(restored) == 2
        assert restored.head_hash() == chain.head_hash()
        # to_json artık şema bilgisini yazar (sürüm-bilgili kanonikleştirme)
        data = json.loads(raw)
        assert data["canon_scheme"] == chain._canon_scheme
        assert "evidence_chain" in data

    def test_json_roundtrip_rfc8785_scheme_preserved(self):
        """rfc8785 şemasıyla kurulan zincir şemasını serileştirmeli.

        not: from_json dict dalı bir report-kaydı ister (demet sözleşmesi);
        bu test saf zincir-seviyesinde serileştirmeyi doğrular.
        """
        chain = EvidenceChain(canon_scheme="rfc8785")
        chain.append("mining", {"name": "v1", "dim": 16})
        data = json.loads(chain.to_json())
        assert data["canon_scheme"] == "rfc8785"
        assert "evidence_chain" in data

    def test_json_roundtrip_legacy_list_format_still_loads(self):
        """Eski liste formatı (canon_scheme'siz) hâlâ yüklenmeli — geri uyum."""
        chain = EvidenceChain()
        chain.append("mining", {"name": "v1", "dim": 16})
        legacy = json.dumps([e.model_dump() for e in chain._entries])
        restored = EvidenceChain.from_json(legacy)
        assert restored._canon_scheme == "jcs_python"
        assert restored.head_hash() == chain.head_hash()

    def test_json_roundtrip_tampered_rejected(self):
        """Serileştirme sonrası kurcalanan zincir geri yüklenemez."""
        chain = EvidenceChain()
        chain.append("mining", {"confidence": 0.95})
        raw = chain.to_json()
        data = json.loads(raw)
        # to_json dict üretir: {"canon_scheme": ..., "evidence_chain": [...]}
        data["evidence_chain"][0]["payload"]["confidence"] = 0.05  # kurcalama
        tampered = json.dumps(data)
        with pytest.raises(ValueError, match="bütünlük"):
            EvidenceChain.from_json(tampered)

    def test_canon_scheme_field_tampering_detected(self):
        """canon_scheme alanı değiştirilirse hash'ler uyuşmaz — reddedilir.

        Yayınlanmış sertifikaların risk_scores'ları float 0.0 içerir:
        jcs_python '0.0', rfc8785 '0' yazar → hash ayrışır. Bu vakayı kullanır.
        """
        chain = EvidenceChain(canon_scheme="rfc8785")
        chain.append("mining", {"risk_scores": {"harm": 0.0}})
        data = json.loads(chain.to_json())
        data["canon_scheme"] = "jcs_python"  # eski-şema demeti taklidi
        with pytest.raises(ValueError, match="bütünlük"):
            EvidenceChain.from_json(json.dumps(data))

    def test_corrupt_json_rejected(self):
        with pytest.raises(ValueError):
            EvidenceChain.from_json("{bozuk json")

    def test_entries_copy_is_defensive(self):
        """get_entries kopya döndürmeli — dış mutasyon zincire sızmamalı."""
        chain = EvidenceChain()
        chain.append("mining", {"a": 1})
        entries = chain.get_entries()
        entries.clear()
        assert len(chain) == 1

    def test_entry_hash_deterministic(self):
        """Aynı alanlar → aynı özet (yeniden üretilebilirlik)."""
        h1 = EvidenceChain._hash_entry(0, "2026-01-01", "mining", {"a": 1}, "0" * 64)
        h2 = EvidenceChain._hash_entry(0, "2026-01-01", "mining", {"a": 1}, "0" * 64)
        assert h1 == h2
        # payload anahtar sırası farklı olsa bile aynı (canonical JSON)
        h3 = EvidenceChain._hash_entry(0, "2026-01-01", "mining", {"b": 2, "a": 1}, "0" * 64)
        h4 = EvidenceChain._hash_entry(0, "2026-01-01", "mining", {"a": 1, "b": 2}, "0" * 64)
        assert h3 == h4
