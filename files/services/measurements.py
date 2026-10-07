from __future__ import annotations

from dataclasses import dataclass

import geopandas as gpd
from shapely.geometry import mapping
from shapely.geometry.base import BaseGeometry

from files.services.crs import crs_to_string, projected_crs_for_geometry


AREA_GEOMETRY_TYPES = {"Polygon", "MultiPolygon"}
LENGTH_GEOMETRY_TYPES = {"LineString", "MultiLineString"}
POINT_GEOMETRY_TYPES = {"Point", "MultiPoint"}


@dataclass
class MeasurementResult:
    measurement_type: str
    value: float | None
    unit: str
    error: str = ""


def _transform_geometry(geometry: BaseGeometry, source_crs: str) -> BaseGeometry:
    target_crs = projected_crs_for_geometry(geometry, source_crs)
    gdf = gpd.GeoDataFrame(geometry=[geometry], crs=source_crs)
    projected = gdf.to_crs(target_crs)
    return projected.geometry.iloc[0]


def calculate_measurement(geometry: BaseGeometry, source_crs: str) -> MeasurementResult:
    geometry_type = geometry.geom_type

    if geometry_type in POINT_GEOMETRY_TYPES:
        return MeasurementResult(measurement_type="none", value=None, unit="")

    if geometry_type in AREA_GEOMETRY_TYPES:
        try:
            projected = _transform_geometry(geometry, source_crs)
            return MeasurementResult(
                measurement_type="area",
                value=float(projected.area),
                unit="m2",
            )
        except Exception as exc:
            return MeasurementResult(
                measurement_type="area",
                value=None,
                unit="m2",
                error=str(exc),
            )

    if geometry_type in LENGTH_GEOMETRY_TYPES:
        try:
            projected = _transform_geometry(geometry, source_crs)
            return MeasurementResult(
                measurement_type="length",
                value=float(projected.length),
                unit="m",
            )
        except Exception as exc:
            return MeasurementResult(
                measurement_type="length",
                value=None,
                unit="m",
                error=str(exc),
            )

    return MeasurementResult(
        measurement_type="unsupported",
        value=None,
        unit="",
        error=f"Geometry type '{geometry_type}' is not supported for measurement.",
    )


def geometry_to_geojson(geometry: BaseGeometry) -> dict:
    return mapping(geometry)
