
from shapely.geometry import mapping

from app.services.crs_handler import prepare_for_measurement


def calculate_measurements(gdf):
    """
    Calculate area and length for supported geometries.

    Returns feature IDs, geometry types, GeoJSON geometries,
    original properties, and measurements in metric units.
    """
    projected_gdf, measurement_crs = prepare_for_measurement(gdf)

    results = []

    for index, row in projected_gdf.iterrows():
        geometry = row.geometry

        result = {
            "feature_id": (
                int(index)
                if isinstance(index, int)
                else str(index)
            ),
            "geometry_type": (
                geometry.geom_type
                if geometry is not None
                else None
            ),
            "geometry": (
                mapping(geometry)
                if geometry is not None and not geometry.is_empty
                else None
            ),
            "area_m2": None,
            "length_m": None,
            "properties": {
                key: value
                for key, value in row.items()
                if key != "geometry"
            },
        }

        if geometry is not None and not geometry.is_empty:
            if geometry.geom_type in ("Polygon", "MultiPolygon"):
                result["area_m2"] = float(geometry.area)

            elif geometry.geom_type in ("LineString", "MultiLineString"):
                result["length_m"] = float(geometry.length)

        results.append(result)

    return {
        "measurement_crs": (
            str(measurement_crs)
            if measurement_crs is not None
            else None
        ),
        "features": results,
    }
