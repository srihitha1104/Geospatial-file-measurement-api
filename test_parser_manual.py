
from app.services.file_parser import read_geospatial_file

file_path = "sample_data/sample.kml"

try:
    gdf = read_geospatial_file(file_path)

    print("File parsed successfully!")
    print("Feature count:", len(gdf))
    print("CRS:", gdf.crs)
    print("\nFeatures:")
    print(gdf[["Name", "geometry"]])

except Exception as exc:
    print("Parsing failed:", exc)
