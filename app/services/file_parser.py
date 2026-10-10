
from pathlib import Path
from zipfile import ZipFile, BadZipFile

import geopandas as gpd


def read_geospatial_file(file_path: str) -> gpd.GeoDataFrame:
    """
    Read a KML file or a ZIP containing a Shapefile.
    Return its features as a GeoDataFrame.
    """
    path = Path(file_path)
    suffix = path.suffix.lower()

    if suffix == ".kml":
        try:
            return gpd.read_file(path, driver="KML")
        except Exception as exc:
            raise ValueError(f"Could not read KML file: {exc}") from exc

    if suffix == ".zip":
        try:
            with ZipFile(path, "r") as archive:
                names = archive.namelist()

                # Basic protection against unsafe archive paths
                if any(
                    name.startswith(("/", "\\"))
                    or ".." in Path(name.replace("\\", "/")).parts
                    for name in names
                ):
                    raise ValueError("ZIP contains unsafe file paths.")

                shp_files = [
                    name for name in names
                    if name.lower().endswith(".shp")
                ]

                if not shp_files:
                    raise ValueError(
                        "ZIP does not contain a Shapefile (.shp)."
                    )

                if len(shp_files) > 1:
                    raise ValueError(
                        "ZIP contains multiple Shapefiles. "
                        "Please upload one Shapefile per ZIP."
                    )

            # GeoPandas can read supported ZIP archives directly.
            return gpd.read_file(f"zip://{path.resolve()}")

        except BadZipFile as exc:
            raise ValueError("The uploaded ZIP file is invalid.") from exc
        except ValueError:
            raise
        except Exception as exc:
            raise ValueError(
                f"Could not read Shapefile ZIP: {exc}"
            ) from exc

    raise ValueError("Only .kml and .zip files are supported.")
