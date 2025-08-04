"""
Content Enricher for SmartBorrow

Cross-references information between PDFs, extracts numerical data,
and builds structured knowledge from unstructured PDFs.
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass
from collections import defaultdict, Counter
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class CrossReference:
    """Represents a cross-reference between documents"""
    source_doc: str
    target_doc: str
    shared_concept: str
    source_context: str
    target_context: str
    confidence: float

@dataclass
class NumericalData:
    """Represents extracted numerical data"""
    value: str
    unit: str
    context: str
    document: str
    category: str
    page_reference: Optional[str] = None

@dataclass
class StructuredKnowledge:
    """Represents structured knowledge extracted from documents"""
    concept: str
    definition: str
    requirements: List[str]
    procedures: List[str]
    related_concepts: List[str]
    numerical_data: List[NumericalData]
    source_documents: List[str]

class ContentEnricher:
    """Enriches content by cross-referencing information between documents"""
    
    def __init__(self, processed_data_path: str = "data/processed") -> None:
        self.processed_data_path = Path(processed_data_path)
        self.raw_data_path = Path("data/raw")
        
        # Key concepts for cross-referencing
        self.key_concepts = {
            'pell_grant': [
                'pell grant', 'federal pell grant', 'pell grant program',
                'pell grant eligibility', 'pell grant amount', 'pell grant limits'
            ],
            'direct_loans': [
                'direct loan', 'direct subsidized loan', 'direct unsubsidized loan',
                'direct plus loan', 'direct loan program', 'direct loan limits'
            ],
            'cost_of_attendance': [
                'cost of attendance', 'coa', 'tuition', 'fees', 'room and board',
                'books and supplies', 'transportation', 'personal expenses'
            ],
            'expected_family_contribution': [
                'expected family contribution', 'efc', 'family contribution',
                'financial need', 'need analysis', 'income protection allowance'
            ],
            'verification': [
                'verification', 'income verification', 'documentation',
                'proof of income', 'tax returns', 'w-2 forms', 'pay stubs'
            ],
            'repayment_plans': [
                'repayment plan', 'income-driven repayment', 'idr',
                'standard repayment', 'graduated repayment', 'extended repayment'
            ],
            'forgiveness': [
                'loan forgiveness', 'public service loan forgiveness', 'pslf',
                'teacher loan forgiveness', 'discharge', 'cancellation'
            ],
            'academic_calendar': [
                'academic calendar', 'semester', 'quarter', 'term',
                'enrollment period', 'registration', 'drop/add period'
            ]
        }
        
        # Numerical data patterns
        self.numerical_patterns = {
            'dollar_amounts': r'\$[\d,]+(?:\.\d{2})?',
            'percentages': r'\d+(?:\.\d+)?%',
            'dates': r'\b\d{1,2}/\d{1,2}/\d{2,4}\b',
            'years': r'\b\d{4}\b',
            'loan_limits': r'(?:subsidized|unsubsidized|total)\s+(?:loan|limit)s?\s*(?:of\s+)?\$[\d,]+',
            'grant_amounts': r'(?:pell\s+grant|maximum\s+grant)\s*(?:of\s+)?\$[\d,]+',
            'income_thresholds': r'(?:income|salary)\s+(?:of\s+)?\$[\d,]+',
            'time_periods': r'\d+\s+(?:years?|months?|weeks?|days?)'
        }
        
        # Document relationships
        self.document_relationships = {
            'pell_grant_guide': ['direct_loan_guide', 'application_verification_guide'],
            'direct_loan_guide': ['pell_grant_guide', 'application_verification_guide'],
            'application_verification_guide': ['pell_grant_guide', 'direct_loan_guide', 'academic_calendar_cost_guide'],
            'academic_calendar_cost_guide': ['application_verification_guide', 'pell_grant_guide']
        }
    
    def load_processed_pdf_data(self) -> Dict[str, Dict[str, Any]]:
        """Load processed PDF data from JSON files"""
        pdf_data = {}
        
        # Look for processed PDF metadata files
        for metadata_file in self.processed_data_path.glob("*_metadata.json"):
            doc_name = metadata_file.stem.replace('_metadata', '')
            
            try:
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                
                # Also load the text content
                text_file = self.processed_data_path / f"{doc_name}_text.txt"
                if text_file.exists():
                    with open(text_file, 'r', encoding='utf-8') as f:
                        text_content = f.read()
                    
                    metadata['text_content'] = text_content
                    pdf_data[doc_name] = metadata
                    
            except Exception as e:
                logger.error(f"Error loading {metadata_file}: {e}")
        
        logger.info(f"Loaded {len(pdf_data)} processed PDF documents")
        return pdf_data
    
    def extract_numerical_data(self, text: str, document_name: str) -> List[NumericalData]:
        """Extract numerical data from text with context"""
        numerical_data = []
        
        # Extract dollar amounts
        dollar_matches = re.finditer(self.numerical_patterns['dollar_amounts'], text)
        for match in dollar_matches:
            # Get context around the match
            start = max(0, match.start() - 100)
            end = min(len(text), match.end() + 100)
            context = text[start:end].strip()
            
            numerical_data.append(NumericalData(
                value=match.group(),
                unit='dollars',
                context=context,
                document=document_name,
                category='dollar_amount'
            ))
        
        # Extract percentages
        percentage_matches = re.finditer(self.numerical_patterns['percentages'], text)
        for match in percentage_matches:
            start = max(0, match.start() - 100)
            end = min(len(text), match.end() + 100)
            context = text[start:end].strip()
            
            numerical_data.append(NumericalData(
                value=match.group(),
                unit='percentage',
                context=context,
                document=document_name,
                category='percentage'
            ))
        
        # Extract loan limits
        loan_limit_matches = re.finditer(self.numerical_patterns['loan_limits'], text, re.IGNORECASE)
        for match in loan_limit_matches:
            start = max(0, match.start() - 100)
            end = min(len(text), match.end() + 100)
            context = text[start:end].strip()
            
            numerical_data.append(NumericalData(
                value=match.group(),
                unit='loan_limit',
                context=context,
                document=document_name,
                category='loan_limit'
            ))
        
        # Extract grant amounts
        grant_matches = re.finditer(self.numerical_patterns['grant_amounts'], text, re.IGNORECASE)
        for match in grant_matches:
            start = max(0, match.start() - 100)
            end = min(len(text), match.end() + 100)
            context = text[start:end].strip()
            
            numerical_data.append(NumericalData(
                value=match.group(),
                unit='grant_amount',
                context=context,
                document=document_name,
                category='grant_amount'
            ))
        
        return numerical_data
    
    def find_cross_references(self, pdf_data: Dict[str, Dict[str, Any]]) -> List[CrossReference]:
        """Find cross-references between documents"""
        cross_references = []
        
        for concept_name, concept_keywords in self.key_concepts.items():
            # Find documents that mention this concept
            documents_with_concept = {}
            
            for doc_name, doc_data in pdf_data.items():
                text_content = doc_data.get('text_content', '').lower()
                
                for keyword in concept_keywords:
                    if keyword in text_content:
                        if doc_name not in documents_with_concept:
                            documents_with_concept[doc_name] = []
                        documents_with_concept[doc_name].append(keyword)
            
            # Create cross-references between documents that mention the same concept
            doc_names = list(documents_with_concept.keys())
            for i in range(len(doc_names)):
                for j in range(i + 1, len(doc_names)):
                    doc1 = doc_names[i]
                    doc2 = doc_names[j]
                    
                    # Find context for each document
                    context1 = self._find_concept_context(pdf_data[doc1]['text_content'], concept_keywords)
                    context2 = self._find_concept_context(pdf_data[doc2]['text_content'], concept_keywords)
                    
                    if context1 and context2:
                        cross_references.append(CrossReference(
                            source_doc=doc1,
                            target_doc=doc2,
                            shared_concept=concept_name,
                            source_context=context1,
                            target_context=context2,
                            confidence=0.8  # High confidence for keyword matches
                        ))
        
        return cross_references
    
    def _find_concept_context(self, text: str, keywords: List[str]) -> str:
        """Find context around a concept in text"""
        text_lower = text.lower()
        
        for keyword in keywords:
            if keyword in text_lower:
                # Find the position of the keyword
                pos = text_lower.find(keyword)
                if pos != -1:
                    # Extract context around the keyword
                    start = max(0, pos - 200)
                    end = min(len(text), pos + len(keyword) + 200)
                    return text[start:end].strip()
        
        return ""
    
    def build_structured_knowledge(self, pdf_data: Dict[str, Dict[str, Any]], 
                                 cross_references: List[CrossReference],
                                 numerical_data: List[NumericalData]) -> Dict[str, StructuredKnowledge]:
        """Build structured knowledge from cross-referenced information"""
        structured_knowledge = {}
        
        # Group numerical data by concept
        concept_numerical_data = defaultdict(list)
        for data in numerical_data:
            # Determine concept based on context
            context_lower = data.context.lower()
            for concept_name, concept_keywords in self.key_concepts.items():
                for keyword in concept_keywords:
                    if keyword in context_lower:
                        concept_numerical_data[concept_name].append(data)
                        break
        
        # Build structured knowledge for each concept
        for concept_name, concept_keywords in self.key_concepts.items():
            # Find documents that mention this concept
            relevant_docs = []
            for doc_name, doc_data in pdf_data.items():
                text_content = doc_data.get('text_content', '').lower()
                for keyword in concept_keywords:
                    if keyword in text_content:
                        relevant_docs.append(doc_name)
                        break
            
            if relevant_docs:
                # Extract definition and requirements
                definition = self._extract_definition(concept_name, pdf_data, relevant_docs)
                requirements = self._extract_requirements(concept_name, pdf_data, relevant_docs)
                procedures = self._extract_procedures(concept_name, pdf_data, relevant_docs)
                
                # Find related concepts
                related_concepts = self._find_related_concepts(concept_name, cross_references)
                
                # Get numerical data for this concept
                concept_data = concept_numerical_data.get(concept_name, [])
                
                structured_knowledge[concept_name] = StructuredKnowledge(
                    concept=concept_name,
                    definition=definition,
                    requirements=requirements,
                    procedures=procedures,
                    related_concepts=related_concepts,
                    numerical_data=concept_data,
                    source_documents=relevant_docs
                )
        
        return structured_knowledge
    
    def _extract_definition(self, concept_name: str, pdf_data: Dict[str, Dict[str, Any]], 
                           relevant_docs: List[str]) -> str:
        """Extract definition for a concept"""
        definitions = []
        
        for doc_name in relevant_docs:
            text_content = pdf_data[doc_name]['text_content']
            
            # Look for definition patterns
            definition_patterns = [
                rf'{concept_name.replace("_", " ")} is',
                rf'{concept_name.replace("_", " ")} refers to',
                rf'{concept_name.replace("_", " ")} means',
                rf'The {concept_name.replace("_", " ")}',
                rf'A {concept_name.replace("_", " ")}'
            ]
            
            for pattern in definition_patterns:
                matches = re.finditer(pattern, text_content, re.IGNORECASE)
                for match in matches:
                    # Extract sentence containing the definition
                    start = max(0, match.start() - 50)
                    end = min(len(text_content), match.end() + 200)
                    definition = text_content[start:end].strip()
                    definitions.append(definition)
        
        return definitions[0] if definitions else f"Information about {concept_name.replace('_', ' ')}"
    
    def _extract_requirements(self, concept_name: str, pdf_data: Dict[str, Dict[str, Any]], 
                            relevant_docs: List[str]) -> List[str]:
        """Extract requirements for a concept"""
        requirements = []
        
        requirement_keywords = ['requirement', 'must', 'required', 'eligible', 'qualify', 'criteria']
        
        for doc_name in relevant_docs:
            text_content = pdf_data[doc_name]['text_content']
            sentences = re.split(r'[.!?]+', text_content)
            
            for sentence in sentences:
                sentence_lower = sentence.lower()
                if any(keyword in sentence_lower for keyword in requirement_keywords):
                    # Check if sentence is related to the concept
                    concept_terms = concept_name.replace('_', ' ').split()
                    if any(term in sentence_lower for term in concept_terms):
                        requirements.append(sentence.strip())
        
        return list(set(requirements))[:5]  # Limit to top 5 requirements
    
    def _extract_procedures(self, concept_name: str, pdf_data: Dict[str, Dict[str, Any]], 
                           relevant_docs: List[str]) -> List[str]:
        """Extract procedures for a concept"""
        procedures = []
        
        procedure_keywords = ['procedure', 'process', 'step', 'how to', 'apply', 'submit']
        
        for doc_name in relevant_docs:
            text_content = pdf_data[doc_name]['text_content']
            sentences = re.split(r'[.!?]+', text_content)
            
            for sentence in sentences:
                sentence_lower = sentence.lower()
                if any(keyword in sentence_lower for keyword in procedure_keywords):
                    # Check if sentence is related to the concept
                    concept_terms = concept_name.replace('_', ' ').split()
                    if any(term in sentence_lower for term in concept_terms):
                        procedures.append(sentence.strip())
        
        return list(set(procedures))[:5]  # Limit to top 5 procedures
    
    def _find_related_concepts(self, concept_name: str, cross_references: List[CrossReference]) -> List[str]:
        """Find concepts related to the given concept"""
        related = set()
        
        for ref in cross_references:
            if ref.shared_concept == concept_name:
                # Add the other document's concept
                if ref.source_doc != concept_name:
                    related.add(ref.source_doc)
                if ref.target_doc != concept_name:
                    related.add(ref.target_doc)
        
        return list(related)
    
    def create_connections_summary(self, cross_references: List[CrossReference]) -> Dict[str, Any]:
        """Create a summary of connections between documents"""
        connections_summary = {
            'total_connections': len(cross_references),
            'concept_connections': defaultdict(list),
            'document_connections': defaultdict(list),
            'most_connected_concepts': [],
            'most_connected_documents': []
        }
        
        # Group by concept
        for ref in cross_references:
            connections_summary['concept_connections'][ref.shared_concept].append({
                'source': ref.source_doc,
                'target': ref.target_doc,
                'confidence': ref.confidence
            })
        
        # Group by document
        for ref in cross_references:
            connections_summary['document_connections'][ref.source_doc].append({
                'target': ref.target_doc,
                'concept': ref.shared_concept,
                'confidence': ref.confidence
            })
            connections_summary['document_connections'][ref.target_doc].append({
                'target': ref.source_doc,
                'concept': ref.shared_concept,
                'confidence': ref.confidence
            })
        
        # Find most connected concepts
        concept_counts = Counter([ref.shared_concept for ref in cross_references])
        connections_summary['most_connected_concepts'] = concept_counts.most_common(5)
        
        # Find most connected documents
        doc_counts = Counter()
        for ref in cross_references:
            doc_counts[ref.source_doc] += 1
            doc_counts[ref.target_doc] += 1
        connections_summary['most_connected_documents'] = doc_counts.most_common(5)
        
        return connections_summary
    
    def save_enriched_data(self, cross_references: List[CrossReference],
                          numerical_data: List[NumericalData],
                          structured_knowledge: Dict[str, StructuredKnowledge],
                          connections_summary: Dict[str, Any]) -> None:
        """Save enriched data to JSON files"""
        
        # Save cross-references
        cross_refs_data = []
        for ref in cross_references:
            cross_refs_data.append({
                'source_doc': ref.source_doc,
                'target_doc': ref.target_doc,
                'shared_concept': ref.shared_concept,
                'source_context': ref.source_context,
                'target_context': ref.target_context,
                'confidence': ref.confidence
            })
        
        cross_refs_file = self.processed_data_path / "cross_references.json"
        with open(cross_refs_file, 'w') as f:
            json.dump(cross_refs_data, f, indent=2)
        
        # Save numerical data
        numerical_data_list = []
        for data in numerical_data:
            numerical_data_list.append({
                'value': data.value,
                'unit': data.unit,
                'context': data.context,
                'document': data.document,
                'category': data.category,
                'page_reference': data.page_reference
            })
        
        numerical_file = self.processed_data_path / "numerical_data.json"
        with open(numerical_file, 'w') as f:
            json.dump(numerical_data_list, f, indent=2)
        
        # Save structured knowledge
        structured_knowledge_data = {}
        for concept_name, knowledge in structured_knowledge.items():
            structured_knowledge_data[concept_name] = {
                'concept': knowledge.concept,
                'definition': knowledge.definition,
                'requirements': knowledge.requirements,
                'procedures': knowledge.procedures,
                'related_concepts': knowledge.related_concepts,
                'numerical_data': [
                    {
                        'value': data.value,
                        'unit': data.unit,
                        'context': data.context,
                        'document': data.document,
                        'category': data.category
                    }
                    for data in knowledge.numerical_data
                ],
                'source_documents': knowledge.source_documents
            }
        
        knowledge_file = self.processed_data_path / "structured_knowledge.json"
        with open(knowledge_file, 'w') as f:
            json.dump(structured_knowledge_data, f, indent=2)
        
        # Save connections summary
        connections_file = self.processed_data_path / "connections_summary.json"
        with open(connections_file, 'w') as f:
            json.dump(connections_summary, f, indent=2)
        
        logger.info(f"Saved enriched data to {cross_refs_file}, {numerical_file}, {knowledge_file}, and {connections_file}")
    
    def enrich_content(self) -> Tuple[List[CrossReference], List[NumericalData], 
                                    Dict[str, StructuredKnowledge], Dict[str, Any]]:
        """Main function to enrich content by cross-referencing information"""
        logger.info("Starting content enrichment...")
        
        # Load processed PDF data
        pdf_data = self.load_processed_pdf_data()
        
        if not pdf_data:
            logger.warning("No processed PDF data found. Please run PDF processor first.")
            return [], [], {}, {}
        
        # Extract numerical data from all documents
        all_numerical_data = []
        for doc_name, doc_data in pdf_data.items():
            text_content = doc_data.get('text_content', '')
            numerical_data = self.extract_numerical_data(text_content, doc_name)
            all_numerical_data.extend(numerical_data)
        
        # Find cross-references
        cross_references = self.find_cross_references(pdf_data)
        
        # Build structured knowledge
        structured_knowledge = self.build_structured_knowledge(pdf_data, cross_references, all_numerical_data)
        
        # Create connections summary
        connections_summary = self.create_connections_summary(cross_references)
        
        # Save enriched data
        self.save_enriched_data(cross_references, all_numerical_data, structured_knowledge, connections_summary)
        
        logger.info(f"Content enrichment complete.")
        logger.info(f"Found {len(cross_references)} cross-references")
        logger.info(f"Extracted {len(all_numerical_data)} numerical data points")
        logger.info(f"Built structured knowledge for {len(structured_knowledge)} concepts")
        
        return cross_references, all_numerical_data, structured_knowledge, connections_summary

def main() -> None:
    """Main function to enrich content"""
    enricher = ContentEnricher()
    
    try:
        cross_references, numerical_data, structured_knowledge, connections_summary = enricher.enrich_content()
        
        # Print summary
        logger.info("\nContent Enrichment Summary:")
        logger.info("Cross-references found: {len(cross_references)}")
        logger.info("Numerical data points extracted: {len(numerical_data)}")
        logger.info("Structured knowledge concepts: {len(structured_knowledge)}")
        
        if connections_summary:
            logger.info("\nMost connected concepts:")
            for concept, count in connections_summary['most_connected_concepts'][:3]:
                logger.info("  {concept}: {count} connections")
        
        return cross_references, numerical_data, structured_knowledge, connections_summary
        
    except Exception as e:
        logger.error(f"Error enriching content: {e}")
        raise

if __name__ == "__main__":
    main() 