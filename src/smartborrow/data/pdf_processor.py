"""
PDF Processor for SmartBorrow

Extracts text, metadata, and key information from PDF documents.
Handles the 4 PDF files in data/raw/ directory.
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import logging

try:
    import PyPDF2
    import pdfplumber
except ImportError:
    logger.info("Installing required PDF processing libraries...")
    import subprocess
    subprocess.check_call(["pip", "install", "PyPDF2", "pdfplumber"])
    import PyPDF2
    import pdfplumber

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class PDFMetadata:
    """Metadata extracted from PDF documents"""
    document_type: str
    title: str
    page_count: int
    file_size: int
    extraction_date: str
    sections: List[str]
    key_topics: List[str]
    numerical_data: Dict[str, Any]
    dates: List[str]
    dollar_amounts: List[str]

class PDFProcessor:
    """Comprehensive PDF processing for SmartBorrow documents"""
    
    def __init__(self, raw_data_path: str = "data/raw") -> None:
        self.raw_data_path = Path(raw_data_path)
        self.processed_data_path = Path("data/processed")
        self.processed_data_path.mkdir(exist_ok=True)
        
        # Document type mappings
        self.doc_type_mapping = {
            "The_Federal_Pell_Grant_Program.pdf": "pell_grant_guide",
            "The_Direct_Loan_Program.pdf": "direct_loan_guide", 
            "Applications_and_Verification_Guide.pdf": "application_verification_guide",
            "Academic_Calenders_Cost_of_Attendance_and_Packaging.pdf": "academic_calendar_cost_guide"
        }
        
        # Key information patterns
        self.dollar_pattern = r'\$[\d,]+(?:\.\d{2})?'
        self.date_pattern = r'\b\d{1,2}/\d{1,2}/\d{2,4}\b'
        self.percentage_pattern = r'\d+(?:\.\d+)?%'
        self.amount_pattern = r'\$\d+(?:,\d{3})*(?:\.\d{2})?'
        
    def get_pdf_files(self) -> List[Path]:
        """Get all PDF files from raw data directory"""
        pdf_files = list(self.raw_data_path.glob("*.pdf"))
        logger.info(f"Found {len(pdf_files)} PDF files: {[f.name for f in pdf_files]}")
        return pdf_files
    
    def extract_text_with_pdfplumber(self, pdf_path: Path) -> Tuple[str, int]:
        """Extract text using pdfplumber for better formatting"""
        try:
            text_content = []
            page_count = 0
            
            with pdfplumber.open(pdf_path) as pdf:
                page_count = len(pdf.pages)
                
                for page_num, page in enumerate(pdf.pages, 1):
                    page_text = page.extract_text()
                    if page_text:
                        text_content.append(f"--- PAGE {page_num} ---\n{page_text}\n")
                    else:
                        text_content.append(f"--- PAGE {page_num} --- [No text extracted]\n")
            
            return "\n".join(text_content), page_count
            
        except Exception as e:
            logger.error(f"Error extracting text from {pdf_path}: {e}")
            return "", 0
    
    def extract_metadata(self, pdf_path: Path) -> Dict[str, Any]:
        """Extract basic PDF metadata"""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                metadata = {
                    'file_name': pdf_path.name,
                    'file_size': pdf_path.stat().st_size,
                    'page_count': len(pdf_reader.pages),
                    'document_type': self.doc_type_mapping.get(pdf_path.name, "unknown"),
                    'extraction_date': datetime.now().isoformat()
                }
                
                # Try to get PDF info
                if pdf_reader.metadata:
                    metadata.update({
                        'title': pdf_reader.metadata.get('/Title', ''),
                        'author': pdf_reader.metadata.get('/Author', ''),
                        'subject': pdf_reader.metadata.get('/Subject', ''),
                        'creator': pdf_reader.metadata.get('/Creator', '')
                    })
                
                return metadata
                
        except Exception as e:
            logger.error(f"Error extracting metadata from {pdf_path}: {e}")
            return {}
    
    def identify_sections(self, text: str) -> List[str]:
        """Identify document sections based on headers and structure"""
        sections = []
        
        # Common section patterns
        section_patterns = [
            r'^[A-Z][A-Z\s]{3,}$',  # ALL CAPS headers
            r'^[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*$',  # Title Case headers
            r'^\d+\.\s+[A-Z][a-z]',  # Numbered sections
            r'^[A-Z][A-Z\s]+:$',  # ALL CAPS with colon
        ]
        
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if len(line) > 3 and len(line) < 100:  # Reasonable header length
                for pattern in section_patterns:
                    if re.match(pattern, line):
                        sections.append(line)
                        break
        
        return list(set(sections))  # Remove duplicates
    
    def extract_numerical_data(self, text: str) -> Dict[str, Any]:
        """Extract numerical data including dollar amounts, percentages, dates"""
        numerical_data = {
            'dollar_amounts': [],
            'percentages': [],
            'dates': [],
            'amounts': []
        }
        
        # Extract dollar amounts
        dollar_matches = re.findall(self.dollar_pattern, text)
        numerical_data['dollar_amounts'] = list(set(dollar_matches))
        
        # Extract percentages
        percentage_matches = re.findall(self.percentage_pattern, text)
        numerical_data['percentages'] = list(set(percentage_matches))
        
        # Extract dates
        date_matches = re.findall(self.date_pattern, text)
        numerical_data['dates'] = list(set(date_matches))
        
        # Extract general amounts
        amount_matches = re.findall(self.amount_pattern, text)
        numerical_data['amounts'] = list(set(amount_matches))
        
        return numerical_data
    
    def identify_key_topics(self, text: str) -> List[str]:
        """Identify key topics and themes in the document"""
        key_topics = []
        
        # Financial aid related keywords
        financial_keywords = [
            'pell grant', 'direct loan', 'federal student aid', 'fafsa',
            'cost of attendance', 'expected family contribution', 'efc',
            'subsidized loan', 'unsubsidized loan', 'parent plus loan',
            'income-driven repayment', 'forbearance', 'deferment',
            'loan forgiveness', 'discharge', 'default'
        ]
        
        # Application and verification keywords
        application_keywords = [
            'application', 'verification', 'documentation', 'proof',
            'income verification', 'tax return', 'w-2', 'pay stub',
            'dependency status', 'independent student', 'dependent student'
        ]
        
        # Academic calendar keywords
        academic_keywords = [
            'academic year', 'semester', 'quarter', 'term',
            'enrollment period', 'registration', 'drop/add',
            'withdrawal', 'graduation', 'academic calendar'
        ]
        
        text_lower = text.lower()
        
        # Check for financial keywords
        for keyword in financial_keywords:
            if keyword in text_lower:
                key_topics.append(keyword.replace('_', ' ').title())
        
        # Check for application keywords
        for keyword in application_keywords:
            if keyword in text_lower:
                key_topics.append(keyword.replace('_', ' ').title())
        
        # Check for academic keywords
        for keyword in academic_keywords:
            if keyword in text_lower:
                key_topics.append(keyword.replace('_', ' ').title())
        
        return list(set(key_topics))
    
    def extract_procedures_and_requirements(self, text: str) -> Dict[str, List[str]]:
        """Extract procedures and requirements from text"""
        procedures = []
        requirements = []
        
        # Look for procedure indicators
        procedure_indicators = [
            'procedure', 'process', 'step', 'how to', 'instructions',
            'follow these', 'complete the', 'submit', 'apply'
        ]
        
        # Look for requirement indicators
        requirement_indicators = [
            'requirement', 'must', 'required', 'necessary', 'eligible',
            'qualify', 'criteria', 'condition', 'prerequisite'
        ]
        
        sentences = re.split(r'[.!?]+', text)
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 10:
                continue
                
            sentence_lower = sentence.lower()
            
            # Check for procedures
            for indicator in procedure_indicators:
                if indicator in sentence_lower:
                    procedures.append(sentence)
                    break
            
            # Check for requirements
            for indicator in requirement_indicators:
                if indicator in sentence_lower:
                    requirements.append(sentence)
                    break
        
        return {
            'procedures': list(set(procedures)),
            'requirements': list(set(requirements))
        }
    
    def process_pdf(self, pdf_path: Path) -> PDFMetadata:
        """Process a single PDF file and extract comprehensive information"""
        logger.info(f"Processing PDF: {pdf_path.name}")
        
        # Extract text
        text_content, page_count = self.extract_text_with_pdfplumber(pdf_path)
        
        # Extract metadata
        metadata = self.extract_metadata(pdf_path)
        
        # Identify sections
        sections = self.identify_sections(text_content)
        
        # Extract numerical data
        numerical_data = self.extract_numerical_data(text_content)
        
        # Identify key topics
        key_topics = self.identify_key_topics(text_content)
        
        # Extract procedures and requirements
        procedures_reqs = self.extract_procedures_and_requirements(text_content)
        
        # Create PDFMetadata object
        pdf_metadata = PDFMetadata(
            document_type=metadata.get('document_type', 'unknown'),
            title=metadata.get('title', pdf_path.name),
            page_count=page_count,
            file_size=metadata.get('file_size', 0),
            extraction_date=metadata.get('extraction_date', ''),
            sections=sections,
            key_topics=key_topics,
            numerical_data=numerical_data,
            dates=numerical_data['dates'],
            dollar_amounts=numerical_data['dollar_amounts']
        )
        
        return pdf_metadata
    
    def save_processed_data(self, pdf_metadata: PDFMetadata, text_content: str) -> None:
        """Save processed data to JSON and text files"""
        # Create filename without extension
        base_name = pdf_metadata.title.replace(' ', '_').lower()
        
        # Save metadata as JSON
        metadata_file = self.processed_data_path / f"{base_name}_metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump({
                'document_type': pdf_metadata.document_type,
                'title': pdf_metadata.title,
                'page_count': pdf_metadata.page_count,
                'file_size': pdf_metadata.file_size,
                'extraction_date': pdf_metadata.extraction_date,
                'sections': pdf_metadata.sections,
                'key_topics': pdf_metadata.key_topics,
                'numerical_data': pdf_metadata.numerical_data,
                'dates': pdf_metadata.dates,
                'dollar_amounts': pdf_metadata.dollar_amounts
            }, f, indent=2)
        
        # Save extracted text
        text_file = self.processed_data_path / f"{base_name}_text.txt"
        with open(text_file, 'w', encoding='utf-8') as f:
            f.write(text_content)
        
        logger.info(f"Saved processed data to {metadata_file} and {text_file}")
    
    def process_all_pdfs(self) -> Dict[str, PDFMetadata]:
        """Process all PDF files and return comprehensive metadata"""
        pdf_files = self.get_pdf_files()
        all_metadata = {}
        
        for pdf_path in pdf_files:
            try:
                # Process the PDF
                pdf_metadata = self.process_pdf(pdf_path)
                
                # Extract text for saving
                text_content, _ = self.extract_text_with_pdfplumber(pdf_path)
                
                # Save processed data
                self.save_processed_data(pdf_metadata, text_content)
                
                # Store metadata
                all_metadata[pdf_path.name] = pdf_metadata
                
                logger.info(f"Successfully processed {pdf_path.name}")
                
            except Exception as e:
                logger.error(f"Error processing {pdf_path.name}: {e}")
        
        return all_metadata
    
    def generate_summary_report(self, all_metadata: Dict[str, PDFMetadata]) -> Dict[str, Any]:
        """Generate a comprehensive summary report of all processed PDFs"""
        summary = {
            'total_documents': len(all_metadata),
            'total_pages': sum(md.page_count for md in all_metadata.values()),
            'total_file_size': sum(md.file_size for md in all_metadata.values()),
            'document_types': list(set(md.document_type for md in all_metadata.values())),
            'all_sections': [],
            'all_key_topics': [],
            'all_dollar_amounts': [],
            'all_dates': [],
            'documents': {}
        }
        
        for filename, metadata in all_metadata.items():
            summary['all_sections'].extend(metadata.sections)
            summary['all_key_topics'].extend(metadata.key_topics)
            summary['all_dollar_amounts'].extend(metadata.dollar_amounts)
            summary['all_dates'].extend(metadata.dates)
            
            summary['documents'][filename] = {
                'document_type': metadata.document_type,
                'title': metadata.title,
                'page_count': metadata.page_count,
                'key_topics': metadata.key_topics,
                'sections_count': len(metadata.sections),
                'dollar_amounts_count': len(metadata.dollar_amounts),
                'dates_count': len(metadata.dates)
            }
        
        # Remove duplicates
        summary['all_sections'] = list(set(summary['all_sections']))
        summary['all_key_topics'] = list(set(summary['all_key_topics']))
        summary['all_dollar_amounts'] = list(set(summary['all_dollar_amounts']))
        summary['all_dates'] = list(set(summary['all_dates']))
        
        return summary

def main() -> None:
    """Main function to process all PDFs"""
    processor = PDFProcessor()
    
    logger.info("Starting PDF processing...")
    
    # Process all PDFs
    all_metadata = processor.process_all_pdfs()
    
    # Generate summary report
    summary = processor.generate_summary_report(all_metadata)
    
    # Save summary report
    summary_file = processor.processed_data_path / "pdf_processing_summary.json"
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    logger.info(f"PDF processing complete. Summary saved to {summary_file}")
    logger.info(f"Processed {summary['total_documents']} documents with {summary['total_pages']} total pages")
    
    return all_metadata, summary

if __name__ == "__main__":
    main() 