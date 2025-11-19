# Documentacion general

Este directorio agrupa la documentacion en español para el proyecto `nt_data`.

- `USAGE.md`: ejemplos practicos de como suscribirse a datos en tiempo real,
  descargar historicos y trabajar con la base SQLite generada.
- `NinjaTraderSetup.md`: recordatorios para preparar NinjaTrader 8 y exponer
  datos mediante un API/bridge.

A continuacion se describe la arquitectura a alto nivel.

## Arquitectura

1. **Connectors**: encapsulan la comunicacion con NinjaTrader. Incluyen una
   version simulada (`SimulatedNinjaTraderClient`) y el cliente
   `KinetickEODClient` listo para coordinarse con el AddOn descrito en la
   documentacion.
2. **Models**: dataclasses (`TickData`, `BarData`, `OrderBookSnapshot`).
3. **Services**: orquestan negocio (`MarketDataService`, `HistoricalDataService`,
   `StorageService`).
4. **CLI**: script demostrativo en `nt_data/cli/main.py`.

## Flujo tipico

1. Configurar `Settings` mediante variables de entorno o parametros CLI.
2. Instanciar el `NinjaTraderClient` (simulado o real).
3. Crear servicios y lanzar suscripciones / descargas.
4. Guardar y consultar datos usando `StorageService` (SQLite por defecto).

Lee `USAGE.md` para ejemplos ejecutables.
