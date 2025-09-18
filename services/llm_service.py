# services/llm_service.py

from groq import Groq
# --- UPDATED IMPORT ---
from deep_translator import GoogleTranslator
import re
from typing import List, Dict, Any
import logging
from config.config import Config
from google.api_core.exceptions import GoogleAPICallError
try:
    from google_search import google_search
except (ImportError, GoogleAPICallError) as e:
    print(f"Warning: Google Search tool not available. Keyword explanations will be disabled. Error: {e}")
    google_search = None


logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        self.groq_client = Groq(api_key=Config.GROQ_API_KEY)

    async def identify_and_explain_keywords(self, text: str) -> Dict[str, str]:
        explanations = {}
        if not google_search:
            return explanations # Return empty if search is not available

        try:
            prompt = f"""From the following text, identify a maximum of 3 key spiritual or Sanskrit terms that a beginner might not understand. List only the terms, separated by commas.

Text: "{text}"

Terms:"""

            response = self.groq_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama3-8b-8192",
                temperature=0.1,
                max_tokens=50,
            )
            
            keywords_str = response.choices[0].message.content.strip()
            keywords = [kw.strip() for kw in keywords_str.split(',') if kw.strip()]

            if not keywords:
                return {}

            search_queries = [f"what is the meaning of {kw} in hinduism" for kw in keywords]
            search_results_list = google_search.search(queries=search_queries)
            
            # The tool returns a list of lists of dictionaries
            search_results = [item for sublist in search_results_list for item in sublist]

            for i, keyword in enumerate(keywords):
                # Find the corresponding search result
                result_for_keyword = next((res for res in search_results if keyword.lower() in res.get('query', '').lower()), None)
                
                if result_for_keyword and result_for_keyword.get('snippets'):
                    definition = result_for_keyword['snippets'][0]
                    explanations[keyword.title()] = definition
                else:
                    explanations[keyword.title()] = "Meaning not found."

        except Exception as e:
            logger.error(f"Error identifying or explaining keywords: {e}")
            return {}
            
        return explanations

    def get_book_recommendations(self, context_docs: List[Dict]) -> List[str]:
        if not context_docs:
            return []
        
        source_books = list(set(
            doc['metadata'].get('book_name') 
            for doc in context_docs 
            if doc.get('metadata') and doc['metadata'].get('book_name')
        ))
        
        return source_books[:3]
    
    def create_prompt(self, query: str, context_docs: List[Dict], mode: str) -> str:
        context_text = "\n\n".join([
            f"Source: {doc['metadata'].get('book_name', 'Unknown')} - {doc['metadata'].get('chapter', '')} {doc['metadata'].get('section', '')}\nContent: {doc['content']}"
            for doc in context_docs
        ])
        
        if mode == "beginner":
            prompt = f"""You are The Monk AI, a helpful guide to Hindu philosophy for beginners.
Use the following context from Hindu scriptures to answer the user's question.
Your answer must be clear, simple, and directly based on the provided context.
Explain any complex spiritual terms for a beginner.
Always cite the sources you used from the context.
Context from Hindu scriptures:
---
{context_text}
---
User Question: {query}
Please provide a clear, direct answer. Be concise and educational for someone new to these concepts."""
        else:
            prompt = f"""You are The Monk AI, an advanced scholarly assistant for Hindu philosophy.
Use the provided context from Hindu scriptures to give a detailed and nuanced answer to the user's question.
Your analysis should be in-depth, referencing multiple sources from the context where applicable and discussing philosophical perspectives.
Use appropriate Sanskrit terminology.
Always cite the specific sources used from the context.
Context from Hindu scriptures:
---
{context_text}
---
User Question: {query}
Provide a comprehensive and scholarly response based on the context."""
        return prompt
    
    async def generate_response(self, query: str, context_docs: List[Dict], mode: str) -> Dict[str, Any]:
        try:
            prompt = self.create_prompt(query, context_docs, mode)
            
            chat_completion = self.groq_client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are The Monk AI, an expert in Hindu philosophy. Provide accurate, respectful, and well-cited responses based on the context given."},
                    {"role": "user", "content": prompt}
                ],
                model=Config.LLM_MODEL,
                temperature=Config.TEMPERATURE,
                max_tokens=Config.MAX_TOKENS,
            )
            response_text = chat_completion.choices[0].message.content
            
            citations = self.extract_citations(context_docs)
            recommendations = self.get_book_recommendations(context_docs)
            
            keywords_explained = None
            if mode == "beginner":
                keywords_explained = await self.identify_and_explain_keywords(response_text)
            
            return {
                "response": response_text,
                "citations": citations,
                "recommendations": recommendations,
                "keywords_explained": keywords_explained
            }
        except Exception as e:
            logger.error(f"Error generating LLM response: {e}")
            raise
    
    def extract_citations(self, context_docs: List[Dict]) -> List[Dict]:
        citations = []
        for doc in context_docs:
            citation = {
                "book": doc['metadata'].get('book_name', 'Unknown Source'),
                "chapter": doc['metadata'].get('chapter', ''),
                "section": doc['metadata'].get('section', ''),
                "verse": doc['metadata'].get('verse_number', ''),
                "content_preview": doc['content'][:100] + "...",
            }
            citations.append(citation)
        return citations
    
    # --- UPDATED FUNCTION ---
    async def translate_to_hindi(self, text: str) -> str:
        """Translate response to Hindi using deep-translator."""
        try:
            if not text or not text.strip():
                return ""
            # This runs in a separate thread to avoid blocking asyncio event loop
            translated_text = GoogleTranslator(source='auto', target='hi').translate(text)
            return translated_text
        except Exception as e:
            logger.error(f"Translation error: {e}")
            return "अनुवाद अनुपलब्ध है"  # Translation unavailable

    async def transcribe_audio(self, audio_file_path: str) -> str:
        """Transcribe audio to text using Groq's Whisper API"""
        try:
            with open(audio_file_path, "rb") as audio_file:
                transcription = self.groq_client.audio.transcriptions.create(
                    file=audio_file,
                    model=Config.WHISPER_MODEL,
                    response_format="text"
                )
            return str(transcription)
        except Exception as e:
            logger.error(f"Audio transcription error: {e}")
            raise

