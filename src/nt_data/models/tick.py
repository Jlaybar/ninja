"""Modelos de datos intradia."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(slots=True)
class TickData:
    """Representa un tick individual."""

    time: datetime
    bid: Optional[float]
    ask: Optional[float]
    last: Optional[float]
    volume: Optional[int]
    instrument: str


__all__ = ["TickData"]