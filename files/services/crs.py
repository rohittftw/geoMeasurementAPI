from __future__ import annotations

from pyproj import CRS


def crs_to_string(crs) -> str:
    if crs is None:
        return "EPSG:4326"
    if isinstance(crs, str):
        return crs
    try:
        authority = crs.to_authority()
        if authority:
            return f"{authority[0]}:{authority[1]}"
    except Exception:
        pass
    return crs.to_string()


def is_geographic(crs_string: str) -> bool:
    try:
        return CRS.from_user_input(crs_string).is_geographic
    except Exception:
        return True


def utm_epsg_for_point(lon: float, lat: float) -> str:
    zone = int((lon + 180) / 6) + 1
    zone = max(1, min(60, zone))
    if lat >= 0:
        return f"EPSG:{32600 + zone}"
    return f"EPSG:{32700 + zone}"


def projected_crs_for_geometry(geometry, source_crs: str) -> str:
    if not is_geographic(source_crs):
        return source_crs

    representative = geometry
    if geometry.geom_type in ("Polygon", "MultiPolygon"):
        representative = geometry.centroid
    elif geometry.geom_type in ("LineString", "MultiLineString"):
        midpoint = geometry.interpolate(0.5, normalized=True)
        representative = midpoint
    elif geometry.geom_type in ("MultiPoint", "GeometryCollection"):
        representative = geometry.representative_point()

    return utm_epsg_for_point(representative.x, representative.y)
