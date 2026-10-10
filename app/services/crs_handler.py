
import geopandas as gpd


def prepare_for_measurement(gdf: gpd.GeoDataFrame):
    """
    Transform geographic geometries to a suitable
    projected CRS before measuring area or length.
    """
    if gdf.crs is None:
        raise ValueError(
            "The input file has no CRS. "
            "Cannot safely calculate measurements."
        )

    if gdf.empty:
        return gdf, None

    measurement_crs = gdf.estimate_utm_crs()

    if measurement_crs is None:
        raise ValueError(
            "Could not determine a suitable measurement CRS."
        )

    projected_gdf = gdf.to_crs(measurement_crs)

    return projected_gdf, measurement_crs
