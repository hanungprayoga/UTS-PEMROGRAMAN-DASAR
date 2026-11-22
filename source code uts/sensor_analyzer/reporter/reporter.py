"""Modul presentasi output di terminal command line."""

from __future__ import annotations

from typing import Any


def print_summary_table(summary: dict[str, dict[str, Any]]) -> None:
    """Mencetak tabel ringkasan statistik per node ke terminal.

    Args:
        summary: Dictionary hasil summarize_by_node().
    """
    print("\n=== REKAPITULASI PER NODE SENSOR ===")
    if not summary:
        print("Tidak ada data node yang dapat direkapitulasi.")
        return

    header = (
        f"{'NODE ID':<10} | {'LOKASI':<14} | {'JML':>3} | "
        f"{'AVG T(C)':>8} | {'MIN/MAX T':>11} | {'AVG H(%)':>8} | {'STATUS TERTINGGI':<16}"
    )
    print(header)
    print("-" * len(header))

    for nid, stats in summary.items():
        loc_display = ", ".join(stats["locations"])[:14]
        minmax_t = f"{stats['min_temperature_c']:.1f}/{stats['max_temperature_c']:.1f}"
        print(
            f"{nid:<10} | {loc_display:<14} | {stats['reading_count']:>3} | "
            f"{stats['avg_temperature_c']:>8.2f} | {minmax_t:>11} | "
            f"{stats['avg_humidity_pct']:>8.2f} | {stats['highest_alert']:<16}"
        )


def print_records_list(title: str, records: list[dict[str, Any]]) -> None:
    """Mencetak daftar record hasil filtering atau pencarian.

    Args:
        title: Judul bagian tampilan.
        records: Daftar record sensor.
    """
    print(f"\n=== {title} ({len(records)} data) ===")
    if not records:
        print("Tidak ada data yang cocok dengan kriteria.")
        return

    for rec in records:
        print(
            f"- [{rec['timestamp']}] {rec['node_id']} ({rec['location']}) "
            f"-> Suhu: {rec['temperature_c']}C, Kelembapan: {rec['humidity_pct']}%, "
            f"Level: {rec['alert_level']}"
        )


def print_issues(title: str, issues: list[str]) -> None:
    """Mencetak catatan validasi atau anomali data.

    Args:
        title: Judul bagian catatan.
        issues: Daftar pesan isu/error.
    """
    print(f"\n=== {title} ({len(issues)}) ===")
    if not issues:
        print("Tidak ada isu.")
        return

    for issue in issues:
        print(f"  * {issue}")
