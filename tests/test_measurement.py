
import geopandas as gpd
from shapely.geometry import LineString, Polygon

from app.services.measurement import calculate_measurements


def test_polygon_area_is_calculated():
    polygon = Polygon([
        (78.0000, 17.0000),
        (78.0010, 17.0000),
        (78.0010, 17.0010),
        (78.0000, 17.0010),
        (78.0000, 17.0000),
    ])

    gdf = gpd.GeoDataFrame(
        {"name": ["Test Polygon"]},
        geometry=[polygon],
        crs="EPSG:4326",
    )

    result = calculate_measurements(gdf)

    feature = result["features"][0]

    assert feature["geometry_type"] == "Polygon"
    assert feature["area_m2"] > 0
    assert feature["length_m"] is None
    assert result["measurement_crs"] is not None


def test_line_length_is_calculated():
    line = LineString([
        (78.0000, 17.0000),
        (78.0010, 17.0010),
    ])

    gdf = gpd.GeoDataFrame(
        {"name": ["Test Line"]},
        geometry=[line],
        crs="EPSG:4326",
    )

    result = calculate_measurements(gdf)

    feature = result["features"][0]

    assert feature["geometry_type"] == "LineString"
    assert feature["length_m"] > 0
    assert feature["area_m2"] is None


def test_geometry_is_included_in_result():
    polygon = Polygon([
        (78.0000, 17.0000),
        (78.0010, 17.0000),
        (78.0010, 17.0010),
        (78.0000, 17.0010),
        (78.0000, 17.0000),
    ])

    gdf = gpd.GeoDataFrame(
        {"name": ["Geometry Test"]},
        geometry=[polygon],
        crs="EPSG:4326",
    )

    result = calculate_measurements(gdf)
    feature = result["features"][0]

    assert feature["geometry"] is not None
    assert feature["geometry"]["type"] == "Polygon"


def test_missing_crs_is_rejected():
    line = LineString([
        (78.0, 17.0),
        (78.001, 17.001),
    ])

    gdf = gpd.GeoDataFrame(
        {"name": ["Missing CRS"]},
        geometry=[line],
    )

    try:
        calculate_measurements(gdf)
        assert False, "Expected missing CRS to be rejected"
    except ValueError as exc:
        assert "no CRS" in str(exc)
