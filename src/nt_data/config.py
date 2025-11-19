"""Configuracion general de la aplicacion."""
from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import timedelta


def _get_env(name: str, default: str) -> str:
    value = os.getenv(name)
    return value if value else default


@dataclass(slots=True)
class Settings:
    """Configuracion basica leida de variables de entorno."""

    instrument: str = _get_env("NT_INSTRUMENT", "ES 12-25")
    timeframe: str = _get_env("NT_TIMEFRAME", "5m")
    historical_days: int = int(_get_env("NT_HISTORICAL_DAYS", "5"))
    realtime_duration: timedelta = timedelta(
        seconds=int(_get_env("NT_REALTIME_SECONDS", "15"))
    )
    data_folder: str = _get_env("NT_DATA_DIR", os.path.join("data"))
    use_simulator: bool = _get_env("NT_USE_SIMULATOR", "true").lower() == "true"
    database_path: str = _get_env(
        "NT_DATABASE_PATH", os.path.join(data_folder, "market_data.db")
    )
    data_provider: str = _get_env("NT_DATA_PROVIDER", "kinetick_eod")
    commands_dir: str = _get_env(
        "NT_COMMANDS_DIR", os.path.join(data_folder, "commands")
    )
    export_dir: str = _get_env("NT_EXPORT_DIR", os.path.join(data_folder, "exports"))
    export_timeout: int = int(_get_env("NT_EXPORT_TIMEOUT", "90"))
    export_poll_seconds: float = float(_get_env("NT_EXPORT_POLL_SECONDS", "1.0"))


settings = Settings()
