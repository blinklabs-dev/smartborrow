#!/usr/bin/env python3
"""
Advanced Hybrid Retrieval for SmartBorrow

Implements multiple retrieval techniques:
- Multi-query retrieval
- Reranking with multiple models
- Contextual retrieval
- Metadata filtering
- Ensemble retrieval
"""

import asyncio
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from langchain.schema import Document
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings

@dataclass
class RetrievalConfig:
    """Configuration for advanced retrieval"""
    semantic_weight: float = 0.6
    keyword_weight: float = 0.4
    rerank_top_k: int = 10
    ensemble_size: int = 3
    context_window: int = 5
    metadata_boost: float = 1.5

class AdvancedHybridRetriever:
    """Advanced hybrid retrieval with multiple techniques"""
    
    def __init__(self, config: RetrievalConfig = RetrievalConfig()):
        self.config = config
        self.embeddings = OpenAIEmbeddings()
        self.vector_store = None
        self.keyword_index = {}
        self.metadata_index = {}
    
    def setup_vector_store(self, documents: List[Document]) -> None:
        """Setup vector store with advanced indexing"""
        if not documents:
            return
        
        # Create vector store
        texts = [doc.page_content for doc in documents]
        metadatas = [doc.metadata for doc in documents]
        
        self.vector_store = FAISS.from_texts(
            texts=texts,
            embedding=self.embeddings,
            metadatas=metadatas
        )
        
        # Build keyword index
        self._build_keyword_index(documents)
        
        # Build metadata index
        self._build_metadata_index(documents)
    
    def _build_keyword_index(self, documents: List[Document]) -> None:
        """Build keyword-based index for hybrid search"""
        import re
        
        for i, doc in enumerate(documents):
            # Extract keywords (financial terms, amounts, etc.)
            text = doc.page_content.lower()
            
            # Financial keywords
            financial_terms = re.findall(r'\$[\d,]+(?:\.\d{2})?', text)
            percentages = re.findall(r'\d+(?:\.\d+)?%', text)
            loan_types = re.findall(r'(?:direct|subsidized|unsubsidized|plus|private)\s+loan', text)
            
            # Process terms
            keywords = set()
            keywords.update(financial_terms)
            keywords.update(percentages)
            keywords.update(loan_types)
            
            # Add to index
            for keyword in keywords:
                if keyword not in self.keyword_index:
                    self.keyword_index[keyword] = []
                self.keyword_index[keyword].append(i)
    
    def _build_metadata_index(self, documents: List[Document]) -> None:
        """Build metadata-based index"""
        for i, doc in enumerate(documents):
            metadata = doc.metadata
            
            # Index by document type
            doc_type = metadata.get("document_type", "general")
            if doc_type not in self.metadata_index:
                self.metadata_index[doc_type] = []
            self.metadata_index[doc_type].append(i)
            
            # Index by chunk type
            chunk_type = metadata.get("chunk_type", "general")
            if chunk_type not in self.metadata_index:
                self.metadata_index[chunk_type] = []
            self.metadata_index[chunk_type].append(i)
    
    def multi_query_retrieval(self, query: str, k: int = 5) -> List[Document]:
        """Multi-query retrieval with query expansion"""
        # Generate multiple query variations
        query_variations = self._generate_query_variations(query)
        
        all_results = []
        for variation in query_variations:
            results = self.vector_store.similarity_search(variation, k=k)
            all_results.extend(results)
        
        # Deduplicate and rerank
        unique_results = self._deduplicate_results(all_results)
        reranked_results = self._rerank_results(unique_results, query)
        
        return reranked_results[:k]
    
    def _generate_query_variations(self, query: str) -> List[str]:
        """Generate query variations for better retrieval"""
        variations = [query]
        
        # Financial aid specific variations
        if "loan" in query.lower():
            variations.extend([
                f"{query} interest rate",
                f"{query} repayment",
                f"{query} eligibility"
            ])
        
        if "grant" in query.lower():
            variations.extend([
                f"{query} application",
                f"{query} requirements",
                f"{query} deadline"
            ])
        
        if "fafsa" in query.lower():
            variations.extend([
                f"{query} application process",
                f"{query} requirements",
                f"{query} documents needed"
            ])
        
        # Add synonyms
        synonyms = {
            "loan": ["borrowing", "debt", "financial aid"],
            "grant": ["scholarship", "award", "free money"],
            "interest": ["rate", "percentage", "cost"],
            "application": ["apply", "submit", "process"]
        }
        
        for word, syns in synonyms.items():
            if word in query.lower():
                for syn in syns:
                    variations.append(query.lower().replace(word, syn))
        
        return list(set(variations))  # Remove duplicates
    
    def contextual_retrieval(self, query: str, context: str = "", k: int = 5) -> List[Document]:
        """Contextual retrieval considering conversation history"""
        # Combine query with context
        contextual_query = f"{context} {query}".strip()
        
        # Get semantic results
        semantic_results = self.vector_store.similarity_search(contextual_query, k=k*2)
        
        # Apply context-based filtering
        filtered_results = self._filter_by_context(semantic_results, context)
        
        # Rerank with context
        reranked_results = self._rerank_with_context(filtered_results, query, context)
        
        return reranked_results[:k]
    
    def _filter_by_context(self, results: List[Document], context: str) -> List[Document]:
        """Filter results based on conversation context"""
        if not context:
            return results
        
        # Extract context keywords
        context_keywords = set(context.lower().split())
        
        filtered_results = []
        for result in results:
            # Check if result is relevant to context
            result_text = result.page_content.lower()
            result_keywords = set(result_text.split())
            
            # Calculate relevance score
            overlap = len(context_keywords.intersection(result_keywords))
            relevance_score = overlap / max(len(context_keywords), 1)
            
            if relevance_score > 0.1:  # Minimum relevance threshold
                filtered_results.append(result)
        
        return filtered_results
    
    def _rerank_with_context(self, results: List[Document], query: str, context: str) -> List[Document]:
        """Rerank results considering context"""
        if not results:
            return results
        
        # Calculate context-aware scores
        scored_results = []
        for result in results:
            score = self._calculate_context_score(result, query, context)
            scored_results.append((result, score))
        
        # Sort by score
        scored_results.sort(key=lambda x: x[1], reverse=True)
        
        return [result for result, score in scored_results]
    
    def _calculate_context_score(self, result: Document, query: str, context: str) -> float:
        """Calculate context-aware relevance score"""
        score = 0.0
        
        # Query relevance
        query_words = set(query.lower().split())
        result_words = set(result.page_content.lower().split())
        query_overlap = len(query_words.intersection(result_words))
        score += query_overlap / max(len(query_words), 1)
        
        # Context relevance
        if context:
            context_words = set(context.lower().split())
            context_overlap = len(context_words.intersection(result_words))
            score += context_overlap / max(len(context_words), 1) * 0.5
        
        # Metadata boost
        metadata = result.metadata
        if metadata.get("chunk_type") == "hierarchical":
            score += 0.2
        if metadata.get("key_sentence"):
            score += 0.3
        
        return score
    
    def ensemble_retrieval(self, query: str, k: int = 5) -> List[Document]:
        """Ensemble retrieval combining multiple methods"""
        # Get results from different methods
        semantic_results = self.vector_store.similarity_search(query, k=k)
        keyword_results = self._keyword_search(query, k=k)
        metadata_results = self._metadata_search(query, k=k)
        
        # Combine and score
        all_results = semantic_results + keyword_results + metadata_results
        unique_results = self._deduplicate_results(all_results)
        
        # Ensemble scoring
        ensemble_scores = self._calculate_ensemble_scores(unique_results, query)
        
        # Sort by ensemble score
        scored_results = [(result, score) for result, score in ensemble_scores]
        scored_results.sort(key=lambda x: x[1], reverse=True)
        
        return [result for result, score in scored_results[:k]]
    
    def _keyword_search(self, query: str, k: int = 5) -> List[Document]:
        """Keyword-based search"""
        query_words = query.lower().split()
        matching_docs = set()
        
        for word in query_words:
            if word in self.keyword_index:
                matching_docs.update(self.keyword_index[word])
        
        # Get documents by indices
        if self.vector_store and hasattr(self.vector_store, 'docstore'):
            results = []
            for idx in list(matching_docs)[:k]:
                if idx < len(self.vector_store.docstore._dict):
                    doc = list(self.vector_store.docstore._dict.values())[idx]
                    results.append(doc)
            return results
        
        return []
    
    def _metadata_search(self, query: str, k: int = 5) -> List[Document]:
        """Metadata-based search"""
        query_lower = query.lower()
        matching_docs = set()
        
        # Search by document type
        if "loan" in query_lower:
            if "loan_information" in self.metadata_index:
                matching_docs.update(self.metadata_index["loan_information"])
        
        if "grant" in query_lower or "financial aid" in query_lower:
            if "financial_aid" in self.metadata_index:
                matching_docs.update(self.metadata_index["financial_aid"])
        
        if "application" in query_lower or "apply" in query_lower:
            if "application_process" in self.metadata_index:
                matching_docs.update(self.metadata_index["application_process"])
        
        # Get documents by indices
        if self.vector_store and hasattr(self.vector_store, 'docstore'):
            results = []
            for idx in list(matching_docs)[:k]:
                if idx < len(self.vector_store.docstore._dict):
                    doc = list(self.vector_store.docstore._dict.values())[idx]
                    results.append(doc)
            return results
        
        return []
    
    def _calculate_ensemble_scores(self, results: List[Document], query: str) -> List[Tuple[Document, float]]:
        """Calculate ensemble scores for results"""
        scored_results = []
        
        for result in results:
            # Semantic score
            semantic_score = self._calculate_semantic_score(result, query)
            
            # Keyword score
            keyword_score = self._calculate_keyword_score(result, query)
            
            # Metadata score
            metadata_score = self._calculate_metadata_score(result, query)
            
            # Ensemble score (weighted average)
            ensemble_score = (
                semantic_score * self.config.semantic_weight +
                keyword_score * self.config.keyword_weight +
                metadata_score * (1 - self.config.semantic_weight - self.config.keyword_weight)
            )
            
            scored_results.append((result, ensemble_score))
        
        return scored_results
    
    def _calculate_semantic_score(self, result: Document, query: str) -> float:
        """Calculate semantic similarity score"""
        # Simple word overlap for now
        query_words = set(query.lower().split())
        result_words = set(result.page_content.lower().split())
        
        overlap = len(query_words.intersection(result_words))
        return overlap / max(len(query_words), 1)
    
    def _calculate_keyword_score(self, result: Document, query: str) -> float:
        """Calculate keyword-based score"""
        query_words = set(query.lower().split())
        result_words = set(result.page_content.lower().split())
        
        # Weight financial terms higher
        financial_terms = {"loan", "grant", "scholarship", "interest", "rate", "amount", "cost"}
        financial_overlap = len(query_words.intersection(result_words).intersection(financial_terms))
        
        return financial_overlap / max(len(query_words), 1)
    
    def _calculate_metadata_score(self, result: Document, query: str) -> float:
        """Calculate metadata-based score"""
        metadata = result.metadata
        score = 0.0
        
        # Boost for hierarchical chunks
        if metadata.get("chunk_type") == "hierarchical":
            score += 0.3
        
        # Boost for key sentences
        if metadata.get("key_sentence"):
            score += 0.4
        
        # Boost for financial documents
        if metadata.get("document_type") in ["financial_aid", "loan_information"]:
            score += 0.2
        
        return min(score, 1.0)
    
    def _deduplicate_results(self, results: List[Document]) -> List[Document]:
        """Remove duplicate results"""
        seen_contents = set()
        unique_results = []
        
        for result in results:
            content_hash = hash(result.page_content)
            if content_hash not in seen_contents:
                seen_contents.add(content_hash)
                unique_results.append(result)
        
        return unique_results
    
    def _rerank_results(self, results: List[Document], query: str) -> List[Document]:
        """Rerank results using multiple criteria"""
        if not results:
            return results
        
        scored_results = []
        for result in results:
            score = self._calculate_rerank_score(result, query)
            scored_results.append((result, score))
        
        # Sort by score
        scored_results.sort(key=lambda x: x[1], reverse=True)
        
        return [result for result, score in scored_results]

# Factory function
def create_advanced_hybrid_retriever(config: Optional[RetrievalConfig] = None) -> AdvancedHybridRetriever:
    """Create an advanced hybrid retriever"""
    if config is None:
        config = RetrievalConfig()
    return AdvancedHybridRetriever(config) 