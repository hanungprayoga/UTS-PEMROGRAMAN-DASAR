"""Aplikasi CLI Pemantauan & Analisis Data Sensor IoT."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
import sys
from typing import Any

from sensor_analyzer import __version__
from sensor_analyzer.io_handler import DataFormatError, load_sensor_csv, write_json_report
from sensor_analyzer.processor import (
    deduplicate_records,
    enrich_records,
    filter_records,
    summarize_by_node,
)
from sensor_analyzer.reporter import print_issues, print_records_list, print_summary_table


def build_parser() -> argparse.ArgumentParser:
    """Membuat parser argumen baris perintah (CLI)."""
    parser = argparse.ArgumentParser(
        prog="iot-sensor-cli",
        description="CLI untuk membersihkan, menganalisis, dan mengekspor data sensor IoT (CSV -> JSON).",
    )
    parser.add_argument(
        "--input",
        "-i",
        default="data/sensor_input.csv",
        help="Path file CSV input (default: data/sensor_input.csv)",
    )
    parser.add_argument(
        "--output",
        "-o",
        default="data/sensor_report.json",
        help="Path file JSON output (default: data/sensor_report.json)",
    )
    parser.add_argument(
        "--node",
        "-n",
        default=None,
        help="Filter pembacaan berdasarkan node_id tertentu (contoh: NODE-01)",
    )
    parser.add_argument(
        "--min-temp",
        type=float,
        default=None,
        help="Filter pembacaan dengan suhu >= nilai tertentu (contoh: 30.0)",
    )
    parser.add_argument(
        "--alert-level",
        choices=["NORMAL", "WARNING", "CRITICAL"],
        default=None,
        help="Filter berdasarkan level kondisi",
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Jalankan mode menu interaktif setelah analisis awal",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    return parser


def run_interactive_menu(enriched_records: list[dict[str, Any]], summary: dict[str, dict[str, Any]]) -> None:
    """Menjalankan menu interaktif CLI untuk pencarian dan filter data."""
    while True:
        print("\n--- MENU INTERAKTIF SENSOR CLI ---")
        print("1. Tampilkan rekapitulasi per node")
        print("2. Cari/filter data berdasarkan Node ID")
        print("3. Filter data berdasarkan suhu minimum")
        print("4. Tampilkan semua record WARNING & CRITICAL")
        print("0. Keluar")

        choice = input("Pilih menu [0-4]: ").strip()
        if choice == "1":
            print_summary_table(summary)
        elif choice == "2":
            target_node = input("Masukkan Node ID (contoh: NODE-01): ").strip()
            if not target_node:
                print("Input Node ID tidak boleh kosong.")
                continue
            filtered = filter_records(enriched_records, node_id=target_node)
            print_records_list(f"HASIL FILTER NODE {target_node.upper()}", filtered)
        elif choice == "3":
            raw_temp = input("Masukkan batas suhu minimum (angka, misal 30): ").strip()
            try:
                threshold = float(raw_temp)
            except ValueError:
                print("Input suhu tidak valid. Harap masukkan angka.")
                continue
            filtered = filter_records(enriched_records, min_temperature=threshold)
            print_records_list(f"DATA SUHU >= {threshold}C", filtered)
        elif choice == "4":
            alerts = [
                r for r in enriched_records if r.get("alert_level") in {"WARNING", "CRITICAL"}
            ]
            print_records_list("DAFTAR PEMBACAAN WARNING / CRITICAL", alerts)
        elif choice == "0":
            print("Keluar dari menu interaktif.")
            break
        else:
            print("Pilihan menu tidak dikenali. Silakan pilih angka 0-4.")


def main(argv: list[str] | None = None) -> int:
    """Fungsi utama eksekusi program CLI."""
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        raw_records, validation_issues = load_sensor_csv(args.input)
        unique_records, duplicate_count = deduplicate_records(raw_records)
        enriched_records = enrich_records(unique_records)
        summary = summarize_by_node(enriched_records)

        filtered_records = filter_records(
            enriched_records,
            node_id=args.node,
            min_temperature=args.min_temp,
            alert_level=args.alert_level,
        )

        print(f"Berhasil memuat {len(raw_records)} baris valid dari '{args.input}'.")
        print(f"Duplikat terhapus: {duplicate_count} | Record bersih: {len(enriched_records)}")

        print_summary_table(summary)

        if args.node or args.min_temp is not None or args.alert_level:
            print_records_list("HASIL FILTER ARGUMEN CLI", filtered_records)

        alert_records = [
            rec for rec in enriched_records if rec.get("alert_level") != "NORMAL"
        ]
        print_records_list("PERINGATAN & KONDISI KRITIS", alert_records)
        print_issues("CATATAN VALIDASI DATA INPUT", validation_issues)

        report_payload = {
            "metadata": {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "source_file": str(Path(args.input)),
                "version": __version__,
                "raw_valid_rows": len(raw_records),
                "duplicates_removed": duplicate_count,
                "clean_records_count": len(enriched_records),
                "validation_issues_count": len(validation_issues),
            },
            "node_summary": summary,
            "alerts": alert_records,
            "filtered_records": filtered_records,
            "validation_issues": validation_issues,
        }

        saved_path = write_json_report(args.output, report_payload)
        print(f"\nLaporan JSON berhasil disimpan ke: {saved_path}")

        if args.interactive:
            run_interactive_menu(enriched_records, summary)

        return 0

    except FileNotFoundError as exc:
        print(f"[ERROR - FILE TIDAK DITEMUKAN] {exc}", file=sys.stderr)
        return 1
    except DataFormatError as exc:
        print(f"[ERROR - FORMAT DATA TIDAK VALID] {exc}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"[ERROR - I/O SISTEM] {exc}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    sys.exit(main())
