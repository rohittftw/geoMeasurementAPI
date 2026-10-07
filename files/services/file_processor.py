from __future__ import annotations

import shutil
import tempfile
import zipfile
from pathlib import Path

import geopandas as gpd
import pandas as pd

from files.models import FeatureRecord, GeospatialFile, ProcessingStatus
from files.services.crs import crs_to_string
from files.services.measurements import calculate_measurement, geometry_to_geojson


ALLOWED_EXTENSIONS = {".zip", ".kml"}


class FileProcessingError(Exception):
    pass


def validate_upload(filename: str) -> None:
    extension = Path(filename).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise FileProcessingError(
            "Unsupported file type. Upload a .zip containing a Shapefile or a .kml file."
        )


def _read_geodataframe(file_path: Path) -> gpd.GeoDataFrame:
    extension = file_path.suffix.lower()

    if extension == ".kml":
        return gpd.read_file(file_path, driver="KML")

    if extension == ".zip":
        with tempfile.TemporaryDirectory() as temp_dir:
            with zipfile.ZipFile(file_path, "r") as archive:
                archive.extractall(temp_dir)

            shapefiles = list(Path(temp_dir).rglob("*.shp"))
            if not shapefiles:
                raise FileProcessingError("No .shp file found inside the uploaded zip archive.")

            return gpd.read_file(shapefiles[0])

    raise FileProcessingError("Unsupported file type.")


def process_geospatial_file(geospatial_file: GeospatialFile) -> None:
    geospatial_file.status = ProcessingStatus.PROCESSING
    geospatial_file.error_message = ""
    geospatial_file.save(update_fields=["status", "error_message", "updated_at"])

    try:
        source_path = Path(geospatial_file.file.path)
        gdf = _read_geodataframe(source_path)

        if gdf.empty:
            raise FileProcessingError("The uploaded file contains no features.")

        source_crs = crs_to_string(gdf.crs)
        geospatial_file.crs = source_crs
        geospatial_file.feature_count = len(gdf)
        geospatial_file.features.all().delete()

        feature_records = []
        for index, row in gdf.iterrows():
            geometry = row.geometry
            if geometry is None or geometry.is_empty:
                continue

            properties = {
                key: _serialize_property(value)
                for key, value in row.items()
                if key != "geometry"
            }

            measurement = calculate_measurement(geometry, source_crs)

            feature_records.append(
                FeatureRecord(
                    geospatial_file=geospatial_file,
                    feature_index=len(feature_records),
                    geometry_type=geometry.geom_type,
                    geometry=geometry_to_geojson(geometry),
                    crs=source_crs,
                    properties=properties,
                    measurement_type=measurement.measurement_type,
                    measurement_value=measurement.value,
                    measurement_unit=measurement.unit,
                    measurement_error=measurement.error,
                )
            )

        FeatureRecord.objects.bulk_create(feature_records)
        geospatial_file.feature_count = len(feature_records)
        geospatial_file.status = ProcessingStatus.COMPLETED
        geospatial_file.save(
            update_fields=["crs", "feature_count", "status", "updated_at"]
        )
    except Exception as exc:
        geospatial_file.status = ProcessingStatus.FAILED
        geospatial_file.error_message = str(exc)
        geospatial_file.save(
            update_fields=["status", "error_message", "updated_at"]
        )
        raise


def _serialize_property(value):
    if value is None:
        return None
    if isinstance(value, float) and pd.isna(value):
        return None
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    if hasattr(value, "isoformat"):
        return value.isoformat()
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            pass
    return value
