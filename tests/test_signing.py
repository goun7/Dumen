"""Ed25519 zincir-imzalama testleri — modül API'sı GERÇEK dosya akışlarıyla.

Kapıdan geçen senaryolar: temiz imza/doğrulama, payload tahrifi (bütünlük
kapısı), imza-sonrası append (head uyuşmazlığı), yanlış public anahtar,
mevcut anahtarın sessiz-ezilmemesi. CLI testleri ayrı dosyadadır (CliRunner).
"""
from __future__ import annotations

import json

import pytest

from dumen.reports.evidence_chain import EvidenceChain
from dumen.reports.signing import (
    SignatureRecord,
    generate_keypair,
    sign_chain_file,
    verify_chain_file,
)


def _chain_with(n: int = 3) -> EvidenceChain:
    chain = EvidenceChain()
    for i in range(n):
        chain.append("evaluation", {"task": f"t{i}", "refused": bool(i % 2)})
    return chain


@pytest.fixture()
def signed(tmp_path):
    """Anahtar çifti + zincir dosyası + .sig üreten ortak kurulum."""
    kp = generate_keypair("auditor", str(tmp_path))
    chain = _chain_with(4)
    chain_file = tmp_path / "chain.json"
    chain_file.write_text(chain.to_json(), encoding="utf-8")
    rec = sign_chain_file(str(chain_file), kp["private_key_path"], "Acme Denetim")
    return {"kp": kp, "chain_file": chain_file, "rec": rec, "tmp": tmp_path}


class TestKeypair:
    def test_private_key_file_mode_is_0600(self, tmp_path):
        kp = generate_keypair("m", str(tmp_path))
        mode = tmp_path.joinpath("m.key").stat().st_mode & 0o777
        assert mode == 0o600, "gizli anahtar dünyaya-okunur olmamalı"
        assert tmp_path.joinpath("m.pub").exists()
        assert kp["fingerprint"].startswith("ed25519:")

    def test_existing_key_never_silently_overwritten(self, tmp_path):
        generate_keypair("dup", str(tmp_path))
        with pytest.raises(FileExistsError):
            generate_keypair("dup", str(tmp_path))
        again = generate_keypair("dup", str(tmp_path), overwrite=True)
        assert again["fingerprint"]  # --force bilinçli rotasyona izin verir


class TestSignVerify:
    def test_happy_path(self, signed):
        out = verify_chain_file(
            str(signed["chain_file"]),
            str(signed["chain_file"]) + ".sig",
            signed["kp"]["public_key_path"],
        )
        assert out.valid is True
        assert out.head_hash == signed["rec"].head_hash
        assert out.signer_name == "Acme Denetim"

    def test_payload_tamper_caught_by_integrity_gate(self, signed):
        """Tahrif Zaten zincir bütünlük kapısına çarpar (imzaya gelmeden)."""
        data = json.loads(signed["chain_file"].read_text(encoding="utf-8"))
        data[1]["payload"]["refused"] = not data[1]["payload"]["refused"]
        signed["chain_file"].write_text(json.dumps(data), encoding="utf-8")
        out = verify_chain_file(
            str(signed["chain_file"]), str(signed["chain_file"]) + ".sig",
            signed["kp"]["public_key_path"],
        )
        assert out.valid is False
        assert "bütünlük" in out.reason

    def test_append_after_sign_invalidates_head_match(self, signed):
        """Append-only tasarım: yeni kayıt imzayı bozmaz ama head kaydı ister."""
        chain = EvidenceChain.from_json(signed["chain_file"].read_text(encoding="utf-8"))
        chain.append("report", {"note": "imza-sonrası ek kayıt"})
        signed["chain_file"].write_text(chain.to_json(), encoding="utf-8")
        out = verify_chain_file(
            str(signed["chain_file"]), str(signed["chain_file"]) + ".sig",
            signed["kp"]["public_key_path"],
        )
        assert out.valid is False
        assert "head uyuşmuyor" in out.reason

    def test_wrong_pubkey_detected(self, signed, tmp_path):
        other = generate_keypair("saldırgan", str(tmp_path))
        out = verify_chain_file(
            str(signed["chain_file"]), str(signed["chain_file"]) + ".sig",
            other["public_key_path"],
        )
        assert out.valid is False
        assert "imza GEÇERSİZ" in out.reason

    def test_sig_file_schema_roundtrip(self, signed):
        raw = json.loads(
            signed["chain_file"].with_name(signed["chain_file"].name + ".sig").read_text()
        )
        rec = SignatureRecord.model_validate(raw)
        assert rec.magic == "dumen-ed25519-chain-sig-v1"
        assert rec.chain_length == 4

    def test_signing_refuses_broken_chain(self, tmp_path):
        kp = generate_keypair("g", str(tmp_path))
        broken = tmp_path / "broken.json"
        data = json.loads(_chain_with(2).to_json())
        data[0]["prev_hash"] = "f" * 64  # genesis çalımı
        broken.write_text(json.dumps(data), encoding="utf-8")
        with pytest.raises(ValueError, match="bütünlük doğrulamasından geçemedi"):
            sign_chain_file(str(broken), kp["private_key_path"], "x")


class TestHonestDegradation:
    def test_private_key_wrong_type_rejected(self, tmp_path):
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.primitives.serialization import (
            Encoding,
            NoEncryption,
            PrivateFormat,
        )
        bogus = tmp_path / "rsa.key"
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        bogus.write_bytes(key.private_bytes(Encoding.PEM, PrivateFormat.PKCS8, NoEncryption()))
        cf = tmp_path / "c.json"
        cf.write_text(_chain_with(1).to_json(), encoding="utf-8")
        with pytest.raises(ValueError, match="Ed25519 GİZLİ"):
            sign_chain_file(str(cf), str(bogus), "x")

    def test_public_key_wrong_type_rejected(self, tmp_path):
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
        bogus = tmp_path / "rsa.pub"
        bogus.write_bytes(rsa.generate_private_key(
            public_exponent=65537, key_size=2048).public_key().public_bytes(
            Encoding.PEM, PublicFormat.SubjectPublicKeyInfo))
        kp = generate_keypair("k2", str(tmp_path))
        chain = _chain_with(1)
        cf = tmp_path / "c.json"
        cf.write_text(chain.to_json(), encoding="utf-8")
        sign_chain_file(str(cf), kp["private_key_path"], "s")
        with pytest.raises(ValueError, match="Ed25519 PUBLIC"):
            verify_chain_file(str(cf), str(cf) + ".sig", str(bogus))
