"""Command-line utilities for the Meshcore heatmap project."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer

from .db import PingSample, get_session, init_db
from .heatmap import render_heatmap_html
from .models import PingSampleIn
from .settings import settings

app = typer.Typer(add_completion=False, help="Meshcore heatmap CLI")


@app.command("init-db")
def init_db_command():
    """Create database tables."""
    init_db()
    typer.echo(f"Database initialized at {settings.database_url}")


@app.command("ingest-sample")
def ingest_sample(file: Path):
    """Ingest ping samples from a JSON file."""
    if not file.exists():
        typer.echo(f"File not found: {file}", err=True)
        raise typer.Exit(code=1)

    data = json.loads(file.read_text())
    if isinstance(data, dict):
        data = [data]

    samples = [PingSampleIn(**item) for item in data]
    inserted = 0
    with get_session() as session:
        for sample in samples:
            record = PingSample(
                origin_node_id=sample.origin_node_id,
                target_node_id=sample.target_node_id,
                created_at=sample.timestamp,
                latitude=sample.latitude,
                longitude=sample.longitude,
                altitude_m=sample.altitude_m,
                rssi_dbm=sample.rssi_dbm,
                snr_db=sample.snr_db,
                round_trip_ms=sample.round_trip_ms,
                hardware_model=sample.hardware_model,
                firmware_version=sample.firmware_version,
                antenna_model=sample.antenna_model,
                antenna_gain_dbi=sample.antenna_gain_dbi,
                antenna_polarization=sample.antenna_polarization,
                tx_power_dbm=sample.tx_power_dbm,
                frequency_mhz=sample.frequency_mhz,
                channel_id=sample.channel_id,
                region=sample.region,
            )
            session.add(record)
            inserted += 1
    typer.echo(f"Ingested {inserted} ping samples from {file}")


@app.command("export-heatmap")
def export_heatmap(
    output: Path = typer.Option(..., "--output", "-o", help="Path for the generated heatmap HTML file."),
    metric: str = typer.Option("rssi_dbm", "--metric", help="Metric to visualize. Default: rssi_dbm"),
    hours: Optional[int] = typer.Option(None, "--hours", help="Limit to samples within the last N hours."),
    hardware_model: Optional[str] = typer.Option(None, "--hardware-model", help="Filter by radio model."),
    antenna_model: Optional[str] = typer.Option(None, "--antenna-model", help="Filter by antenna model."),
):
    """Export a heatmap HTML file for offline viewing."""
    from sqlalchemy import func, select

    from .db import PingSample, get_session
    from .heatmap import build_heatmap_points

    init_db()

    column = getattr(PingSample, metric, None)
    if column is None:
        typer.echo(f"Unsupported metric: {metric}", err=True)
        raise typer.Exit(code=1)

    query = (
        select(
            PingSample.latitude,
            PingSample.longitude,
            func.avg(column).label("metric_value"),
            func.count(PingSample.id).label("sample_count"),
            func.max(PingSample.created_at).label("latest_seen"),
            func.avg(PingSample.antenna_gain_dbi).label("antenna_gain"),
            func.avg(PingSample.tx_power_dbm).label("tx_power"),
            func.max(PingSample.hardware_model).label("hardware_model"),
        )
        .where(PingSample.latitude.isnot(None), PingSample.longitude.isnot(None))
        .group_by(PingSample.latitude, PingSample.longitude)
    )

    if hours:
        from datetime import datetime, timedelta

        cutoff = datetime.utcnow() - timedelta(hours=hours)
        query = query.where(PingSample.created_at >= cutoff)

    if hardware_model:
        query = query.where(PingSample.hardware_model == hardware_model)

    if antenna_model:
        query = query.where(PingSample.antenna_model == antenna_model)

    with get_session() as session:
        results = session.execute(query).all()

    points = build_heatmap_points(results, metric)
    if not points:
        typer.echo("No data available to render heatmap.", err=True)
        raise typer.Exit(code=1)

    path = render_heatmap_html(points, output, metric)
    typer.echo(f"Heatmap written to {path}")


def main():
    app()


if __name__ == "__main__":
    main()


