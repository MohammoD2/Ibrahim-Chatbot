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
os.makedirs(LOCAL_STORAGE_PATH, exist_ok=True)

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

@app.post("/update-file")
async def update_file(request: FileUpdateRequest):
    try:
        # Validate file exists
        if not os.path.exists(request.file_path):
            raise HTTPException(status_code=404, detail="File not found")

        # Get database session
        db = next(get_db())
        
        # Verify file key exists in database
        existing_file = db.query(FileMetadata).filter(
            FileMetadata.file_name == request.file_name,
            FileMetadata.file_key == request.file_key
        ).first()
        
        if not existing_file:
            raise HTTPException(status_code=401, detail="Invalid file name or key")

        # Create local storage path
        local_path = os.path.join(LOCAL_STORAGE_PATH, request.file_name)
        os.makedirs(local_path, exist_ok=True)
        
        # Copy new file to local storage (replacing existing file)
        destination_path = os.path.join(local_path, "product_info.txt")
        shutil.copy2(request.file_path, destination_path)

        # Update metadata in PostgreSQL
        existing_file.source_path = request.file_path
        existing_file.local_path = destination_path
        db.commit()
        db.refresh(existing_file)

        return {
            "message": "File updated successfully",
            "file_name": request.file_name,
            "file_key": request.file_key,
            "local_path": destination_path
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
