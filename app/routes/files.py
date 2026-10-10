
import json
import math
from datetime import date, datetime
from pathlib import Path
from uuid import uuid4

import numpy as np
import pandas as pd
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import UploadedFile
from app.services.file_parser import read_geospatial_file
from app.services.measurement import calculate_measurements


router = APIRouter(prefix="/api/files", tags=["Geospatial Files"])

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB


def make_json_safe(value):
    """Convert pandas/NumPy values into JSON-compatible values."""

    if value is None or value is pd.NA or value is pd.NaT:
        return None

    if isinstance(value, dict):
        return {
            str(key): make_json_safe(item)
            for key, item in value.items()
        }

    if isinstance(value, (list, tuple)):
        return [make_json_safe(item) for item in value]

    if isinstance(value, np.generic):
        value = value.item()

    if isinstance(value, float):
        if not math.isfinite(value):
            return None
        return value

    if isinstance(value, (datetime, date, pd.Timestamp)):
        if pd.isna(value):
            return None
        return value.isoformat()

    if isinstance(value, (str, int, bool)):
        return value

    try:
        missing = pd.isna(value)
        if isinstance(missing, (bool, np.bool_)) and missing:
            return None
    except (TypeError, ValueError):
        pass

    # Fallback for other values that JSON cannot encode.
    return str(value)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/")
def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Filename is required.",
        )

    suffix = Path(file.filename).suffix.lower()

    if suffix not in {".kml", ".zip"}:
        raise HTTPException(
            status_code=400,
            detail="Only KML and Shapefile ZIP files are supported.",
        )

    # Generate a unique filename instead of trusting the uploaded path.
    saved_path = UPLOAD_DIR / f"{uuid4().hex}{suffix}"

    try:
        total_size = 0

        # Save the upload, enforcing the 20 MB limit.
        with saved_path.open("wb") as destination:
            while True:
                chunk = file.file.read(1024 * 1024)

                if not chunk:
                    break

                total_size += len(chunk)

                if total_size > MAX_FILE_SIZE:
                    raise HTTPException(
                        status_code=413,
                        detail="Uploaded file exceeds the 20 MB limit.",
                    )

                destination.write(chunk)

        # Read the KML or Shapefile ZIP.
        gdf = read_geospatial_file(str(saved_path))

        if gdf.empty:
            raise HTTPException(
                status_code=400,
                detail="The uploaded file contains no features.",
            )

        if gdf.crs is None:
            raise HTTPException(
                status_code=400,
                detail=(
                    "The file has no CRS. "
                    "Cannot safely measure geometries."
                ),
            )

        original_crs = str(gdf.crs)

        # Calculate area and length in a suitable projected CRS.
        measurements = calculate_measurements(gdf)

        # Replace NaN, NaT, and other missing values with JSON null.
        safe_features = make_json_safe(measurements["features"])

        results_json = json.dumps(
            safe_features,
            allow_nan=False,
        )

        # Store the processed result in SQLite.
        record = UploadedFile(
            filename=Path(file.filename).name,
            crs=original_crs,
            measurement_crs=measurements["measurement_crs"],
            feature_count=len(gdf),
            status="COMPLETED",
            results_json=results_json,
        )

        db.add(record)
        db.commit()
        db.refresh(record)

        return {
            "id": record.id,
            "filename": record.filename,
            "feature_count": record.feature_count,
            "crs": record.crs,
            "measurement_crs": record.measurement_crs,
            "status": record.status,
        }

    except HTTPException:
        raise

    except ValueError as exc:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"File processing failed: {exc}",
        ) from exc

    finally:
        file.file.close()

        if saved_path.exists():
            saved_path.unlink()


@router.get("/{file_id}")
def get_file_info(
    file_id: int,
    db: Session = Depends(get_db),
):
    record = db.get(UploadedFile, file_id)

    if record is None:
        raise HTTPException(
            status_code=404,
            detail="File not found.",
        )

    return {
        "id": record.id,
        "filename": record.filename,
        "feature_count": record.feature_count,
        "crs": record.crs,
        "measurement_crs": record.measurement_crs,
        "status": record.status,
    }


@router.get("/{file_id}/measurements")
def get_measurements(
    file_id: int,
    db: Session = Depends(get_db),
):
    record = db.get(UploadedFile, file_id)

    if record is None:
        raise HTTPException(
            status_code=404,
            detail="File not found.",
        )

    return {
        "file_id": record.id,
        "filename": record.filename,
        "crs": record.crs,
        "measurement_crs": record.measurement_crs,
        "feature_count": record.feature_count,
        "features": json.loads(record.results_json or "[]"),
    }
