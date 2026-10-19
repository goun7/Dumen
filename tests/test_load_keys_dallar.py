"""77-Dumen signing._load_private + _load_public dal-kesen testleri (LEED).

Kural-1: mevcut dosyalara DOKUNULMADI, SADECE bu yeni dosya eklendi.
Kural-4: saf in-memory (cryptography anahtarlari tmp_path PEM — dis cagri YOK).
Ed25519 anahtar yukleme + tur-dogrulama.
"""
import sys

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519, x25519

sys.path.insert(0, ".")
from dumen.reports.signing import _load_private, _load_public  # noqa: E402


def _pem_priv(tmp_path, key=None, ad="k.pem"):
    key = key or ed25519.Ed25519PrivateKey.generate()
    p = tmp_path / ad
    p.write_bytes(key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()))
    return p


def _pem_pub(tmp_path, key=None, ad="k.pub"):
    key = key or ed25519.Ed25519PrivateKey.generate().public_key()
    p = tmp_path / ad
    p.write_bytes(key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo))
    return p


# == _load_private: temel ==============================================================================

def test_priv_doner(tmp_path):
    k = _load_private(str(_pem_priv(tmp_path)))
    assert isinstance(k, ed25519.Ed25519PrivateKey)


def test_priv_anahtar_uyumu(tmp_path):
    """ORTAM: ayni PEM ayni anahtari verir (public_bytes karsilastirma)."""
    kaynak = ed25519.Ed25519PrivateKey.generate()
    p = _pem_priv(tmp_path, kaynak)
    yuklenen = _load_private(str(p))
    assert (yuklenen.public_key().public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw)
        == kaynak.public_key().public_bytes(
            serialization.Encoding.Raw, serialization.PublicFormat.Raw))


def test_priv_imzalama_calisir(tmp_path):
    """ORTAM: yuklenen anahtar imzalayabilir."""
    k = _load_private(str(_pem_priv(tmp_path)))
    imza = k.sign(b"mesaj")
    assert len(imza) == 64


def test_priv_str_path(tmp_path):
    """ORTAM: path str olarak verilir."""
    assert isinstance(_load_private(str(_pem_priv(tmp_path))),
                      ed25519.Ed25519PrivateKey)


# == _load_private: hata ===============================================================================

def test_priv_dosya_yok(tmp_path):
    with pytest.raises(Exception):
        _load_private(str(tmp_path / "yok.pem"))


def test_priv_bos_dosya(tmp_path):
    p = tmp_path / "b.pem"
    p.write_bytes(b"")
    with pytest.raises(Exception):
        _load_private(str(p))


def test_priv_gecersiz_pem(tmp_path):
    p = tmp_path / "g.pem"
    p.write_bytes(b"NOT A PEM")
    with pytest.raises(Exception):
        _load_private(str(p))


def test_priv_yanlis_tur(tmp_path):
    """ORTAM: x25519 anahtari -> ValueError (Ed25519 DEGIL!)."""
    xk = x25519.X25519PrivateKey.generate()
    p = tmp_path / "x.pem"
    p.write_bytes(xk.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption()))
    with pytest.raises(ValueError):
        _load_private(str(p))


def test_priv_public_key_dosya(tmp_path):
    """ORTAM: public PEM -> private loader hata."""
    p = _pem_pub(tmp_path, ad="pub_as_priv.pem")
    with pytest.raises(Exception):
        _load_private(str(p))


def test_priv_sifreli(tmp_path):
    """ORTAM: sifreli PEM (NoEncryption bekleniyor) -> hata."""
    kaynak = ed25519.Ed25519PrivateKey.generate()
    p = tmp_path / "sifre.pem"
    p.write_bytes(kaynak.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.BestAvailableEncryption(b"sifre1234")))
    with pytest.raises(Exception):
        _load_private(str(p))


def test_priv_dizin(tmp_path):
    with pytest.raises(Exception):
        _load_private(str(tmp_path))


# == _load_public: temel ===============================================================================

def test_pub_doner(tmp_path):
    k = _load_public(str(_pem_pub(tmp_path)))
    assert isinstance(k, ed25519.Ed25519PublicKey)


def test_pub_anahtar_uyumu(tmp_path):
    kaynak = ed25519.Ed25519PrivateKey.generate()
    p = _pem_pub(tmp_path, kaynak.public_key())
    yuklenen = _load_public(str(p))
    assert (yuklenen.public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw)
        == kaynak.public_key().public_bytes(
            serialization.Encoding.Raw, serialization.PublicFormat.Raw))


def test_pub_dogrulama_calisir(tmp_path):
    """ORTAM: yuklenen public anahtar imzayi dogrular."""
    kaynak = ed25519.Ed25519PrivateKey.generate()
    pub = kaynak.public_key()
    imza = kaynak.sign(b"mesaj")
    p = _pem_pub(tmp_path, pub)
    yuklenen = _load_public(str(p))
    yuklenen.verify(imza, b"mesaj")  # hata atmaz


def test_pub_dogrulama_yanlis(tmp_path):
    pub = ed25519.Ed25519PrivateKey.generate().public_key()
    p = _pem_pub(tmp_path, pub)
    yuklenen = _load_public(str(p))
    with pytest.raises(Exception):
        yuklenen.verify(b"x" * 64, b"mesaj")


# == _load_public: hata ===============================================================================

def test_pub_dosya_yok(tmp_path):
    with pytest.raises(Exception):
        _load_public(str(tmp_path / "yok.pub"))


def test_pub_bos_dosya(tmp_path):
    p = tmp_path / "b.pub"
    p.write_bytes(b"")
    with pytest.raises(Exception):
        _load_public(str(p))


def test_pub_gecersiz_pem(tmp_path):
    p = tmp_path / "g.pub"
    p.write_bytes(b"NOT A PEM")
    with pytest.raises(Exception):
        _load_public(str(p))


def test_pub_priv_key_dosya(tmp_path):
    """ORTAM: private PEM -> public loader hata."""
    p = _pem_priv(tmp_path, ad="priv_as_pub.pem")
    with pytest.raises(Exception):
        _load_public(str(p))


def test_pub_yanlis_tur(tmp_path):
    """ORTAM: x25519 public -> ValueError (Ed25519 DEGIL!)."""
    xk = x25519.X25519PrivateKey.generate()
    p = tmp_path / "x.pub"
    p.write_bytes(xk.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo))
    with pytest.raises(ValueError):
        _load_public(str(p))


def test_pub_dizin(tmp_path):
    with pytest.raises(Exception):
        _load_public(str(tmp_path))


# == cesitli ===========================================================================================

def test_anahtar_cifti(tmp_path):
    """ORTAM: private + public ayni anahtardan uretilirse eslesir."""
    kaynak = ed25519.Ed25519PrivateKey.generate()
    priv = _load_private(str(_pem_priv(tmp_path, kaynak, "a.pem")))
    pub = _load_public(str(_pem_pub(tmp_path, kaynak.public_key(), "a.pub")))
    imza = priv.sign(b"x")
    pub.verify(imza, b"x")


def test_farkli_anahtarlar_eslesmez(tmp_path):
    """ORTAM: farkli anahtarlarin raw-bytes'lari farkli."""
    a = _load_private(str(_pem_priv(tmp_path, ad="a.pem")))
    b = _load_private(str(_pem_priv(tmp_path, ad="b.pem")))
    ra = a.public_key().public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    rb = b.public_key().public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    assert ra != rb


def test_repeatable(tmp_path):
    p = str(_pem_priv(tmp_path))
    a = _load_private(p).public_key().public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    b = _load_private(p).public_key().public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    assert a == b


def test_uzun_path(tmp_path):
    derin = tmp_path
    for i in range(5):
        derin = derin / f"d{i}"
        derin.mkdir()
    p = _pem_priv(tmp_path, ad="k.pem")
    import shutil
    hedef = derin / "k.pem"
    shutil.copy(p, hedef)
    assert isinstance(_load_private(str(hedef)), ed25519.Ed25519PrivateKey)


def test_imza_uzunlugu(tmp_path):
    """ORTAM: Ed25519 imza 64-byte."""
    k = _load_private(str(_pem_priv(tmp_path)))
    assert len(k.sign(b"")) == 64


@pytest.mark.parametrize("ad", ["k.pem", "k.pem.pem", "turkçe-anahtar.pem",
                                "a b c.pem"])
def test_path_matrix(tmp_path, ad):
    assert isinstance(_load_private(str(_pem_priv(tmp_path, ad=ad))),
                      ed25519.Ed25519PrivateKey)


@pytest.mark.parametrize("ad", ["k.pub", "public.pem", "türkçe.pub"])
def test_pub_path_matrix(tmp_path, ad):
    assert isinstance(_load_public(str(_pem_pub(tmp_path, ad=ad))),
                      ed25519.Ed25519PublicKey)


@pytest.mark.parametrize("mesaj", [b"", b"x", "DÜMEN".encode(), b"\x00\x01", b"a" * 1000])
def test_imza_matrix(tmp_path, mesaj):
    """ORTAM: her mesaj-boyutu icin imza 64-byte."""
    k = _load_private(str(_pem_priv(tmp_path)))
    assert len(k.sign(mesaj)) == 64
