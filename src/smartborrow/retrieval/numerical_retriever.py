"""
Specialized Numerical Retriever for Exact Matching of Rates, Amounts, Dates, and Deadlines
"""

import json
import logging
import re
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from datetime import datetime, date
import numpy as np
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class NumericalMatch:
    """Represents a numerical match with context"""
    value: str
    unit: str
    category: str
    context: str
    confidence: float
    exact_match: bool
    query_terms: List[str]
    document_reference: Optional[str] = None

class NumericalRetriever:
    """Specialized retriever for numerical data points with exact matching"""
    
    def __init__(self, processed_data_path: str = "data/processed") -> None:
        self.processed_data_path = Path(processed_data_path)
        self.numerical_data = []
        self.value_index = {}
        self.category_index = {}
        self.unit_index = {}
        
        self._load_numerical_data()
        self._build_indices()
    
    def _load_numerical_data(self) -> None:
        """Load numerical data from processed files"""
        try:
            numerical_path = self.processed_data_path / "numerical_data.json"
            with open(numerical_path, 'r') as f:
                self.numerical_data = json.load(f)
            logger.info(f"Loaded {len(self.numerical_data)} numerical data points")
        except Exception as e:
            logger.error(f"Error loading numerical data: {e}")
            self.numerical_data = []
    
    def _build_indices(self) -> None:
        """Build search indices for fast retrieval"""
        try:
            # Build value index
            for item in self.numerical_data:
                value = item.get('value', '').lower()
                if value:
                    if value not in self.value_index:
                        self.value_index[value] = []
                    self.value_index[value].append(item)
            
            # Build category index
            for item in self.numerical_data:
                category = item.get('category', '').lower()
                if category:
                    if category not in self.category_index:
                        self.category_index[category] = []
                    self.category_index[category].append(item)
            
            # Build unit index
            for item in self.numerical_data:
                unit = item.get('unit', '').lower()
                if unit:
                    if unit not in self.unit_index:
                        self.unit_index[unit] = []
                    self.unit_index[unit].append(item)
            
            logger.info(f"Built indices: {len(self.value_index)} values, {len(self.category_index)} categories, {len(self.unit_index)} units")
        except Exception as e:
            logger.error(f"Error building indices: {e}")
    
    def extract_numerical_entities(self, query: str) -> List[Dict[str, Any]]:
        """Extract numerical entities from query"""
        entities = []
        
        # Extract dollar amounts
        dollar_pattern = r'\$[\d,]+(?:\.\d{2})?'
        dollar_matches = re.findall(dollar_pattern, query)
        for match in dollar_matches:
            entities.append({
                'type': 'dollar_amount',
                'value': match,
                'confidence': 1.0
            })
        
        # Extract percentages
        percent_pattern = r'\d+(?:\.\d+)?%'
        percent_matches = re.findall(percent_pattern, query)
        for match in percent_matches:
            entities.append({
                'type': 'percentage',
                'value': match,
                'confidence': 1.0
            })
        
        # Extract plain numbers
        number_pattern = r'\b\d+(?:,\d{3})*(?:\.\d+)?\b'
        number_matches = re.findall(number_pattern, query)
        for match in number_matches:
            entities.append({
                'type': 'number',
                'value': match,
                'confidence': 0.8
            })
        
        # Extract years
        year_pattern = r'\b(?:19|20)\d{2}\b'
        year_matches = re.findall(year_pattern, query)
        for match in year_matches:
            entities.append({
                'type': 'year',
                'value': match,
                'confidence': 1.0
            })
        
        return entities
    
    def exact_value_match(self, query: str) -> List[NumericalMatch]:
        """Find exact value matches"""
        matches = []
        query_lower = query.lower()
        
        # Extract numerical entities from query
        entities = self.extract_numerical_entities(query)
        
        for entity in entities:
            entity_value = entity['value'].lower()
            
            # Look for exact matches in value index
            if entity_value in self.value_index:
                for item in self.value_index[entity_value]:
                    match = NumericalMatch(
                        value=item['value'],
                        unit=item.get('unit', ''),
                        category=item.get('category', ''),
                        context=item.get('context', ''),
                        confidence=entity['confidence'],
                        exact_match=True,
                        query_terms=[entity_value]
                    )
                    matches.append(match)
        
        return matches
    
    def fuzzy_value_match(self, query: str, threshold: float = 0.8) -> List[NumericalMatch]:
        """Find fuzzy value matches"""
        matches = []
        query_lower = query.lower()
        
        # Extract numerical entities from query
        entities = self.extract_numerical_entities(query)
        
        for entity in entities:
            entity_value = entity['value'].lower()
            
            # Look for similar values
            for value, items in self.value_index.items():
                # Simple similarity check
                if self._calculate_similarity(entity_value, value) >= threshold:
                    for item in items:
                        match = NumericalMatch(
                            value=item['value'],
                            unit=item.get('unit', ''),
                            category=item.get('category', ''),
                            context=item.get('context', ''),
                            confidence=entity['confidence'] * 0.8,
                            exact_match=False,
                            query_terms=[entity_value]
                        )
                        matches.append(match)
        
        return matches
    
    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """Calculate string similarity"""
        if str1 == str2:
            return 1.0
        
        # Remove common formatting
        str1_clean = re.sub(r'[^\w]', '', str1.lower())
        str2_clean = re.sub(r'[^\w]', '', str2.lower())
        
        if str1_clean == str2_clean:
            return 0.9
        
        # Simple character overlap
        set1 = set(str1_clean)
        set2 = set(str2_clean)
        
        if len(set1) == 0 or len(set2) == 0:
            return 0.0
        
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        return intersection / union if union > 0 else 0.0
    
    def category_based_search(self, query: str) -> List[NumericalMatch]:
        """Search based on category matching"""
        matches = []
        query_lower = query.lower()
        
        # Extract potential categories from query
        query_words = set(query_lower.split())
        
        for category, items in self.category_index.items():
            category_words = set(category.lower().split())
            
            # Check for category overlap
            overlap = len(query_words.intersection(category_words))
            if overlap > 0:
                for item in items:
                    match = NumericalMatch(
                        value=item['value'],
                        unit=item.get('unit', ''),
                        category=item.get('category', ''),
                        context=item.get('context', ''),
                        confidence=overlap / len(query_words),
                        exact_match=False,
                        query_terms=list(query_words)
                    )
                    matches.append(match)
        
        return matches
    
    def context_aware_search(self, query: str) -> List[NumericalMatch]:
        """Search using context awareness"""
        matches = []
        query_lower = query.lower()
        query_words = set(query_lower.split())
        
        for item in self.numerical_data:
            if not item.get('context'):
                continue
            
            context_lower = item['context'].lower()
            context_words = set(context_lower.split())
            
            # Calculate context overlap
            overlap = len(query_words.intersection(context_words))
            if overlap > 0:
                # Calculate relevance score
                relevance_score = overlap / len(query_words)
                
                if relevance_score > 0.1:  # Minimum relevance threshold
                    match = NumericalMatch(
                        value=item['value'],
                        unit=item.get('unit', ''),
                        category=item.get('category', ''),
                        context=item.get('context', ''),
                        confidence=relevance_score,
                        exact_match=False,
                        query_terms=list(query_words)
                    )
                    matches.append(match)
        
        return matches
    
    def retrieve_numerical_data(self, query: str, search_type: str = "hybrid") -> Dict[str, Any]:
        """Main numerical retrieval method"""
        try:
            results = {
                'query': query,
                'exact_matches': [],
                'fuzzy_matches': [],
                'category_matches': [],
                'context_matches': [],
                'total_matches': 0
            }
            
            if search_type in ["exact", "hybrid"]:
                results['exact_matches'] = self.exact_value_match(query)
            
            if search_type in ["fuzzy", "hybrid"]:
                results['fuzzy_matches'] = self.fuzzy_value_match(query)
            
            if search_type in ["category", "hybrid"]:
                results['category_matches'] = self.category_based_search(query)
            
            if search_type in ["context", "hybrid"]:
                results['context_matches'] = self.context_aware_search(query)
            
            # Calculate total matches
            results['total_matches'] = (
                len(results['exact_matches']) +
                len(results['fuzzy_matches']) +
                len(results['category_matches']) +
                len(results['context_matches'])
            )
            
            # Sort all matches by confidence
            all_matches = (
                results['exact_matches'] +
                results['fuzzy_matches'] +
                results['category_matches'] +
                results['context_matches']
            )
            all_matches.sort(key=lambda x: x.confidence, reverse=True)
            
            results['all_matches'] = all_matches[:20]  # Top 20 matches
            
            logger.info(f"Numerical retrieval completed: {results['total_matches']} matches found")
            return results
            
        except Exception as e:
            logger.error(f"Error in numerical retrieval: {e}")
            return {
                'query': query,
                'exact_matches': [],
                'fuzzy_matches': [],
                'category_matches': [],
                'context_matches': [],
                'total_matches': 0,
                'error': str(e)
            }
    
    def get_numerical_summary(self, query: str) -> Dict[str, Any]:
        """Get a summary of numerical data for a query"""
        results = self.retrieve_numerical_data(query, "hybrid")
        
        # Group by category
        category_summary = {}
        for match in results['all_matches']:
            category = match.category
            if category not in category_summary:
                category_summary[category] = []
            category_summary[category].append({
                'value': match.value,
                'unit': match.unit,
                'confidence': match.confidence,
                'context': match.context[:100] + "..." if len(match.context) > 100 else match.context
            })
        
        # Find most common values
        value_counts = {}
        for match in results['all_matches']:
            value = match.value
            if value not in value_counts:
                value_counts[value] = 0
            value_counts[value] += 1
        
        most_common = sorted(value_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            'query': query,
            'total_matches': results['total_matches'],
            'category_summary': category_summary,
            'most_common_values': most_common,
            'exact_matches_count': len(results['exact_matches']),
            'fuzzy_matches_count': len(results['fuzzy_matches'])
        }
    
    def search_by_date_range(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """Search for numerical data within a date range"""
        # This would be implemented if we had date-specific numerical data
        # For now, return empty list
        return []
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about the numerical data"""
        if not self.numerical_data:
            return {}
        
        categories = {}
        units = {}
        values = {}
        
        for item in self.numerical_data:
            # Count categories
            category = item.get('category', 'unknown')
            categories[category] = categories.get(category, 0) + 1
            
            # Count units
            unit = item.get('unit', 'unknown')
            units[unit] = units.get(unit, 0) + 1
            
            # Count values
            value = item.get('value', 'unknown')
            values[value] = values.get(value, 0) + 1
        
        return {
            'total_items': len(self.numerical_data),
            'unique_categories': len(categories),
            'unique_units': len(units),
            'unique_values': len(values),
            'top_categories': sorted(categories.items(), key=lambda x: x[1], reverse=True)[:5],
            'top_units': sorted(units.items(), key=lambda x: x[1], reverse=True)[:5],
            'top_values': sorted(values.items(), key=lambda x: x[1], reverse=True)[:5]
        }
    
    def get_retrieval_stats(self) -> Dict[str, Any]:
        """Get retrieval statistics"""
        return {
            'total_items': len(self.numerical_data),
            'unique_categories': len(self.category_index),
            'unique_units': len(self.unit_index),
            'unique_values': len(self.value_index)
        }