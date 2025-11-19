"""Servicio para descarga de historicos."""
from __future__ import annotations

import logging
from datetime import datetime
from typing import List

from ..connectors import ConnectionError, NinjaTraderClient
from ..models.bar import BarData

logger = logging.getLogger(__name__)


class HistoricalDataService:
    """Se encarga de orquestar la descarga de barras historicas."""

    def __init__(self, client: NinjaTraderClient) -> None:
        self._client = client

    def get_historical_bars(
        self, instrument: str, timeframe: str, start: datetime, end: datetime
    ) -> List[BarData]:
        if not self._client.is_connected:
            try:
                self._client.connect()
            except ConnectionError as exc:
                logger.error("No se pudo conectar para descargar historicos: %s", exc)
                raise
        logger.info(
            "Solicitando historicos: instrumento=%s timeframe=%s %s -> %s",
            instrument,
            timeframe,
            start.isoformat(),
            end.isoformat(),
        )
        return self._client.request_historical_data(instrument, timeframe, start, end)


__all__ = ["HistoricalDataService"]