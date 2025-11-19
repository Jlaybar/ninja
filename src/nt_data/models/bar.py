"""Modelo OHLC basico."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class BarData:
    time: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    instrument: str
    timeframe: str


__all__ = ["BarData"]