# Data processing
import json
import pandas as pd
from typing import List, Dict, Any
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document
import logging
import os

logger = logging.getLogger(__name__)

class DocumentProcessor:
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""]
        )
    
    def csv_to_jsonl(self, csv_file_path: str, output_path: str = None) -> str:
        """Convert CSV to JSONL format"""
        try:
            df = pd.read_csv(csv_file_path)
            
            if output_path is None:
                output_path = csv_file_path.replace('.csv', '.jsonl')
            
            with open(output_path, 'w', encoding='utf-8') as f:
                for _, row in df.iterrows():
                    # Create content from paragraph column
                    content = row.get('paragraph', '')
                    
                    # Create metadata from other columns
                    metadata = {
                        "book_name": row.get('book_name', ''),
                        "chapter": row.get('chapter', ''),
                        "section": row.get('section', ''),
                        "verse_number": row.get('verse_number', ''),
                    }
                    
                    # Remove empty values from metadata
                    metadata = {k: v for k, v in metadata.items() if v != '' and pd.notna(v)}
                    
                    jsonl_record = {
                        "content": content,
                        "metadata": metadata
                    }
                    
                    f.write(json.dumps(jsonl_record, ensure_ascii=False) + '\n')
            
            logger.info(f"CSV converted to JSONL: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error converting CSV to JSONL: {e}")
            raise
    
    def txt_to_jsonl(self, txt_file_path: str, output_path: str = None) -> str:
        """Convert TXT to JSONL format"""
        try:
            with open(txt_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if output_path is None:
                output_path = txt_file_path.replace('.txt', '.jsonl')
            
            # Split the content into chunks
            chunks = self.text_splitter.split_text(content)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                for i, chunk in enumerate(chunks):
                    metadata = {
                        "source_file": os.path.basename(txt_file_path),
                        "chunk_id": i
                    }
                    
                    jsonl_record = {
                        "content": chunk.strip(),
                        "metadata": metadata
                    }
                    
                    f.write(json.dumps(jsonl_record, ensure_ascii=False) + '\n')
            
            logger.info(f"TXT converted to JSONL: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error converting TXT to JSONL: {e}")
            raise
    
    def load_jsonl_documents(self, jsonl_file_path: str) -> List[Document]:
        """Load documents from JSONL file"""
        documents = []
        try:
            with open(jsonl_file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    data = json.loads(line.strip())
                    doc = Document(
                        page_content=data['content'],
                        metadata=data['metadata']
                    )
                    documents.append(doc)
            
            logger.info(f"Loaded {len(documents)} documents from {jsonl_file_path}")
            return documents
            
        except Exception as e:
            logger.error(f"Error loading JSONL documents: {e}")
            raise
    
    def chunk_documents(self, documents: List[Document]) -> List[Document]:
        """Chunk documents for better retrieval"""
        try:
            chunked_docs = []
            for doc in documents:
                chunks = self.text_splitter.split_text(doc.page_content)
                for i, chunk in enumerate(chunks):
                    if chunk.strip():  # Only add non-empty chunks
                        metadata = doc.metadata.copy()
                        metadata['chunk_id'] = i
                        metadata['total_chunks'] = len(chunks)
                        
                        chunked_doc = Document(
                            page_content=chunk,
                            metadata=metadata
                        )
                        chunked_docs.append(chunked_doc)
            
            logger.info(f"Created {len(chunked_docs)} chunks from {len(documents)} documents")
            return chunked_docs
            
        except Exception as e:
            logger.error(f"Error chunking documents: {e}")
            raise
    
    def process_all_data(self, data_directory: str) -> List[Document]:
        """Process all CSV and TXT files in directory"""
        all_documents = []
        
        try:
            for filename in os.listdir(data_directory):
                file_path = os.path.join(data_directory, filename)
                
                if filename.endswith('.csv'):
                    jsonl_path = self.csv_to_jsonl(file_path)
                    docs = self.load_jsonl_documents(jsonl_path)
                    all_documents.extend(docs)
                    
                elif filename.endswith('.txt'):
                    jsonl_path = self.txt_to_jsonl(file_path)
                    docs = self.load_jsonl_documents(jsonl_path)
                    all_documents.extend(docs)
                    
                elif filename.endswith('.jsonl'):
                    docs = self.load_jsonl_documents(file_path)
                    all_documents.extend(docs)
            
            # Chunk all documents
            chunked_documents = self.chunk_documents(all_documents)
            
            logger.info(f"Processed total {len(chunked_documents)} document chunks")
            return chunked_documents
            
        except Exception as e:
            logger.error(f"Error processing data directory: {e}")
            raise