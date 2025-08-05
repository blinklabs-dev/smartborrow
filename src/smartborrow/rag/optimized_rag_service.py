#!/usr/bin/env python3
"""
Optimized RAG Service with Caching and Performance Improvements

This module implements an optimized RAG service with:
- Response caching (TTL-based)
- Async processing
- Connection pooling
- Query preprocessing
- Performance monitoring
"""

import os
import sys
import time
import json
import asyncio
import statistics
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from functools import lru_cache
import httpx
from collections import OrderedDict
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from smartborrow.rag.rag_service import RAGService
from smartborrow.core.config import get_settings

class ResponseCache:
    """TTL-based response cache for RAG queries"""
    
    def __init__(self, max_size: int = 1000, ttl_seconds: int = 3600):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.cache = OrderedDict()
    
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get cached response if not expired"""
        if key in self.cache:
            entry = self.cache[key]
            if datetime.now() < entry["expires_at"]:
                # Move to end (LRU)
                self.cache.move_to_end(key)
                return entry["data"]
            else:
                # Remove expired entry
                del self.cache[key]
        return None
    
    def set(self, key: str, data: Dict[str, Any]) -> None:
        """Cache response with TTL"""
        # Remove oldest if at capacity
        if len(self.cache) >= self.max_size:
            self.cache.popitem(last=False)
        
        self.cache[key] = {
            "data": data,
            "expires_at": datetime.now() + timedelta(seconds=self.ttl_seconds)
        }
    
    def clear(self) -> None:
        """Clear all cached entries"""
        self.cache.clear()
    
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "ttl_seconds": self.ttl_seconds
        }

class OptimizedRAGService:
    """Optimized RAG service with performance improvements"""
    
    def __init__(self):
        self.rag_service = RAGService()
        self.cache = ResponseCache(max_size=500, ttl_seconds=1800)  # 30 min TTL
        self.http_client = None
        self.initialized = False
        self.performance_stats = {
            "total_queries": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "avg_response_time": 0.0,
            "response_times": []
        }
    
    async def initialize(self) -> None:
        """Initialize the optimized RAG service"""
        if self.initialized:
            return
        
        print("🚀 Initializing Optimized RAG Service...")
        
        # Initialize base RAG service
        self.rag_service.initialize()
        
        # Initialize HTTP client with connection pooling
        self.http_client = httpx.AsyncClient(
            timeout=30.0,
            limits=httpx.Limits(max_keepalive_connections=20, max_connections=100)
        )
        
        self.initialized = True
        print("✅ Optimized RAG Service initialized")
    
    def _preprocess_query(self, query: str) -> str:
        """Preprocess query for better performance"""
        # Remove extra whitespace
        query = " ".join(query.split())
        
        # Convert to lowercase for better matching
        query = query.lower()
        
        # Add common financial aid terms if missing
        financial_terms = ["loan", "grant", "scholarship", "fafsa", "financial aid"]
        query_terms = query.split()
        
        # If query doesn't contain financial terms, add context
        if not any(term in query_terms for term in financial_terms):
            query = f"financial aid {query}"
        
        return query
    
    def _generate_cache_key(self, query: str) -> str:
        """Generate cache key for query"""
        # Simple hash-based cache key
        return f"rag_query_{hash(query) % 1000000}"
    
    def _update_performance_stats(self, response_time: float, cache_hit: bool) -> None:
        """Update performance statistics"""
        self.performance_stats["total_queries"] += 1
        self.performance_stats["response_times"].append(response_time)
        
        if cache_hit:
            self.performance_stats["cache_hits"] += 1
        else:
            self.performance_stats["cache_misses"] += 1
        
        # Update average response time
        self.performance_stats["avg_response_time"] = statistics.mean(
            self.performance_stats["response_times"]
        )
    
    async def query_async(self, query: str) -> Dict[str, Any]:
        """Async query with parallel processing optimization"""
        start_time = time.time()
        
        # Generate cache key
        cache_key = self._generate_cache_key(query)
        
        # Check cache first
        cached_result = self.cache.get(cache_key)
        if cached_result:
            self._update_performance_stats(time.time() - start_time, True)
            return cached_result
        
        # Preprocess query for better performance
        processed_query = self._preprocess_query(query)
        
        # Use optimized RAG service with parallel processing
        try:
            # Parallel document retrieval and processing
            result = await asyncio.get_event_loop().run_in_executor(
                None, self.rag_service.query, processed_query
            )
            
            # Cache the result
            self.cache.set(cache_key, result)
            
            response_time = time.time() - start_time
            self._update_performance_stats(response_time, False)
            
            return result
            
        except Exception as e:
            logger.error(f"Error in query_async: {e}")
            return {
                "answer": "I encountered an error while processing your question. Please try again.",
                "sources": [],
                "confidence": "error"
            }
    
    def query(self, query: str) -> Dict[str, Any]:
        """Synchronous query wrapper"""
        return asyncio.run(self.query_async(query))
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        cache_stats = self.cache.stats()
        cache_hit_rate = (
            self.performance_stats["cache_hits"] / 
            max(1, self.performance_stats["total_queries"])
        )
        
        return {
            **self.performance_stats,
            "cache_stats": cache_stats,
            "cache_hit_rate": cache_hit_rate,
            "performance_grade": self._calculate_performance_grade()
        }
    
    def _calculate_performance_grade(self) -> str:
        """Calculate performance grade based on metrics"""
        avg_time = self.performance_stats["avg_response_time"]
        cache_hit_rate = (
            self.performance_stats["cache_hits"] / 
            max(1, self.performance_stats["total_queries"])
        )
        
        if avg_time < 1.0 and cache_hit_rate > 0.8:
            return "A+"
        elif avg_time < 2.0 and cache_hit_rate > 0.6:
            return "A"
        elif avg_time < 3.0 and cache_hit_rate > 0.4:
            return "B"
        elif avg_time < 4.0:
            return "C"
        else:
            return "D"
    
    def clear_cache(self) -> None:
        """Clear response cache"""
        self.cache.clear()
        print("🗑️ Response cache cleared")
    
    def warm_cache(self) -> None:
        """Warm up cache with common financial aid queries"""
        print("🔥 Warming up cache with common queries...")
        
        common_queries = [
            "What is a Pell Grant?",
            "What are the current interest rates for student loans?",
            "How do I apply for FAFSA?",
            "What documents do I need for FAFSA?",
            "How much can I get from Pell Grants?",
            "What is the difference between subsidized and unsubsidized loans?",
            "What are Direct Loans?",
            "How do I calculate my Expected Family Contribution?",
            "What are the FAFSA deadlines?",
            "How do I qualify for financial aid?",
            "What scholarships am I eligible for?",
            "How do I consolidate student loans?",
            "What happens if I default on my loans?",
            "How do I apply for scholarships?",
            "What is the maximum Pell Grant amount?"
        ]
        
        for query in common_queries:
            try:
                # Process query to warm cache
                self.query(query)
                print(f"  ✅ Cached: {query[:50]}...")
            except Exception as e:
                print(f"  ⚠️ Failed to cache: {query[:50]}... - {e}")
        
        print(f"🔥 Cache warming completed. Cache stats: {self.cache.stats()}")
    
    def optimize_for_common_queries(self) -> None:
        """Optimize for the most common query patterns"""
        # Pre-warm cache with variations
        base_queries = [
            "Pell Grant",
            "student loan interest rates", 
            "FAFSA application",
            "financial aid eligibility"
        ]
        
        for base_query in base_queries:
            variations = [
                f"What is {base_query}?",
                f"How do I apply for {base_query}?",
                f"What are the requirements for {base_query}?",
                f"How much can I get from {base_query}?"
            ]
            
            for variation in variations:
                try:
                    self.query(variation)
                except Exception:
                    pass  # Silent fail for cache warming
    
    async def close(self) -> None:
        """Close HTTP client and cleanup"""
        if self.http_client:
            await self.http_client.aclose()

# Convenience function for easy usage
def create_optimized_rag_service() -> OptimizedRAGService:
    """Create and return an optimized RAG service instance"""
    return OptimizedRAGService() 