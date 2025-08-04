"""
Advanced RAG Service using Hybrid Retrieval with A/B Testing Framework
"""

import json
import logging
import time
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime
import uuid

from .hybrid_retriever import HybridRetriever, HybridResult
# Import RAGService only when needed to avoid circular import
# Import EvaluationRunner only when needed to avoid circular import

logger = logging.getLogger(__name__)

@dataclass
class ABTestResult:
    """Represents an A/B test result"""
    test_id: str
    query: str
    method_a: str
    method_b: str
    result_a: Dict[str, Any]
    result_b: Dict[str, Any]
    winner: str
    confidence: float
    timestamp: str
    metadata: Dict[str, Any]

@dataclass
class PerformanceMetrics:
    """Represents performance metrics for retrieval methods"""
    method: str
    response_time: float
    relevance_score: float
    precision: float
    recall: float
    f1_score: float
    user_satisfaction: Optional[float] = None

class AdvancedRAGService:
    """Advanced RAG service with hybrid retrieval and A/B testing"""
    
    def __init__(self, processed_data_path: str = "data/processed") -> None:
        self.processed_data_path = Path(processed_data_path)
        
        # Initialize retrievers
        self.hybrid_retriever = HybridRetriever(processed_data_path)
        # Import RAGService only when needed to avoid circular import
        from ..rag.rag_service import RAGService
        self.standard_rag_service = RAGService(processed_data_path)
        
        # Initialize the standard RAG service
        if not self.standard_rag_service.initialize():
            logger.error("Failed to initialize standard RAG service")
        
        # A/B testing data
        self.ab_test_results = []
        self.performance_metrics = []
        
        # Load existing results
        self._load_ab_test_results()
        self._load_performance_metrics()
    
    def _load_ab_test_results(self) -> None:
        """Load existing A/B test results"""
        try:
            results_path = self.processed_data_path / "ab_test_results.json"
            if results_path.exists():
                with open(results_path, 'r') as f:
                    self.ab_test_results = json.load(f)
                logger.info(f"Loaded {len(self.ab_test_results)} A/B test results")
        except Exception as e:
            logger.error(f"Error loading A/B test results: {e}")
            self.ab_test_results = []
    
    def _load_performance_metrics(self) -> None:
        """Load existing performance metrics"""
        try:
            metrics_path = self.processed_data_path / "performance_metrics.json"
            if metrics_path.exists():
                with open(metrics_path, 'r') as f:
                    self.performance_metrics = json.load(f)
                logger.info(f"Loaded {len(self.performance_metrics)} performance metrics")
        except Exception as e:
            logger.error(f"Error loading performance metrics: {e}")
            self.performance_metrics = []
    
    def _save_ab_test_results(self) -> None:
        """Save A/B test results to file"""
        try:
            results_path = self.processed_data_path / "ab_test_results.json"
            with open(results_path, 'w') as f:
                json.dump(self.ab_test_results, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving A/B test results: {e}")
    
    def _save_performance_metrics(self) -> None:
        """Save performance metrics to file"""
        try:
            metrics_path = self.processed_data_path / "performance_metrics.json"
            with open(metrics_path, 'w') as f:
                json.dump(self.performance_metrics, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving performance metrics: {e}")
    
    def query_with_hybrid_retrieval(self, query: str, use_faq: bool = True, 
                                   use_complaints: bool = True) -> Dict[str, Any]:
        """Query using hybrid retrieval"""
        try:
            start_time = time.time()
            
            # Get hybrid retrieval results
            hybrid_result = self.hybrid_retriever.retrieve_hybrid(query, use_faq, use_complaints)
            
            # Get standard RAG results for comparison
            standard_result = self.standard_rag_service.query(query)
            
            response_time = time.time() - start_time
            
            # Combine results
            combined_result = {
                'query': query,
                'hybrid_retrieval': {
                    'knowledge_results': hybrid_result.knowledge_results,
                    'numerical_results': hybrid_result.numerical_results,
                    'complaint_results': hybrid_result.complaint_results,
                    'faq_results': hybrid_result.faq_results,
                    'combined_score': hybrid_result.combined_score,
                    'retrieval_method': hybrid_result.retrieval_method
                },
                'standard_rag': standard_result,
                'response_time': response_time,
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"Hybrid retrieval completed in {response_time:.2f}s")
            return combined_result
            
        except Exception as e:
            logger.error(f"Error in hybrid retrieval query: {e}")
            return {
                'query': query,
                'error': str(e),
                'response_time': 0.0,
                'timestamp': datetime.now().isoformat()
            }
    
    def run_ab_test(self, query: str, method_a: str = "hybrid", 
                   method_b: str = "standard") -> ABTestResult:
        """Run A/B test between two retrieval methods"""
        try:
            test_id = str(uuid.uuid4())
            start_time = time.time()
            
            # Run method A
            if method_a == "hybrid":
                result_a = self.hybrid_retriever.retrieve_hybrid(query)
                result_a_dict = asdict(result_a)
            else:
                result_a_dict = self.standard_rag_service.query(query)
            
            # Run method B
            if method_b == "hybrid":
                result_b = self.hybrid_retriever.retrieve_hybrid(query)
                result_b_dict = asdict(result_b)
            else:
                result_b_dict = self.standard_rag_service.query(query)
            
            response_time = time.time() - start_time
            
            # Determine winner based on combined score
            score_a = result_a_dict.get('combined_score', 0) if method_a == "hybrid" else 0.5
            score_b = result_b_dict.get('combined_score', 0) if method_b == "hybrid" else 0.5
            
            winner = method_a if score_a > score_b else method_b
            confidence = abs(score_a - score_b)
            
            # Create A/B test result
            ab_result = ABTestResult(
                test_id=test_id,
                query=query,
                method_a=method_a,
                method_b=method_b,
                result_a=result_a_dict,
                result_b=result_b_dict,
                winner=winner,
                confidence=confidence,
                timestamp=datetime.now().isoformat(),
                metadata={
                    'response_time': response_time,
                    'score_a': score_a,
                    'score_b': score_b
                }
            )
            
            # Save result
            self.ab_test_results.append(asdict(ab_result))
            self._save_ab_test_results()
            
            logger.info(f"A/B test completed: {winner} won with confidence {confidence:.3f}")
            return ab_result
            
        except Exception as e:
            logger.error(f"Error in A/B test: {e}")
            return ABTestResult(
                test_id=str(uuid.uuid4()),
                query=query,
                method_a=method_a,
                method_b=method_b,
                result_a={},
                result_b={},
                winner="error",
                confidence=0.0,
                timestamp=datetime.now().isoformat(),
                metadata={'error': str(e)}
            )
    
    def evaluate_performance(self, test_queries: List[str]) -> Dict[str, Any]:
        """Evaluate performance across different retrieval methods"""
        try:
            evaluation_results = {
                'hybrid': {'queries': [], 'metrics': []},
                'standard': {'queries': [], 'metrics': []},
                'knowledge_only': {'queries': [], 'metrics': []},
                'numerical_only': {'queries': [], 'metrics': []}
            }
            
            for query in test_queries:
                # Test hybrid retrieval
                start_time = time.time()
                hybrid_result = self.hybrid_retriever.retrieve_hybrid(query)
                hybrid_time = time.time() - start_time
                
                evaluation_results['hybrid']['queries'].append(query)
                evaluation_results['hybrid']['metrics'].append({
                    'response_time': hybrid_time,
                    'combined_score': hybrid_result.combined_score,
                    'retrieval_method': hybrid_result.retrieval_method
                })
                
                # Test standard RAG
                start_time = time.time()
                standard_result = self.standard_rag_service.query(query)
                standard_time = time.time() - start_time
                
                evaluation_results['standard']['queries'].append(query)
                evaluation_results['standard']['metrics'].append({
                    'response_time': standard_time,
                    'confidence': standard_result.get('confidence', 'medium')
                })
                
                # Test knowledge-only retrieval
                start_time = time.time()
                knowledge_result = self.hybrid_retriever.knowledge_retriever.retrieve_knowledge(query)
                knowledge_time = time.time() - start_time
                
                evaluation_results['knowledge_only']['queries'].append(query)
                evaluation_results['knowledge_only']['metrics'].append({
                    'response_time': knowledge_time,
                    'total_results': knowledge_result.get('total_results', 0)
                })
                
                # Test numerical-only retrieval
                start_time = time.time()
                numerical_result = self.hybrid_retriever.numerical_retriever.retrieve_numerical_data(query)
                numerical_time = time.time() - start_time
                
                evaluation_results['numerical_only']['queries'].append(query)
                evaluation_results['numerical_only']['metrics'].append({
                    'response_time': numerical_time,
                    'total_matches': numerical_result.get('total_matches', 0)
                })
            
            # Calculate aggregate metrics
            for method, data in evaluation_results.items():
                if data['metrics']:
                    avg_response_time = sum(m['response_time'] for m in data['metrics']) / len(data['metrics'])
                    data['aggregate_metrics'] = {
                        'avg_response_time': avg_response_time,
                        'total_queries': len(data['queries'])
                    }
            
            logger.info(f"Performance evaluation completed for {len(test_queries)} queries")
            return evaluation_results
            
        except Exception as e:
            logger.error(f"Error in performance evaluation: {e}")
            return {'error': str(e)}
    
    def compare_retrieval_methods(self, query: str) -> Dict[str, Any]:
        """Compare different retrieval methods for a single query"""
        try:
            comparison = {
                'query': query,
                'methods': {},
                'recommendation': None
            }
            
            # Test hybrid retrieval
            start_time = time.time()
            hybrid_result = self.hybrid_retriever.retrieve_hybrid(query)
            hybrid_time = time.time() - start_time
            
            comparison['methods']['hybrid'] = {
                'response_time': hybrid_time,
                'combined_score': hybrid_result.combined_score,
                'retrieval_method': hybrid_result.retrieval_method,
                'knowledge_results': len(hybrid_result.knowledge_results.get('related_concepts', [])),
                'numerical_results': hybrid_result.numerical_results.get('total_matches', 0),
                'faq_results': hybrid_result.faq_results.get('total_matches', 0)
            }
            
            # Test standard RAG
            start_time = time.time()
            standard_result = self.standard_rag_service.query(query)
            standard_time = time.time() - start_time
            
            comparison['methods']['standard'] = {
                'response_time': standard_time,
                'confidence': standard_result.get('confidence', 'medium'),
                'sources_count': len(standard_result.get('sources', []))
            }
            
            # Test knowledge-only
            start_time = time.time()
            knowledge_result = self.hybrid_retriever.knowledge_retriever.retrieve_knowledge(query)
            knowledge_time = time.time() - start_time
            
            comparison['methods']['knowledge_only'] = {
                'response_time': knowledge_time,
                'total_results': knowledge_result.get('total_results', 0),
                'related_concepts': len(knowledge_result.get('related_concepts', []))
            }
            
            # Test numerical-only
            start_time = time.time()
            numerical_result = self.hybrid_retriever.numerical_retriever.retrieve_numerical_data(query)
            numerical_time = time.time() - start_time
            
            comparison['methods']['numerical_only'] = {
                'response_time': numerical_time,
                'total_matches': numerical_result.get('total_matches', 0),
                'exact_matches': len(numerical_result.get('exact_matches', []))
            }
            
            # Determine recommendation
            scores = {}
            for method, data in comparison['methods'].items():
                if method == 'hybrid':
                    scores[method] = data['combined_score']
                elif method == 'standard':
                    scores[method] = 0.5  # Default score for standard
                else:
                    # Calculate score based on results
                    if method == 'knowledge_only':
                        scores[method] = min(data['total_results'] / 10.0, 1.0)
                    elif method == 'numerical_only':
                        scores[method] = min(data['total_matches'] / 20.0, 1.0)
            
            best_method = max(scores.items(), key=lambda x: x[1])
            comparison['recommendation'] = {
                'method': best_method[0],
                'score': best_method[1],
                'reason': f"Best performance with score {best_method[1]:.3f}"
            }
            
            return comparison
            
        except Exception as e:
            logger.error(f"Error comparing retrieval methods: {e}")
            return {'error': str(e)}
    
    def get_ab_test_statistics(self) -> Dict[str, Any]:
        """Get statistics from A/B test results"""
        if not self.ab_test_results:
            return {'total_tests': 0}
        
        total_tests = len(self.ab_test_results)
        method_wins = {}
        avg_confidence = 0.0
        avg_response_time = 0.0
        
        for result in self.ab_test_results:
            winner = result.get('winner', 'unknown')
            method_wins[winner] = method_wins.get(winner, 0) + 1
            
            confidence = result.get('confidence', 0)
            avg_confidence += confidence
            
            response_time = result.get('metadata', {}).get('response_time', 0)
            avg_response_time += response_time
        
        if total_tests > 0:
            avg_confidence /= total_tests
            avg_response_time /= total_tests
        
        return {
            'total_tests': total_tests,
            'method_wins': method_wins,
            'avg_confidence': avg_confidence,
            'avg_response_time': avg_response_time,
            'recent_tests': self.ab_test_results[-10:] if self.ab_test_results else []
        }
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary"""
        hybrid_stats = self.hybrid_retriever.get_statistics()
        
        return {
            'hybrid_retriever_stats': hybrid_stats,
            'ab_test_stats': self.get_ab_test_statistics(),
            'total_performance_metrics': len(self.performance_metrics)
        } 