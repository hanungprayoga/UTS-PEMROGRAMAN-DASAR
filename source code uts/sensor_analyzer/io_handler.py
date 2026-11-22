"""Modul penanganan input/output file CSV dan JSON dengan validasi defensif."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


class DataFormatError(Exception):
    """Exception khusus ketika struktur atau format file data tidak valid."""


REQUIRED_COLUMNS = {
    "timestamp",
    "node_id",
    "location",
    "temperature_c",
    "humidity_pct",
    "status",
}


def parse_sensor_row(row: dict[str, str], line_number: int) -> tuple[dict[str, Any] | None, str | None]:
    """Memvalidasi dan mengonversi satu baris CSV menjadi dictionary terstruktur.

    Args:
        row: Dictionary satu baris hasil pembacaan csv.DictReader.
        line_number: Nomor baris pada file CSV (termasuk header).

    Returns:
        Tuple (record_dict, error_message). Jika valid, error_message bernilai None.
    """
    if not isinstance(row, dict):
        return None, f"Baris {line_number}: format baris bukan dictionary."

    cleaned_raw = {
        str(k).strip(): (str(v).strip() if v is not None else "")
        for k, v in row.items()
        if k is not None
    }

    node_id = cleaned_raw.get("node_id", "").upper()
    location = cleaned_raw.get("location", "")
    timestamp = cleaned_raw.get("timestamp", "")
    status = cleaned_raw.get("status", "").upper() or "UNKNOWN"

    if not node_id or not timestamp:
        return None, f"Baris {line_number}: 'timestamp' atau 'node_id' kosong."

    try:
        temperature_c = float(cleaned_raw.get("temperature_c", ""))
        humidity_pct = float(cleaned_raw.get("humidity_pct", ""))
    except ValueError:
        return (
            None,
            f"Baris {line_number} ({node_id}): nilai suhu atau kelembapan bukan angka valid.",
        )

    # Defensive check untuk rentang fisik sensor yang masuk akal
    if not (-50.0 <= temperature_c <= 125.0):
        return (
            None,
            f"Baris {line_number} ({node_id}): suhu {temperature_c}C di luar rentang valid (-50..125C).",
        )

    if not (0.0 <= humidity_pct <= 100.0):
        return (
            None,
            f"Baris {line_number} ({node_id}): kelembapan {humidity_pct}% di luar rentang valid (0..100%).",
        )

    record = {
        "timestamp": timestamp,
        "node_id": node_id,
        "location": location or "Tidak Diketahui",
        "temperature_c": round(temperature_c, 2),
        "humidity_pct": round(humidity_pct, 2),
        "status": status,
    }
    return record, None


def load_sensor_csv(file_path: str | Path) -> tuple[list[dict[str, Any]], list[str]]:
    """Membaca dan memvalidasi data sensor dari file CSV.

    Args:
        file_path: Lokasi file CSV input.

    Returns:
        Tuple (valid_records, validation_issues).

    Raises:
        FileNotFoundError: Jika file tidak ditemukan.
        DataFormatError: Jika header kolom tidak sesuai atau file kosong.
    """
    path = Path(file_path)
    if not path.exists() or not path.is_file():
        raise FileNotFoundError(f"File input tidak ditemukan: {path}")

    valid_records: list[dict[str, Any]] = []
    validation_issues: list[str] = []

    with path.open(mode="r", encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        if not reader.fieldnames:
            raise DataFormatError(f"File CSV kosong atau tidak memiliki header: {path}")

        actual_columns = {col.strip() for col in reader.fieldnames if col is not None}
        missing_cols = REQUIRED_COLUMNS - actual_columns
        if missing_cols:
            raise DataFormatError(
                f"Kolom wajib tidak lengkap pada {path}: {', '.join(sorted(missing_cols))}"
            )

        for idx, row in enumerate(reader, start=2):
            record, err = parse_sensor_row(row, idx)
            if err is not None:
                validation_issues.append(err)
            elif record is not None:
                valid_records.append(record)

    return valid_records, validation_issues


def write_json_report(output_path: str | Path, payload: dict[str, Any]) -> Path:
    """Menyimpan hasil analisis sensor ke file JSON.

    Args:
        output_path: Lokasi file JSON keluaran.
        payload: Dictionary data laporan yang akan disimpan.

    Returns:
        Objek Path file JSON yang berhasil ditulis.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open(mode="w", encoding="utf-8") as json_file:
        json.dump(payload, json_file, indent=2, ensure_ascii=False)

    return path
