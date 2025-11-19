"""Clientes para conectar con NinjaTrader u otras fuentes de datos."""
from __future__ import annotations

import csv
import logging
import random
import threading
import time
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from pathlib import Path
from typing import Callable, List
from uuid import uuid4

from ..models.bar import BarData
from ..models.tick import TickData

logger = logging.getLogger(__name__)

MarketDataCallback = Callable[[TickData], None]


class ConnectionError(RuntimeError):
    """Error lanzado cuando la conexion con NinjaTrader falla."""


class NinjaTraderClient(ABC):
    """Interfaz de alto nivel para comunicarse con NinjaTrader."""

    def __init__(self) -> None:
        self._connected = False

    @abstractmethod
    def connect(self) -> None:
        """Establece la conexion con NinjaTrader."""

    @abstractmethod
    def disconnect(self) -> None:
        """Cierra la conexion activa."""

    @abstractmethod
    def subscribe_market_data(
        self, instrument: str, on_tick: MarketDataCallback
    ) -> Callable[[], None]:
        """Suscribe datos en tiempo real y devuelve un callback para cancelar."""

    @abstractmethod
    def request_historical_data(
        self, instrument: str, timeframe: str, start: datetime, end: datetime
    ) -> List[BarData]:
        """Descarga datos historicos."""

    @property
    def is_connected(self) -> bool:
        return self._connected

    @property
    def supports_realtime(self) -> bool:
        """Indica si el cliente permite suscripcion en tiempo real."""
        return True

    def _set_connected(self, value: bool) -> None:
        self._connected = value


class SimulatedNinjaTraderClient(NinjaTraderClient):
    """Cliente simulado que genera datos aleatorios."""

    def __init__(self, tick_interval: float = 1.0) -> None:
        super().__init__()
        self._tick_interval = tick_interval
        self._stop_event = threading.Event()
        self._subscriptions: list[tuple[str, threading.Event, threading.Thread]] = []
        self._lock = threading.Lock()

    def connect(self) -> None:
        logger.info("Conectando al cliente simulado de NinjaTrader...")
        time.sleep(0.2)
        self._set_connected(True)
        logger.info("Cliente simulado conectado")

    def disconnect(self) -> None:
        logger.info("Desconectando cliente simulado")
        self._stop_event.set()
        with self._lock:
            for _, stop_event, thread in self._subscriptions:
                stop_event.set()
                thread.join(timeout=1)
            self._subscriptions.clear()
        self._set_connected(False)
        logger.info("Cliente simulado desconectado")

    def subscribe_market_data(
        self, instrument: str, on_tick: MarketDataCallback
    ) -> Callable[[], None]:
        if not self.is_connected:
            raise ConnectionError("No hay conexion con NinjaTrader")

        stop_event = threading.Event()

        def _stream() -> None:
            last_price = random.uniform(1000, 5000)
            while not (stop_event.is_set() or self._stop_event.is_set()):
                change = random.uniform(-1.5, 1.5)
                bid = max(0.0, last_price + change - 0.5)
                ask = bid + random.uniform(0.25, 1.25)
                last_price = bid + random.uniform(0, ask - bid)
                tick = TickData(
                    time=datetime.utcnow(),
                    bid=round(bid, 2),
                    ask=round(ask, 2),
                    last=round(last_price, 2),
                    volume=random.randint(1, 10),
                    instrument=instrument,
                )
                try:
                    on_tick(tick)
                except Exception as exc:  # pragma: no cover - logging defensivo
                    logger.exception("Error en callback de tick: %s", exc)
                time.sleep(self._tick_interval)

        thread = threading.Thread(target=_stream, daemon=True)
        thread.start()

        with self._lock:
            self._subscriptions.append((instrument, stop_event, thread))

        def cancel() -> None:
            stop_event.set()
            thread.join(timeout=1)
            with self._lock:
                self._subscriptions = [
                    sub for sub in self._subscriptions if sub[1] is not stop_event
                ]

        return cancel

    def request_historical_data(
        self, instrument: str, timeframe: str, start: datetime, end: datetime
    ) -> List[BarData]:
        if not self.is_connected:
            raise ConnectionError("No hay conexion con NinjaTrader")
        logger.info(
            "Generando datos historicos simulados para %s (%s)",
            instrument,
            timeframe,
        )
        bars: List[BarData] = []
        delta = _timeframe_to_timedelta(timeframe)
        current = start
        price = random.uniform(1000, 5000)
        while current < end:
            high = price + random.uniform(0, 5)
            low = price - random.uniform(0, 5)
            close = random.uniform(low, high)
            volume = random.randint(10, 1000)
            bars.append(
                BarData(
                    time=current,
                    open=round(price, 2),
                    high=round(high, 2),
                    low=round(low, 2),
                    close=round(close, 2),
                    volume=volume,
                    instrument=instrument,
                    timeframe=timeframe,
                )
            )
            current += delta
            price = close
        return bars


def _timeframe_to_timedelta(timeframe: str) -> timedelta:
    unit = timeframe[-1]
    value = int(timeframe[:-1]) if timeframe[:-1] else 1
    if unit == "m":
        return timedelta(minutes=value)
    if unit == "h":
        return timedelta(hours=value)
    if unit == "s":
        return timedelta(seconds=value)
    logger.warning("Timeframe %s no reconocido, usando 1m", timeframe)
    return timedelta(minutes=1)


class KinetickEODClient(NinjaTraderClient):
    """Cliente que coordina con un AddOn de NinjaTrader para descargar datos diarios."""

    def __init__(
        self,
        commands_dir: str | Path,
        export_dir: str | Path,
        export_timeout: float = 90.0,
        poll_interval: float = 1.0,
    ) -> None:
        super().__init__()
        self._commands_dir = Path(commands_dir)
        self._export_dir = Path(export_dir)
        self._export_timeout = export_timeout
        self._poll_interval = poll_interval

    @property
    def supports_realtime(self) -> bool:
        return False

    def connect(self) -> None:
        self._commands_dir.mkdir(parents=True, exist_ok=True)
        self._export_dir.mkdir(parents=True, exist_ok=True)
        logger.info(
            "Cliente KinetickEOD listo. Asegure que NinjaTrader y el AddOn esten activos"
        )
        self._set_connected(True)

    def disconnect(self) -> None:
        self._set_connected(False)

    def subscribe_market_data(
        self, instrument: str, on_tick: MarketDataCallback
    ) -> Callable[[], None]:
        raise NotImplementedError(
            "Kinetick EOD solo ofrece datos diarios, no suscripciones en tiempo real"
        )

    def request_historical_data(
        self, instrument: str, timeframe: str, start: datetime, end: datetime
    ) -> List[BarData]:
        if not self.is_connected:
            raise ConnectionError("Debe conectar el cliente antes de solicitar historicos")
        if timeframe.lower() not in {"1d", "d", "day"}:
            logger.warning("Kinetick EOD solo expone timeframe diario. Se usara 1D")
        command_id = uuid4().hex
        command_path = self._commands_dir / f"cmd_{command_id}.txt"
        export_path = self._export_dir / f"{command_id}.csv"
        payload = ";".join(
            [
                "DOWNLOAD",
                instrument,
                start.date().isoformat(),
                end.date().isoformat(),
                export_path.as_posix(),
            ]
        )
        command_path.write_text(payload, encoding="utf-8")
        logger.info("Comando KinetickEOD generado: %s", payload)
        try:
            bars = self._wait_for_export(export_path, instrument)
        finally:
            if command_path.exists():
                command_path.unlink(missing_ok=True)
        return bars

    def _wait_for_export(self, export_path: Path, instrument: str) -> List[BarData]:
        start_time = time.time()
        while time.time() - start_time < self._export_timeout:
            if export_path.exists():
                logger.info("Archivo generado por NinjaTrader: %s", export_path)
                bars = self._parse_export(export_path, instrument)
                export_path.unlink(missing_ok=True)
                return bars
            time.sleep(self._poll_interval)
        raise TimeoutError(
            f"No se recibio respuesta de NinjaTrader dentro de {self._export_timeout}s"
        )

    def _parse_export(self, export_path: Path, instrument: str) -> List[BarData]:
        bars: List[BarData] = []
        with export_path.open("r", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                date_value = row.get("Date") or row.get("date")
                if not date_value:
                    continue
                try:
                    time_value = datetime.fromisoformat(date_value)
                except ValueError:
                    time_value = datetime.strptime(date_value, "%Y-%m-%d")
                bars.append(
                    BarData(
                        time=time_value,
                        open=float(row.get("Open", 0.0) or 0.0),
                        high=float(row.get("High", 0.0) or 0.0),
                        low=float(row.get("Low", 0.0) or 0.0),
                        close=float(row.get("Close", 0.0) or 0.0),
                        volume=int(float(row.get("Volume", 0) or 0)),
                        instrument=instrument,
                        timeframe="1D",
                    )
                )
        if not bars:
            logger.warning("El archivo %s no contenia barras", export_path)
        return bars