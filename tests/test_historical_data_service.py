from datetime import datetime, timedelta

from nt_data.connectors import SimulatedNinjaTraderClient
from nt_data.services import HistoricalDataService


def test_historical_service_returns_bars():
    client = SimulatedNinjaTraderClient()
    service = HistoricalDataService(client)
    now = datetime.utcnow()
    bars = service.get_historical_bars(
        instrument="ES 12-25",
        timeframe="5m",
        start=now - timedelta(hours=1),
        end=now,
    )
    assert bars, "Se esperaban barras simuladas"
    assert bars[0].instrument == "ES 12-25"