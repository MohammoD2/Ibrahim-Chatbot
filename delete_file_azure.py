from fastapi import FastAPI, HTTPException
from azure.storage.blob import BlobServiceClient
from sqlalchemy import create_engine, Column, String, Integer
from sqlalchemy.orm import declarative_base, sessionmaker
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
class FileDeleteRequest(BaseModel):
    file_name: str
    file_key: str

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.delete("/delete-file")
async def delete_file(request: FileDeleteRequest):
    try:
        # Get database session
        db = next(get_db())
        
        # Verify file key exists in database
        existing_file = db.query(FileMetadata).filter(
            FileMetadata.file_name == request.file_name,
            FileMetadata.file_key == request.file_key
        ).first()
        
        if not existing_file:
            raise HTTPException(status_code=401, detail="Invalid file name or key")

        # Initialize Azure Blob Service Client
        blob_service_client = BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)
        container_client = blob_service_client.get_container_client(CONTAINER_NAME)

        # Create blob path
        blob_path = f"{request.file_name}/product_info.txt"
        blob_client = container_client.get_blob_client(blob_path)

        # Check if blob exists and delete it
        try:
            blob_client.get_blob_properties()
            blob_client.delete_blob()
        except Exception as e:
            # If blob doesn't exist, we can still proceed with metadata deletion
            pass

        # Delete metadata from database
        db.delete(existing_file)
        db.commit()

        return {
            "message": "File deleted successfully",
            "file_name": request.file_name,
            "file_key": request.file_key
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
