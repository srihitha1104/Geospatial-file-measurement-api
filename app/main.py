from fastapi import FastAPI
from app.database import Base, engine
from app.routes.files import router as files_router

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Geospatial File Measurement API",
    description="Upload KML or Shapefile ZIP files and calculate feature measurements.",
    version="1.0.0",
)

@app.get("/")
def home():
    return {
        "message": "Welcome to the Geospatial File Measurement API",
        "docs": "/docs",
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}

app.include_router(files_router)

