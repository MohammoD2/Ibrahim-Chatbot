import os
import pickle
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

# Settings
LOCAL_STORAGE = "local_storage"
OUTPUT_DIR = "processed_data"
CHUNK_SIZE = 10000
CHUNK_OVERLAP = 500
MODEL_NAME = "all-MiniLM-L6-v2"

# Initialize model globally
model = SentenceTransformer(MODEL_NAME)

# Helper: chunk text
def chunk_text(text, chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP):
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunks.append(text[start:end])
        if end == len(text):
            break
        start = end - chunk_overlap
    return chunks

def process_file(file_path):
    """Process a single text file and create embeddings."""
    if not file_path.endswith('.txt'):
        return
    
    product_name = os.path.basename(os.path.dirname(file_path))
    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()
    
    chunks = chunk_text(text)
    embeddings = model.encode(chunks)
    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings.astype("float32"))
    
    # Prepare output dirs
    out_dir = os.path.join(OUTPUT_DIR, product_name)
    faiss_dir = os.path.join(out_dir, "faiss_store")
    os.makedirs(faiss_dir, exist_ok=True)
    
    # Save chunks
    with open(os.path.join(out_dir, "chunks.pkl"), "wb") as f:
        pickle.dump({"chunks": chunks, "embeddings": embeddings}, f)
    
    # Save FAISS index
    faiss.write_index(index, os.path.join(faiss_dir, "index.faiss"))
    print(f"Processed {file_path} -> {out_dir}")

# Main pipeline
if __name__ == "__main__":
    for root, dirs, files in os.walk(LOCAL_STORAGE):
        for file in files:
            if file.endswith(".txt"):
                file_path = os.path.join(root, file)
                process_file(file_path) 