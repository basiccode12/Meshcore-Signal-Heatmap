"""Heatmap generation utilities."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Tuple

import folium
from folium.plugins import HeatMap

from .models import HeatmapPoint
from .settings import settings


def build_heatmap_points(
    records: Iterable[Tuple[float, float, Optional[float], Optional[float], datetime, Optional[float], Optional[float], Optional[str]]],
    metric: str,
) -> List[HeatmapPoint]:
    """Convert database rows into heatmap points."""
    points: List[HeatmapPoint] = []
    for latitude, longitude, metric_value, sample_count, latest_seen, antenna_gain, tx_power, hardware_model in records:
        if latitude is None or longitude is None or metric_value is None:
            continue
        points.append(
            HeatmapPoint(
                latitude=latitude,
                longitude=longitude,
                intensity=metric_value,
                samples=int(sample_count or 1),
                latest_seen=latest_seen,
                antenna_gain_dbi=antenna_gain,
                tx_power_dbm=tx_power,
                hardware_model=hardware_model,
            )
        )
    return points


def render_heatmap_html(points: Sequence[HeatmapPoint], output_path: Path, metric: str) -> Path:
    """Render a Folium heatmap to an HTML file."""
    if not points:
        raise ValueError("No heatmap points available to render.")

    avg_lat = sum(p.latitude for p in points) / len(points)
    avg_lon = sum(p.longitude for p in points) / len(points)

    base_map = folium.Map(location=[avg_lat, avg_lon], tiles=settings.map_tile_url or "OpenStreetMap", zoom_start=11)

    heat_data = [[p.latitude, p.longitude, p.intensity] for p in points]
    HeatMap(
        heat_data,
        min_opacity=settings.heatmap_min_opacity,
        radius=settings.heatmap_radius,
        blur=settings.heatmap_blur,
        max_zoom=settings.heatmap_max_zoom,
    ).add_to(base_map)

    for point in points:
        folium.CircleMarker(
            location=(point.latitude, point.longitude),
            radius=4,
            fill=True,
            color="white",
            fill_opacity=0.0,
            tooltip=folium.Tooltip(
                f"{metric}: {point.intensity:.1f}\nSamples: {point.samples}\n"
                f"Antenna gain: {point.antenna_gain_dbi or 'n/a'} dBi"
            ),
        ).add_to(base_map)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    base_map.save(str(output_path))
    return output_path


