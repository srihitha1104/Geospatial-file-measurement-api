
from sqlalchemy import Column, Integer, String, Text
from app.database import Base


class UploadedFile(Base):
    __tablename__ = "uploaded_files"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    crs = Column(String(100), nullable=True)
    measurement_crs = Column(String(100), nullable=True)
    feature_count = Column(Integer, default=0)
    status = Column(String(30), default="PROCESSING")
    results_json = Column(Text, nullable=True)
