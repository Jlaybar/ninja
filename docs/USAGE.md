# Guia de uso

Todos los ejemplos asumen que ya activaste tu entorno virtual y ejecutaste
`pip install -r requirements.txt`.

## Ejemplo 1: Descarga diaria con Kinetick EOD

1. Ejecuta NinjaTrader 8 con el AddOn descrito en `docs/NinjaTraderSetup.md`.
2. Define los directorios de intercambio (opcional):

```powershell
$env:NT_COMMANDS_DIR="C:\NTCommands"
$env:NT_EXPORT_DIR="C:\NTExports"
```

3. Lanza el CLI apuntando al proveedor `kinetick_eod`:

```bash
python -m nt_data.cli.main --instrument "ES ##-##" --timeframe 1D --provider kinetick_eod
```

El cliente escribira un archivo `DOWNLOAD;...` en `NT_COMMANDS_DIR` y esperara a
que NinjaTrader deje un CSV diario en `NT_EXPORT_DIR`. Todas las barras
obtenidas se guardan en `data/market_data.db`.

## Ejemplo 2: Uso del simulador

```bash
python -m nt_data.cli.main --instrument "ES 12-25" --timeframe 5m --seconds 20 --simulator
```

Esta opcion mantiene el flujo original de tiempo real para pruebas locales.

## Ejemplo 3: Lectura directa desde SQLite

```python
from nt_data.services import StorageService

storage = StorageService(db_path="data/market_data.db")
recent = storage.get_bars(instrument="ES ##-##", timeframe="1D", limit=5)
print("Ultimas barras: ", recent)
```

## Variables de entorno disponibles

| Variable | Descripcion | Valor por defecto |
| --- | --- | --- |
| `NT_INSTRUMENT` | Instrumento objetivo | `ES 12-25` |
| `NT_TIMEFRAME` | Timeframe historico | `5m` |
| `NT_HISTORICAL_DAYS` | Dias atras para historicos | `5` |
| `NT_REALTIME_SECONDS` | Segundos a capturar ticks (simulador) | `15` |
| `NT_USE_SIMULATOR` | Usa cliente simulado si `true` | `true` |
| `NT_DATA_PROVIDER` | Nombre del proveedor (`kinetick_eod`) | `kinetick_eod` |
| `NT_COMMANDS_DIR` | Carpeta monitoreada por el AddOn para comandos | `data/commands` |
| `NT_EXPORT_DIR` | Carpeta donde el AddOn deja los CSV | `data/exports` |
| `NT_EXPORT_TIMEOUT` | Tiempo maximo (s) para esperar el CSV | `90` |
| `NT_EXPORT_POLL_SECONDS` | Intervalo de sondeo para detectar el CSV | `1.0` |
| `NT_DATABASE_PATH` | Ruta completa a la base SQLite | `data/market_data.db` |

## Formato esperado de los CSV

El AddOn debe exportar archivos con encabezado `Date,Open,High,Low,Close,Volume`.
El cliente los borra tras importarlos, por lo que es recomendable generar
identificadores unicos para cada solicitud (por ejemplo, usando el nombre que se
incluye en el comando `DOWNLOAD`).

Consulta `docs/NinjaTraderSetup.md` para el detalle del AddOn y la automatizacion
de NinjaTrader desde Visual Studio/PowerShell.