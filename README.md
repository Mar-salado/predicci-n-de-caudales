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
- `--point-id`: (Opcional) Identificador del punto que se añadirá al nombre del
  archivo de salida. Si se omite, se genera automáticamente a partir de la
  latitud/longitud.

El archivo generado se denomina `forecast_<IDENTIFICADOR>_<AAAAMMDD>.csv` e
incluye las columnas `date`, `precipitation_mm`, `temp_max_c` y
`temp_min_c`. El identificador por defecto utiliza las coordenadas normalizadas
(por ejemplo, `forecast_lat12p3456N_lon076p5432W_20240101.csv`).
> **Nota:** Open-Meteo no requiere autenticación, pero respeta sus límites de
uso y términos de servicio.

## Script histórico previo

Se mantiene el script [`download_meteo.py`](download_meteo.py) que descarga
series diarias de la misma API con un enfoque distinto (archivo Excel con
precipitación y temperaturas mínima, máxima y media para un rango de fechas
personalizado).
