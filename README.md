# Meshcore Signal Heatmap

Prototype toolkit for collecting Meshcore ping telemetry, storing it in a shared SQLite database, and exploring coverage through an interactive web interface. It includes:

- Serial ingestion console that streams ping data from a USB-connected Meshcore companion node directly into the database.
- Browser-based dashboards for visualizing filtered or full network heatmaps.
- REST APIs and CLI helpers for automation, data export, and integration.

## Features

- **Ping Telemetry Capture**: Record RSSI, SNR, round-trip time, antenna details, device metadata, and location.
- **SQLite Storage**: Shared development database checked into the repository under `data/meshcore_heatmap_dev.db`.
- **REST API**: Lightweight FastAPI service for ingesting telemetry and serving aggregated heatmap tiles.
- **Heatmap Generation**: Utilities to produce GeoJSON/HTML heatmap overlays from stored samples.

## Getting Started

### Prerequisites

- Python 3.10 or newer
- `pip` (or `uv`/`pipx`) for dependency installation

### Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Development Database

- `data/meshcore_heatmap_dev.db` is committed to the repo for team sharing.
- Treat it as disposable development data only—do **not** store production information here.
- If you prefer a local-only copy, duplicate the file and point the `DATABASE_URL` environment variable at your copy.

#### Alternative Shared DB

If storing SQLite in Git is inconvenient, point `DATABASE_URL` at a network path, or use a lightweight managed instance such as:

- [liteFS](https://fly.io/docs/litefs/) or [libSQL/Turso](https://turso.tech/) for a serverless SQLite-compatible backend
- A shared PostgreSQL container (e.g., via Docker Compose) by swapping the SQLAlchemy URI in `settings.py`

### Running the API

```bash
source .venv/bin/activate
uvicorn meshcore_heatmap.api:app --reload
```

API docs will be available at `http://127.0.0.1:8000/docs`.

### Web Dashboard

Launch the FastAPI server (see above), then open:

- `http://127.0.0.1:8000/` — **Filtered Heatmap**: choose metrics, time windows, and antenna/hardware filters to explore slices of the data.
- `http://127.0.0.1:8000/heatmap/full` — **Full Dataset Heatmap**: view every recorded sample, ideal for overall coverage checks.
- `http://127.0.0.1:8000/ingest` — **Device Ingestion Console**: connects to a USB Meshcore node using Web Serial, auto-fills device metadata when available, and lets you edit antenna/device details before capturing pings.

> **Web Serial requirement:** use a Chromium-based browser (Chrome, Edge, Brave). Localhost (`http://127.0.0.1`) counts as a secure origin, so HTTPS is not required for local testing.

### Ingesting Sample Data

```bash
python -m meshcore_heatmap.cli ingest-sample data/sample_pings.json
```

### Generating a Heatmap

```bash
python -m meshcore_heatmap.cli export-heatmap --output build/heatmap.html
```

Open the resulting HTML in a browser to view the overlay.

## Project Structure

```
meshcore_heatmap/
├── api.py              # FastAPI routes
├── cli.py              # Command-line utilities
├── db.py               # Database models and helpers
├── heatmap.py          # Heatmap rendering utilities
├── models.py           # Pydantic schemas
├── settings.py         # Environment/config management
└── __init__.py
data/
└── meshcore_heatmap_dev.db
```

## Environment Configuration

Override defaults using environment variables:

- `DATABASE_URL` – SQLAlchemy connection string (default: `sqlite:///data/meshcore_heatmap_dev.db`)
- `MAP_TILE_URL` – Custom base map tiles for heatmap rendering

Use a `.env` file for local settings (automatically loaded by `python-dotenv` if present).

## Testing

```bash
pytest
```

## Original Concept (Background)

The initial proposal for Meshcore signal heatmaps focused on device-initiated pings and deep app integration. For future reference, the original plan emphasized:

- Devices exchange short “ping” messages, recording signal clarity, endpoints, time, location, and attached gear.
- Data synchronizes to a central node/server once connectivity is available, where it’s blended into heatmap tiles with filtering by time, device, or antenna.
- The Meshcore app adds a toggleable heatmap layer with adjustable opacity, metric selection, and detailed popups—plus export options for further analysis.
- Operational safeguards such as spaced pings, battery-aware sampling, and opt-out privacy controls prevent network overload and respect user consent.
- Implementation steps: telemetry logging, sync pipeline, heatmap service, app UI work, and user-facing documentation.

These ideas remain compatible with the current toolkit and can guide the next phase of Meshcore app integration.

## Next Steps

- Integrate real Meshcore ping ingestion
- Adjust the Web Serial parser to match your firmware’s exact telemetry format
- Add authentication/authorization
- Hook into the Meshcore app UI for overlay rendering
- Extend CLI for field calibration workflows

## License

MIT


