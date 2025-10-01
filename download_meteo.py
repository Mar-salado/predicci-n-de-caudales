 (cd "$(git rev-parse --show-toplevel)" && git apply --3way <<'EOF' 
diff --git a//dev/null b/download_meteo.py
index 0000000000000000000000000000000000000000..71bb3192544bf19c7ea24d654cc82bfd51b94c2f 100644
--- a//dev/null
+++ b/download_meteo.py
@@ -0,0 +1,163 @@
+"""Herramientas para descargar precipitación y temperatura diarias usando la API de Open-Meteo.
+
+Este script descarga series diarias de precipitación acumulada y temperaturas
+máxima, mínima y media entre dos fechas dadas (ambas inclusive). Está pensado
+como complemento para alimentar el modelo GR4J con datos de precipitación y
+una estimación de temperatura.
+
+Ejemplo de uso desde la línea de comandos::
+
+    python download_meteo.py --lat -9.0 --lon -75.0 \
+        --start 2024-01-01 --end 2024-01-20 --out datos.xlsx
+
+La API de Open-Meteo es pública y no requiere autenticación. Consulta los
+límites de uso en https://open-meteo.com/.
+"""
+from __future__ import annotations
+
+import argparse
+import datetime as dt
+from dataclasses import dataclass
+from typing import Optional
+
+import pandas as pd
+import requests
+
+
+OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
+
+
+@dataclass
+class MeteoRequest:
+    """Parámetros necesarios para realizar la solicitud de datos meteorológicos."""
+
+    latitude: float
+    longitude: float
+    start_date: dt.date
+    end_date: dt.date
+    timezone: str = "UTC"
+
+    def validate(self) -> None:
+        """Valida los parámetros de entrada.
+
+        - Verifica que la ventana temporal tenga al menos 10 días.
+        - Valida que la fecha de inicio sea anterior o igual a la de fin.
+        """
+
+        if self.start_date > self.end_date:
+            raise ValueError("La fecha de inicio no puede ser posterior a la de fin.")
+
+        min_days = 10
+        delta = (self.end_date - self.start_date).days + 1
+        if delta < min_days:
+            raise ValueError(
+                "El intervalo debe cubrir al menos 10 días. "
+                f"Actualmente solo cubre {delta} días."
+            )
+
+
+def fetch_daily_precip_and_temperature(request: MeteoRequest) -> pd.DataFrame:
+    """Descarga precipitación diaria y temperaturas para la ubicación solicitada.
+
+    Parameters
+    ----------
+    request:
+        Instancia de :class:`MeteoRequest` con los parámetros de descarga.
+
+    Returns
+    -------
+    pandas.DataFrame
+        DataFrame con columnas ``Fecha``, ``precipitacion_mm``, ``temp_min_c``,
+        ``temp_max_c`` y ``temp_media_c``.
+    """
+
+    request.validate()
+
+    params = {
+        "latitude": request.latitude,
+        "longitude": request.longitude,
+        "daily": "precipitation_sum,temperature_2m_max,temperature_2m_min",
+        "start_date": request.start_date.isoformat(),
+        "end_date": request.end_date.isoformat(),
+        "timezone": request.timezone,
+    }
+
+    response = requests.get(OPEN_METEO_URL, params=params, timeout=30)
+    response.raise_for_status()
+    payload = response.json()
+
+    if "daily" not in payload:
+        raise RuntimeError(
+            "Respuesta inesperada de la API de Open-Meteo: 'daily' no encontrado"
+        )
+
+    daily = payload["daily"]
+    required_keys = {"time", "precipitation_sum", "temperature_2m_max", "temperature_2m_min"}
+    if not required_keys.issubset(daily):
+        faltantes = required_keys - set(daily)
+        raise RuntimeError(
+            "La respuesta de la API no contiene las claves requeridas: "
+            + ", ".join(sorted(faltantes))
+        )
+
+    df = pd.DataFrame(
+        {
+            "Fecha": pd.to_datetime(daily["time"], utc=True).tz_convert(request.timezone),
+            "precipitacion_mm": daily["precipitation_sum"],
+            "temp_max_c": daily["temperature_2m_max"],
+            "temp_min_c": daily["temperature_2m_min"],
+        }
+    )
+    df["temp_media_c"] = df[["temp_max_c", "temp_min_c"]].mean(axis=1)
+
+    return df
+
+
+def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
+    parser = argparse.ArgumentParser(
+        description=(
+            "Descarga precipitación acumulada y temperaturas diarias desde la API "
+            "de Open-Meteo para un intervalo de al menos 10 días."
+        )
+    )
+    parser.add_argument("--lat", "--latitude", dest="latitude", type=float, required=True,
+                        help="Latitud en grados decimales.")
+    parser.add_argument("--lon", "--longitude", dest="longitude", type=float, required=True,
+                        help="Longitud en grados decimales.")
+    parser.add_argument("--start", dest="start_date", required=True,
+                        help="Fecha inicial en formato AAAA-MM-DD.")
+    parser.add_argument("--end", dest="end_date", required=True,
+                        help="Fecha final en formato AAAA-MM-DD.")
+    parser.add_argument("--timezone", default="America/Lima",
+                        help="Zona horaria para las fechas de salida (por defecto America/Lima).")
+    parser.add_argument("--out", dest="output_path", default="datos_meteo.xlsx",
+                        help="Ruta del archivo Excel a generar (por defecto datos_meteo.xlsx).")
+    return parser.parse_args(argv)
+
+
+def build_request_from_args(args: argparse.Namespace) -> MeteoRequest:
+    start = dt.date.fromisoformat(args.start_date)
+    end = dt.date.fromisoformat(args.end_date)
+    return MeteoRequest(
+        latitude=args.latitude,
+        longitude=args.longitude,
+        start_date=start,
+        end_date=end,
+        timezone=args.timezone,
+    )
+
+
+def main(argv: Optional[list[str]] = None) -> None:
+    args = parse_args(argv)
+    request = build_request_from_args(args)
+    df = fetch_daily_precip_and_temperature(request)
+
+    df.to_excel(args.output_path, index=False)
+    print(
+        "Datos descargados correctamente. Archivo generado:",
+        args.output_path,
+    )
+
+
+if __name__ == "__main__":
+    main()
 
EOF
)
