from datetime import datetime

from nt_data.models import BarData, TickData
from nt_data.services import StorageService


def test_storage_service_persists_and_fetches(tmp_path):
    ticks = [
        TickData(
            time=datetime.utcnow(),
            bid=1.0,
            ask=1.5,
            last=1.25,
            volume=10,
            instrument="ES",
        )
    ]
    bars = [
        BarData(
            time=datetime.utcnow(),
            open=1.0,
            high=2.0,
            low=0.5,
            close=1.5,
            volume=100,
            instrument="ES",
            timeframe="5m",
        )
    ]
    service = StorageService(db_path=tmp_path / "market.db")
    assert service.save_ticks(ticks) == 1
    assert service.save_bars(bars) == 1
    fetched_ticks = service.get_ticks(instrument="ES")
    fetched_bars = service.get_bars(instrument="ES")
    assert fetched_ticks and fetched_ticks[0].last == 1.25
    assert fetched_bars and fetched_bars[0].close == 1.5