"""
Document Loader for SmartBorrow RAG System

Loads processed JSON files from data/processed/ and creates
LangChain Document objects with rich metadata.
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)

@dataclass
class ProcessedDocument:
    """Represents a processed document with metadata"""
    content: str
    metadata: Dict[str, Any]
    source_type: str
    document_type: str

class SmartBorrowDocumentLoader:
    """Loads processed data and creates LangChain Documents"""
    
    def __init__(self, processed_data_path: str = "data/processed") -> None:
        self.processed_data_path = Path(processed_data_path)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1500,  # Larger chunks for better context
            chunk_overlap=300,  # More overlap for continuity
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        
        # Document type mappings
        self.document_types = {
            'structured_knowledge': 'knowledge_base',
            'synthetic_qa_pairs': 'qa_pairs',
            'complaint_categories': 'complaints',
            'complaint_faqs': 'faqs',
            'numerical_data': 'numerical',
            'procedure_variations': 'procedures',
            'test_datasets': 'test_data'
        }
    
    def load_processed_data(self) -> List[ProcessedDocument]:
        """Load all processed data files and create documents"""
        documents = []
        
        # Load structured knowledge
        knowledge_docs = self._load_structured_knowledge()
        documents.extend(knowledge_docs)
        
        # Load synthetic Q&A pairs
        qa_docs = self._load_synthetic_qa_pairs()
        documents.extend(qa_docs)
        
        # Load complaint data
        complaint_docs = self._load_complaint_data()
        documents.extend(complaint_docs)
        
        # Load numerical data
        numerical_docs = self._load_numerical_data()
        documents.extend(numerical_docs)
        
        # Load procedure variations
        procedure_docs = self._load_procedure_variations()
        documents.extend(procedure_docs)
        
        # Load test datasets
        test_docs = self._load_test_datasets()
        documents.extend(test_docs)
        
        logger.info(f"Loaded {len(documents)} processed documents")
        return documents
    
    def _load_structured_knowledge(self) -> List[ProcessedDocument]:
        """Load structured knowledge from JSON"""
        documents = []
        knowledge_file = self.processed_data_path / "structured_knowledge.json"
        
        if not knowledge_file.exists():
            logger.warning("Structured knowledge file not found")
            return documents
        
        try:
            with open(knowledge_file, 'r') as f:
                knowledge_data = json.load(f)
            
            for concept_name, concept_data in knowledge_data.items():
                # Create document for concept definition
                if concept_data.get('definition'):
                    doc = ProcessedDocument(
                        content=f"Concept: {concept_name}\n\nDefinition: {concept_data['definition']}",
                        metadata={
                            'source_type': 'structured_knowledge',
                            'document_type': 'knowledge_base',
                            'concept': concept_name,
                            'content_type': 'definition',
                            'source_documents': concept_data.get('source_documents', [])
                        },
                        source_type='structured_knowledge',
                        document_type='knowledge_base'
                    )
                    documents.append(doc)
                
                # Create documents for requirements
                requirements = concept_data.get('requirements', [])
                for i, requirement in enumerate(requirements[:3]):  # Limit to first 3
                    doc = ProcessedDocument(
                        content=f"Concept: {concept_name}\n\nRequirement {i+1}: {requirement}",
                        metadata={
                            'source_type': 'structured_knowledge',
                            'document_type': 'knowledge_base',
                            'concept': concept_name,
                            'content_type': 'requirement',
                            'requirement_index': i+1,
                            'source_documents': concept_data.get('source_documents', [])
                        },
                        source_type='structured_knowledge',
                        document_type='knowledge_base'
                    )
                    documents.append(doc)
                
                # Create documents for procedures
                procedures = concept_data.get('procedures', [])
                for i, procedure in enumerate(procedures[:3]):  # Limit to first 3
                    doc = ProcessedDocument(
                        content=f"Concept: {concept_name}\n\nProcedure {i+1}: {procedure}",
                        metadata={
                            'source_type': 'structured_knowledge',
                            'document_type': 'knowledge_base',
                            'concept': concept_name,
                            'content_type': 'procedure',
                            'procedure_index': i+1,
                            'source_documents': concept_data.get('source_documents', [])
                        },
                        source_type='structured_knowledge',
                        document_type='knowledge_base'
                    )
                    documents.append(doc)
                
                # Create documents for numerical data
                numerical_data = concept_data.get('numerical_data', [])
                for i, data_point in enumerate(numerical_data[:5]):  # Limit to first 5
                    doc = ProcessedDocument(
                        content=f"Concept: {concept_name}\n\nNumerical Data: {data_point['value']} ({data_point['unit']})\nContext: {data_point['context']}",
                        metadata={
                            'source_type': 'structured_knowledge',
                            'document_type': 'knowledge_base',
                            'concept': concept_name,
                            'content_type': 'numerical_data',
                            'value': data_point['value'],
                            'unit': data_point['unit'],
                            'category': data_point['category'],
                            'source_documents': concept_data.get('source_documents', [])
                        },
                        source_type='structured_knowledge',
                        document_type='knowledge_base'
                    )
                    documents.append(doc)
            
            logger.info(f"Loaded {len(documents)} structured knowledge documents")
            
        except Exception as e:
            logger.error(f"Error loading structured knowledge: {e}")
        
        return documents
    
    def _load_synthetic_qa_pairs(self) -> List[ProcessedDocument]:
        """Load synthetic Q&A pairs from JSON"""
        documents = []
        qa_file = self.processed_data_path / "synthetic_qa_pairs.json"
        
        if not qa_file.exists():
            logger.warning("Synthetic Q&A pairs file not found")
            return documents
        
        try:
            with open(qa_file, 'r') as f:
                qa_data = json.load(f)
            
            for qa_pair in qa_data:
                doc = ProcessedDocument(
                    content=f"Question: {qa_pair['question']}\n\nAnswer: {qa_pair['answer']}",
                    metadata={
                        'source_type': 'synthetic_qa_pairs',
                        'document_type': 'qa_pairs',
                        'category': qa_pair['category'],
                        'confidence': qa_pair['confidence'],
                        'source_document': qa_pair['source_document'],
                        'variations': qa_pair.get('variations', [])
                    },
                    source_type='synthetic_qa_pairs',
                    document_type='qa_pairs'
                )
                documents.append(doc)
            
            logger.info(f"Loaded {len(documents)} synthetic Q&A pair documents")
            
        except Exception as e:
            logger.error(f"Error loading synthetic Q&A pairs: {e}")
        
        return documents
    
    def _load_complaint_data(self) -> List[ProcessedDocument]:
        """Load complaint categories and FAQs"""
        documents = []
        
        # Load complaint categories
        categories_file = self.processed_data_path / "complaint_categories.json"
        if categories_file.exists():
            try:
                with open(categories_file, 'r') as f:
                    categories_data = json.load(f)
                
                for category_name, category_data in categories_data.items():
                    # Create document for category overview
                    doc = ProcessedDocument(
                        content=f"Complaint Category: {category_name}\n\nPercentage: {category_data['percentage']:.1f}%\nComplaint Count: {category_data['complaint_count']}\n\nCommon Keywords: {', '.join(category_data['common_keywords'][:10])}\n\nCommon Companies: {', '.join(category_data['common_companies'])}\n\nCommon Issues: {', '.join(category_data['common_issues'])}",
                        metadata={
                            'source_type': 'complaint_categories',
                            'document_type': 'complaints',
                            'category': category_name,
                            'complaint_count': category_data['complaint_count'],
                            'percentage': category_data['percentage'],
                            'common_keywords': category_data['common_keywords'],
                            'common_companies': category_data['common_companies'],
                            'common_issues': category_data['common_issues'],
                            'avg_response_time': category_data.get('avg_response_time')
                        },
                        source_type='complaint_categories',
                        document_type='complaints'
                    )
                    documents.append(doc)
                    
                    # Create documents for sample complaints
                    sample_complaints = category_data.get('sample_complaints', [])
                    for i, complaint in enumerate(sample_complaints[:2]):  # Limit to first 2
                        doc = ProcessedDocument(
                            content=f"Complaint Category: {category_name}\n\nSample Complaint {i+1}: {complaint}",
                            metadata={
                                'source_type': 'complaint_categories',
                                'document_type': 'complaints',
                                'category': category_name,
                                'content_type': 'sample_complaint',
                                'complaint_index': i+1
                            },
                            source_type='complaint_categories',
                            document_type='complaints'
                        )
                        documents.append(doc)
                
                logger.info(f"Loaded {len(documents)} complaint category documents")
                
            except Exception as e:
                logger.error(f"Error loading complaint categories: {e}")
        
        # Load complaint FAQs
        faqs_file = self.processed_data_path / "complaint_faqs.json"
        if faqs_file.exists():
            try:
                with open(faqs_file, 'r') as f:
                    faqs_data = json.load(f)
                
                for faq in faqs_data:
                    doc = ProcessedDocument(
                        content=f"FAQ Question: {faq['question']}\n\nAnswer: {faq['answer']}",
                        metadata={
                            'source_type': 'complaint_faqs',
                            'document_type': 'faqs',
                            'category': faq['category'],
                            'frequency': faq['frequency'],
                            'keywords': faq['keywords']
                        },
                        source_type='complaint_faqs',
                        document_type='faqs'
                    )
                    documents.append(doc)
                
                logger.info(f"Loaded {len(documents)} complaint FAQ documents")
                
            except Exception as e:
                logger.error(f"Error loading complaint FAQs: {e}")
        
        return documents
    
    def _load_numerical_data(self) -> List[ProcessedDocument]:
        """Load numerical data with context"""
        documents = []
        numerical_file = self.processed_data_path / "numerical_data.json"
        
        if not numerical_file.exists():
            logger.warning("Numerical data file not found")
            return documents
        
        try:
            with open(numerical_file, 'r') as f:
                numerical_data = json.load(f)
            
            # Group by category for better organization
            by_category = {}
            for data_point in numerical_data:
                category = data_point['category']
                if category not in by_category:
                    by_category[category] = []
                by_category[category].append(data_point)
            
            for category, data_points in by_category.items():
                # Create summary document for each category
                values = [dp['value'] for dp in data_points[:10]]  # Limit to first 10
                doc = ProcessedDocument(
                    content=f"Numerical Data Category: {category}\n\nValues: {', '.join(values)}\n\nTotal data points: {len(data_points)}",
                    metadata={
                        'source_type': 'numerical_data',
                        'document_type': 'numerical',
                        'category': category,
                        'data_point_count': len(data_points),
                        'values': values
                    },
                    source_type='numerical_data',
                    document_type='numerical'
                )
                documents.append(doc)
                
                # Create individual documents for important data points
                for i, data_point in enumerate(data_points[:5]):  # Limit to first 5
                    doc = ProcessedDocument(
                        content=f"Numerical Data: {data_point['value']} ({data_point['unit']})\n\nContext: {data_point['context']}",
                        metadata={
                            'source_type': 'numerical_data',
                            'document_type': 'numerical',
                            'category': data_point['category'],
                            'value': data_point['value'],
                            'unit': data_point['unit'],
                            'document': data_point['document'],
                            'page_reference': data_point.get('page_reference')
                        },
                        source_type='numerical_data',
                        document_type='numerical'
                    )
                    documents.append(doc)
            
            logger.info(f"Loaded {len(documents)} numerical data documents")
            
        except Exception as e:
            logger.error(f"Error loading numerical data: {e}")
        
        return documents
    
    def _load_procedure_variations(self) -> List[ProcessedDocument]:
        """Load procedure variations"""
        documents = []
        procedures_file = self.processed_data_path / "procedure_variations.json"
        
        if not procedures_file.exists():
            logger.warning("Procedure variations file not found")
            return documents
        
        try:
            with open(procedures_file, 'r') as f:
                procedures_data = json.load(f)
            
            for procedure in procedures_data:
                doc = ProcessedDocument(
                    content=f"Procedure Type: {procedure['type']}\nCategory: {procedure['category']}\n\nOriginal: {procedure['original']}\n\nVariation: {procedure['variation']}",
                    metadata={
                        'source_type': 'procedure_variations',
                        'document_type': 'procedures',
                        'type': procedure['type'],
                        'category': procedure['category']
                    },
                    source_type='procedure_variations',
                    document_type='procedures'
                )
                documents.append(doc)
            
            logger.info(f"Loaded {len(documents)} procedure variation documents")
            
        except Exception as e:
            logger.error(f"Error loading procedure variations: {e}")
        
        return documents
    
    def _load_test_datasets(self) -> List[ProcessedDocument]:
        """Load test datasets"""
        documents = []
        test_file = self.processed_data_path / "test_datasets.json"
        
        if not test_file.exists():
            logger.warning("Test datasets file not found")
            return documents
        
        try:
            with open(test_file, 'r') as f:
                test_data = json.load(f)
            
            for difficulty, test_cases in test_data.items():
                for test_case in test_cases:
                    doc = ProcessedDocument(
                        content=f"Test Case (Difficulty: {difficulty})\n\nScenario: {test_case['scenario']}\n\nExpected Answer: {test_case['expected_answer']}",
                        metadata={
                            'source_type': 'test_datasets',
                            'document_type': 'test_data',
                            'difficulty': difficulty,
                            'category': test_case['category'],
                            'source_document': test_case['source_document']
                        },
                        source_type='test_datasets',
                        document_type='test_data'
                    )
                    documents.append(doc)
            
            logger.info(f"Loaded {len(documents)} test dataset documents")
            
        except Exception as e:
            logger.error(f"Error loading test datasets: {e}")
        
        return documents
    
    def create_langchain_documents(self, processed_docs: List[ProcessedDocument]) -> List[Document]:
        """Convert processed documents to LangChain Documents"""
        langchain_docs = []
        
        for doc in processed_docs:
            # Split content if it's too long
            if len(doc.content) > 2000:
                chunks = self.text_splitter.split_text(doc.content)
                for i, chunk in enumerate(chunks):
                    langchain_doc = Document(
                        page_content=chunk,
                        metadata={
                            **doc.metadata,
                            'chunk_index': i,
                            'total_chunks': len(chunks)
                        }
                    )
                    langchain_docs.append(langchain_doc)
            else:
                langchain_doc = Document(
                    page_content=doc.content,
                    metadata=doc.metadata
                )
                langchain_docs.append(langchain_doc)
        
        logger.info(f"Created {len(langchain_docs)} LangChain documents")
        return langchain_docs
    
    def get_document_summary(self, documents: List[Document]) -> Dict[str, Any]:
        """Get summary statistics of loaded documents"""
        summary = {
            'total_documents': len(documents),
            'by_source_type': {},
            'by_document_type': {},
            'by_category': {}
        }
        
        for doc in documents:
            metadata = doc.metadata
            
            # Count by source type
            source_type = metadata.get('source_type', 'unknown')
            summary['by_source_type'][source_type] = summary['by_source_type'].get(source_type, 0) + 1
            
            # Count by document type
            doc_type = metadata.get('document_type', 'unknown')
            summary['by_document_type'][doc_type] = summary['by_document_type'].get(doc_type, 0) + 1
            
            # Count by category
            category = metadata.get('category', 'unknown')
            summary['by_category'][category] = summary['by_category'].get(category, 0) + 1
        
        return summary

def main() -> None:
    """Test the document loader"""
    loader = SmartBorrowDocumentLoader()
    
    # Load processed documents
    processed_docs = loader.load_processed_data()
    
    # Convert to LangChain documents
    langchain_docs = loader.create_langchain_documents(processed_docs)
    
    # Get summary
    summary = loader.get_document_summary(langchain_docs)
    
    logger.info("Document Loading Summary:")
    logger.info("Total documents: {summary['total_documents']}")
    logger.info("\nBy source type:")
    for source_type, count in summary['by_source_type'].items():
        logger.info("  {source_type}: {count}")
    logger.info("\nBy document type:")
    for doc_type, count in summary['by_document_type'].items():
        logger.info("  {doc_type}: {count}")
    
    return langchain_docs

if __name__ == "__main__":
    main() 