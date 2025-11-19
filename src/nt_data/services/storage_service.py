"""Servicio de persistencia mediante SQLite."""
from __future__ import annotations

import logging
import sqlite3
import threading
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import List, Sequence

from ..models.bar import BarData
from ..models.tick import TickData

logger = logging.getLogger(__name__)


class StorageBackend(ABC):
    @abstractmethod
    def save_ticks(self, ticks: Sequence[TickData]) -> int:
        raise NotImplementedError

    @abstractmethod
    def save_bars(self, bars: Sequence[BarData]) -> int:
        raise NotImplementedError

    @abstractmethod
    def fetch_ticks(
        self,
        instrument: str | None = None,
        start: datetime | None = None,
        end: datetime | None = None,
        limit: int | None = None,
    ) -> List[TickData]:
        raise NotImplementedError

    @abstractmethod
    def fetch_bars(
        self,
        instrument: str | None = None,
        timeframe: str | None = None,
        start: datetime | None = None,
        end: datetime | None = None,
        limit: int | None = None,
    ) -> List[BarData]:
        raise NotImplementedError


class SQLiteStorageBackend(StorageBackend):
    """Backend que persiste datos en archivos SQLite."""

    def __init__(self, db_path: str | Path) -> None:
        self._db_path = Path(db_path)
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path, check_same_thread=False)
        conn.execute("PRAGMA journal_mode=WAL;")
        return conn

    def _initialize(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS ticks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    instrument TEXT NOT NULL,
                    time TEXT NOT NULL,
                    bid REAL,
                    ask REAL,
                    last REAL,
                    volume INTEGER
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS bars (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    instrument TEXT NOT NULL,
                    timeframe TEXT NOT NULL,
                    time TEXT NOT NULL,
                    open REAL NOT NULL,
                    high REAL NOT NULL,
                    low REAL NOT NULL,
                    close REAL NOT NULL,
                    volume INTEGER NOT NULL
                )
                """
            )
            conn.commit()

    def save_ticks(self, ticks: Sequence[TickData]) -> int:
        if not ticks:
            return 0
        rows = [
            (
                tick.instrument,
                tick.time.isoformat(),
                tick.bid,
                tick.ask,
                tick.last,
                tick.volume,
            )
            for tick in ticks
        ]
        with self._lock, self._connect() as conn:
            conn.executemany(
                """
                INSERT INTO ticks (instrument, time, bid, ask, last, volume)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                rows,
            )
            conn.commit()
        return len(rows)

    def save_bars(self, bars: Sequence[BarData]) -> int:
        if not bars:
            return 0
        rows = [
            (
                bar.instrument,
                bar.timeframe,
                bar.time.isoformat(),
                bar.open,
                bar.high,
                bar.low,
                bar.close,
                bar.volume,
            )
            for bar in bars
        ]
        with self._lock, self._connect() as conn:
            conn.executemany(
                """
                INSERT INTO bars (
                    instrument, timeframe, time, open, high, low, close, volume
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                rows,
            )
            conn.commit()
        return len(rows)

    def fetch_ticks(
        self,
        instrument: str | None = None,
        start: datetime | None = None,
        end: datetime | None = None,
        limit: int | None = None,
    ) -> List[TickData]:
        query = "SELECT instrument, time, bid, ask, last, volume FROM ticks"
        clauses: list[str] = []
        params: list[object] = []
        if instrument:
            clauses.append("instrument = ?")
            params.append(instrument)
        if start:
            clauses.append("time >= ?")
            params.append(start.isoformat())
        if end:
            clauses.append("time <= ?")
            params.append(end.isoformat())
        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        query += " ORDER BY time"
        if limit:
            query += " LIMIT ?"
            params.append(limit)
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [self._row_to_tick(row) for row in rows]

    def fetch_bars(
        self,
        instrument: str | None = None,
        timeframe: str | None = None,
        start: datetime | None = None,
        end: datetime | None = None,
        limit: int | None = None,
    ) -> List[BarData]:
        query = (
            "SELECT instrument, timeframe, time, open, high, low, close, volume"
            " FROM bars"
        )
        clauses: list[str] = []
        params: list[object] = []
        if instrument:
            clauses.append("instrument = ?")
            params.append(instrument)
        if timeframe:
            clauses.append("timeframe = ?")
            params.append(timeframe)
        if start:
            clauses.append("time >= ?")
            params.append(start.isoformat())
        if end:
            clauses.append("time <= ?")
            params.append(end.isoformat())
        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        query += " ORDER BY time"
        if limit:
            query += " LIMIT ?"
            params.append(limit)
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [self._row_to_bar(row) for row in rows]

    def _row_to_tick(self, row: tuple) -> TickData:
        instrument, time_str, bid, ask, last, volume = row
        return TickData(
            time=datetime.fromisoformat(time_str),
            bid=bid,
            ask=ask,
            last=last,
            volume=volume,
            instrument=instrument,
        )

    def _row_to_bar(self, row: tuple) -> BarData:
        (
            instrument,
            timeframe,
            time_str,
            open_,
            high,
            low,
            close,
            volume,
        ) = row
        return BarData(
            time=datetime.fromisoformat(time_str),
            open=open_,
            high=high,
            low=low,
            close=close,
            volume=volume,
            instrument=instrument,
            timeframe=timeframe,
        )


class StorageService:
    """Fachada sencilla sobre el backend de almacenamiento."""

    def __init__(
        self,
        backend: StorageBackend | None = None,
        db_path: str | Path | None = None,
    ) -> None:
        if backend is not None:
            self._backend = backend
        else:
            final_path = db_path or (Path("data") / "market_data.db")
            self._backend = SQLiteStorageBackend(final_path)

    def save_ticks(self, ticks: Sequence[TickData]) -> int:
        count = self._backend.save_ticks(ticks)
        logger.info("%s ticks guardados en la base de datos", count)
        return count

    def save_bars(self, bars: Sequence[BarData]) -> int:
        count = self._backend.save_bars(bars)
        logger.info("%s barras guardadas en la base de datos", count)
        return count

    def get_ticks(
        self,
        instrument: str | None = None,
        start: datetime | None = None,
        end: datetime | None = None,
        limit: int | None = None,
    ) -> List[TickData]:
        return self._backend.fetch_ticks(instrument, start, end, limit)

    def get_bars(
        self,
        instrument: str | None = None,
        timeframe: str | None = None,
        start: datetime | None = None,
        end: datetime | None = None,
        limit: int | None = None,
    ) -> List[BarData]:
        return self._backend.fetch_bars(instrument, timeframe, start, end, limit)


__all__ = [
    "StorageBackend",
    "SQLiteStorageBackend",
    "StorageService",
]
