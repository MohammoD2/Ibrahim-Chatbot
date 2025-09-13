from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
import os
import pickle
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from typing import Dict, Optional
import requests
import json
from sqlalchemy import create_engine, Column, String, Integer
from sqlalchemy.orm import declarative_base, sessionmaker

app = FastAPI()

# Configuration
PROCESSED_DATA_DIR = "processed_data"
MODEL_NAME = "all-MiniLM-L6-v2"
OLLAMA_API_URL = "http://localhost:11434/api/generate"

# Database configuration
DATABASE_URL = "postgresql://postgres:8523@localhost:7000/file_metadata_db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database Model (using existing file_metadata table)
class FileMetadata(Base):
    __tablename__ = "file_metadata"
    
    id = Column(Integer, primary_key=True, index=True)
    file_name = Column(String, index=True)
    file_key = Column(String, unique=True, index=True)
    source_path = Column(String)
    local_path = Column(String)

# Initialize embeddings model
embeddings_model = SentenceTransformer(MODEL_NAME)

class ChatRequest(BaseModel):
    message: str
    api_key: str | None = None

class ProductData:
    def __init__(self, product_name: str):
        self.product_name = product_name
        self.data_dir = os.path.join(PROCESSED_DATA_DIR, product_name)
        self.faiss_index = None
        self.chunks = None
        self.embeddings = None
        self.load_data()

    def load_data(self):
        """Load FAISS index and chunks for the product"""
        try:
            # Load FAISS index
            faiss_path = os.path.join(self.data_dir, "faiss_store", "index.faiss")
            if os.path.exists(faiss_path):
                self.faiss_index = faiss.read_index(faiss_path)
            
            # Load chunks and embeddings
            chunks_path = os.path.join(self.data_dir, "chunks.pkl")
            if os.path.exists(chunks_path):
                with open(chunks_path, 'rb') as f:
                    data = pickle.load(f)
                    self.chunks = data['chunks']
                    self.embeddings = data['embeddings']
        except Exception as e:
            print(f"Error loading data for {self.product_name}: {str(e)}")

class ChatManager:
    def __init__(self):
        self.product_data: Dict[str, ProductData] = {}
        self.db = SessionLocal()
        self.initialize_products()

    def initialize_products(self):
        """Initialize data for all products from file_metadata table"""
        try:
            # Get all unique file_names from file_metadata
            products = self.db.query(FileMetadata.file_name).distinct().all()
            
            # Initialize data for each product
            for product in products:
                product_name = product[0]
                self.product_data[product_name] = ProductData(product_name)
                print(f"Initialized data for product: {product_name}")
        except Exception as e:
            print(f"Error initializing products: {str(e)}")

    def get_product_from_key(self, api_key: str) -> Optional[str]:
        """Get product name from API key using file_metadata table"""
        try:
            product = self.db.query(FileMetadata).filter(
                FileMetadata.file_key == api_key
            ).first()
            return product.file_name if product else None
        except Exception as e:
            print(f"Error getting product from key: {str(e)}")
            return None

    def search_similar_chunks(self, query: str, product: str, k: int = 3) -> list:
        """Search for similar chunks using FAISS"""
        if product not in self.product_data:
            print(f"Product {product} not found in product data")
            return []
        
        product_data = self.product_data[product]
        if not product_data.faiss_index or not product_data.chunks:
            print(f"No FAISS index or chunks found for product {product}")
            return []

        try:
            # Get query embedding
            query_embedding = embeddings_model.encode([query])[0]
            
            # Search in FAISS index
            distances, indices = product_data.faiss_index.search(
                query_embedding.reshape(1, -1).astype('float32'), 
                k
            )
            
            # Get relevant chunks and verify they belong to the correct product
            relevant_chunks = []
            for idx in indices[0]:
                if idx < len(product_data.chunks):  # Ensure index is valid
                    chunk = product_data.chunks[idx]
                    # Add product verification in the chunk
                    relevant_chunks.append(f"[{product.upper()}] {chunk}")
            
            if not relevant_chunks:
                print(f"No relevant chunks found for product {product}")
                return []
                
            return relevant_chunks
        except Exception as e:
            print(f"Error searching chunks for product {product}: {str(e)}")
            return []

    async def generate_response(self, query: str, context: list, product: str) -> str:
        """Generate response using Ollama"""
        if not context:
            return f"I can only provide information about {product.upper()}, but I don't have enough information to answer your question."

        prompt = f"""Context:
{chr(10).join(context)}

Instructions: You are a helpful AI assistant for {product.upper()}. You must ONLY answer questions about {product.upper()}. If the question is about any other company or topic, respond with "I can only provide information about {product.upper()}." Answer the question with ONLY the direct answer based on the context provided.

Question: {query}

Answer:"""

        try:
            response = requests.post(
                OLLAMA_API_URL,
                json={
                    "model": "llama3.2",
                    "prompt": prompt,
                    "stream": False
                }
            )
            response.raise_for_status()
            return response.json()['response']
        except Exception as e:
            print(f"Error generating response: {str(e)}")
            return "I apologize, but I'm having trouble generating a response at the moment."

    def __del__(self):
        """Cleanup database connection"""
        self.db.close()

# Initialize chat manager
chat_manager = ChatManager()

@app.post("/chat")
async def chat(request: ChatRequest, x_api_key: str | None = Header(None)):
    # Get API key from either request body or header
    api_key = request.api_key or x_api_key
    if not api_key:
        raise HTTPException(status_code=401, detail="API key is required either in request body or X-API-Key header")

    # Verify API key and get product
    product = chat_manager.get_product_from_key(api_key)
    if not product:
        raise HTTPException(status_code=401, detail="Invalid API key")

    print(f"Processing request for product: {product}")

    # Search for relevant chunks
    relevant_chunks = chat_manager.search_similar_chunks(request.message, product)
    if not relevant_chunks:
        return {"response": f"I can only provide information about {product.upper()}, but I don't have enough information to answer your question."}

    # Generate response with product context
    response = await chat_manager.generate_response(request.message, relevant_chunks, product)
    
    return {
        "response": response,
        "product": product
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 