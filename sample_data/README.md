# Geospatial File Measurement API

A REST API built with **FastAPI** for uploading geospatial files,
extracting feature information, and calculating polygon areas and line
lengths. The API supports KML files and ZIP archives containing a single
Shapefile.

## Features

-   Upload `.kml` files and `.zip` files containing a Shapefile.
-   Extract feature IDs, geometry types, geometries, and feature
    properties.
-   Calculate polygon area in square metres (`m²`).
-   Calculate line length in metres (`m`).
-   Transform geographic coordinates to a projected coordinate reference
    system (CRS) before measuring.
-   Store file metadata and measurement results in SQLite.
-   Retrieve uploaded-file metadata and measurements through REST
    endpoints.
-   Interactive API documentation using Swagger UI.
-   Enforce a 20 MB upload limit and validate supported file extensions.
-   Automated API and measurement tests using `pytest` (after adding the
    test files described below).

## Technology Stack

  Component                  Technology
  -------------------------- ----------------------
  API framework              FastAPI
  ASGI server                Uvicorn
  Geospatial file handling   GeoPandas
  Geometry operations        Shapely
  CRS transformation         GeoPandas / PyProj
  Database                   SQLite
  ORM                        SQLAlchemy
  Data handling              pandas, NumPy
  API documentation          Swagger UI / OpenAPI
  Testing                    pytest, HTTPX

## Project Structure

``` text
Aereo/
├── app/
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   ├── routes/
│   │   └── files.py
│   └── services/
│       ├── file_parser.py
│       ├── crs_handler.py
│       └── measurement.py
├── sample_data/
│   └── sample.kml
├── tests/
│   ├── conftest.py
│   ├── test_api.py
│   └── test_measurement.py
├── uploads/
├── geospatial.db          # Created at runtime
├── requirements.txt       # Recommended dependency list
└── README.md
```

> The test files shown above should exist before running the test suite.
> If you have not created them yet, create them first or adjust the
> project tree accordingly.

`uploads/` is used for temporary processing. The current upload route
deletes the uploaded temporary file after processing, while file
metadata and measurement results are stored in SQLite.

## Requirements

-   Python 3.10 or later recommended.
-   pip.
-   Windows, macOS, or Linux.
-   GeoPandas and its supported geospatial dependencies.

## Installation and Setup

### 1. Clone the repository

``` bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd Aereo
```

Replace `<YOUR_GITHUB_REPOSITORY_URL>` with your repository URL.

### 2. Create and activate a virtual environment

**Windows PowerShell**

``` powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, use Command Prompt:

``` bat
.venv\Scripts\activate.bat
```

**macOS / Linux**

``` bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

``` bash
python -m pip install fastapi "uvicorn[standard]" python-multipart geopandas shapely pyproj sqlalchemy pandas numpy pytest httpx
```

If installation fails for GeoPandas or its native dependencies, use a
supported Python version and follow the official GeoPandas installation
guidance for your operating system.

To capture the installed dependency versions in a reproducible file:

``` bash
python -m pip freeze > requirements.txt
```

Commit `requirements.txt` after reviewing it. For subsequent
installations, use:

``` bash
python -m pip install -r requirements.txt
```

### 4. Start the API

Run from the project root:

``` bash
python -m uvicorn app.main:app --reload
```

Open:

-   API root: http://127.0.0.1:8000/
-   Health check: http://127.0.0.1:8000/health
-   Swagger UI: http://127.0.0.1:8000/docs
-   OpenAPI schema: http://127.0.0.1:8000/openapi.json

Keep the terminal open while testing the API. Press `Ctrl+C` to stop the
server.

## API Endpoints

### 1. Health check

**`GET /health`**

Checks whether the API is running.

Example response:

``` json
{
  "status": "healthy"
}
```

### 2. Upload a geospatial file

**`POST /api/files/`**

Accepts a multipart form upload with the field name `file`.

Supported formats:

-   `.kml`
-   `.zip` containing exactly one `.shp` file and its required companion
    files

Example with cURL:

``` bash
curl -X POST "http://127.0.0.1:8000/api/files/" \
  -H "accept: application/json" \
  -F "file=@sample_data/sample.kml"
```

Example successful response:

``` json
{
  "id": 1,
  "filename": "sample.kml",
  "feature_count": 2,
  "crs": "EPSG:4326",
  "measurement_crs": "EPSG:32644",
  "status": "COMPLETED"
}
```

The ID is assigned by the database. Use the ID returned by your actual
upload response. CRS values above are illustrative and may differ with
other input data.

Common error responses:

-   `400 Bad Request` --- unsupported format, invalid file, empty
    dataset, missing CRS, or validation error.
-   `413 Payload Too Large` --- upload exceeds the 20 MB limit.
-   `500 Internal Server Error` --- unexpected processing or database
    error.

### 3. Retrieve file metadata

**`GET /api/files/{file_id}`**

Example request:

``` bash
curl "http://127.0.0.1:8000/api/files/1"
```

Example response:

``` json
{
  "id": 1,
  "filename": "sample.kml",
  "feature_count": 2,
  "crs": "EPSG:4326",
  "measurement_crs": "EPSG:32644",
  "status": "COMPLETED"
}
```

Returns `404 Not Found` if the requested file ID does not exist.

### 4. Retrieve feature measurements

**`GET /api/files/{file_id}/measurements`**

Example request:

``` bash
curl "http://127.0.0.1:8000/api/files/1/measurements"
```

Example response structure (coordinate arrays are shortened for
readability):

``` json
{
  "file_id": 1,
  "filename": "sample.kml",
  "crs": "EPSG:4326",
  "measurement_crs": "EPSG:32644",
  "feature_count": 2,
  "features": [
    {
      "feature_id": 0,
      "geometry_type": "Polygon",
      "geometry": {
        "type": "Polygon",
        "coordinates": []
      },
      "area_m2": 11804.993839917557,
      "length_m": null,
      "properties": {
        "Name": "Sample Plot",
        "description": null
      }
    },
    {
      "feature_id": 1,
      "geometry_type": "LineString",
      "geometry": {
        "type": "LineString",
        "coordinates": []
      },
      "area_m2": null,
      "length_m": 106.57758259132162,
      "properties": {
        "Name": "Sample Route"
      }
    }
  ]
}
```

The empty coordinate arrays in this documentation example are
placeholders; actual API responses should contain the geometry
coordinates. The numeric measurements are illustrative examples from the
sample file and may differ if the sample data changes.

## Architecture and Workflow

1.  **Request handling:** FastAPI receives an upload at
    `POST /api/files/`.
2.  **Validation:** The route checks the extension and enforces the 20
    MB limit.
3.  **Temporary storage:** The upload is saved using a generated
    temporary filename.
4.  **Parsing:** `file_parser.py` reads KML or Shapefile ZIP into a
    GeoPandas `GeoDataFrame`.
5.  **CRS preparation:** `crs_handler.py` verifies the CRS and estimates
    a suitable UTM CRS for measurement.
6.  **Measurement:** `measurement.py` calculates polygon area and line
    length using projected geometries.
7.  **JSON conversion:** Missing values such as `NaN` and `NaT` are
    converted to JSON `null` before storage.
8.  **Persistence:** SQLAlchemy stores file metadata and serialized
    measurement results in SQLite.
9.  **Retrieval:** GET endpoints return metadata or measurement results.
10. **Cleanup:** The temporary upload is deleted after processing.

## CRS Handling

A geographic CRS such as **EPSG:4326** usually stores longitude and
latitude in degrees. Directly treating degrees as metres would produce
incorrect area and length values.

The current approach is:

1.  Read the source CRS from the input file.
2.  Reject files with no CRS because their coordinates cannot be safely
    interpreted.
3.  Use GeoPandas `estimate_utm_crs()` to estimate a suitable UTM CRS.
4.  Transform geometries into the estimated projected CRS.
5.  Calculate polygon area in square metres and line length in metres.
6.  Return the original CRS and the measurement CRS in the API response.

**Limitations:** UTM is suitable for many local datasets but is not
ideal for every dataset. Large datasets spanning multiple UTM zones,
polar datasets, or workflows requiring a specific accuracy may need a
different projection strategy.

In the current measurement implementation, the geometry field is built
from the projected GeoDataFrame. Its coordinates therefore use the
measurement CRS. Use the `measurement_crs` value to interpret those
coordinates. A future improvement would return original geometry
separately from projected measurement geometry.

## Geometry and Measurement Rules

  Geometry type          Area               Length
  ---------------------- ------------------ -----------------
  `Polygon`              Calculated in m²   `null`
  `MultiPolygon`         Calculated in m²   `null`
  `LineString`           `null`             Calculated in m
  `MultiLineString`      `null`             Calculated in m
  Other geometry types   `null`             `null`

The parser libraries determine which geometries can be read. The
measurement service calculates area for polygons and length for lines.
Geometry repair and extra measurement types can be added later.

## Automated Testing

The proposed test suite uses pytest and FastAPI's `TestClient`. The test
fixture uses an in-memory SQLite database so tests do not add records to
the development database.

Install test dependencies:

``` bash
python -m pip install pytest httpx
```

Run tests from the project root:

``` bash
python -m pytest -v
```

The test files described for this project are:

-   `tests/conftest.py` --- test client and isolated test database.
-   `tests/test_api.py` --- health check, KML upload, metadata,
    measurements, invalid extensions, invalid ZIP files, and unknown
    IDs.
-   `tests/test_measurement.py` --- polygon area, line length, geometry
    output, and missing CRS.

**Important:** Run the tests and confirm they pass before claiming the
test suite is verified. If you have not created these files yet, create
them first. Test coverage should be expanded to include Shapefile ZIP
uploads, upload-size limits, empty files, and missing-CRS API uploads.

## Database

SQLite is configured in `app/database.py`:

``` python
DATABASE_URL = "sqlite:///./geospatial.db"
```

The application creates its database tables at startup. The
`uploaded_files` table stores the database ID, original filename, source
CRS, measurement CRS, feature count, status, and serialized measurement
results.

The SQLite database is local to the environment where the API runs.

## Security and Operational Notes

-   The API enforces a 20 MB upload limit.
-   Uploaded files use generated temporary filenames.
-   ZIP input is checked for unsafe paths and must contain exactly one
    Shapefile.
-   Temporary uploads are deleted after processing.
-   Production deployments should consider authentication, rate
    limiting, decompressed ZIP-size limits, structured logging, and less
    revealing error messages.
-   Do not commit virtual environments, secrets, or temporary upload
    contents.

Suggested `.gitignore`:

``` gitignore
.venv/
__pycache__/
*.py[cod]
.env
geospatial.db
uploads/*
!uploads/.gitkeep
.pytest_cache/
```

## Future Improvements

-   Add and verify the automated test suite.
-   Pin dependency versions.
-   Return source geometry separately from projected geometry.
-   Improve CRS selection for large or multi-zone datasets.
-   Add archive decompression limits and more robust input validation.
-   Add Pydantic response schemas and structured logging.
-   Support more geospatial formats if required.

## License

Choose a license before publishing the repository publicly. If you
choose MIT, add a `LICENSE` file containing the MIT License text.

## Author

**Your Name**\
Geospatial File Measurement API --- a REST API built with FastAPI,
GeoPandas, Shapely, and SQLite.
