"""Pydantic schemas for API and CLI interactions."""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, ConfigDict


class PingSampleIn(BaseModel):
    """Payload for ingesting a new ping sample."""

    origin_node_id: str = Field(..., description="Node ID of the transmitting radio")
    target_node_id: str = Field(..., description="Node ID of the responding radio")
    timestamp: Optional[datetime] = Field(None, description="UTC timestamp of the measurement")

    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    altitude_m: Optional[float] = None

    rssi_dbm: Optional[float] = None
    snr_db: Optional[float] = None
    round_trip_ms: Optional[float] = None

    hardware_model: Optional[str] = None
    firmware_version: Optional[str] = None
    antenna_model: Optional[str] = None
    antenna_gain_dbi: Optional[float] = None
    antenna_polarization: Optional[str] = None
    tx_power_dbm: Optional[float] = None
    frequency_mhz: Optional[float] = None

    channel_id: Optional[str] = None
    region: Optional[str] = None


class PingSampleOut(BaseModel):
    """Response model representing a stored sample."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    origin_node_id: str
    target_node_id: str
    latitude: Optional[float]
    longitude: Optional[float]
    altitude_m: Optional[float]
    rssi_dbm: Optional[float]
    snr_db: Optional[float]
    round_trip_ms: Optional[float]
    hardware_model: Optional[str]
    firmware_version: Optional[str]
    antenna_model: Optional[str]
    antenna_gain_dbi: Optional[float]
    antenna_polarization: Optional[str]
    tx_power_dbm: Optional[float]
    frequency_mhz: Optional[float]
    channel_id: Optional[str]
    region: Optional[str]

class HeatmapPoint(BaseModel):
    """Represents a geographic point and intensity for rendering."""

    latitude: float
    longitude: float
    intensity: float
    samples: int
    latest_seen: Optional[datetime]
    antenna_gain_dbi: Optional[float] = None
    tx_power_dbm: Optional[float] = None
    hardware_model: Optional[str] = None


class HeatmapResponse(BaseModel):
    """Response payload for heatmap layers."""

    metric: str
    points: List[HeatmapPoint]
    min_value: Optional[float]
    max_value: Optional[float]


