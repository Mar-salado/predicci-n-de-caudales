#!/usr/bin/env python3
"""Descarga pronósticos diarios ECMWF Open Data a 10 días."""

import argparse
import csv
import datetime as dt
import re
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List, cast

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
    parser.add_argument(
        "--interval-minutes",
        type=float,
        default=60,
        help="Intervalo en minutos entre descargas consecutivas en modo iterativo (por defecto: 60).",
    )
    loop_group = parser.add_mutually_exclusive_group()
    loop_group.add_argument(
        "--iterations",
        type=int,
        metavar="N",
        help="Número de iteraciones a ejecutar. Si se omite, se realiza una sola iteración.",
    )
    loop_group.add_argument(
        "--continuous",
        action="store_true",
        help="Ejecuta descargas indefinidas hasta recibir una señal de parada (Ctrl+C).",
    )
    parser.add_argument(
        "--keep-last",
        type=int,
        default=0,
        metavar="N",
        help=(
            "Número de archivos más recientes a conservar por punto. Si es 0, no se elimina ninguno."
        ),
    )
    args = parser.parse_args()

    if args.points_file is None:
        if args.latitude is None or args.longitude is None:
            parser.error("Debe proporcionar latitud y longitud o usar --points-file.")
    else:
        if not args.points_file.exists():
            parser.error(f"El archivo de puntos '{args.points_file}' no existe.")

    if args.iterations is None and not args.continuous:
        args.iterations = 1
    if args.iterations is not None and args.iterations < 1:
        parser.error("--iterations debe ser un entero positivo.")
    if args.interval_minutes <= 0:
        parser.error("--interval-minutes debe ser un número positivo.")
    if args.keep_last < 0:
        parser.error("--keep-last no puede ser negativo.")

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
@@ -106,78 +143,118 @@ def parse_daily_data(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
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


def rotate_history(output_dir: Path, point_slug: str, keep_last: int) -> None:
    if keep_last <= 0:
        return

    pattern = f"forecast_{point_slug}_*.csv"
    files = sorted(output_dir.glob(pattern))
    excess = len(files) - keep_last
    for old_file in files[: max(0, excess)]:
        try:
            old_file.unlink()
        except OSError as exc:
            print(f"No se pudo eliminar '{old_file}': {exc}")


def run_iteration(args: argparse.Namespace, run_timestamp: dt.datetime) -> None:
    run_id = run_timestamp.strftime("%Y%m%d_%H%M%S")

    for point in iterate_points(args):
        params = build_request_params(
            latitude=point["latitude"],
            longitude=point["longitude"],
            start_date=args.start_date,
            forecast_days=args.forecast_days,
        )
        payload = fetch_forecast(params)
        rows = parse_daily_data(payload)

        point_name = slugify(point["name"])
        output_file = args.output_dir / f"forecast_{point_name}_{run_id}.csv"

        save_csv(rows, output_file)
        rotate_history(args.output_dir, point_name, args.keep_last)

        print(f"[{point['name']}] ({run_id}) Datos guardados en {output_file}")


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
    iteration = 0

    while True:
        iteration += 1
        run_timestamp = dt.datetime.now()
        print(
            f"Iniciando iteración {iteration} a las "
            f"{run_timestamp.isoformat(timespec='seconds')}"
        )

        run_iteration(args, run_timestamp)

        if not args.continuous and iteration >= cast(int, args.iterations):
            break

        sleep_seconds = args.interval_minutes * 60
        print(
            f"Esperando {args.interval_minutes} minutos antes de la siguiente iteración..."
        )
        try:
            time.sleep(sleep_seconds)
        except KeyboardInterrupt:
            print("Interrupción recibida durante la espera. Finalizando.")
            break


if __name__ == "__main__":
    main()
