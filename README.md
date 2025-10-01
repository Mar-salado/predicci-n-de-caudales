
Herramientas y datos para apoyar ejercicios de predicción de caudales.

## Descarga de datos meteorológicos

El script [`download_meteo.py`](download_meteo.py) permite descargar, desde la
API pública de [Open-Meteo](https://open-meteo.com/), series diarias de
precipitación acumulada y temperatura (mínima, máxima y media) para un intervalo
mínimo de 10 días. Los datos se guardan en un archivo Excel listo para ser
utilizado en el script del modelo GR4J que compartiste.

### Requisitos

- Python 3.9 o superior
- Paquetes: `pandas`, `requests`

Puedes instalarlos con:

```bash
pip install pandas requests
```

### Uso

```bash
python download_meteo.py --lat <LATITUD> --lon <LONGITUD> \
    --start <AAAA-MM-DD> --end <AAAA-MM-DD> --out datos_meteo.xlsx
```

Parámetros principales:

- `--lat`, `--lon`: Coordenadas en grados decimales del punto de interés.
- `--start`, `--end`: Fechas inicial y final (inclusive). Deben cubrir al menos
  10 días.
- `--timezone`: (Opcional) Zona horaria para las fechas del archivo de salida
  (por defecto `America/Lima`).
- `--out`: (Opcional) Nombre del archivo Excel a generar.

El archivo resultante incluye las columnas `Fecha`, `precipitacion_mm`,
`temp_max_c`, `temp_min_c` y `temp_media_c`.

> **Nota:** Open-Meteo no requiere autenticación, pero respeta sus límites de uso
y términos de servicio.
