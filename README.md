# Predicción de caudales

Herramientas y datos para apoyar ejercicios de predicción de caudales.

## Descarga de pronósticos ECMWF (Open-Meteo)

El script [`scripts/download_forecast.py`](scripts/download_forecast.py) descarga
pronósticos diarios provenientes de **ECMWF Open Data** (a través de la API
pública de [Open-Meteo](https://open-meteo.com/)). Obtiene la precipitación
acumulada y las temperaturas máxima y mínima para un horizonte configurable de
hasta 16 días (por defecto, 10 días) y guarda un CSV en el directorio `data/`.

### Requisitos

- Python 3.9 o superior
- Paquete: `requests`

Instalación rápida:

```bash
pip install requests
```

### Uso

```bash
python scripts/download_forecast.py <LATITUD> <LONGITUD> \
    --start-date AAAA-MM-DD --forecast-days 10
```

Parámetros principales:

- Posicionales `latitude` y `longitude`: Coordenadas del punto de interés en
  grados decimales.
- `--start-date`: (Opcional) Fecha inicial del pronóstico. Si se omite, usa la
  fecha actual.
- `--forecast-days`: (Opcional) Número de días a descargar (máx. 16 según la
  API).
- `--output-dir`: (Opcional) Directorio donde se guardará el archivo CSV. Por
  defecto, `data/`.
- `--points-file`: (Opcional) CSV con columnas `Name`, `Latitud` y `Longitud`
  para descargar múltiples puntos en una sola ejecución.
- `--interval-minutes`: (Opcional) Intervalo en minutos entre ejecuciones
  consecutivas al usar `--iterations` o `--continuous`. Por defecto, 60 minutos.
- `--iterations`: (Opcional) Número de iteraciones en modo iterativo. Si no se
  especifica, solo se ejecuta una descarga.
- `--continuous`: Activa el modo continuo (se ejecuta hasta recibir `Ctrl+C`).
- `--keep-last`: (Opcional) Conserva únicamente los `N` archivos más recientes
  por punto; el resto se elimina tras cada iteración.

Los archivos generados incorporan la marca temporal de cada ejecución en su
nombre (`forecast_<punto>_<AAAAMMDD_HHMMSS>.csv`) e incluyen las columnas
`date`, `precipitation_mm`, `temp_max_c` y `temp_min_c`. Cuando no se indica un
nombre para el punto, se emplea uno derivado de las coordenadas.

### Modo continuo

Para programar ejecuciones periódicas basta con usar `--iterations` o
`--continuous`. Por ejemplo, para descargar datos cada 30 minutos durante 12
iteraciones:

```bash
python scripts/download_forecast.py 4.6097 -74.0817 --interval-minutes 30 --iterations 12
```

Si se desea mantener la descarga indefinidamente hasta interrumpirla manualmente:

```bash
python scripts/download_forecast.py 4.6097 -74.0817 --interval-minutes 60 --continuous
```

Puedes detener la ejecución continua con `Ctrl+C`, o bien integrarla en
herramientas del sistema como `systemd` o `cron` para que gestionen el ciclo de
vida del proceso.
> **Nota:** Open-Meteo no requiere autenticación, pero respeta sus límites de
uso y términos de servicio.

## Descarga histórica de datos meteorológicos (Open-Meteo)

El script [`download_meteo.py`](download_meteo.py) descarga series históricas
de precipitación diaria acumulada y temperaturas máxima, mínima y media para
un rango de fechas personalizado y guarda los resultados en un archivo Excel.
Se apoya en la API pública de [Open-Meteo](https://open-meteo.com/), que no
requiere autenticación.

### Requisitos

- Python 3.9 o superior
- Paquetes: `requests`, `pandas`

Instalación rápida:

```bash
pip install requests pandas
```

### Uso

```bash
python download_meteo.py --lat <LATITUD> --lon <LONGITUD> \
    --start AAAA-MM-DD --end AAAA-MM-DD [--timezone ZONA/HORARIA] [--out archivo.xlsx]
```

Parámetros principales:

- `--lat` / `--latitude`: Latitud en grados decimales (obligatorio).
- `--lon` / `--longitude`: Longitud en grados decimales (obligatorio).
- `--start`: Fecha inicial del intervalo en formato ISO AAAA-MM-DD (obligatorio).
- `--end`: Fecha final del intervalo en formato ISO AAAA-MM-DD (obligatorio).
- `--timezone`: Zona horaria para las fechas generadas. Por defecto `America/Lima`.
- `--out`: Ruta del archivo Excel a crear. Por defecto `datos_meteo.xlsx`.

El intervalo debe abarcar al menos 10 días (ambas fechas inclusive). El archivo
Excel resultante contiene las columnas `Fecha`, `precipitacion_mm`, `temp_max_c`,
`temp_min_c` y `temp_media_c`.
