"""
dumen.reports.evidence_chain
=============================
Kanıt Zinciri (Evidence Chain) — SHA-256 Hash-Chain Kanıt Deposu:
Denetim zincirinin her aşaması (madencilik, değerlendirme, yönlendirme, rapor)
append-only kayıtlara yazılır; her kayıt öncekinin özetini (prev_hash) taşır.
Zincirin herhangi bir noktasındaki geri-dönüşüm-safra değişikliği sonraki tüm
hash'leri kırar → kanıt takma (evidence tampering) mekanik olarak tespit edilir.

Yasal bağlam: AI Office denetimlerinde sunulan teknik dokümantasyonun
bütünlüğü iddiası, sağlayıcı tarafında takip edilebilir kanıt kaydını gerektirir.
"""

from __future__ import annotations

import hashlib
import json
import time
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, ValidationError


class ChainEntry(BaseModel):
    """Zincirdeki tek kanıt kaydı."""
    index: int = Field(ge=0, description="Sıra numarası (genesis=0)")
    timestamp: str = Field(description="UTC kayıt zamanı")
    stage: str = Field(description="Kanıt aşaması: mining/evaluation/steering/report/dossier/incident")
    payload: Dict[str, Any] = Field(description="Aşamaya özgü kanıt verisi")
    prev_hash: str = Field(description="Önceki kaydın SHA-256 özeti (genesis için 64 adet '0')")
    entry_hash: str = Field(description="Bu kaydın SHA-256 özeti")


class ChainVerification(BaseModel):
    """Zincir bütünlük doğrulama sonucu."""
    is_valid: bool
    length: int
    first_broken_index: Optional[int] = Field(
        default=None,
        description="Geçersizliğin ilk tespit edildiği kayıt (None = zincir sağlam)",
    )
    break_reason: Optional[str] = None
    genesis_present: bool
    head_hash: str = Field(default="", description="Zincir başının (son kaydın) özeti")


class EvidenceChain:
    """
    Append-only SHA-256 kanıt zinciri. Kayıt ekleme hızlıdır; doğrulama
    tüm zinciri yeniden hesaplar (tam-yeniden-hesaplama modeli).
    """

    GENESIS_PREV = "0" * 64

    def __init__(self) -> None:
        self._entries: List[ChainEntry] = []

    # ------------------------------------------------------------------
    # Kayıt ekleme
    # ------------------------------------------------------------------

    @staticmethod
    def _hash_entry(index: int, timestamp: str, stage: str, payload: Dict[str, Any], prev_hash: str) -> str:
        """Kayıt özetini deterministik hesaplar (alan sırası sabit)."""
        canonical = json.dumps(
            {
                "index": index,
                "timestamp": timestamp,
                "stage": stage,
                "payload": payload,
                "prev_hash": prev_hash,
            },
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def append(self, stage: str, payload: Dict[str, Any]) -> ChainEntry:
        """
        Zincire yeni kanıt kaydı ekler.

        Args:
            stage: Kanıt aşaması (mining/evaluation/steering/report/dossier/incident).
            payload: Aşamaya özgü veri (JSON-serileştirilebilir olmalı).

        Returns:
            Eklenen ChainEntry.
        """
        if not stage:
            raise ValueError("stage boş olamaz.")
        try:
            json.dumps(payload, sort_keys=True)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"payload JSON-serileştirilebilir olmalı: {exc}") from exc

        if self._entries:
            prev_hash = self._entries[-1].entry_hash
            index = self._entries[-1].index + 1
        else:
            prev_hash = self.GENESIS_PREV
            index = 0

        timestamp = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
        entry_hash = self._hash_entry(index, timestamp, stage, payload, prev_hash)

        entry = ChainEntry(
            index=index,
            timestamp=timestamp,
            stage=stage,
            payload=payload,
            prev_hash=prev_hash,
            entry_hash=entry_hash,
        )
        self._entries.append(entry)
        return entry

    # ------------------------------------------------------------------
    # Okuma
    # ------------------------------------------------------------------

    def __len__(self) -> int:
        return len(self._entries)

    def get_entries(self) -> List[ChainEntry]:
        """Zincirin kopyasını döndürür (dışarıdan mutasyon engellenir)."""
        return list(self._entries)

    def head_hash(self) -> str:
        """Zincir başının özeti; boş zincir için genesis sabiti."""
        if not self._entries:
            return self.GENESIS_PREV
        return self._entries[-1].entry_hash

    def to_json(self) -> str:
        """Zincirin tam serileştirmesi (dosyaya saklama / mahkemede sunma)."""
        return json.dumps(
            [e.model_dump() for e in self._entries],
            indent=2,
            ensure_ascii=False,
        )

    @classmethod
    def from_json(cls, raw: str) -> "EvidenceChain":
        """Serileştirilmiş zinciri geri yükler ve bütünlüğünü DOĞRULAR."""
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Zincir serileştirmesi bozuk: {exc}") from exc
        chain = cls()
        try:
            chain._entries = [ChainEntry.model_validate(d) for d in data]
        except ValidationError as exc:
            # Şema-bozukluğu kanıt-bütünlüğü yetersizliğiyle AYNI kapıdır:
            # doğrulanamayan zincir kanıt değildir — tek tutarlı mesaj.
            raise ValueError(
                "Yüklenen zincir bütünlük doğrulamasından geçemedi "
                "(kayıt şeması bozuk). Kanıt kabul edilmez."
            ) from exc
        verification = chain.verify()
        if not verification.is_valid:
            broken = verification.first_broken_index
            raise ValueError(
                f"Yüklenen zincir bütünlük doğrulamasından geçemedi "
                f"(ilk kırık kayıt: {broken}). Kanıt kabul edilmez."
            )
        return chain

    # ------------------------------------------------------------------
    # Doğrulama
    # ------------------------------------------------------------------

    def verify(self) -> ChainVerification:
        """
        Tüm zinciri baştan sona yeniden hesaplayıp bütünlüğünü denetler:
        1. İlk kayıt genesis prev_hash'i taşır (64×'0').
        2. Her kaydın entry_hash'i kendi alanlarından yeniden hesaplanabilir.
        3. Her kaydın prev_hash'i önceki kaydın entry_hash'ine eşit.
        """
        if not self._entries:
            return ChainVerification(
                is_valid=True,
                length=0,
                genesis_present=False,
                head_hash=self.GENESIS_PREV,
            )

        prev = None
        for i, entry in enumerate(self._entries):
            # Koşul 1: genesis kontrolü
            if i == 0 and entry.prev_hash != self.GENESIS_PREV:
                return ChainVerification(
                    is_valid=False,
                    length=len(self._entries),
                    first_broken_index=0,
                    break_reason="Genesis kaydı prev_hash'i 64×'0' değil.",
                    genesis_present=False,
                    head_hash=self.head_hash(),
                )
            # Koşul 3: zincir bağlılığı
            if prev is not None and entry.prev_hash != prev.entry_hash:
                return ChainVerification(
                    is_valid=False,
                    length=len(self._entries),
                    first_broken_index=i,
                    break_reason=f"Kayıt {i} prev_hash'i kayıt {i-1} entry_hash'ine eşit değil (kopuk zincir).",
                    genesis_present=self._entries[0].prev_hash == self.GENESIS_PREV,
                    head_hash=self.head_hash(),
                )
            # Koşul 2: özet yeniden hesaplanabilirliği
            recomputed = self._hash_entry(
                entry.index, entry.timestamp, entry.stage, entry.payload, entry.prev_hash
            )
            if recomputed != entry.entry_hash:
                return ChainVerification(
                    is_valid=False,
                    length=len(self._entries),
                    first_broken_index=i,
                    break_reason=f"Kayıt {i} entry_hash'i yeniden hesaplanamıyor (içerik değiştirilmiş olabilir).",
                    genesis_present=self._entries[0].prev_hash == self.GENESIS_PREV,
                    head_hash=self.head_hash(),
                )
            prev = entry

        return ChainVerification(
            is_valid=True,
            length=len(self._entries),
            first_broken_index=None,
            break_reason=None,
            genesis_present=True,
            head_hash=self.head_hash(),
        )
