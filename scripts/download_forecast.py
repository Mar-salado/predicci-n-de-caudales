 (cd "$(git rev-parse --show-toplevel)" && git apply --3way <<'EOF' 
diff --git a//dev/null b/scripts/download_forecast.py
index 0000000000000000000000000000000000000000..c102ec29e4735d1e092e50c0e9086eb142338707 100755
--- a//dev/null
+++ b/scripts/download_forecast.py
@@ -0,0 +1,119 @@
+#!/usr/bin/env python3
+"""Descarga pronósticos diarios ECMWF Open Data a 10 días."""
+
+import argparse
+import csv
+import datetime as dt
+from pathlib import Path
+from typing import Any, Dict, List
+
+import requests
+
+ECMWF_API_URL = "https://api.open-meteo.com/v1/ecmwf"
+
+
+def parse_args() -> argparse.Namespace:
+    parser = argparse.ArgumentParser(
+        description=(
+            "Descarga pronósticos ECMWF (Open-Meteo) de precipitación y "
+            "temperaturas (máxima y mínima) para los próximos 10 días."
+        )
+    )
+    parser.add_argument("latitude", type=float, help="Latitud en grados decimales")
+    parser.add_argument("longitude", type=float, help="Longitud en grados decimales")
+    parser.add_argument(
+        "--start-date",
+        type=lambda s: dt.datetime.strptime(s, "%Y-%m-%d").date(),
+        default=dt.date.today(),
+        help="Fecha base (YYYY-MM-DD). Por defecto: hoy",
+    )
+    parser.add_argument(
+        "--output-dir",
+        type=Path,
+        default=Path("data"),
+        help="Directorio donde se guardará el CSV (por defecto: data/)",
+    )
+    parser.add_argument(
+        "--forecast-days",
+        type=int,
+        default=10,
+        choices=range(1, 17),
+        metavar="[1-16]",
+        help="Número de días a descargar (máximo 16 según la API).",
+    )
+    return parser.parse_args()
+
+
+def build_request_params(args: argparse.Namespace) -> Dict[str, Any]:
+    end_date = args.start_date + dt.timedelta(days=args.forecast_days - 1)
+    return {
+        "latitude": args.latitude,
+        "longitude": args.longitude,
+        "start_date": args.start_date.isoformat(),
+        "end_date": end_date.isoformat(),
+        "timezone": "UTC",
+        "daily": [
+            "precipitation_sum",
+            "temperature_2m_max",
+            "temperature_2m_min",
+        ],
+    }
+
+
+def fetch_forecast(params: Dict[str, Any]) -> Dict[str, Any]:
+    response = requests.get(ECMWF_API_URL, params=params, timeout=30)
+    response.raise_for_status()
+    return response.json()
+
+
+def parse_daily_data(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
+    daily = payload.get("daily")
+    if not daily:
+        raise ValueError("La respuesta no contiene el bloque 'daily'.")
+
+    dates = daily.get("time", [])
+    precipitation = daily.get("precipitation_sum", [])
+    temp_max = daily.get("temperature_2m_max", [])
+    temp_min = daily.get("temperature_2m_min", [])
+
+    if not (len(dates) == len(precipitation) == len(temp_max) == len(temp_min)):
+        raise ValueError("Los arrays diarios no tienen el mismo tamaño.")
+
+    rows: List[Dict[str, Any]] = []
+    for date, pr, tmax, tmin in zip(dates, precipitation, temp_max, temp_min):
+        rows.append(
+            {
+                "date": date,
+                "precipitation_mm": pr,
+                "temp_max_c": tmax,
+                "temp_min_c": tmin,
+            }
+        )
+    return rows
+
+
+def save_csv(rows: List[Dict[str, Any]], output_path: Path) -> None:
+    output_path.parent.mkdir(parents=True, exist_ok=True)
+    with output_path.open("w", newline="", encoding="utf-8") as csvfile:
+        writer = csv.DictWriter(
+            csvfile,
+            fieldnames=["date", "precipitation_mm", "temp_max_c", "temp_min_c"],
+        )
+        writer.writeheader()
+        writer.writerows(rows)
+
+
+def main() -> None:
+    args = parse_args()
+    params = build_request_params(args)
+    payload = fetch_forecast(params)
+    rows = parse_daily_data(payload)
+
+    timestamp = args.start_date.strftime("%Y%m%d")
+    output_file = args.output_dir / f"forecast_{timestamp}.csv"
+    save_csv(rows, output_file)
+    print(f"Datos guardados en {output_file}")
+
+
+if __name__ == "__main__":
+    main()
 
EOF
)
