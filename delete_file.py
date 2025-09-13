from fastapi import FastAPI, HTTPException
from sqlalchemy import create_engine, Column, String, Integer
from sqlalchemy.orm import declarative_base, sessionmaker
import os
import shutil
from pydantic import BaseModel
from typing import Optional

# Initialize FastAPI app
app = FastAPI()

# Local storage configuration
LOCAL_STORAGE_PATH = "local_storage"
PROCESSED_DATA_PATH = "processed_data"
os.makedirs(LOCAL_STORAGE_PATH, exist_ok=True)
os.makedirs(PROCESSED_DATA_PATH, exist_ok=True)

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
    local_path = Column(String)

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

        # Delete file from local storage
        local_path = os.path.join(LOCAL_STORAGE_PATH, request.file_name)
        if os.path.exists(local_path):
            shutil.rmtree(local_path)

        # Delete file from processed_data if it exists
        processed_path = os.path.join(PROCESSED_DATA_PATH, request.file_name)
        if os.path.exists(processed_path):
            shutil.rmtree(processed_path)

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
