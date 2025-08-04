"""
Hybrid Retriever combining Knowledge-based, Numerical, and Semantic Search
"""

import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import numpy as np
from dataclasses import dataclass
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .knowledge_retriever import KnowledgeRetriever
from .numerical_retriever import NumericalRetriever

logger = logging.getLogger(__name__)

@dataclass
class HybridResult:
    """Represents a hybrid retrieval result"""
    query: str
    knowledge_results: Dict[str, Any]
    numerical_results: Dict[str, Any]
    complaint_results: Dict[str, Any]
    faq_results: Dict[str, Any]
    combined_score: float
    retrieval_method: str

class HybridRetriever:
    """Hybrid retriever combining multiple retrieval methods"""
    
    def __init__(self, processed_data_path: str = "data/processed") -> None:
        self.processed_data_path = Path(processed_data_path)
        
        # Initialize component retrievers
        self.knowledge_retriever = KnowledgeRetriever(processed_data_path)
        self.numerical_retriever = NumericalRetriever(processed_data_path)
        
        # Load additional data
        self.complaint_categories = {}
        self.complaint_faqs = []
        self.expanded_categories = {}
        
        self._load_complaint_data()
        self._load_faq_data()
        self._load_expanded_categories()
        self._build_complaint_embeddings()
    
    def _load_complaint_data(self) -> None:
        """Load complaint categories data"""
        try:
            complaint_path = self.processed_data_path / "complaint_categories.json"
            with open(complaint_path, 'r') as f:
                self.complaint_categories = json.load(f)
            logger.info(f"Loaded complaint categories with {len(self.complaint_categories)} categories")
        except Exception as e:
            logger.error(f"Error loading complaint categories: {e}")
            self.complaint_categories = {}
    
    def _load_faq_data(self) -> None:
        """Load FAQ data"""
        try:
            faq_path = self.processed_data_path / "complaint_faqs.json"
            with open(faq_path, 'r') as f:
                self.complaint_faqs = json.load(f)
            logger.info(f"Loaded {len(self.complaint_faqs)} FAQ entries")
        except Exception as e:
            logger.error(f"Error loading FAQ data: {e}")
            self.complaint_faqs = []
    
    def _load_expanded_categories(self) -> None:
        """Load expanded categories data"""
        try:
            expanded_path = self.processed_data_path / "expanded_categories.json"
            with open(expanded_path, 'r') as f:
                expanded_data = json.load(f)
            
            # Convert list to dictionary using original_category as key
            self.expanded_categories = {}
            for item in expanded_data:
                category_name = item.get('original_category', 'unknown')
                self.expanded_categories[category_name] = {
                    'keywords': item.get('expanded_keywords', []),
                    'similar_scenarios': item.get('similar_scenarios', []),
                    'original_data': item.get('original_data', {})
                }
            
            logger.info(f"Loaded expanded categories with {len(self.expanded_categories)} categories")
        except Exception as e:
            logger.error(f"Error loading expanded categories: {e}")
            self.expanded_categories = {}
    
    def _build_complaint_embeddings(self) -> None:
        """Build embeddings for complaint categories"""
        try:
            # Prepare complaint texts for vectorization
            complaint_texts = []
            complaint_names = []
            
            for category_name, category_data in self.complaint_categories.items():
                # Combine keywords and common issues
                text_parts = []
                if category_data.get('common_keywords'):
                    text_parts.extend(category_data['common_keywords'])
                if category_data.get('common_issues'):
                    text_parts.extend(category_data['common_issues'])
                
                complaint_text = " ".join(text_parts)
                if complaint_text.strip():
                    complaint_texts.append(complaint_text)
                    complaint_names.append(category_name)
            
            # Build TF-IDF vectors
            self.complaint_vectorizer = TfidfVectorizer(
                max_features=500,
                stop_words='english',
                ngram_range=(1, 2)
            )
            self.complaint_vectors = self.complaint_vectorizer.fit_transform(complaint_texts)
            self.complaint_names = complaint_names
            
            logger.info(f"Built complaint embeddings for {len(complaint_names)} categories")
        except Exception as e:
            logger.error(f"Error building complaint embeddings: {e}")
            self.complaint_vectorizer = None
            self.complaint_vectors = None
    
    def classify_query_intent(self, query: str) -> Dict[str, Any]:
        """Classify query intent using complaint categories"""
        if not self.complaint_vectorizer or self.complaint_vectors is None:
            return {'intent': 'general', 'confidence': 0.5}
        
        try:
            # Vectorize the query
            query_vector = self.complaint_vectorizer.transform([query])
            
            # Calculate similarities
            similarities = cosine_similarity(query_vector, self.complaint_vectors).flatten()
            # Convert to list to avoid numpy array issues
            similarities = similarities.tolist()
            
            # Get top matches
            top_indices = np.argsort(similarities)[::-1][:3]
            # Convert to list to avoid numpy array issues
            top_indices = top_indices.tolist()
            
            intents = []
            for idx in top_indices:
                if similarities[idx] > 0.1:  # Minimum similarity threshold
                    category_name = self.complaint_names[idx]
                    category_data = self.complaint_categories.get(category_name, {})
                    
                    intents.append({
                        'category': category_name,
                        'confidence': similarities[idx],
                        'complaint_count': category_data.get('complaint_count', 0),
                        'common_keywords': category_data.get('common_keywords', []),
                        'common_issues': category_data.get('common_issues', [])
                    })
            
            if intents:
                primary_intent = intents[0]
                return {
                    'intent': primary_intent['category'],
                    'confidence': primary_intent['confidence'],
                    'all_intents': intents
                }
            else:
                return {'intent': 'general', 'confidence': 0.5}
                
        except Exception as e:
            logger.error(f"Error classifying query intent: {e}")
            return {'intent': 'general', 'confidence': 0.5}
    
    def search_faqs(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search FAQ entries"""
        if not self.complaint_faqs:
            return []
        
        try:
            # Simple keyword matching for FAQ search
            query_lower = query.lower()
            query_words = set(query_lower.split())
            
            faq_matches = []
            for faq in self.complaint_faqs:
                relevance_score = 0
                
                # Check question relevance
                if faq.get('question'):
                    question_lower = faq['question'].lower()
                    question_words = set(question_lower.split())
                    overlap = len(query_words.intersection(question_words))
                    relevance_score += overlap * 0.5
                
                # Check answer relevance
                if faq.get('answer'):
                    answer_lower = faq['answer'].lower()
                    answer_words = set(answer_lower.split())
                    overlap = len(query_words.intersection(answer_words))
                    relevance_score += overlap * 0.3
                
                # Check category relevance
                if faq.get('category'):
                    category_lower = faq['category'].lower()
                    if any(word in category_lower for word in query_words):
                        relevance_score += 1.0
                
                if relevance_score > 0:
                    faq_matches.append({
                        **faq,
                        'relevance_score': relevance_score
                    })
            
            # Sort by relevance and return top matches
            faq_matches.sort(key=lambda x: x['relevance_score'], reverse=True)
            return faq_matches[:top_k]
            
        except Exception as e:
            logger.error(f"Error searching FAQs: {e}")
            return []
    
    def expand_query_with_categories(self, query: str) -> List[str]:
        """Expand query using expanded categories"""
        expanded_queries = [query]
        query_lower = query.lower()
        
        for category_name, category_data in self.expanded_categories.items():
            # Check if category is relevant to query
            category_text = f"{category_name} {' '.join(category_data.get('keywords', []))}"
            category_lower = category_text.lower()
            
            query_words = set(query_lower.split())
            category_words = set(category_lower.split())
            
            overlap = len(query_words.intersection(category_words))
            if overlap > 0:
                # Add category-specific terms to query
                expanded_query = f"{query} {' '.join(category_data.get('keywords', [])[:3])}"
                expanded_queries.append(expanded_query)
        
        return expanded_queries
    
    def retrieve_hybrid(self, query: str, use_faq: bool = True, use_complaints: bool = True) -> HybridResult:
        """Main hybrid retrieval method"""
        try:
            # Step 1: Classify query intent
            intent_classification = self.classify_query_intent(query)
            
            # Step 2: Expand query with categories
            expanded_queries = self.expand_query_with_categories(query)
            
            # Step 3: Knowledge-based retrieval
            knowledge_results = self.knowledge_retriever.retrieve_knowledge(query)
            
            # Step 4: Numerical retrieval
            numerical_results = self.numerical_retriever.retrieve_numerical_data(query, "hybrid")
            
            # Step 5: Complaint-based retrieval
            complaint_results = {}
            if use_complaints:
                complaint_results = {
                    'intent_classification': intent_classification,
                    'relevant_categories': intent_classification.get('all_intents', []),
                    'query_expansion': expanded_queries
                }
            
            # Step 6: FAQ retrieval
            faq_results = {}
            if use_faq:
                faq_matches = self.search_faqs(query)
                faq_results = {
                    'matches': faq_matches,
                    'total_matches': len(faq_matches)
                }
            
            # Step 7: Calculate combined score
            combined_score = self._calculate_combined_score(
                knowledge_results,
                numerical_results,
                complaint_results,
                faq_results
            )
            
            # Step 8: Determine retrieval method
            retrieval_method = self._determine_retrieval_method(
                knowledge_results,
                numerical_results,
                complaint_results,
                faq_results
            )
            
            result = HybridResult(
                query=query,
                knowledge_results=knowledge_results,
                numerical_results=numerical_results,
                complaint_results=complaint_results,
                faq_results=faq_results,
                combined_score=combined_score,
                retrieval_method=retrieval_method
            )
            
            logger.info(f"Hybrid retrieval completed for query: {query}")
            return result
            
        except Exception as e:
            logger.error(f"Error in hybrid retrieval: {e}")
            return HybridResult(
                query=query,
                knowledge_results={},
                numerical_results={},
                complaint_results={},
                faq_results={},
                combined_score=0.0,
                retrieval_method="error"
            )
    
    def _calculate_combined_score(self, knowledge_results: Dict, numerical_results: Dict, 
                                complaint_results: Dict, faq_results: Dict) -> float:
        """Calculate combined relevance score"""
        scores = []
        
        # Knowledge score
        if knowledge_results.get('total_results', 0) > 0:
            knowledge_score = min(knowledge_results['total_results'] / 10.0, 1.0)
            scores.append(knowledge_score * 0.4)  # 40% weight
        
        # Numerical score
        if numerical_results.get('total_matches', 0) > 0:
            numerical_score = min(numerical_results['total_matches'] / 20.0, 1.0)
            scores.append(numerical_score * 0.3)  # 30% weight
        
        # Complaint score
        if complaint_results.get('intent_classification', {}).get('confidence', 0) > 0:
            complaint_score = complaint_results['intent_classification']['confidence']
            scores.append(complaint_score * 0.2)  # 20% weight
        
        # FAQ score
        if faq_results.get('total_matches', 0) > 0:
            faq_score = min(faq_results['total_matches'] / 5.0, 1.0)
            scores.append(faq_score * 0.1)  # 10% weight
        
        return sum(scores) if scores else 0.0
    
    def _determine_retrieval_method(self, knowledge_results: Dict, numerical_results: Dict,
                                  complaint_results: Dict, faq_results: Dict) -> str:
        """Determine the primary retrieval method used"""
        method_scores = {
            'knowledge': knowledge_results.get('total_results', 0),
            'numerical': numerical_results.get('total_matches', 0),
            'complaint': complaint_results.get('intent_classification', {}).get('confidence', 0),
            'faq': faq_results.get('total_matches', 0)
        }
        
        # Debug: check if method_scores is a dictionary
        if not isinstance(method_scores, dict):
            logger.error(f"method_scores is not a dict: {type(method_scores)}")
            return "hybrid"
        
        # Find the method with highest score
        if method_scores:
            best_method = max(method_scores.items(), key=lambda x: x[1])
        else:
            return "hybrid"
        
        if best_method[1] > 0:
            return best_method[0]
        else:
            return "hybrid"
    
    def get_retrieval_summary(self, query: str) -> Dict[str, Any]:
        """Get a comprehensive retrieval summary"""
        result = self.retrieve_hybrid(query)
        
        summary = {
            'query': query,
            'combined_score': result.combined_score,
            'retrieval_method': result.retrieval_method,
            'knowledge_results': {
                'total_concepts': len(result.knowledge_results.get('related_concepts', [])),
                'numerical_context': len(result.knowledge_results.get('numerical_context', [])),
                'cross_links': len(result.knowledge_results.get('cross_document_links', []))
            },
            'numerical_results': {
                'exact_matches': len(result.numerical_results.get('exact_matches', [])),
                'fuzzy_matches': len(result.numerical_results.get('fuzzy_matches', [])),
                'total_matches': result.numerical_results.get('total_matches', 0)
            },
            'complaint_results': {
                'intent': result.complaint_results.get('intent_classification', {}).get('intent', 'general'),
                'confidence': result.complaint_results.get('intent_classification', {}).get('confidence', 0),
                'categories': len(result.complaint_results.get('relevant_categories', []))
            },
            'faq_results': {
                'total_matches': result.faq_results.get('total_matches', 0),
                'top_matches': result.faq_results.get('matches', [])[:3]
            }
        }
        
        return summary
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about the hybrid retrieval system"""
        return {
            'knowledge_concepts': len(self.knowledge_retriever.structured_knowledge),
            'numerical_data_points': len(self.numerical_retriever.numerical_data),
            'complaint_categories': len(self.complaint_categories),
            'faq_entries': len(self.complaint_faqs),
            'expanded_categories': len(self.expanded_categories)
        }
    
    def get_retrieval_stats(self) -> Dict[str, Any]:
        """Get retrieval statistics"""
        return {
            'knowledge_concepts': len(self.knowledge_retriever.structured_knowledge),
            'numerical_data_points': len(self.numerical_retriever.numerical_data),
            'complaint_categories': len(self.complaint_categories),
            'faq_entries': len(self.complaint_faqs),
            'expanded_categories': len(self.expanded_categories)
        }