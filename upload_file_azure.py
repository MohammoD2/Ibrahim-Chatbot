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
class FileUploadRequest(BaseModel):
    file_path: str
    file_name: str
    file_key: str

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/upload-file")
async def upload_file(request: FileUploadRequest):
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

        # Upload file to Azure Blob Storage
        with open(request.file_path, "rb") as data:
            blob_client.upload_blob(data, overwrite=True)

        # Store metadata in PostgreSQL
        db = next(get_db())
        file_metadata = FileMetadata(
            file_name=request.file_name,
            file_key=request.file_key,
            source_path=request.file_path,
            blob_path=blob_path
        )
        db.add(file_metadata)
        db.commit()
        db.refresh(file_metadata)

        return {
            "message": "File uploaded successfully",
            "file_name": request.file_name,
            "file_key": request.file_key,
            "blob_path": blob_path
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
