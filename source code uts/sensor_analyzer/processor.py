"""Modul pemrosesan, deduplikasi, klasifikasi, filtering, dan rekapitulasi data sensor."""

from __future__ import annotations

from typing import Any


def classify_reading(temperature_c: float, humidity_pct: float) -> str:
    """Menentukan tingkat kondisi pembacaan sensor berdasarkan suhu dan kelembapan.

    Args:
        temperature_c: Suhu dalam derajat Celsius.
        humidity_pct: Kelembapan relatif dalam persen (0-100).

    Returns:
        Label kondisi: 'CRITICAL', 'WARNING', atau 'NORMAL'.
    """
    if temperature_c >= 35.0 or humidity_pct > 85.0:
        return "CRITICAL"
    elif temperature_c >= 30.0 or temperature_c < 15.0 or humidity_pct < 20.0:
        return "WARNING"
    else:
        return "NORMAL"


def deduplicate_records(records: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], int]:
    """Menghapus record duplikat menggunakan struktur data set.

    Args:
        records: Daftar record pembacaan sensor.

    Returns:
        Tuple (unique_records, duplicate_count).
    """
    seen_signatures: set[tuple[str, str, float, float]] = set()
    unique_records: list[dict[str, Any]] = []
    duplicate_count = 0

    for rec in records:
        signature = (
            rec["timestamp"],
            rec["node_id"],
            rec["temperature_c"],
            rec["humidity_pct"],
        )
        if signature in seen_signatures:
            duplicate_count += 1
            continue

        seen_signatures.add(signature)
        unique_records.append(rec)

    return unique_records, duplicate_count


def enrich_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Menambahkan field 'alert_level' pada setiap record tanpa memodifikasi input asli.

    Args:
        records: Daftar record sensor yang telah tervalidasi.

    Returns:
        Daftar record baru yang telah dilengkapi status alert_level.
    """
    enriched: list[dict[str, Any]] = []
    for rec in records:
        item = dict(rec)
        item["alert_level"] = classify_reading(item["temperature_c"], item["humidity_pct"])
        enriched.append(item)
    return enriched


def filter_records(
    records: list[dict[str, Any]],
    node_id: str | None = None,
    min_temperature: float | None = None,
    alert_level: str | None = None,
) -> list[dict[str, Any]]:
    """Menyaring record berdasarkan node_id, batas suhu minimum, atau level peringatan.

    Args:
        records: Daftar record sensor.
        node_id: Filter ID node spesifik (opsional).
        min_temperature: Filter suhu >= nilai ini (opsional).
        alert_level: Filter level 'NORMAL', 'WARNING', atau 'CRITICAL' (opsional).

    Returns:
        Daftar record yang memenuhi seluruh kriteria filter.
    """
    normalized_node = node_id.strip().upper() if node_id else None
    normalized_alert = alert_level.strip().upper() if alert_level else None

    results: list[dict[str, Any]] = []
    for rec in records:
        if normalized_node and rec.get("node_id") != normalized_node:
            continue
        if min_temperature is not None and rec.get("temperature_c", 0.0) < min_temperature:
            continue
        if normalized_alert and rec.get("alert_level") != normalized_alert:
            continue
        results.append(rec)

    return results


def summarize_by_node(records: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Mengelompokkan dan menghitung statistik rekapitulasi per node_id.

    Args:
        records: Daftar record sensor yang telah dilengkapi 'alert_level'.

    Returns:
        Dictionary rekapitulasi dengan key berupa node_id.
    """
    grouped: dict[str, list[dict[str, Any]]] = {}
    for rec in records:
        nid = rec["node_id"]
        grouped.setdefault(nid, []).append(rec)

    # Set comprehension untuk daftar unik node dan list comprehension untuk node bermasalah
    unique_nodes: set[str] = {rec["node_id"] for rec in records}
    alert_nodes: list[str] = [
        rec["node_id"] for rec in records if rec.get("alert_level") != "NORMAL"
    ]

    # Dictionary comprehension untuk rata-rata suhu cepat per node
    avg_temp_map: dict[str, float] = {
        nid: round(sum(item["temperature_c"] for item in items) / len(items), 2)
        for nid, items in grouped.items()
        if items
    }

    summary: dict[str, dict[str, Any]] = {}
    for nid in sorted(unique_nodes):
        items = grouped.get(nid, [])
        if not items:
            continue

        temps = [item["temperature_c"] for item in items]
        humidities = [item["humidity_pct"] for item in items]
        locations = sorted({item["location"] for item in items})

        level_counts = {"NORMAL": 0, "WARNING": 0, "CRITICAL": 0}
        for item in items:
            lvl = item.get("alert_level", "NORMAL")
            level_counts[lvl] = level_counts.get(lvl, 0) + 1

        if level_counts["CRITICAL"] > 0:
            highest_alert = "CRITICAL"
        elif level_counts["WARNING"] > 0:
            highest_alert = "WARNING"
        else:
            highest_alert = "NORMAL"

        summary[nid] = {
            "node_id": nid,
            "locations": locations,
            "reading_count": len(items),
            "avg_temperature_c": avg_temp_map.get(nid, 0.0),
            "min_temperature_c": min(temps),
            "max_temperature_c": max(temps),
            "avg_humidity_pct": round(sum(humidities) / len(humidities), 2),
            "alert_counts": level_counts,
            "highest_alert": highest_alert,
            "has_alert_history": nid in set(alert_nodes),
        }

    return summary
