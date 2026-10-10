
from app.services.file_parser import read_geospatial_file
from app.services.measurement import calculate_measurements

gdf = read_geospatial_file("sample_data/sample.kml")

result = calculate_measurements(gdf)

print("Measurement CRS:", result["measurement_crs"])

for feature in result["features"]:
    print("\nFeature:", feature["geometry_type"])
    print("Area (m²):", feature["area_m2"])
    print("Length (m):", feature["length_m"])
