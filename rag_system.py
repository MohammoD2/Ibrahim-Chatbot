from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
import os
import json
from typing import List, Dict, Optional
import pickle
import hashlib

class RAGSystem:
    def __init__(self):
        # Set data directory
        self.data_dir = "data"
        
        # Define secret keys for different information sources
        self.secret_keys = {
            "macdora": "macdora_secret_key_2024",  # Key for Macdora info
            "bulipe": "bulipe_secret_key_2024"     # Key for Bulipe Tech info
        }
        
        # Map keys to their respective data directories
        self.key_to_data = {
            "macdora": "macdora_data",
            "bulipe": "bulipe_data"
        }
        
        # Initialize embeddings
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'}
        )
        
        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=10000,
            chunk_overlap=500
        )
        
        # Initialize vector stores dictionary
        self.vector_stores = {}
        self.chunks = {}
        
        # Load data for each source
        self._load_all_sources()

    def _load_all_sources(self):
        """Load all data sources"""
        for source, data_dir in self.key_to_data.items():
            source_path = os.path.join(self.data_dir, data_dir)
            if os.path.exists(source_path):
                # Load FAISS index
                faiss_path = os.path.join(source_path, "faiss_index")
                if os.path.exists(faiss_path):
                    try:
                        self.vector_stores[source] = FAISS.load_local(
                            faiss_path,
                            self.embeddings,
                            allow_dangerous_deserialization=True
                        )
                        print(f"Successfully loaded FAISS index for {source}")
                    except Exception as e:
                        print(f"Error loading FAISS index for {source}: {str(e)}")
                
                # Load chunks
                chunks_path = os.path.join(source_path, "chunks2.pkl")
                if os.path.exists(chunks_path):
                    try:
                        with open(chunks_path, 'rb') as f:
                            self.chunks[source] = pickle.load(f)
                        print(f"Successfully loaded chunks for {source}")
                    except Exception as e:
                        print(f"Error loading chunks for {source}: {str(e)}")

    def _verify_key(self, key: str) -> Optional[str]:
        """Verify the provided key and return the corresponding source"""
        for source, secret_key in self.secret_keys.items():
            if key == secret_key:
                return source
        return None

    def query(self, query: str, key: str, k: int = 20):
        """Query the RAG system with key-based access control"""
        # Verify the key
        source = self._verify_key(key)
        if not source:
            return "Error: Invalid access key. Access denied."
        
        # Check if vector store exists for the source
        if source not in self.vector_stores:
            return f"Error: No data available for {source}."
        
        try:
            # Search for relevant documents
            docs = self.vector_stores[source].similarity_search(query, k=k)
            
            # Format the context
            context = "\n".join([doc.page_content for doc in docs])
            
            # Debug prints
            print(f"[DEBUG] Querying source: {source}")
            print(f"[DEBUG] Retrieved context:\n{context}\n---")
            
            # Create the prompt with context and source verification
            prompt = f"""Context:
{context}

Instructions: You are a warm, friendly, and human-like AI assistant for {source.upper()}. You must ONLY answer questions about {source.upper()}. If the question is about any other company or topic, respond with "I can only provide information about {source.upper()}." Answer the question with ONLY the direct answer based on the context provided.

Question: {query}"""
            
            return prompt
        except Exception as e:
            return f"Error: Failed to process query for {source}: {str(e)}"

    def add_document(self, content: str, key: str, metadata: Optional[Dict] = None) -> str:
        """Add a document to the specified source"""
        # Verify the key
        source = self._verify_key(key)
        if not source:
            return "Error: Invalid access key. Access denied."
        
        try:
            # Create document object with source metadata
            metadata = metadata or {}
            metadata['source'] = source
            doc = Document(page_content=content, metadata=metadata)
            
            # Split into chunks
            chunks = self.text_splitter.split_documents([doc])
            
            # Create or update vector store for the source
            if source not in self.vector_stores:
                self.vector_stores[source] = FAISS.from_documents(chunks, self.embeddings)
            else:
                self.vector_stores[source].add_documents(chunks)
            
            # Save vector store
            source_path = os.path.join(self.data_dir, self.key_to_data[source])
            os.makedirs(source_path, exist_ok=True)
            self.vector_stores[source].save_local(os.path.join(source_path, "faiss_index"))
            
            # Save chunks
            with open(os.path.join(source_path, "chunks2.pkl"), 'wb') as f:
                pickle.dump(chunks, f)
            
            print(f"Successfully added document for {source}")
            return "Document added successfully"
        except Exception as e:
            return f"Error: Failed to add document for {source}: {str(e)}"

    def get_all_documents(self) -> List[Dict]:
        """Get all documents from the document store"""
        return self.document_store.get_all_documents()

    def delete_document(self, doc_id: str) -> bool:
        """Delete a document from both stores"""
        # Get document before deletion
        doc = self.document_store.get_document(doc_id)
        if not doc:
            return False
            
        # Delete from document store
        if not self.document_store.delete_document(doc_id):
            return False
            
        # Rebuild vector store
        self.vector_store = FAISS.from_texts([""], self.embeddings)
        for doc in self.document_store.get_all_documents():
            self.add_document(doc["content"], doc["metadata"])
            
        return True

# Example usage
if __name__ == "__main__":
    # Initialize RAG system
    rag = RAGSystem()
    
    # Example query with key
    query = "What is the company name?"
    result = rag.query(query, key="macdora_secret_key_2024")
    print(result) 