"""Servicios relacionados con datos en tiempo real."""
from __future__ import annotations

import logging
import threading
import time
from typing import Callable, List

from ..connectors import ConnectionError, MarketDataCallback, NinjaTraderClient
from ..models.tick import TickData

logger = logging.getLogger(__name__)


class MarketDataService:
    """Gestiona suscripciones y reconexiones basicas."""

    def __init__(self, client: NinjaTraderClient, reconnect_delay: float = 2.0) -> None:
        self._client = client
        self._reconnect_delay = reconnect_delay
        self._subscriptions: List[Callable[[], None]] = []
        self._lock = threading.Lock()

    def ensure_connection(self) -> None:
        if self._client.is_connected:
            return
        while not self._client.is_connected:
            try:
                logger.info("Intentando conectar al proveedor de datos...")
                self._client.connect()
            except ConnectionError as exc:
                logger.warning("Conexion fallida: %s. Reintentando...", exc)
                time.sleep(self._reconnect_delay)
            else:
                break

    def subscribe_realtime_ticks(
        self, instrument: str, callback: Callable[[TickData], None]
    ) -> Callable[[], None]:
        """Suscribe a ticks y devuelve funcion para cancelar."""

        if not self._client.supports_realtime:
            raise NotImplementedError(
                "El cliente configurado no soporta suscripciones en tiempo real"
            )
        self.ensure_connection()

        def _on_tick(tick: TickData) -> None:
            try:
                callback(tick)
            except Exception as exc:  # pragma: no cover - logging defensivo
                logger.exception("Callback de usuario lanzo excepcion: %s", exc)

        cancel = self._client.subscribe_market_data(instrument, _on_tick)
        with self._lock:
            self._subscriptions.append(cancel)
        return cancel

    def stop_all(self) -> None:
        with self._lock:
            for cancel in self._subscriptions:
                try:
                    cancel()
                except Exception as exc:  # pragma: no cover
                    logger.error("Error cancelando suscripcion: %s", exc)
            self._subscriptions.clear()


__all__ = ["MarketDataService"]
