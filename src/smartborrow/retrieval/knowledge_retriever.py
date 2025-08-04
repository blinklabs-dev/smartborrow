"""
Advanced Knowledge Retriever using Structured Knowledge and Numerical Data
"""

import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re

logger = logging.getLogger(__name__)

class KnowledgeRetriever:
    """Advanced knowledge retriever using structured knowledge and numerical context"""
    
    def __init__(self, processed_data_path: str = "data/processed") -> None:
        self.processed_data_path = Path(processed_data_path)
        self.structured_knowledge = {}
        self.numerical_data = []
        self.concept_embeddings = {}
        self.tfidf_vectorizer = None
        self.concept_vectors = None
        
        self._load_structured_knowledge()
        self._load_numerical_data()
        self._build_concept_embeddings()
    
    def _load_structured_knowledge(self) -> None:
        """Load structured knowledge from processed data"""
        try:
            knowledge_path = self.processed_data_path / "structured_knowledge.json"
            with open(knowledge_path, 'r') as f:
                self.structured_knowledge = json.load(f)
            logger.info(f"Loaded structured knowledge with {len(self.structured_knowledge)} concepts")
        except Exception as e:
            logger.error(f"Error loading structured knowledge: {e}")
            self.structured_knowledge = {}
    
    def _load_numerical_data(self) -> None:
        """Load numerical data for context enhancement"""
        try:
            numerical_path = self.processed_data_path / "numerical_data.json"
            with open(numerical_path, 'r') as f:
                self.numerical_data = json.load(f)
            logger.info(f"Loaded {len(self.numerical_data)} numerical data points")
        except Exception as e:
            logger.error(f"Error loading numerical data: {e}")
            self.numerical_data = []
    
    def _build_concept_embeddings(self) -> None:
        """Build TF-IDF embeddings for concept matching"""
        try:
            # Prepare concept texts for vectorization
            concept_texts = []
            concept_names = []
            
            for concept_name, concept_data in self.structured_knowledge.items():
                # Combine definition, requirements, and procedures
                text_parts = []
                if concept_data.get('definition'):
                    text_parts.append(concept_data['definition'])
                if concept_data.get('requirements'):
                    text_parts.extend(concept_data['requirements'])
                if concept_data.get('procedures'):
                    text_parts.extend(concept_data['procedures'])
                
                concept_text = " ".join(text_parts)
                if concept_text.strip():
                    concept_texts.append(concept_text)
                    concept_names.append(concept_name)
            
            # Build TF-IDF vectors
            self.tfidf_vectorizer = TfidfVectorizer(
                max_features=1000,
                stop_words='english',
                ngram_range=(1, 2)
            )
            self.concept_vectors = self.tfidf_vectorizer.fit_transform(concept_texts)
            self.concept_names = concept_names
            
            logger.info(f"Built concept embeddings for {len(concept_names)} concepts")
        except Exception as e:
            logger.error(f"Error building concept embeddings: {e}")
    
    def extract_numerical_context(self, query: str) -> List[Dict[str, Any]]:
        """Extract numerical context relevant to the query"""
        relevant_numerical = []
        
        # Extract numbers and amounts from query
        query_numbers = re.findall(r'\$[\d,]+|\d+%|\d+\.\d+', query)
        
        for numerical_item in self.numerical_data:
            relevance_score = 0
            
            # Check if numerical value matches query numbers
            for query_num in query_numbers:
                if query_num in numerical_item['value']:
                    relevance_score += 2.0
            
            # Check context similarity
            if numerical_item.get('context'):
                context_words = set(numerical_item['context'].lower().split())
                query_words = set(query.lower().split())
                overlap = len(context_words.intersection(query_words))
                relevance_score += overlap * 0.1
            
            # Check category relevance
            if numerical_item.get('category'):
                category = numerical_item['category'].lower()
                if any(word in category for word in query.lower().split()):
                    relevance_score += 1.0
            
            if relevance_score > 0:
                relevant_numerical.append({
                    **numerical_item,
                    'relevance_score': relevance_score
                })
        
        # Sort by relevance and return top matches
        relevant_numerical.sort(key=lambda x: x['relevance_score'], reverse=True)
        return relevant_numerical[:10]
    
    def find_related_concepts(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Find related concepts using semantic similarity"""
        if not self.tfidf_vectorizer or self.concept_vectors is None:
            return []
        
        try:
            # Vectorize the query
            query_vector = self.tfidf_vectorizer.transform([query])
            
            # Calculate similarities
            similarities = cosine_similarity(query_vector, self.concept_vectors).flatten()
            # Convert to list to avoid numpy array issues
            similarities = similarities.tolist()
            
            # Get top matches
            top_indices = np.argsort(similarities)[::-1][:top_k]
            # Convert to list to avoid numpy array issues
            top_indices = top_indices.tolist()
            
            related_concepts = []
            for idx in top_indices:
                if similarities[idx] > 0.1:  # Minimum similarity threshold
                    concept_name = self.concept_names[idx]
                    concept_data = self.structured_knowledge.get(concept_name, {})
                    
                    related_concepts.append({
                        'concept': concept_name,
                        'similarity': similarities[idx],
                        'definition': concept_data.get('definition', ''),
                        'requirements': concept_data.get('requirements', []),
                        'procedures': concept_data.get('procedures', []),
                        'numerical_data': concept_data.get('numerical_data', [])
                    })
            
            return related_concepts
        except Exception as e:
            logger.error(f"Error finding related concepts: {e}")
            return []
    
    def cross_document_linking(self, query: str) -> List[Dict[str, Any]]:
        """Perform cross-document knowledge linking"""
        cross_links = []
        
        # Find related concepts
        related_concepts = self.find_related_concepts(query)
        
        for concept in related_concepts:
            # Find numerical data related to this concept
            concept_numerical = []
            for numerical_item in self.numerical_data:
                if numerical_item.get('context'):
                    context_lower = numerical_item['context'].lower()
                    concept_lower = concept['concept'].lower()
                    
                    # Check if numerical data mentions the concept
                    if concept_lower in context_lower:
                        concept_numerical.append(numerical_item)
            
            if concept_numerical:
                cross_links.append({
                    'concept': concept['concept'],
                    'similarity': concept['similarity'],
                    'numerical_data': concept_numerical[:5],  # Top 5 numerical items
                    'definition': concept['definition'],
                    'requirements': concept['requirements'],
                    'procedures': concept['procedures']
                })
        
        return cross_links
    
    def retrieve_knowledge(self, query: str, top_k: int = 10) -> Dict[str, Any]:
        """Main knowledge retrieval method"""
        try:
            # Extract numerical context
            numerical_context = self.extract_numerical_context(query)
            
            # Find related concepts
            related_concepts = self.find_related_concepts(query, top_k=5)
            
            # Perform cross-document linking
            cross_links = self.cross_document_linking(query)
            
            # Combine and rank results
            results = {
                'query': query,
                'numerical_context': numerical_context,
                'related_concepts': related_concepts,
                'cross_document_links': cross_links,
                'total_results': len(numerical_context) + len(related_concepts) + len(cross_links)
            }
            
            logger.info(f"Knowledge retrieval completed for query: {query}")
            return results
            
        except Exception as e:
            logger.error(f"Error in knowledge retrieval: {e}")
            return {
                'query': query,
                'numerical_context': [],
                'related_concepts': [],
                'cross_document_links': [],
                'total_results': 0,
                'error': str(e)
            }
    
    def get_concept_details(self, concept_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific concept"""
        if concept_name in self.structured_knowledge:
            concept_data = self.structured_knowledge[concept_name]
            
            # Find related numerical data
            related_numerical = []
            for numerical_item in self.numerical_data:
                if numerical_item.get('context'):
                    context_lower = numerical_item['context'].lower()
                    concept_lower = concept_name.lower()
                    if concept_lower in context_lower:
                        related_numerical.append(numerical_item)
            
            return {
                'concept': concept_name,
                'definition': concept_data.get('definition', ''),
                'requirements': concept_data.get('requirements', []),
                'procedures': concept_data.get('procedures', []),
                'related_numerical': related_numerical[:10],
                'related_concepts': concept_data.get('related_concepts', [])
            }
        
        return None
    
    def search_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Search for concepts by category"""
        matching_concepts = []
        
        for concept_name, concept_data in self.structured_knowledge.items():
            # Check if category appears in concept data
            concept_text = f"{concept_name} {concept_data.get('definition', '')}"
            if category.lower() in concept_text.lower():
                matching_concepts.append({
                    'concept': concept_name,
                    'definition': concept_data.get('definition', ''),
                    'requirements': concept_data.get('requirements', []),
                    'procedures': concept_data.get('procedures', [])
                })
        
        return matching_concepts
    
    def get_retrieval_stats(self) -> Dict[str, Any]:
        """Get retrieval statistics"""
        return {
            'concepts': len(self.structured_knowledge),
            'numerical_data': len(self.numerical_data),
            'concept_embeddings': len(self.concept_embeddings) if self.concept_embeddings else 0
        } 