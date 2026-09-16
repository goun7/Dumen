"""Ed25519 zincir-kanıt imzalama — kimlik = anahtar muhafazası (honest boundary).

Bir denetim raporunun SHA-256 kanıt zinciri bütünlüğü kendi başına *kendi
kendine tutarlılık* kanıtlar; bu modül üstüne **kaynak bağlar**: imzalayan
anahtarın açık (public) parmak-izi, dosyanın kim tarafından mühürlendiğini
kriptografik olarak bağlar.

Kapsam dışı (bilinçli): eIDAS/nitelikli elektronik imza DEĞİLDİR — kimlik
iddiası anahtar muhafazasına dayanır ("kimlik = anahtarı taşıyan"). Kurumsal
hukuki delil zinciri için harici zaman-mühürü (RFC 3161 TSA) veya nitelikli
CAt eklenmesi gerekir; bu, README ve SECURITY'de aynı dürüstlükle yazar.
"""
from __future__ import annotations

import hashlib
import json
import os
import time
from typing import Dict, Optional

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from pydantic import BaseModel

from .evidence_chain import EvidenceChain

_MAGIC = "dumen-ed25519-chain-sig-v1"


class SignatureRecord(BaseModel):
    """`.sig` dosyasının şeması — imza + bağlam, tek JSON."""
    magic: str = _MAGIC
    head_hash: str
    signature_hex: str
    pubkey_fingerprint: str
    signer_name: str
    signed_at: str
    chain_length: int


class VerifyOutcome(BaseModel):
    """Bağımsız doğrulama sonucu — her başarısızlık ayrı nedeniWith taşır."""
    valid: bool
    reason: Optional[str] = None
    head_hash: str = ""
    pubkey_fingerprint: str = ""
    signer_name: str = ""
    signed_at: str = ""


def _fingerprint(pub: Ed25519PublicKey) -> str:
    raw = pub.public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw
    )
    return "ed25519:" + hashlib.sha256(raw).hexdigest()[:16]


def generate_keypair(name: str, out_dir: str, overwrite: bool = False) -> Dict[str, str]:
    """Yeni Ed25519 çifti üretir: <name>.key (0600) + <name>.pub.

    Returns: {private_key_path, public_key_path, fingerprint}
    Raises: FileExistsError — mevcut anahtar SESSİZCE ezilmez.
    """
    key_path = os.path.join(out_dir, f"{name}.key")
    pub_path = os.path.join(out_dir, f"{name}.pub")
    if (os.path.exists(key_path) or os.path.exists(pub_path)) and not overwrite:
        raise FileExistsError(
            f"{name}.key/.pub zaten var — ezilmek için --force gerekir "
            "(mevcut imzalar bu anahtara bağlı; sessiz rotasyon yasak)."
        )
    os.makedirs(out_dir, exist_ok=True)
    priv = Ed25519PrivateKey.generate()
    pub = priv.public_key()
    key_blob = priv.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )
    pub_blob = pub.public_bytes(
        serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
    )
    fd = os.open(key_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "wb") as f:
        f.write(key_blob)
    with open(pub_path, "wb") as f:
        f.write(pub_blob)
    return {
        "private_key_path": key_path,
        "public_key_path": pub_path,
        "fingerprint": _fingerprint(pub),
    }


def _load_private(path: str) -> Ed25519PrivateKey:
    with open(path, "rb") as f:
        key = serialization.load_pem_private_key(f.read(), password=None)
    if not isinstance(key, Ed25519PrivateKey):
        raise ValueError("dosya bir Ed25519 GİZLİ anahtarı değil.")
    return key


def _load_public(path: str) -> Ed25519PublicKey:
    with open(path, "rb") as f:
        key = serialization.load_pem_public_key(f.read())
    if not isinstance(key, Ed25519PublicKey):
        raise ValueError("dosya bir Ed25519 PUBLIC anahtarı değil.")
    return key


def sign_chain_file(chain_path: str, key_path: str,
                    signer_name: str, sig_path: Optional[str] = None) -> SignatureRecord:
    """Zincir DOSYASINI imzalar: yükleme (bütünlük kapısı) → head → imza.

    from_json yükleme anında tüm zinciri yeniden-hesapla doğrular; bozuk
    zincir imzalanamaz (ValueError). İmza head_hash üzerinedir — sonraki
    append'ler imzayı bozmaz, head kaydı yeni imza ister (append-only tasarım).
    """
    with open(chain_path, "r", encoding="utf-8") as f:
        chain = EvidenceChain.from_json(f.read())  # bütünlük kapısı
    head = chain.head_hash()
    priv = _load_private(key_path)
    pub = priv.public_key()
    sig = priv.sign(_MAGIC.encode("utf-8") + head.encode("ascii"))
    record = SignatureRecord(
        head_hash=head,
        signature_hex=sig.hex(),
        pubkey_fingerprint=_fingerprint(pub),
        signer_name=signer_name,
        signed_at=time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        chain_length=len(chain),
    )
    target = sig_path or (chain_path + ".sig")
    with open(target, "w", encoding="utf-8") as f:
        json.dump(record.model_dump(), f, indent=2, ensure_ascii=False)
    return record


def verify_chain_file(chain_path: str, sig_path: str,
                      pubkey_path: str) -> VerifyOutcome:
    """Üçlü doğrulama: (1) zincir kendi içinde sağlam, (2) imza bu anahtardan,
    (3) imzalanan head = bugünkü head. Her başarısızlık AYRIK gerekçeyle."""
    with open(sig_path, "r", encoding="utf-8") as f:
        rec = SignatureRecord.model_validate(json.load(f))
    pub = _load_public(pubkey_path)
    fp = _fingerprint(pub)

    try:
        with open(chain_path, "r", encoding="utf-8") as f:
            chain = EvidenceChain.from_json(f.read())
    except ValueError as exc:
        return VerifyOutcome(valid=False, reason=f"zincir bütünlüğü bozuk: {exc}",
                             head_hash="", pubkey_fingerprint=fp,
                             signer_name=rec.signer_name, signed_at=rec.signed_at)

    head = chain.head_hash()
    if head != rec.head_hash:
        return VerifyOutcome(valid=False,
                             reason=f"head uyuşmuyor — imza {rec.head_hash[:16]}… "
                                    f"üzerine, dosyanın bugünkü head'i {head[:16]}… "
                                    "(zincir imzadan sonra değişti ya da dosya ikame)",
                             head_hash=head, pubkey_fingerprint=fp,
                             signer_name=rec.signer_name, signed_at=rec.signed_at)
    try:
        pub.verify(bytes.fromhex(rec.signature_hex),
                   _MAGIC.encode("utf-8") + head.encode("ascii"))
    except InvalidSignature:
        return VerifyOutcome(valid=False,
                             reason="imza GEÇERSİZ — public anahtar bu imzayı "
                                    "üretmedi (anahtar yanlış ya da .sig tahrif).",
                             head_hash=head, pubkey_fingerprint=fp,
                             signer_name=rec.signer_name, signed_at=rec.signed_at)
    return VerifyOutcome(valid=True, head_hash=head, pubkey_fingerprint=rec.pubkey_fingerprint,
                         signer_name=rec.signer_name, signed_at=rec.signed_at)
