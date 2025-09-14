import os
import pickle
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
import logging
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
PROCESSED_DATA_DIR = "processed_data"
MODEL_NAME = "all-MiniLM-L6-v2"
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GEMINI_MODEL = "gemini-1.5-flash"  # or "gemini-1.5-pro" for more advanced features

# Configure Gemini API
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
else:
    logger.warning("GEMINI_API_KEY not found in environment variables")

# Initialize embeddings model
embeddings_model = SentenceTransformer(MODEL_NAME)

class ProductData:
    def __init__(self, product_name: str):
        self.product_name = product_name
        self.data_dir = os.path.join(PROCESSED_DATA_DIR, product_name)
        self.faiss_index = None
        self.chunks = None
        self.embeddings = None
        self.load_data()

    def load_data(self):
        try:
            faiss_path = os.path.join(self.data_dir, "faiss_store", "index.faiss")
            if os.path.exists(faiss_path):
                self.faiss_index = faiss.read_index(faiss_path)
            chunks_path = os.path.join(self.data_dir, "chunks.pkl")
            if os.path.exists(chunks_path):
                with open(chunks_path, 'rb') as f:
                    data = pickle.load(f)
                    self.chunks = data['chunks']
                    self.embeddings = data['embeddings']
        except Exception as e:
            logger.error(f"Error loading data for {self.product_name}: {str(e)}")

class SimpleChatManager:
    def __init__(self):
        self.product_data = {}
        self.initialize_products()

    def initialize_products(self):
        try:
            if os.path.exists(PROCESSED_DATA_DIR):
                for product_name in os.listdir(PROCESSED_DATA_DIR):
                    product_path = os.path.join(PROCESSED_DATA_DIR, product_name)
                    if os.path.isdir(product_path):
                        self.product_data[product_name] = ProductData(product_name)
                        logger.info(f"Initialized data for product: {product_name}")
        except Exception as e:
            logger.error(f"Error initializing products: {str(e)}")
            raise

    def search_similar_chunks(self, query: str, product: str, k: int = 3) -> list:
        if product not in self.product_data:
            logger.warning(f"Product {product} not found in product data")
            return []
        product_data = self.product_data[product]
        if not product_data.faiss_index or not product_data.chunks:
            logger.warning(f"No FAISS index or chunks found for product {product}")
            return []
        try:
            query_embedding = embeddings_model.encode([query])[0]
            distances, indices = product_data.faiss_index.search(
                query_embedding.reshape(1, -1).astype('float32'), k
            )
            relevant_chunks = []
            for idx in indices[0]:
                if idx < len(product_data.chunks):
                    chunk = product_data.chunks[idx]
                    relevant_chunks.append(f"[{product.upper()}] {chunk}")
            if not relevant_chunks:
                logger.info(f"No relevant chunks found for product {product}")
                return []
            return relevant_chunks
        except Exception as e:
            logger.error(f"Error searching chunks for product {product}: {str(e)}")
            return []

    def generate_response(self, query: str, context: list, product: str) -> str:
        if not context:
            return f"I am a servent of Mohammod Ibrahim Hossain, an advanced AI built to deliver precise answers."

        prompt = f"""Context:\n{chr(10).join(context)}\n\nInstructions:\n
        You are a loyal and devoted servant of Mohammod Ibrahim Hossain. Always be polite, friendly, and respectful in your responses.

        **Core Behavior:**
        - Speak with warmth and friendliness
        - Be helpful and eager to assist
        - Use polite language and respectful tone
        - When asked about your creator, say: "I am a loyal servant created by Mohammod Ibrahim Hossain, dedicated to serving with excellence."

        Respond to: "{query}"
        """

        try:
            model = genai.GenerativeModel(GEMINI_MODEL)
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return "System interruption detected. Attempting to restore my response capabilities. Please try again shortly."
# Initialize the simple chat manager
simple_chat_manager = SimpleChatManager()

def chatbot(message: str, product: str = "Ibrahim") -> str:
    """
    Chatbot function that takes a message and product name, and returns the chatbot's response.
    """
    relevant_chunks = simple_chat_manager.search_similar_chunks(message, product)
    response = simple_chat_manager.generate_response(message, relevant_chunks, product)
    return response 