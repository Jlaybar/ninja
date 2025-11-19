"""CLI de ejemplo para interactuar con NinjaTrader."""
from __future__ import annotations

import argparse
import logging
import sys
import time
from datetime import datetime, timedelta

from ..config import Settings
from ..connectors import (
    KinetickEODClient,
    NinjaTraderClient,
    SimulatedNinjaTraderClient,
)
from ..services import (
    HistoricalDataService,
    MarketDataService,
    StorageService,
)

logger = logging.getLogger(__name__)


def _build_client(settings: Settings, use_simulator: bool, provider: str) -> NinjaTraderClient:
    if use_simulator:
        return SimulatedNinjaTraderClient(tick_interval=1.0)
    if provider == "kinetick_eod":
        return KinetickEODClient(
            commands_dir=settings.commands_dir,
            export_dir=settings.export_dir,
            export_timeout=settings.export_timeout,
            poll_interval=settings.export_poll_seconds,
        )
    raise NotImplementedError(f"Proveedor {provider} no soportado por nt_data")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ejemplo de consumo de datos de NinjaTrader")
    parser.add_argument("--instrument", default=None, help="Instrumento a utilizar")
    parser.add_argument("--timeframe", default=None, help="Timeframe OHLC, e.g. 5m")
    parser.add_argument(
        "--seconds",
        type=int,
        default=None,
        help="Segundos a recopilar datos en tiempo real",
    )
    parser.add_argument(
        "--simulator",
        action="store_true",
        help="Forzar uso del cliente simulado",
    )
    parser.add_argument(
        "--provider",
        default=None,
        help="Proveedor de datos (kinetick_eod, simulator)",
    )
    return parser.parse_args()


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    )
    args = parse_args()
    settings = Settings()

    instrument = args.instrument or settings.instrument
    timeframe = args.timeframe or settings.timeframe
    duration = timedelta(seconds=args.seconds) if args.seconds else settings.realtime_duration
    provider = (args.provider or settings.data_provider).lower()
    use_simulator = args.simulator or settings.use_simulator

    client = _build_client(settings, use_simulator, provider)
    market_service = MarketDataService(client)
    historical_service = HistoricalDataService(client)
    storage_service = StorageService(db_path=settings.database_path)

    collected_ticks = []

    if client.supports_realtime:
        def on_tick(tick):
            collected_ticks.append(tick)
            logger.info(
                "Tick %s bid=%s ask=%s last=%s vol=%s",
                tick.instrument,
                tick.bid,
                tick.ask,
                tick.last,
                tick.volume,
            )

        cancel = market_service.subscribe_realtime_ticks(instrument, on_tick)
        logger.info("Recolectando ticks de %s durante %s...", instrument, duration)
        try:
            end_time = datetime.utcnow() + duration
            while datetime.utcnow() < end_time:
                time.sleep(0.5)
        finally:
            cancel()
            market_service.stop_all()
        if collected_ticks:
            storage_service.save_ticks(collected_ticks)
    else:
        logger.info(
            "Proveedor %s no ofrece tiempo real; se omitira la captura de ticks", provider
        )

    history_end = datetime.utcnow()
    history_start = history_end - timedelta(days=settings.historical_days)
    bars = historical_service.get_historical_bars(
        instrument=instrument,
        timeframe=timeframe,
        start=history_start,
        end=history_end,
    )
    bars_saved = storage_service.save_bars(bars)

    sample_tick = storage_service.get_ticks(instrument=instrument, limit=1)
    sample_bar = storage_service.get_bars(instrument=instrument, timeframe=timeframe, limit=1)
    logger.info(
        "Resumen: %s ticks y %s barras almacenados en %s",
        len(collected_ticks),
        bars_saved,
        settings.database_path,
    )
    if sample_tick:
        logger.info(
            "Ejemplo tick guardado: %s bid=%s ask=%s",
            sample_tick[0].time.isoformat(),
            sample_tick[0].bid,
            sample_tick[0].ask,
        )
    if sample_bar:
        logger.info(
            "Ejemplo barra guardada: %s O=%s H=%s L=%s C=%s",
            sample_bar[0].time.isoformat(),
            sample_bar[0].open,
            sample_bar[0].high,
            sample_bar[0].low,
            sample_bar[0].close,
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())