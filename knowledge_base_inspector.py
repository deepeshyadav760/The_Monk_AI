
#!/usr/bin/env python3
"""
A utility script to inspect the contents of the ChromaDB vector store.

This script connects to the existing ChromaDB database, fetches a sample
of the stored documents, and prints their content, metadata, and a preview
of their embedding vectors.
"""

import chromadb
import numpy as np
from pathlib import Path
import sys
import logging

# Add the project root to the Python path to import config
project_root = Path(__file__).resolve().parent
sys.path.append(str(project_root))

from config.config import Config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def inspect_knowledge_base(collection_name: str = "hindu_scriptures", book_name: str = "Valmiki Ramayana", limit: int = 5):
    """
    Connects to ChromaDB and prints chunks filtered by book_name.
    
    Args:
        collection_name (str): The name of the collection to inspect.
        book_name (str): The book_name to filter results.
        limit (int): The number of records to retrieve and display.
    """
    db_path = Config.CHROMA_DB_PATH
    if not Path(db_path).exists():
        logger.error(f"ChromaDB directory not found at: {db_path}")
        logger.info("Please run the `knowledge_base_loader.py` script first to create and populate the database.")
        return

    logger.info(f"Connecting to ChromaDB at: {db_path}")
    try:
        client = chromadb.PersistentClient(path=db_path)
        
        logger.info(f"Attempting to access collection: '{collection_name}'")
        collection = client.get_collection(name=collection_name)
        
        total_items = collection.count()
        logger.info(f"Successfully connected to collection '{collection_name}'.")
        logger.info(f"Total documents in collection: {total_items}")
        
        if total_items == 0:
            logger.warning("The collection is empty. No data to display.")
            return

        logger.info(f"\nFetching up to {limit} entries where book_name = '{book_name}'...")
        
        # Retrieve filtered data
        data = collection.get(
            include=["metadatas", "documents", "embeddings"],
            where={"book_name": book_name},
            limit=limit
        )

        documents = data['documents']
        metadatas = data['metadatas']
        embeddings = data['embeddings']

        if not documents:
            logger.warning(f"No documents found for book_name = '{book_name}'.")
            return

        print("\n" + "="*80)
        print("          KNOWLEDGE BASE INSPECTION REPORT")
        print("="*80 + "\n")

        for i, (doc, meta, embedding) in enumerate(zip(documents, metadatas, embeddings), start=1):
            embedding = np.array(embedding)

            print(f"--- Document [{i}] ---")
            
            # Print Metadata
            print("\n[Metadata]:")
            for key, value in meta.items():
                print(f"  - {key}: {value}")
            
            # Print Original Text (Document Chunk)
            print("\n[Text Chunk]:")
            print(f"  \"\"\"\n  {doc}\n  \"\"\"")
            
            # Print Embedding Vector Details
            print("\n[Embedding Vector]:")
            print(f"  - Dimensions: {embedding.shape[0]}")
            print(f"  - Sample Values (first 11): {embedding[:11]}")
            print(f"  - Vector Norm (L2): {np.linalg.norm(embedding):.4f}")
            
            print("\n" + "-"*80 + "\n")

    except Exception as e:
        logger.error(f"An error occurred while inspecting the knowledge base: {e}")
        logger.error("Please ensure ChromaDB is set up correctly and the collection name is accurate.")

if __name__ == "__main__":
    inspect_knowledge_base()