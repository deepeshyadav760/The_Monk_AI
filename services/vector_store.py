# services/vector_store.py

import chromadb
from chromadb.config import Settings
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.docstore.document import Document
from sentence_transformers import CrossEncoder
from typing import List, Dict, Any
import logging
from config.config import Config
import shutil, os

try:
    from langchain_huggingface import HuggingFaceEmbeddings
    from langchain_chroma import Chroma
except ImportError:
    # Fallback to old imports
    from langchain.embeddings import HuggingFaceEmbeddings
    from langchain.vectorstores import Chroma


logger = logging.getLogger(__name__)

class VectorStore:
    def __init__(self):
        self.embedding_model = HuggingFaceEmbeddings(
            model_name=Config.EMBEDDING_MODEL,
            model_kwargs={'device': 'cpu'}
        )
        
        self.reranker = CrossEncoder(Config.RERANKER_MODEL)
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=Config.CHROMA_DB_PATH,
            settings=Settings(anonymized_telemetry=False)
        )
        
        self.collection_name = "hindu_scriptures"
        self.vectorstore = None
        
    async def initialize_vectorstore(self):
        """Initialize or load existing vector store"""
        try:
            self.vectorstore = Chroma(
                client=self.client,
                collection_name=self.collection_name,
                embedding_function=self.embedding_model,
                persist_directory=Config.CHROMA_DB_PATH
            )
            logger.info("Vector store initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing vector store: {e}")
            return {"error": str(e)}
    
    async def add_documents(self, documents: List[Document]):
        """Add documents to vector store"""
        try:
            if not self.vectorstore:
                await self.initialize_vectorstore()
            
            # Add documents in batches
            batch_size = 100
            for i in range(0, len(documents), batch_size):
                batch = documents[i:i + batch_size]
                self.vectorstore.add_documents(batch)
                logger.info(f"Added batch {i//batch_size + 1} of {(len(documents) + batch_size - 1)//batch_size}")
            
            logger.info(f"Added {len(documents)} documents to vector store")
            
        except Exception as e:
            logger.error(f"Error adding documents to vector store: {e}")
            raise
    
    async def similarity_search(self, query: str, k: int = Config.TOP_K_RETRIEVAL) -> List[Document]:
        """Perform similarity search"""
        try:
            if not self.vectorstore:
                await self.initialize_vectorstore()
            
            results = self.vectorstore.similarity_search(query, k=k)
            logger.info(f"Retrieved {len(results)} documents for query")
            return results
            
        except Exception as e:
            logger.error(f"Error in similarity search: {e}")
            raise
    
    def rerank_documents(self, query: str, documents: List[Document], top_k: int = Config.TOP_K_RERANK) -> List[Dict[str, Any]]:
        """Rerank documents using cross-encoder"""
        try:
            if not documents:
                return []
            
            pairs = [(query, doc.page_content) for doc in documents]
            scores = self.reranker.predict(pairs)
            
            results = [
                {
                    'content': doc.page_content,
                    'metadata': doc.metadata,
                    'score': float(score),
                    'rank': i + 1
                }
                for i, (doc, score) in enumerate(zip(documents, scores))
            ]
            
            results = sorted(results, key=lambda x: x['score'], reverse=True)
            return results[:top_k]
            
        except Exception as e:
            logger.error(f"Error in reranking: {e}")
            return [
                {
                    'content': doc.page_content,
                    'metadata': doc.metadata,
                    'score': 0.5,
                    'rank': i + 1
                }
                for i, doc in enumerate(documents[:top_k])
            ]
    
    async def search_and_rerank(self, query: str) -> List[Dict[str, Any]]:
        """Combined search and rerank pipeline"""
        try:
            initial_results = await self.similarity_search(query, Config.TOP_K_RETRIEVAL)
            return self.rerank_documents(query, initial_results, Config.TOP_K_RERANK)
        except Exception as e:
            logger.error(f"Error in search and rerank: {e}")
            raise
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store"""
        try:
            if not self.vectorstore:
                return {"error": "Vector store not initialized"}
            
            collection = self.client.get_collection(self.collection_name)
            count = collection.count()
            
            return {
                "collection_name": self.collection_name,
                "total_documents": count,
                "embedding_model": Config.EMBEDDING_MODEL,
                "reranker_model": Config.RERANKER_MODEL
            }
            
        except Exception as e:
            logger.error(f"Error getting collection stats: {e}")
            return {"error": str(e)}


    def reset_vectorstore(self):
        """Delete the existing ChromaDB and reset"""
        try:
            if os.path.exists(Config.CHROMA_DB_PATH):
                shutil.rmtree(Config.CHROMA_DB_PATH)
                logger.warning("Vector store reset: deleted old ChromaDB folder")
            self.vectorstore = None
            self.initialize_vectorstore()
        except Exception as e:
            logger.error(f"Error resetting vector store: {e}")
            raise