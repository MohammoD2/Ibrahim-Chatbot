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

        # Create local storage path
        local_path = os.path.join(LOCAL_STORAGE_PATH, request.file_name)
        os.makedirs(local_path, exist_ok=True)
        
        # Copy file to local storage
        destination_path = os.path.join(local_path, "product_info.txt")
        shutil.copy2(request.file_path, destination_path)

        # Store metadata in PostgreSQL
        db = next(get_db())
        file_metadata = FileMetadata(
            file_name=request.file_name,
            file_key=request.file_key,
            source_path=request.file_path,
            local_path=destination_path
        )
        db.add(file_metadata)
        db.commit()
        db.refresh(file_metadata)

        return {
            "message": "File uploaded successfully",
            "file_name": request.file_name,
            "file_key": request.file_key,
            "local_path": destination_path
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
