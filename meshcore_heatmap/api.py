"""FastAPI application exposing Meshcore heatmap endpoints."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import List, Optional

from fastapi.templating import Jinja2Templates
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from fastapi import (
    Depends,
    FastAPI,
    HTTPException,
    Query,
    Request,
    status,
)
from fastapi.responses import HTMLResponse

from .db import PingSample, get_session, init_db
from .heatmap import build_heatmap_points
from .models import HeatmapResponse, PingSampleIn, PingSampleOut
from .settings import settings

app = FastAPI(
    title="Meshcore Heatmap Service",
    description="Collects Meshcore ping telemetry and serves heatmap overlays.",
    version="0.1.0",
)

templates = Jinja2Templates(directory=str(settings.project_root / "templates"))


def get_db_session():
    with get_session() as session:
        yield session


@app.on_event("startup")
def startup() -> None:
    """Initialize database on startup."""
    init_db()


@app.post(
    "/ping-samples",
    response_model=PingSampleOut,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest ping sample",
)
def create_ping_sample(sample: PingSampleIn, session: Session = Depends(get_db_session)):
    """Store a new ping telemetry sample."""
    timestamp = sample.timestamp
    if isinstance(timestamp, (int, float)):  # type: ignore[arg-type]
        timestamp = datetime.utcfromtimestamp(timestamp)  # type: ignore[assignment]

    record = PingSample(
        origin_node_id=sample.origin_node_id,
        target_node_id=sample.target_node_id,
        created_at=timestamp or datetime.utcnow(),
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
    session.flush()
    session.refresh(record)
    return record


@app.post(
    "/ping-samples/bulk",
    response_model=List[PingSampleOut],
    status_code=status.HTTP_201_CREATED,
    summary="Ingest multiple ping samples",
)
def create_ping_samples(samples: List[PingSampleIn], session: Session = Depends(get_db_session)):
    """Store multiple ping telemetry samples."""
    if not samples:
        raise HTTPException(status_code=400, detail="No samples provided.")

    records: List[PingSample] = []
    for sample in samples:
        timestamp = sample.timestamp
        if isinstance(timestamp, (int, float)):  # type: ignore[arg-type]
            timestamp = datetime.utcfromtimestamp(timestamp)  # type: ignore[assignment]

        record = PingSample(
            origin_node_id=sample.origin_node_id,
            target_node_id=sample.target_node_id,
            created_at=timestamp or datetime.utcnow(),
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
        records.append(record)

    session.flush()
    for record in records:
        session.refresh(record)
    return records


@app.get(
    "/heatmap",
    response_model=HeatmapResponse,
    summary="Get aggregated heatmap points",
)
def get_heatmap(
    metric: str = Query("rssi_dbm", regex="^(rssi_dbm|snr_db|round_trip_ms)$"),
    hours: Optional[int] = Query(None, ge=1, le=168),
    hardware_model: Optional[str] = None,
    antenna_model: Optional[str] = None,
    session: Session = Depends(get_db_session),
):
    """Return aggregate heatmap data for the requested metric."""
    column = getattr(PingSample, metric, None)
    if column is None:
        raise HTTPException(status_code=400, detail="Unsupported metric.")

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
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        query = query.where(PingSample.created_at >= cutoff)

    if hardware_model:
        query = query.where(PingSample.hardware_model == hardware_model)

    if antenna_model:
        query = query.where(PingSample.antenna_model == antenna_model)

    results = session.execute(query).all()
    points = build_heatmap_points(results, metric)
    if not points:
        return HeatmapResponse(metric=metric, points=[], min_value=None, max_value=None)

    min_value = min(p.intensity for p in points)
    max_value = max(p.intensity for p in points)

    return HeatmapResponse(metric=metric, points=points, min_value=min_value, max_value=max_value)


@app.get(
    "/ping-samples/recent",
    response_model=List[PingSampleOut],
    summary="List recent ping samples",
)
def recent_ping_samples(
    limit: int = Query(25, ge=1, le=500),
    session: Session = Depends(get_db_session),
):
    """Return the most recent ping samples."""
    query = select(PingSample).order_by(PingSample.created_at.desc()).limit(limit)
    records = session.execute(query).scalars().all()
    return records


@app.get("/health", summary="Service healthcheck")
def healthcheck():
    return {"status": "ok", "database": settings.database_url}


@app.get("/", response_class=HTMLResponse, summary="Interactive heatmap dashboard")
def dashboard(request: Request):
    """Render the web dashboard with live heatmap visualization."""
    context = {
        "request": request,
        "map_tile_url": settings.map_tile_url or "",
        "heatmap_min_opacity": settings.heatmap_min_opacity,
        "heatmap_radius": settings.heatmap_radius,
        "heatmap_blur": settings.heatmap_blur,
        "heatmap_max_zoom": settings.heatmap_max_zoom,
        "filters_enabled": True,
        "auto_refresh_ms": 30000,
    }
    return templates.TemplateResponse("index.html", context)


@app.get(
    "/heatmap/full",
    response_class=HTMLResponse,
    summary="Full-dataset heatmap view",
)
def full_heatmap(request: Request):
    """Render the full database heatmap without additional filters."""
    context = {
        "request": request,
        "map_tile_url": settings.map_tile_url or "",
        "heatmap_min_opacity": settings.heatmap_min_opacity,
        "heatmap_radius": settings.heatmap_radius,
        "heatmap_blur": settings.heatmap_blur,
        "heatmap_max_zoom": settings.heatmap_max_zoom,
        "filters_enabled": False,
        "auto_refresh_ms": 60000,
    }
    return templates.TemplateResponse("index.html", context)


@app.get("/ingest", response_class=HTMLResponse, summary="Device ingestion console")
def ingest_console(request: Request):
    """Render the Web Serial ingestion console for capturing pings."""
    context = {
        "request": request,
        "map_tile_url": settings.map_tile_url or "",
    }
    return templates.TemplateResponse("ingest.html", context)


