# rag_pipeline.py

from typing import Dict, Any, List, Optional
import logging
from services.vector_store import VectorStore
from services.llm_service import LLMService
from services.chat_service import ChatService
from models.database import QueryRequest, QueryResponse, ChatMessage
import os

logger = logging.getLogger(__name__)

class RAGPipeline:
    def __init__(self):
        self.vector_store = VectorStore()
        self.llm_service = LLMService()
        self.chat_service = ChatService()
        self.initialized = False
    
    async def initialize(self):
        if not self.initialized:
            await self.vector_store.initialize_vectorstore()
            self.initialized = True
            logger.info("RAG Pipeline initialized successfully")
    
    async def process_query(self, query_request: QueryRequest, user_id: str) -> QueryResponse:
        try:
            await self.initialize()
            
            relevant_docs = await self.vector_store.search_and_rerank(query_request.query)
            
            if not relevant_docs:
                fallback_answer = "I could not find relevant information in the scriptures to answer your question."
                return QueryResponse(
                    answer=fallback_answer,
                    hindi_translation=await self.llm_service.translate_to_hindi(fallback_answer),
                    citations=[],
                    recommendations=[],
                    session_id=query_request.session_id or ""
                )
            
            llm_response = await self.llm_service.generate_response(
                query_request.query, 
                relevant_docs, 
                query_request.mode
            )
            
            hindi_translation = await self.llm_service.translate_to_hindi(llm_response["response"])
            
            session_id = await self.handle_chat_session(
                user_id=user_id,
                session_id=query_request.session_id,
                query=query_request.query,
                response=llm_response["response"],
                mode=query_request.mode,
                citations=llm_response["citations"],
                hindi_translation=hindi_translation
            )
            
            return QueryResponse(
                answer=llm_response["response"],
                hindi_translation=hindi_translation,
                citations=llm_response["citations"],
                recommendations=llm_response["recommendations"],
                keywords_explained=llm_response.get("keywords_explained"),
                session_id=session_id
            )
            
        except Exception as e:
            logger.error(f"Error in RAG pipeline: {e}")
            raise
    
    async def handle_chat_session(
        self, user_id: str, session_id: Optional[str], query: str, response: str, 
        mode: str, citations: List[Dict], hindi_translation: str
    ) -> str:
        if not session_id:
            title = self.chat_service.generate_session_title(query)
            session = await self.chat_service.create_chat_session(user_id, title)
            session_id = str(session.id)
        
        user_message = ChatMessage(role="user", content=query, mode=mode)
        await self.chat_service.add_message_to_session(session_id, user_id, user_message)
        
        assistant_message = ChatMessage(
            role="assistant", content=response, mode=mode,
            citations=citations, hindi_translation=hindi_translation
        )
        await self.chat_service.add_message_to_session(session_id, user_id, assistant_message)
        
        return session_id
    
    async def process_voice_query(self, audio_file_path: str, mode: str, user_id: str, session_id: Optional[str] = None) -> QueryResponse:
        try:
            logger.info(f"Processing voice query for user {user_id}...")
            query_text = await self.llm_service.transcribe_audio(audio_file_path)
            logger.info(f"Transcribed text: {query_text}")

            if not query_text.strip():
                return QueryResponse(
                    answer="I couldn't understand what you said. Could you please speak clearly?",
                    hindi_translation="मुझे समझ नहीं आया कि आपने क्या कहा। क्या आप कृपया स्पष्ट रूप से बोल सकते हैं?",
                    citations=[],
                    recommendations=[],
                    session_id=session_id or ""
                )

            query_request = QueryRequest(query=query_text, mode=mode, session_id=session_id)
            return await self.process_query(query_request, user_id)
        finally:
            # Clean up the temporary audio file
            if os.path.exists(audio_file_path):
                os.remove(audio_file_path)
                logger.info(f"Removed temporary audio file: {audio_file_path}")