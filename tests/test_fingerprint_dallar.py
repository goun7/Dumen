"""dal-kesen test: signing._fingerprint + _load_private + _load_public.

ORTAM-ANATOMI
-------------
_fingerprint(pub) -> "ed25519:" + sha256(public_bytes(Raw,Raw)).hexdigest()[:16]
  - ham 32-bayt Ed25519 acik-anahtar uzerinden SHA-256, ilk 16 hex
  - cikti SABIT: ayni anahtar icin her zaman ayni 24 karakter ("ed25519:" + 16 hex)

_load_private(path) -> serialization.load_pem_private_key(data, password=None)
  + isinstance kontrolu: Ed25519PrivateKey DEGILse ValueError("dosya bir Ed25519 GİZLİ anahtarı değil.")
_load_public(path)  -> serialization.load_pem_public_key(data)
  + isinstance kontrolu: Ed25519PublicKey DEGILse ValueError("dosya bir Ed25519 PUBLIC anahtarı değil.")

ORTAM-OGRENDILER
----------------
(1) _fingerprint DETERMINISTIK — ayni pub icin byte-birebir ayni cikti (anahtar
    canli olmadigi icin safe in-memory; generate_keypair cagirmaya GEREK YOK).
(2) 100 rastgele anahtar-ciftinde fingerprint CARPISMASI YOK (16 hex = 64 bit).
(3) _fingerprint ham-bayt uzerindendir: ayni 32 bayti yeniden insa edilen
    anahtar ayni parmak-izini verir (public_bytes(Raw,Raw) gidiş-dönüş).
(4) generate_keypair'in dondurdugu "fingerprint" ALANI _fingerprint(pub) ile
    birebir ayni (uretim kaynagi tek; test bunu kanitlar).
(5) _load_private: PUB dosyasini PRIV olarak yuklemek ValueError verir AMA
    mesaj serialize kitapligindandir ("Valid PEM but no BEGIN/END delimiters
    for a private key found") — bizim Turkce isinstance mesajimiz DEGIL,
    cunku load_pem_private_key ONCE calisir (kapsam-disi davranis, characterization).
(6) _load_public: PRIV dosyasini PUB olarak yuklemek ValueError verir, mesaj
    yine kitapligin ("no BEGIN PUBLIC KEY/END PUBLIC KEY delimiters").
(7) RSA anahtari -> isinstance kontrolu DEVREYE GIRER ve Turkce mesaj verilir
    (kitaplik RSA PEM'i legal olarak yukler, sonradan reddederiz).
(8) Sifreli (BestAvailableEncryption) PKCS8 anahtar + password=None -> TypeError
    ("Password was not given but private key is encrypted") — load hatasi,
    isinstance ulasilamaz (uretim quirk; characterization).
(9) Cop dosya -> ValueError (PEK parse hatasi); OLMAYAN dosya -> FileNotFoundError.
"""
import hashlib
import os
import sys

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519, rsa

sys.path.insert(0, ".")
sys.path.insert(0, "src")

from dumen.reports.signing import (  # noqa: E402
    _fingerprint,
    _load_private,
    _load_public,
    generate_keypair,
)

_FP_RE = "ed25519:[0-9a-f]{16}"


# ---------------------------------------------------------------- helpers
def _gen_keypair(tmp_path, name="k"):
    return generate_keypair(name, str(tmp_path))


def _pub_from_raw(raw: bytes):
    return ed25519.Ed25519PublicKey.from_public_bytes(raw)


# ================================================================ _fingerprint
class TestFingerprintFormat:
    """fmt ve sabitlik dal'lari."""

    def test_format_prefix(self):
        pub = ed25519.Ed25519PrivateKey.generate().public_key()
        assert _fingerprint(pub).startswith("ed25519:")

    def test_format_total_length_24(self):
        pub = ed25519.Ed25519PrivateKey.generate().public_key()
        assert len(_fingerprint(pub)) == len("ed25519:") + 16

    def test_format_hex_regex(self):
        import re

        pub = ed25519.Ed25519PrivateKey.generate().public_key()
        assert re.fullmatch(_FP_RE, _fingerprint(pub))

    def test_hex_part_is_16_chars(self):
        pub = ed25519.Ed25519PrivateKey.generate().public_key()
        assert len(_fingerprint(pub).split(":", 1)[1]) == 16

    def test_no_uppercase_in_hex(self):
        pub = ed25519.Ed25519PrivateKey.generate().public_key()
        assert _fingerprint(pub)[9:] == _fingerprint(pub)[9:].lower()

    @pytest.mark.parametrize("name", ["a", "signer-1", "test_key"])
    def test_matches_generate_keypair_field(self, tmp_path, name):
        """generate_keypair['fingerprint'] == _fingerprint(pub) — tek kaynak."""
        info = generate_keypair(name, str(tmp_path))
        pub = _load_public(info["public_key_path"])
        assert info["fingerprint"] == _fingerprint(pub)

    def test_prefix_literal_not_configurable(self):
        """_MAGIC'ten bagimsiz: sabit 'ed25519:' oneki."""
        pub = ed25519.Ed25519PrivateKey.generate().public_key()
        assert _fingerprint(pub).split(":")[0] == "ed25519"


class TestFingerprintDeterminism:
    def test_same_key_called_twice_identical(self):
        pub = ed25519.Ed25519PrivateKey.generate().public_key()
        assert _fingerprint(pub) == _fingerprint(pub)

    def test_same_key_called_many_times_identical(self):
        pub = ed25519.Ed25519PrivateKey.generate().public_key()
        fps = {_fingerprint(pub) for _ in range(50)}
        assert len(fps) == 1

    def test_raw_reconstruction_gives_same_fingerprint(self):
        """public_bytes(Raw,Raw) gidiş-dönüşü — ayni ham bayt ayni cikti."""
        pub = ed25519.Ed25519PrivateKey.generate().public_key()
        raw = pub.public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
        rebuilt = _pub_from_raw(raw)
        assert _fingerprint(rebuilt) == _fingerprint(pub)

    def test_two_independent_keys_differ(self):
        a = ed25519.Ed25519PrivateKey.generate().public_key()
        b = ed25519.Ed25519PrivateKey.generate().public_key()
        assert _fingerprint(a) != _fingerprint(b)

    def test_private_key_public_key_same_fingerprint(self):
        """priv.public_key() ile dosyadaki pub ayni parmak-izi."""
        priv = ed25519.Ed25519PrivateKey.generate()
        fp_priv = _fingerprint(priv.public_key())
        raw = priv.public_key().public_bytes(
            serialization.Encoding.Raw, serialization.PublicFormat.Raw
        )
        assert _fingerprint(_pub_from_raw(raw)) == fp_priv

    def test_hundred_keys_no_collision(self):
        pubs = [ed25519.Ed25519PrivateKey.generate().public_key() for _ in range(100)]
        fps = {_fingerprint(p) for p in pubs}
        assert len(fps) == 100

    def test_fingerprint_matches_manual_sha256_truncation(self):
        """Spec: sha256(raw)[:16] — elle hesapla, karsilastir."""
        pub = ed25519.Ed25519PrivateKey.generate().public_key()
        raw = pub.public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
        expected = "ed25519:" + hashlib.sha256(raw).hexdigest()[:16]
        assert _fingerprint(pub) == expected

    def test_fingerprint_of_known_static_key(self):
        """Deterministik sabit-anahtar vektoru (from_public_bytes)."""
        raw = bytes(range(32))
        pub = _pub_from_raw(raw)
        raw_fp = "ed25519:" + hashlib.sha256(raw).hexdigest()[:16]
        assert _fingerprint(pub) == raw_fp

    def test_known_keypair_files_stable_fingerprint(self, tmp_path):
        info = _gen_keypair(tmp_path)
        pub = _load_public(info["public_key_path"])
        first = _fingerprint(pub)
        # ayni dosyayi tekrar yukle — ayni sonuc
        pub2 = _load_public(info["public_key_path"])
        assert _fingerprint(pub2) == first

    def test_different_keys_same_prefix_format(self):
        a = ed25519.Ed25519PrivateKey.generate().public_key()
        b = ed25519.Ed25519PrivateKey.generate().public_key()
        fa, fb = _fingerprint(a), _fingerprint(b)
        assert fa != fb
        assert fa[:8] == fb[:8] == "ed25519:"


# ================================================================ _load_private
class TestLoadPrivate:
    def test_valid_ed25519_returns_private_key(self, tmp_path):
        info = _gen_keypair(tmp_path)
        key = _load_private(info["private_key_path"])
        assert isinstance(key, ed25519.Ed25519PrivateKey)

    def test_valid_key_signs_and_verifies(self, tmp_path):
        info = _gen_keypair(tmp_path)
        key = _load_private(info["private_key_path"])
        sig = key.sign(b"mesaj")
        key.public_key().verify(sig, b"mesaj")

    def test_loaded_private_public_key_fingerprint(self, tmp_path):
        info = _gen_keypair(tmp_path)
        key = _load_private(info["private_key_path"])
        assert _fingerprint(key.public_key()) == info["fingerprint"]

    def test_public_file_as_private_raises_value_error(self, tmp_path):
        """ORTAM-OGRENDI (5): ValueError kitaplik mesajiyla gelir."""
        info = _gen_keypair(tmp_path)
        with pytest.raises(ValueError):
            _load_private(info["public_key_path"])

    def test_missing_file_raises_file_not_found(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            _load_private(str(tmp_path / "yok.key"))

    def test_garbage_file_raises_value_error(self, tmp_path):
        p = tmp_path / "cop.key"
        p.write_bytes(b"bu bir anahtar degil")
        with pytest.raises(ValueError):
            _load_private(str(p))

    def test_empty_file_raises_value_error(self, tmp_path):
        p = tmp_path / "bos.key"
        p.write_bytes(b"")
        with pytest.raises(ValueError):
            _load_private(str(p))

    def test_rsa_private_key_rejected_with_turkish_message(self, tmp_path):
        """ORTAM-OGRENDI (7): RSA legal PEM ama isinstance reddeder."""
        rk = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        p = tmp_path / "rsa.key"
        p.write_bytes(
            rk.private_bytes(
                serialization.Encoding.PEM,
                serialization.PrivateFormat.PKCS8,
                serialization.NoEncryption(),
            )
        )
        with pytest.raises(ValueError, match="Ed25519"):
            _load_private(str(p))

    def test_encrypted_key_without_password_raises_type_error(self, tmp_path):
        """ORTAM-OGRENDI (8): BestAvailableEncryption + password=None -> TypeError."""
        blob = ed25519.Ed25519PrivateKey.generate().private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.BestAvailableEncryption(b"sifre"),
        )
        p = tmp_path / "enc.key"
        p.write_bytes(blob)
        with pytest.raises(TypeError):
            _load_private(str(p))

    def test_directory_path_raises(self, tmp_path):
        with pytest.raises(IsADirectoryError):
            _load_private(str(tmp_path))


# ================================================================ _load_public
class TestLoadPublic:
    def test_valid_ed25519_returns_public_key(self, tmp_path):
        info = _gen_keypair(tmp_path)
        key = _load_public(info["public_key_path"])
        assert isinstance(key, ed25519.Ed25519PublicKey)

    def test_loaded_public_matches_fingerprint(self, tmp_path):
        info = _gen_keypair(tmp_path)
        key = _load_public(info["public_key_path"])
        assert _fingerprint(key) == info["fingerprint"]

    def test_loaded_public_verifies_signature(self, tmp_path):
        info = _gen_keypair(tmp_path)
        priv = _load_private(info["private_key_path"])
        pub = _load_public(info["public_key_path"])
        sig = priv.sign(b"x")
        pub.verify(sig, b"x")

    def test_private_file_as_public_raises_value_error(self, tmp_path):
        """ORTAM-OGRENDI (6): ValueError kitaplik mesajiyla gelir."""
        info = _gen_keypair(tmp_path)
        with pytest.raises(ValueError):
            _load_public(info["private_key_path"])

    def test_missing_file_raises_file_not_found(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            _load_public(str(tmp_path / "yok.pub"))

    def test_garbage_file_raises_value_error(self, tmp_path):
        p = tmp_path / "cop.pub"
        p.write_bytes(b"cop")
        with pytest.raises(ValueError):
            _load_public(str(p))

    def test_rsa_public_key_rejected_with_turkish_message(self, tmp_path):
        rk = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        p = tmp_path / "rsa.pub"
        p.write_bytes(
            rk.public_key().public_bytes(
                serialization.Encoding.PEM,
                serialization.PublicFormat.SubjectPublicKeyInfo,
            )
        )
        with pytest.raises(ValueError, match="Ed25519"):
            _load_public(str(p))

    def test_directory_path_raises(self, tmp_path):
        with pytest.raises(IsADirectoryError):
            _load_public(str(tmp_path))


# ================================================================ generate_keypair interplay
class TestKeypairFingerprintContract:
    """generate_keypair + _fingerprint + _load_* sozlesmesi."""

    def test_generated_keypair_files_load_and_match(self, tmp_path):
        info = _gen_keypair(tmp_path)
        priv = _load_private(info["private_key_path"])
        pub = _load_public(info["public_key_path"])
        assert priv.public_key().public_bytes(
            serialization.Encoding.Raw, serialization.PublicFormat.Raw
        ) == pub.public_bytes(
            serialization.Encoding.Raw, serialization.PublicFormat.Raw
        )
        assert _fingerprint(pub) == info["fingerprint"]

    def test_keypair_files_created_with_expected_names(self, tmp_path):
        info = generate_keypair("denetci", str(tmp_path))
        assert os.path.basename(info["private_key_path"]) == "denetci.key"
        assert os.path.basename(info["public_key_path"]) == "denetci.pub"

    def test_two_keypairs_distinct_fingerprints(self, tmp_path):
        a = generate_keypair("a", str(tmp_path))
        b = generate_keypair("b", str(tmp_path))
        assert a["fingerprint"] != b["fingerprint"]
