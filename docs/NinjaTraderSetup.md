# Configuracion sugerida de NinjaTrader y Kinetick EOD

> **Aviso**: Este proyecto no incluye una integracion oficial con NinjaTrader.
> Debes adaptar los pasos siguientes a tu entorno, licenciamiento y version.

## 1. Conectar a Kinetick End-of-Day

1. En NinjaTrader 8, habilita la conexion "Kinetick - End Of Day (Free)".
2. Crea un AddOn (NinjaScript) similar a `AutoConnectKinetickEOD` que, al
   iniciar NinjaTrader, verifique si la conexion ya esta activa y llame a
   `Connection.Connect("Kinetick - End Of Day (Free)")` cuando sea necesario.
3. Compila e instala el AddOn para que se cargue en cada inicio.

## 2. Canal de comunicacion por archivos

El cliente Python escribe comandos `DOWNLOAD;instrument;start;end;output_path` en
`NT_COMMANDS_DIR`. En NinjaTrader, crea un `FileSystemWatcher` (o mecanismo
similar) que escuche ese directorio y ejecute el siguiente flujo cuando detecte
un nuevo archivo:

1. Leer el contenido y parsear los parametros (`instrument`, fecha `start`,
   fecha `end`, ruta `output`).
2. Ejecutar una `BarsRequest` con `BarsPeriodType.Day` y `BarsPeriod.Value = 1`.
3. Serializar el resultado en CSV con encabezado `Date,Open,High,Low,Close,Volume`
   en la ruta recibida.
4. (Opcional) borrar el archivo de comando.

> Referencia rapida:
>
> ```csharp
> var bars = new BarsRequest(
>     Instrument.GetInstrument(instrument),
>     start,
>     end,
>     BarsPeriodType.Day,
>     1);
> bars.Request((request, code) =>
> {
>     if (code == ErrorCode.NoError)
>     {
>         // escribir CSV en output_path
>     }
> });
> ```

## 3. Activacion desde Visual Studio / scripts externos

1. Lanza NinjaTrader desde tu automatizacion (`Process.Start`).
2. Espera unos segundos a que cargue y se conecte el AddOn.
3. Escribe el archivo `DOWNLOAD` usando la sintaxis esperada.
4. El cliente Python esperara automaticamente el CSV (hasta `NT_EXPORT_TIMEOUT`
   segundos) y lo cargara en SQLite.

## 4. Seguridad y limpieza

- Limita el acceso a los directorios configurados (`NT_COMMANDS_DIR` y
  `NT_EXPORT_DIR`).
- Limpia archivos procesados para evitar acumulaciones.
- Ajusta `NT_EXPORT_TIMEOUT` y `NT_EXPORT_POLL_SECONDS` segun la latencia de tu
  maquina.

Necesitaras adaptar los `TODO` dentro de `src/nt_data/connectors/ninjatrader_client.py`
para reflejar cualquier cambio de protocolo en tu AddOn (por ejemplo, estructuras
JSON en lugar de comandos separados por `;`).