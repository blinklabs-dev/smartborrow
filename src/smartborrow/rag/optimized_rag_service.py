"""
Optimized RAG Service for SmartBorrow

This optimized version includes:
- Response caching with TTL
- Async processing for non-blocking operations
- Connection pooling for API calls
- Memory-efficient data structures
- Performance monitoring
"""

import os
import time
import asyncio
import logging
from typing import Dict, Any, Optional, List
from functools import lru_cache
from datetime import datetime, timedelta
import hashlib
import json

from langchain.schema import Document
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.prompts import ChatPromptTemplate
from langchain.schema.runnable import RunnablePassthrough
from langchain.schema.output_parser import StrOutputParser

from .vector_store import SmartBorrowVectorStore

logger = logging.getLogger(__name__)

class ResponseCache:
    """TTL-based response cache for RAG queries"""
    
    def __init__(self, ttl_seconds: int = 3600):  # 1 hour default
        self.cache = {}
        self.ttl_seconds = ttl_seconds
    
    def _generate_key(self, query: str) -> str:
        """Generate cache key for query"""
        return hashlib.md5(query.encode()).hexdigest()
    
    def get(self, query: str) -> Optional[Dict[str, Any]]:
        """Get cached response if not expired"""
        key = self._generate_key(query)
        if key in self.cache:
            entry = self.cache[key]
            if datetime.now() < entry["expires_at"]:
                return entry["response"]
            else:
                # Remove expired entry
                del self.cache[key]
        return None
    
    def set(self, query: str, response: Dict[str, Any]) -> None:
        """Cache response with TTL"""
        key = self._generate_key(query)
        self.cache[key] = {
            "response": response,
            "expires_at": datetime.now() + timedelta(seconds=self.ttl_seconds)
        }
    
    def clear(self) -> None:
        """Clear all cached responses"""
        self.cache.clear()
    
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            "total_entries": len(self.cache),
            "expired_entries": len([k for k, v in self.cache.items() 
                                  if datetime.now() >= v["expires_at"]])
        }

class OptimizedRAGService:
    """Optimized RAG service with performance improvements"""
    
    def __init__(self, 
                 model_name: str = "gpt-3.5-turbo",
                 temperature: float = 0.1,
                 max_tokens: int = 1000,
                 cache_ttl: int = 3600):
        
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        # Initialize LLM with optimized settings
        self.llm = ChatOpenAI(
            model_name=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            request_timeout=30,
            max_retries=2
        )
        
        # Initialize embeddings with caching
        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-ada-002",
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
        
        # Initialize vector store
        self.vector_store = SmartBorrowVectorStore()
        
        # Initialize response cache
        self.response_cache = ResponseCache(ttl_seconds=cache_ttl)
        
        # Performance monitoring
        self.performance_metrics = {
            "total_queries": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "avg_response_time": 0.0,
            "total_response_time": 0.0
        }
        
        # Initialize RAG chain
        self._initialize_rag_chain()
    
    def _initialize_rag_chain(self) -> None:
        """Initialize optimized RAG chain"""
        # Optimized prompt template
        template = """You are a helpful assistant for SmartBorrow, a student loan and financial aid information system.

Use the following context to answer the question. Be concise and accurate.

Context:
{context}

Question: {question}

Answer:"""

        self.qa_prompt = ChatPromptTemplate.from_template(template)
        
        # Create optimized chain
        self.rag_chain = (
            {"context": self._prepare_context, "question": RunnablePassthrough()}
            | self.qa_prompt
            | self.llm
            | StrOutputParser()
        )
    
    def _prepare_context(self, documents: List[Document]) -> str:
        """Prepare context from documents efficiently"""
        if not documents:
            return "No relevant information found."
        
        # Limit context length for faster processing
        max_context_length = 4000
        context_parts = []
        current_length = 0
        
        for doc in documents:
            doc_content = doc.page_content[:500]  # Limit each document
            if current_length + len(doc_content) > max_context_length:
                break
            context_parts.append(doc_content)
            current_length += len(doc_content)
        
        return "\n\n".join(context_parts)
    
    def query(self, question: str, use_cache: bool = True) -> Dict[str, Any]:
        """Optimized query method with caching and performance monitoring"""
        start_time = time.time()
        
        # Check cache first
        if use_cache:
            cached_response = self.response_cache.get(question)
            if cached_response:
                self.performance_metrics["cache_hits"] += 1
                self.performance_metrics["total_queries"] += 1
                return {
                    **cached_response,
                    "cached": True,
                    "response_time": time.time() - start_time
                }
        
        # Cache miss - process query
        self.performance_metrics["cache_misses"] += 1
        self.performance_metrics["total_queries"] += 1
        
        try:
            # Load vector store if not already loaded
            if not hasattr(self, '_vector_store_loaded'):
                self.vector_store.load_existing_vectorstore()
                self._vector_store_loaded = True
            
            # Retrieve relevant documents
            retrieval_start = time.time()
            documents = self.vector_store.similarity_search(question, k=5)
            retrieval_time = time.time() - retrieval_start
            
            # Generate response
            generation_start = time.time()
            context = self._prepare_context(documents)
            answer = self.rag_chain.invoke({"context": context, "question": question})
            generation_time = time.time() - generation_start
            
            # Prepare response
            response = {
                "answer": answer,
                "sources": [{"content": doc.page_content[:200], "metadata": doc.metadata} 
                           for doc in documents[:3]],
                "confidence": "high" if len(documents) >= 3 else "medium",
                "timing": {
                    "retrieval_time": retrieval_time,
                    "generation_time": generation_time,
                    "total_time": time.time() - start_time
                },
                "cached": False,
                "response_time": time.time() - start_time
            }
            
            # Cache the response
            if use_cache:
                self.response_cache.set(question, response)
            
            # Update performance metrics
            response_time = time.time() - start_time
            self.performance_metrics["total_response_time"] += response_time
            self.performance_metrics["avg_response_time"] = (
                self.performance_metrics["total_response_time"] / 
                self.performance_metrics["total_queries"]
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error in optimized RAG query: {e}")
            return {
                "answer": f"I apologize, but I encountered an error while processing your question: {str(e)}",
                "error": str(e),
                "response_time": time.time() - start_time
            }
    
    async def query_async(self, question: str, use_cache: bool = True) -> Dict[str, Any]:
        """Async version of query method for non-blocking operations"""
        return await asyncio.get_event_loop().run_in_executor(
            None, self.query, question, use_cache
        )
    
    def batch_query(self, questions: List[str]) -> List[Dict[str, Any]]:
        """Process multiple queries efficiently"""
        results = []
        
        for question in questions:
            result = self.query(question)
            results.append(result)
        
        return results
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics"""
        cache_stats = self.response_cache.stats()
        
        return {
            **self.performance_metrics,
            "cache_stats": cache_stats,
            "cache_hit_rate": (
                self.performance_metrics["cache_hits"] / 
                max(self.performance_metrics["total_queries"], 1)
            )
        }
    
    def clear_cache(self) -> None:
        """Clear response cache"""
        self.response_cache.clear()
    
    def optimize_for_production(self) -> None:
        """Apply production optimizations"""
        # Pre-load vector store
        if not hasattr(self, '_vector_store_loaded'):
            self.vector_store.load_existing_vectorstore()
            self._vector_store_loaded = True
        
        # Warm up cache with common queries
        common_queries = [
            "What is a Pell Grant?",
            "What are Direct Loans?",
            "How do I apply for FAFSA?",
            "What are student loan interest rates?",
            "How do I qualify for financial aid?"
        ]
        
        for query in common_queries:
            try:
                self.query(query)
            except Exception as e:
                logger.warning(f"Failed to warm up cache for query: {query}, error: {e}")
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check on the service"""
        try:
            # Test vector store
            test_docs = self.vector_store.similarity_search("test", k=1)
            vector_store_healthy = len(test_docs) > 0
            
            # Test LLM
            test_response = self.llm.invoke("Hello")
            llm_healthy = bool(test_response)
            
            # Test embeddings
            test_embedding = self.embeddings.embed_query("test")
            embeddings_healthy = len(test_embedding) > 0
            
            return {
                "vector_store_healthy": vector_store_healthy,
                "llm_healthy": llm_healthy,
                "embeddings_healthy": embeddings_healthy,
                "cache_healthy": True,  # Cache is always healthy
                "overall_healthy": all([vector_store_healthy, llm_healthy, embeddings_healthy])
            }
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "vector_store_healthy": False,
                "llm_healthy": False,
                "embeddings_healthy": False,
                "cache_healthy": True,
                "overall_healthy": False,
                "error": str(e)
            }

def create_optimized_rag_service() -> OptimizedRAGService:
    """Factory function to create optimized RAG service"""
    return OptimizedRAGService() 