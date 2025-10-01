!/usr/bin/env python3
"""Descarga pronósticos diarios ECMWF Open Data a 10 días."""

import argparse
import csv
import datetime as dt
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List

import requests

ECMWF_API_URL = "https://api.open-meteo.com/v1/ecmwf"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Descarga pronósticos ECMWF (Open-Meteo) de precipitación y "
            "temperaturas (máxima y mínima) para los próximos 10 días."
        )
    )
    parser.add_argument("latitude", type=float, nargs="?", help="Latitud en grados decimales")
    parser.add_argument("longitude", type=float, nargs="?", help="Longitud en grados decimales")
    parser.add_argument(
        "--start-date",
        type=lambda s: dt.datetime.strptime(s, "%Y-%m-%d").date(),
        default=dt.date.today(),
        help="Fecha base (YYYY-MM-DD). Por defecto: hoy",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data"),
        help="Directorio donde se guardará el CSV (por defecto: data/)",
    )
    parser.add_argument(
        "--forecast-days",
        type=int,
        default=10,
        choices=range(1, 17),
        metavar="[1-16]",
        help="Número de días a descargar (máximo 16 según la API).",
    )
    parser.add_argument(
        "--points-file",
        type=Path,
        help="Ruta a un CSV con columnas Name, Latitud, Longitud para descargar múltiples puntos.",
    )
    args = parser.parse_args()

    if args.points_file is None:
        if args.latitude is None or args.longitude is None:
            parser.error("Debe proporcionar latitud y longitud o usar --points-file.")
    else:
        if not args.points_file.exists():
            parser.error(f"El archivo de puntos '{args.points_file}' no existe.")

    return args


def build_request_params(
    latitude: float,
    longitude: float,
    start_date: dt.date,
    forecast_days: int,
) -> Dict[str, Any]:
    end_date = start_date + dt.timedelta(days=forecast_days - 1)
    return {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "timezone": "UTC",
        "daily": [
            "precipitation_sum",
            "temperature_2m_max",
            "temperature_2m_min",
        ],
    }


def fetch_forecast(params: Dict[str, Any]) -> Dict[str, Any]:
    response = requests.get(ECMWF_API_URL, params=params, timeout=30)
    response.raise_for_status()
    return response.json()


def parse_daily_data(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    daily = payload.get("daily")
    if not daily:
        raise ValueError("La respuesta no contiene el bloque 'daily'.")

    dates = daily.get("time", [])
    precipitation = daily.get("precipitation_sum", [])
    temp_max = daily.get("temperature_2m_max", [])
    temp_min = daily.get("temperature_2m_min", [])

    if not (len(dates) == len(precipitation) == len(temp_max) == len(temp_min)):
        raise ValueError("Los arrays diarios no tienen el mismo tamaño.")

    rows: List[Dict[str, Any]] = []
    for date, pr, tmax, tmin in zip(dates, precipitation, temp_max, temp_min):
        rows.append(
            {
                "date": date,
                "precipitation_mm": pr,
                "temp_max_c": tmax,
                "temp_min_c": tmin,
            }
        )
    return rows


def save_csv(rows: List[Dict[str, Any]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(
            csvfile,
            fieldnames=["date", "precipitation_mm", "temp_max_c", "temp_min_c"],
        )
        writer.writeheader()
        writer.writerows(rows)


def slugify(value: str) -> str:
    slug = re.sub(r"[^\w-]+", "_", value.strip())
    return slug or "punto"


def iterate_points(args: argparse.Namespace) -> Iterable[Dict[str, Any]]:
    if args.points_file is None:
        yield {
            "name": f"{args.latitude:.4f}_{args.longitude:.4f}",
            "latitude": args.latitude,
            "longitude": args.longitude,
        }
        return

    with args.points_file.open("r", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            try:
                name = row["Name"].strip()
                latitude = float(row["Latitud"])
                longitude = float(row["Longitud"])
            except (KeyError, TypeError, ValueError) as exc:
                print(f"Fila ignorada por datos inválidos: {row!r} ({exc})")
                continue

            yield {
                "name": name,
                "latitude": latitude,
                "longitude": longitude,
            }


def main() -> None:
    args = parse_args()
    timestamp = args.start_date.strftime("%Y%m%d")

    for point in iterate_points(args):
        params = build_request_params(
            latitude=point["latitude"],
            longitude=point["longitude"],
            start_date=args.start_date,
            forecast_days=args.forecast_days,
        )
        payload = fetch_forecast(params)
        rows = parse_daily_data(payload)

        if args.points_file is None:
            output_file = args.output_dir / f"forecast_{timestamp}.csv"
        else:
            point_name = slugify(point["name"])
            output_file = args.output_dir / f"forecast_{point_name}_{timestamp}.csv"

        save_csv(rows, output_file)
        print(f"[{point['name']}] Datos guardados en {output_file}")


if __name__ == "__main__":
    main()
