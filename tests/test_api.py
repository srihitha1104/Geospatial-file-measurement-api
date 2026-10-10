
from io import BytesIO


SAMPLE_KML = b"""<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <Placemark>
      <name>Sample Plot</name>
      <Polygon>
        <outerBoundaryIs>
          <LinearRing>
            <coordinates>
              78.0000,17.0000,0
              78.0010,17.0000,0
              78.0010,17.0010,0
              78.0000,17.0010,0
              78.0000,17.0000,0
            </coordinates>
          </LinearRing>
        </outerBoundaryIs>
      </Polygon>
    </Placemark>
    <Placemark>
      <name>Sample Route</name>
      <LineString>
        <coordinates>
          78.0000,17.0000,0
          78.0010,17.0010,0
        </coordinates>
      </LineString>
    </Placemark>
  </Document>
</kml>
"""


def test_health_check(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_upload_valid_kml(client):
    response = client.post(
        "/api/files/",
        files={
            "file": (
                "sample.kml",
                BytesIO(SAMPLE_KML),
                "application/vnd.google-earth.kml+xml",
            )
        },
    )

    assert response.status_code == 200

    data = response.json()
    assert data["filename"] == "sample.kml"
    assert data["feature_count"] == 2
    assert data["status"] == "COMPLETED"
    assert data["crs"] is not None
    assert data["measurement_crs"] is not None
    assert isinstance(data["id"], int)


def test_get_file_info(client):
    upload = client.post(
        "/api/files/",
        files={
            "file": (
                "sample.kml",
                BytesIO(SAMPLE_KML),
                "application/vnd.google-earth.kml+xml",
            )
        },
    )

    assert upload.status_code == 200
    file_id = upload.json()["id"]

    response = client.get(f"/api/files/{file_id}")

    assert response.status_code == 200
    assert response.json()["id"] == file_id
    assert response.json()["feature_count"] == 2


def test_get_measurements(client):
    upload = client.post(
        "/api/files/",
        files={
            "file": (
                "sample.kml",
                BytesIO(SAMPLE_KML),
                "application/vnd.google-earth.kml+xml",
            )
        },
    )

    assert upload.status_code == 200
    file_id = upload.json()["id"]

    response = client.get(
        f"/api/files/{file_id}/measurements"
    )

    assert response.status_code == 200

    data = response.json()
    assert data["file_id"] == file_id
    assert data["feature_count"] == 2
    assert len(data["features"]) == 2

    polygon = next(
        feature
        for feature in data["features"]
        if feature["geometry_type"] == "Polygon"
    )

    line = next(
        feature
        for feature in data["features"]
        if feature["geometry_type"] == "LineString"
    )

    assert polygon["area_m2"] > 0
    assert polygon["length_m"] is None
    assert polygon["geometry"] is not None

    assert line["length_m"] > 0
    assert line["area_m2"] is None
    assert line["geometry"] is not None


def test_reject_unsupported_extension(client):
    response = client.post(
        "/api/files/",
        files={
            "file": (
                "notes.txt",
                BytesIO(b"This is not a geospatial file."),
                "text/plain",
            )
        },
    )

    assert response.status_code == 400
    assert "Only KML and Shapefile ZIP files" in (
        response.json()["detail"]
    )


def test_reject_invalid_zip(client):
    response = client.post(
        "/api/files/",
        files={
            "file": (
                "invalid.zip",
                BytesIO(b"This is not a valid ZIP archive."),
                "application/zip",
            )
        },
    )

    assert response.status_code == 400


def test_unknown_file_returns_404(client):
    response = client.get("/api/files/999999")

    assert response.status_code == 404


def test_unknown_measurements_return_404(client):
    response = client.get(
        "/api/files/999999/measurements"
    )

    assert response.status_code == 404
