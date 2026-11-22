# IoT Sensor CLI Analyzer

Aplikasi command line berbasis Python (hanya menggunakan **Python Standard Library**) untuk memvalidasi, membersihkan duplikat, menganalisis, dan mengekspor data telemetri sensor IoT dari file **CSV** ke **JSON**.

## Struktur Proyek

```text
iot_sensor_cli/
├── README.md
├── main.py
├── data/
│   ├── sensor_input.csv
│   └── sensor_report.json
└── sensor_analyzer/
    ├── __init__.py
    ├── io_handler.py
    ├── processor.py
    └── reporter.py
