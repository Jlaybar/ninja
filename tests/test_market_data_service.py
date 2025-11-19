import threading
import time

from nt_data.connectors import SimulatedNinjaTraderClient
from nt_data.services import MarketDataService


def test_subscribe_realtime_ticks_generates_data():
    client = SimulatedNinjaTraderClient(tick_interval=0.01)
    service = MarketDataService(client, reconnect_delay=0.01)
    results = []
    event = threading.Event()

    def on_tick(tick):
        results.append(tick)
        event.set()

    cancel = service.subscribe_realtime_ticks("ES 12-25", on_tick)
    assert event.wait(timeout=1), "No se recibieron ticks simulados"
    cancel()
    service.stop_all()
    assert len(results) > 0