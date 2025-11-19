"""Modelo simplificado de libro de ordenes."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Tuple

PriceLevel = Tuple[float, int]


@dataclass(slots=True)
class OrderBookSnapshot:
    """Instantanea reducida del libro de ordenes."""

    time: datetime
    instrument: str
    bids: List[PriceLevel] = field(default_factory=list)
    asks: List[PriceLevel] = field(default_factory=list)


__all__ = ["OrderBookSnapshot", "PriceLevel"]