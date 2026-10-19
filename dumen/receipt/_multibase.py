#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""did:key multibase kodlamasi — kok'un kok_receipt_verify_en.py'sindeki
elle-yazilmis base58btc'nin uretici-tarafi ( ayni alfabe, ayni multicodec).

Uretici ve verifier ayri dosyalarda: verifier kok'un, uretici dumen'in.
Ikisi de ayni base58btc alfabe'yi ( Bitcoin, no-checksum) ve ayni
multicodec-butunu ( 0xED 0x01) kullanir — did:key:z... ciktilari
bayt-bayt ayni olmak zorundadir.
"""

B58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
MULTICODEC_ED25519_PUB = bytes([0xED, 0x01])


def b58_encode(data: bytes) -> str:
    digits = []
    for byte in data:
        carry = byte
        for i in range(len(digits)):
            carry += digits[i] * 256
            digits[i] = carry % 58
            carry //= 58
        while carry:
            digits.append(carry % 58)
            carry //= 58
    # leading zeros -> '1'
    n_leading = len(data) - len(data.lstrip(b"\x00"))
    return "1" * n_leading + "".join(B58_ALPHABET[d] for d in reversed(digits))


def multibase_encode(data: bytes) -> str:
    """multibase 'z' oneki + base58btc ( did:key formati)."""
    return "z" + b58_encode(data)
