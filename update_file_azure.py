from fastapi import FastAPI, HTTPException
from azure.storage.blob import BlobServiceClient
from sqlalchemy import create_engine, Column, String, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from pydantic import BaseModel
from typing import Optional

# Initialize FastAPI app
app = FastAPI()

# Azure Blob Storage configuration
AZURE_STORAGE_CONNECTION_STRING = "YOUR_AZURE_STORAGE_CONNECTION_STRING"
CONTAINER_NAME = "your-container-name"

# PostgreSQL configuration
DATABASE_URL = "postgresql://postgres:8523@localhost:7000/file_metadata_db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database Model
class FileMetadata(Base):
    __tablename__ = "file_metadata"
    
    id = Column(Integer, primary_key=True, index=True)
    file_name = Column(String, index=True)
    file_key = Column(String, unique=True, index=True)
    source_path = Column(String)
    blob_path = Column(String)

# Create database tables
Base.metadata.create_all(bind=engine)

# Pydantic model for request
class FileUpdateRequest(BaseModel):
    file_path: str
    file_name: str
    file_key: str

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.put("/update-file")
async def update_file(request: FileUpdateRequest):
    try:
        # Validate file exists
        if not os.path.exists(request.file_path):
            raise HTTPException(status_code=404, detail="File not found")

        # Initialize Azure Blob Service Client
        blob_service_client = BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)
        container_client = blob_service_client.get_container_client(CONTAINER_NAME)

        # Create blob path
        blob_path = f"{request.file_name}/product_info.txt"
        blob_client = container_client.get_blob_client(blob_path)

        # Check if blob exists
        try:
            blob_client.get_blob_properties()
        except Exception:
            raise HTTPException(status_code=404, detail="File not found in blob storage")

        # Upload updated file to Azure Blob Storage
        with open(request.file_path, "rb") as data:
            blob_client.upload_blob(data, overwrite=True)

        # Update metadata in PostgreSQL
        db = next(get_db())
        file_metadata = db.query(FileMetadata).filter(FileMetadata.file_key == request.file_key).first()
        if not file_metadata:
            raise HTTPException(status_code=404, detail="File metadata not found")

        file_metadata.file_name = request.file_name
        file_metadata.source_path = request.file_path
        file_metadata.blob_path = blob_path
        
        db.commit()
        db.refresh(file_metadata)

        return {
            "message": "File updated successfully",
            "file_name": request.file_name,
            "file_key": request.file_key,
            "blob_path": blob_path
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8022)
