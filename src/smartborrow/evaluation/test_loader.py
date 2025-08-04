"""
Test Loader for RAGAS Evaluation

Load test datasets from processed data:
- 150 synthetic Q&A pairs
- 26 test cases across difficulty levels
- Create RAGAS evaluation datasets
- Include ground truth from processed knowledge
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datasets import Dataset
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

@dataclass
class TestCase:
    """Individual test case for evaluation"""
    question: str
    answer: str
    context: List[str]
    difficulty: str
    category: str
    ground_truth: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class EvaluationDataset:
    """RAGAS evaluation dataset"""
    name: str
    test_cases: List[TestCase]
    dataset: Dataset
    metadata: Dict[str, Any]

class TestLoader:
    """Load and prepare test datasets for RAGAS evaluation"""
    
    def __init__(self, processed_data_path: str = "data/processed") -> None:
        self.processed_data_path = Path(processed_data_path)
        self.test_cases = []
        self.synthetic_qa_pairs = []
        self.structured_knowledge = {}
        
    def load_synthetic_qa_pairs(self) -> List[Dict[str, Any]]:
        """Load 150 synthetic Q&A pairs from processed data"""
        try:
            qa_file = self.processed_data_path / "synthetic_qa_pairs.json"
            if not qa_file.exists():
                logger.warning(f"Synthetic Q&A pairs file not found: {qa_file}")
                return []
            
            with open(qa_file, 'r') as f:
                qa_data = json.load(f)
            
            logger.info(f"Loaded {len(qa_data)} synthetic Q&A pairs")
            self.synthetic_qa_pairs = qa_data
            return qa_data
            
        except Exception as e:
            logger.error(f"Error loading synthetic Q&A pairs: {e}")
            return []
    
    def load_test_datasets(self) -> List[Dict[str, Any]]:
        """Load 26 test cases across difficulty levels"""
        try:
            test_file = self.processed_data_path / "test_datasets.json"
            if not test_file.exists():
                logger.warning(f"Test datasets file not found: {test_file}")
                return []
            
            with open(test_file, 'r') as f:
                test_data = json.load(f)
            
            logger.info(f"Loaded {len(test_data)} test cases")
            return test_data
            
        except Exception as e:
            logger.error(f"Error loading test datasets: {e}")
            return []
    
    def load_structured_knowledge(self) -> Dict[str, Any]:
        """Load structured knowledge for ground truth"""
        try:
            knowledge_file = self.processed_data_path / "structured_knowledge.json"
            if not knowledge_file.exists():
                logger.warning(f"Structured knowledge file not found: {knowledge_file}")
                return {}
            
            with open(knowledge_file, 'r') as f:
                knowledge_data = json.load(f)
            
            logger.info(f"Loaded structured knowledge with {len(knowledge_data)} concepts")
            self.structured_knowledge = knowledge_data
            return knowledge_data
            
        except Exception as e:
            logger.error(f"Error loading structured knowledge: {e}")
            return {}
    
    def create_test_cases(self) -> List[TestCase]:
        """Create test cases from synthetic Q&A pairs and test datasets"""
        test_cases = []
        
        # Load all data
        qa_pairs = self.load_synthetic_qa_pairs()
        test_datasets = self.load_test_datasets()
        knowledge = self.load_structured_knowledge()
        
        # Create test cases from synthetic Q&A pairs
        for i, qa_pair in enumerate(qa_pairs):
            test_case = TestCase(
                question=qa_pair.get('question', ''),
                answer=qa_pair.get('answer', ''),
                context=qa_pair.get('context', []),
                difficulty=qa_pair.get('difficulty', 'medium'),
                category=qa_pair.get('category', 'general'),
                ground_truth=qa_pair.get('ground_truth'),
                metadata={
                    'source': 'synthetic_qa',
                    'index': i,
                    'original_data': qa_pair
                }
            )
            test_cases.append(test_case)
        
        # Create test cases from test datasets (organized by difficulty)
        for difficulty, difficulty_tests in test_datasets.items():
            for i, test_data in enumerate(difficulty_tests):
                test_case = TestCase(
                    question=test_data.get('scenario', ''),
                    answer=test_data.get('expected_answer', ''),
                    context=test_data.get('source_document', []),
                    difficulty=difficulty,
                    category=test_data.get('category', 'general'),
                    ground_truth=test_data.get('expected_answer'),
                    metadata={
                        'source': 'test_dataset',
                        'index': i,
                        'original_data': test_data
                    }
                )
                test_cases.append(test_case)
        
        self.test_cases = test_cases
        logger.info(f"Created {len(test_cases)} test cases")
        return test_cases
    
    def create_ragas_dataset(self, test_cases: List[TestCase]) -> Dataset:
        """Convert test cases to RAGAS Dataset format"""
        try:
            # Prepare data for RAGAS
            ragas_data = []
            
            for test_case in test_cases:
                # Create context string from list
                context_str = "\n".join(test_case.context) if test_case.context else ""
                
                # Ensure contexts is a list of strings
                contexts = test_case.context
                if contexts:
                    # Convert all elements to strings and filter out empty ones
                    contexts = [str(ctx).strip() for ctx in contexts if ctx]
                    # Remove duplicates while preserving order
                    seen = set()
                    contexts = [ctx for ctx in contexts if not (ctx in seen or seen.add(ctx))]
                else:
                    contexts = []
                
                # Ensure all fields are properly formatted for RAGAS
                ragas_entry = {
                    "question": str(test_case.question or ""),
                    "answer": str(test_case.answer or ""),
                    "contexts": contexts if contexts else [],
                    "context": str(context_str or ""),
                    "ground_truth": str(test_case.ground_truth or test_case.answer or ""),
                    "difficulty": str(test_case.difficulty or "medium"),
                    "category": str(test_case.category or "general"),
                    "metadata": test_case.metadata if test_case.metadata else {}
                }
                ragas_data.append(ragas_entry)
            
            # Create RAGAS Dataset
            try:
                dataset = Dataset.from_list(ragas_data)
                logger.info(f"Created RAGAS dataset with {len(dataset)} entries")
                return dataset
            except Exception as dataset_error:
                logger.error(f"Error creating RAGAS dataset: {dataset_error}")
                # Try to debug the issue
                if ragas_data:
                    logger.error(f"First entry structure: {type(ragas_data[0])}")
                    logger.error(f"First entry keys: {list(ragas_data[0].keys())}")
                    for key, value in ragas_data[0].items():
                        logger.error(f"  {key}: {type(value)} = {value}")
                return Dataset.from_list([])
            
        except Exception as e:
            logger.error(f"Error preparing RAGAS dataset: {e}")
            return Dataset.from_list([])
    
    def create_difficulty_datasets(self) -> Dict[str, EvaluationDataset]:
        """Create separate datasets for each difficulty level"""
        if not self.test_cases:
            self.create_test_cases()
        
        difficulty_datasets = {}
        
        for difficulty in ['easy', 'medium', 'hard']:
            # Filter test cases by difficulty
            filtered_cases = [tc for tc in self.test_cases if tc.difficulty.lower() == difficulty]
            
            if filtered_cases:
                dataset = self.create_ragas_dataset(filtered_cases)
                evaluation_dataset = EvaluationDataset(
                    name=f"{difficulty}_difficulty",
                    test_cases=filtered_cases,
                    dataset=dataset,
                    metadata={
                        'difficulty': difficulty,
                        'count': len(filtered_cases),
                        'categories': list(set(tc.category for tc in filtered_cases))
                    }
                )
                difficulty_datasets[difficulty] = evaluation_dataset
                logger.info(f"Created {difficulty} dataset with {len(filtered_cases)} test cases")
        
        return difficulty_datasets
    
    def create_category_datasets(self) -> Dict[str, EvaluationDataset]:
        """Create separate datasets for each category"""
        if not self.test_cases:
            self.create_test_cases()
        
        category_datasets = {}
        
        # Get all unique categories
        categories = set(tc.category for tc in self.test_cases)
        
        for category in categories:
            # Filter test cases by category
            filtered_cases = [tc for tc in self.test_cases if tc.category == category]
            
            if filtered_cases:
                dataset = self.create_ragas_dataset(filtered_cases)
                evaluation_dataset = EvaluationDataset(
                    name=f"{category}_category",
                    test_cases=filtered_cases,
                    dataset=dataset,
                    metadata={
                        'category': category,
                        'count': len(filtered_cases),
                        'difficulties': list(set(tc.difficulty for tc in filtered_cases))
                    }
                )
                category_datasets[category] = evaluation_dataset
                logger.info(f"Created {category} dataset with {len(filtered_cases)} test cases")
        
        return category_datasets
    
    def get_full_dataset(self) -> EvaluationDataset:
        """Get the complete evaluation dataset"""
        if not self.test_cases:
            self.create_test_cases()
        
        dataset = self.create_ragas_dataset(self.test_cases)
        return EvaluationDataset(
            name="full_evaluation",
            test_cases=self.test_cases,
            dataset=dataset,
            metadata={
                'total_count': len(self.test_cases),
                'difficulties': list(set(tc.difficulty for tc in self.test_cases)),
                'categories': list(set(tc.category for tc in self.test_cases))
            }
        )
    
    def get_dataset_stats(self) -> Dict[str, Any]:
        """Get statistics about the loaded datasets"""
        if not self.test_cases:
            self.create_test_cases()
        
        stats = {
            'total_test_cases': len(self.test_cases),
            'synthetic_qa_pairs': len(self.synthetic_qa_pairs),
            'structured_knowledge_concepts': len(self.structured_knowledge),
            'difficulty_distribution': {},
            'category_distribution': {},
            'source_distribution': {}
        }
        
        # Calculate distributions
        for test_case in self.test_cases:
            # Difficulty distribution
            difficulty = test_case.difficulty.lower()
            stats['difficulty_distribution'][difficulty] = stats['difficulty_distribution'].get(difficulty, 0) + 1
            
            # Category distribution
            category = test_case.category
            stats['category_distribution'][category] = stats['category_distribution'].get(category, 0) + 1
            
            # Source distribution
            source = test_case.metadata.get('source', 'unknown')
            stats['source_distribution'][source] = stats['source_distribution'].get(source, 0) + 1
        
        return stats

def main() -> None:
    """Test the test loader"""
    loader = TestLoader()
    
    # Load all datasets
    full_dataset = loader.get_full_dataset()
    difficulty_datasets = loader.create_difficulty_datasets()
    category_datasets = loader.create_category_datasets()
    stats = loader.get_dataset_stats()
    
    logger.info("Dataset Statistics:")
    logger.info("- Total test cases: {stats['total_test_cases']}")
    logger.info("- Synthetic Q&A pairs: {stats['synthetic_qa_pairs']}")
    logger.info("- Structured knowledge concepts: {stats['structured_knowledge_concepts']}")
    logger.info("- Difficulty distribution: {stats['difficulty_distribution']}")
    logger.info("- Category distribution: {stats['category_distribution']}")
    logger.info("- Source distribution: {stats['source_distribution']}")
    
    logger.info("\nCreated datasets:")
    logger.info("- Full dataset: {len(full_dataset.test_cases)} test cases")
    logger.info("- Difficulty datasets: {len(difficulty_datasets)}")
    logger.info("- Category datasets: {len(category_datasets)}")

if __name__ == "__main__":
    main() 