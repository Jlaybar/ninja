# NinjaTrader Data Bridge (Ejemplo)

Proyecto de referencia en Python 3.10+ para conectarse al API de NinjaTrader 8
(o a un gateway compatible) con el fin de descargar y almacenar datos de mercado.
Incluye conectores simulados, servicios por capas y utilidades para persistir datos
en una base SQLite local.

## Caracteristicas principales

- Arquitectura por capas (`connectors`, `services`, `models`).
- Cliente simulado (`SimulatedNinjaTraderClient`) para trabajar sin NinjaTrader.
- Cliente `KinetickEODClient` listo para coordinarse con un AddOn de NinjaTrader
  que exporte datos diarios gratuitos de Kinetick End-of-Day.
- Servicios para suscripcion en tiempo real e historicos.
- Persistencia en SQLite con un backend preparado para consultas filtradas.
- CLI de ejemplo (`python -m nt_data.cli.main`).
- Documentacion en español con guias de uso y puesta en marcha.
- Tests unitarios basicos con `pytest`.

## Estructura

```
.
├── data/
├── docs/
├── src/nt_data/
│   ├── cli/
│   ├── connectors/
│   ├── models/
│   └── services/
├── tests/
├── pyproject.toml
└── requirements.txt
```

Consulta `docs/README.md` para la guia completa y `docs/USAGE.md` para ejemplos.
`docs/NinjaTraderSetup.md` describe los pasos sugeridos para habilitar el API real.

## Requisitos

- Python 3.10 o superior.
- NinjaTrader 8 con algun metodo de integracion (gateway, add-on, API).
- Dependencias listadas en `requirements.txt`.

## Instalacion rapida

```bash
python -m venv .venv
. .venv/bin/activate  # En Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
```

Opcional: crea un archivo `.env` en la raiz del proyecto para definir variables
como `NT_USE_SIMULATOR`, `NT_COMMANDS_DIR`, etc. (se cargan automaticamente).

## Uso del CLI de ejemplo

```bash
python -m nt_data.cli.main --instrument "ES 12-25" --timeframe 1D --provider kinetick_eod
```

Esto guardara los datos en `data/market_data.db` (ruta configurable mediante
`NT_DATABASE_PATH`). Para operar con Kinetick EOD debes ejecutar NinjaTrader 8
con un AddOn que consuma archivos de comando en `NT_COMMANDS_DIR` y deposite
los CSV generados en `NT_EXPORT_DIR` (ver `docs/NinjaTraderSetup.md`). Usa la
opcion `--simulator` para generar datos sintéticos sin depender de NinjaTrader.

## Tests

```bash
pytest
```

## Licencia

MIT (puede ajustarse segun tus necesidades).
