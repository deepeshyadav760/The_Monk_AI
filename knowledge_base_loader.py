# knowledge_base_loader.py

#!/usr/bin/env python3
"""
Script to initialize the knowledge base with Hindu scriptures data.
Run this script to process your CSV/TXT/JSONL files and populate the vector database.
"""

import asyncio
import os
import sys
import logging
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).resolve().parent
sys.path.append(str(project_root))

from services.document_processor import DocumentProcessor
from services.vector_store import VectorStore
from config.config import Config


# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def initialize_knowledge_base():
    """Initialize the knowledge base with Hindu scriptures"""
    
    data_dir = project_root / "data"
    if not data_dir.exists():
        logger.error(f"Data directory not found: {data_dir}")
        logger.info("Please create a 'data' directory and add your Hindu scriptures files (.csv, .txt, .jsonl)")
        return False
    
    data_files = list(data_dir.glob("*.csv")) + list(data_dir.glob("*.txt")) + list(data_dir.glob("*.jsonl"))
    if not data_files:
        logger.error("No data files found in the data directory")
        logger.info("Please add CSV, TXT, or JSONL files with Hindu scriptures to the data directory")
        return False
    
    logger.info(f"Found {len(data_files)} data files to process:")
    for file in data_files:
        logger.info(f"  - {file.name}")
    
    try:
        logger.info("Initializing document processor...")
        doc_processor = DocumentProcessor(
            chunk_size=Config.CHUNK_SIZE,
            chunk_overlap=Config.CHUNK_OVERLAP
        )
        
        logger.info("Processing documents...")
        documents = doc_processor.process_all_data(str(data_dir))
        
        if not documents:
            logger.error("No documents were processed")
            return False
        
        logger.info(f"Successfully processed {len(documents)} document chunks")
        
        logger.info("Initializing vector store...")
        vector_store = VectorStore()
        await vector_store.initialize_vectorstore()
        
        logger.info("Adding documents to vector store...")
        await vector_store.add_documents(documents)
        
        stats = vector_store.get_collection_stats()
        logger.info("Knowledge base initialization completed!")
        logger.info(f"Statistics: {stats}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error initializing knowledge base: {e}")
        return False

def create_sample_data():
    """Create sample data files for testing"""
    data_dir = project_root / "data"
    data_dir.mkdir(exist_ok=True)
    
    # Sample JSONL data
    sample_jsonl = '''{"content": "The word Upanishad derives from the Sanskrit words upa (near), ni (down), and shad (to sit), thus meaning 'sitting down near' a spiritual teacher to receive instruction.", "metadata": {"book_name": "Introduction to Upanishads", "chapter": "Origins", "section": "Etymology"}}
{"content": "Key concepts discussed in the Upanishads include: Brahman (the ultimate reality), Atman (the individual soul), Moksha (liberation), Maya (the illusory nature of the world), and Dharma (righteous duty).", "metadata": {"book_name": "Introduction to Upanishads", "chapter": "Core Concepts", "section": "Summary"}}
{"content": "Dhritarashtra said: O Sanjaya, after my sons and the sons of Pandu assembled in the place of pilgrimage at Kurukshetra, desiring to fight, what did they do?", "metadata": {"book_name": "Bhagavad Gita", "chapter": "1", "verse_number": "1"}}
{"content": "The Blessed Lord said: While speaking learned words, you are mourning for what is not worthy of grief. Those who are wise lament neither for the living nor for the dead.", "metadata": {"book_name": "Bhagavad Gita", "chapter": "2", "verse_number": "11"}}
'''
    
    try:
        (data_dir / "sample_scriptures.jsonl").write_text(sample_jsonl)
        
        logger.info("Sample data file created in the data directory:")
        logger.info("  - sample_scriptures.jsonl")
        logger.info("You can replace this with your actual Hindu scripture data in JSONL format.")
        
        return True
        
    except Exception as e:
        logger.error(f"Error creating sample data: {e}")
        return False

async def main():
    """Main function"""
    logger.info("=" * 60)
    logger.info("The Monk AI - Knowledge Base Loader")
    logger.info("=" * 60)
    
    data_dir = project_root / "data"
    if not data_dir.exists() or not any(data_dir.glob("*")):
        logger.info("No data directory or files found.")
        create_sample = input("Would you like to create a sample JSONL data file? (y/n): ").lower().strip()
        
        if create_sample == 'y':
            if not create_sample_data():
                logger.error("Failed to create sample data")
                return
        else:
            logger.info("Please add your Hindu scripture data files to the 'data' directory and run this script again.")
            return
    
    logger.info("\nStarting knowledge base initialization...")
    success = await initialize_knowledge_base()
    
    if success:
        logger.info("\n" + "=" * 60)
        logger.info("✅ Knowledge base initialization completed successfully!")
        logger.info("You can now start the FastAPI server.")
        logger.info("=" * 60)
    else:
        logger.error("\n" + "=" * 60)
        logger.error("❌ Knowledge base initialization failed!")
        logger.error("Please check the logs above for error details.")
        logger.error("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())