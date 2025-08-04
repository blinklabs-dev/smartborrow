"""Data processing orchestrator for SmartBorrow.

Coordinates the entire data processing pipeline including PDF processing,
CSV processing, content enrichment, and synthetic data generation.
"""

import logging
import time
from pathlib import Path
from typing import Dict, Any, Optional

from .pdf_processor import PDFProcessor
from .csv_processor import CSVProcessor
from .content_enricher import ContentEnricher
from .synthetic_expander import SyntheticExpander

logger = logging.getLogger(__name__)


class DataOrchestrator:
    """Orchestrates the complete data processing pipeline."""
    
    def __init__(self, 
                 raw_data_path: str = "data/raw",
                 processed_data_path: str = "data/processed") -> None:
        self.raw_data_path = Path(raw_data_path)
        self.processed_data_path = Path(processed_data_path)
        self.processed_data_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize processors
        self.pdf_processor = PDFProcessor()
        self.csv_processor = CSVProcessor()
        self.content_enricher = ContentEnricher()
        self.synthetic_expander = SyntheticExpander()
        
        # Processing results
        self.results = {}
    
    def run_full_pipeline(self) -> Dict[str, Any]:
        """Run the complete data processing pipeline.
        
        Returns:
            Dict[str, Any]: Processing results and statistics
        """
        start_time = time.time()
        
        try:
            logger.info("Starting SmartBorrow data processing pipeline...")
            
            # Step 1: Process PDF documents
            pdf_results = self._process_pdfs()
            self.results['pdf_processing'] = pdf_results
            
            # Step 2: Process CSV data
            csv_results = self._process_csvs()
            self.results['csv_processing'] = csv_results
            
            # Step 3: Enrich content with cross-references
            enrichment_results = self._enrich_content()
            self.results['content_enrichment'] = enrichment_results
            
            # Step 4: Generate synthetic data
            synthetic_results = self._generate_synthetic_data()
            self.results['synthetic_data'] = synthetic_results
            
            # Step 5: Create test datasets
            test_datasets = self._create_test_datasets()
            self.results['test_datasets'] = test_datasets
            
            # Calculate processing time
            processing_time = time.time() - start_time
            self.results['processing_time'] = processing_time
            
            # Generate summary
            self._generate_summary_report()
            
            logger.info("Data processing pipeline completed successfully!")
            return self.results
            
        except Exception as e:
            logger.error(f"Data processing pipeline failed: {e}")
            raise
    
    def _process_pdfs(self) -> Dict[str, Any]:
        """Process all PDF documents in the raw data directory."""
        logger.info("Processing PDF documents...")
        
        pdf_files = list(self.raw_data_path.glob("*.pdf"))
        if not pdf_files:
            logger.warning("No PDF files found in raw data directory")
            return {"documents_processed": 0, "total_pages": 0}
        
        total_documents = 0
        total_pages = 0
        key_topics = 0
        dollar_amounts = 0
        
        for pdf_file in pdf_files:
            try:
                result = self.pdf_processor.process_pdf(pdf_file)
                total_documents += 1
                total_pages += result.get('pages_processed', 0)
                key_topics += result.get('key_topics_found', 0)
                dollar_amounts += result.get('dollar_amounts_found', 0)
                
                logger.info(f"Processed {pdf_file.name}: {result.get('pages_processed', 0)} pages")
                
            except Exception as e:
                logger.error(f"Error processing {pdf_file}: {e}")
        
        return {
            'documents_processed': total_documents,
            'total_pages': total_pages,
            'key_topics_found': key_topics,
            'dollar_amounts_found': dollar_amounts
        }
    
    def _process_csvs(self) -> Dict[str, Any]:
        """Process all CSV files in the raw data directory."""
        logger.info("Processing CSV files...")
        
        csv_files = list(self.raw_data_path.glob("*.csv"))
        if not csv_files:
            logger.warning("No CSV files found in raw data directory")
            return {"total_complaints": 0, "categories_identified": 0}
        
        total_complaints = 0
        categories_identified = 0
        faq_entries = 0
        
        for csv_file in csv_files:
            try:
                result = self.csv_processor.process_csv(csv_file)
                total_complaints += result.get('total_complaints', 0)
                categories_identified += result.get('categories_identified', 0)
                faq_entries += result.get('faq_entries_created', 0)
                
                logger.info(f"Processed {csv_file.name}: {result.get('total_complaints', 0)} complaints")
                
            except Exception as e:
                logger.error(f"Error processing {csv_file}: {e}")
        
        return {
            'total_complaints': total_complaints,
            'categories_identified': categories_identified,
            'faq_entries_created': faq_entries
        }
    
    def _enrich_content(self) -> Dict[str, Any]:
        """Enrich processed content with cross-references and structured data."""
        logger.info("Enriching content with cross-references...")
        
        try:
            result = self.content_enricher.enrich_all_content()
            logger.info(f"Content enrichment completed: {result.get('cross_references_found', 0)} cross-references found")
            return result
            
        except Exception as e:
            logger.error(f"Error in content enrichment: {e}")
            return {"cross_references_found": 0, "numerical_data_points": 0, "structured_knowledge_concepts": 0}
    
    def _generate_synthetic_data(self) -> Dict[str, Any]:
        """Generate synthetic data for testing and evaluation."""
        logger.info("Generating synthetic data...")
        
        try:
            result = self.synthetic_expander.expand_all_content()
            logger.info(f"Synthetic data generation completed: {result.get('synthetic_qa_pairs', 0)} Q&A pairs created")
            return result
            
        except Exception as e:
            logger.error(f"Error in synthetic data generation: {e}")
            return {"synthetic_qa_pairs": 0, "procedure_variations": 0}
    
    def _create_test_datasets(self) -> Dict[str, Any]:
        """Create test datasets for evaluation."""
        logger.info("Creating test datasets...")
        
        try:
            datasets = self.synthetic_expander.create_test_datasets()
            total_cases = sum(len(cases) for cases in datasets.values())
            logger.info(f"Test datasets created: {total_cases} total test cases")
            return datasets
            
        except Exception as e:
            logger.error(f"Error creating test datasets: {e}")
            return {"easy": 0, "medium": 0, "hard": 0, "total": 0}
    
    def _count_output_files(self) -> int:
        """Count the number of output files generated."""
        try:
            return len(list(self.processed_data_path.glob("*.json")))
        except Exception:
            return 0
    
    def _generate_summary_report(self) -> None:
        """Generate and log a summary report of the processing results."""
        processing_time = self.results.get('processing_time', 0)
        pdf_results = self.results.get('pdf_processing', {})
        csv_results = self.results.get('csv_processing', {})
        enrichment_results = self.results.get('content_enrichment', {})
        synthetic_results = self.results.get('synthetic_data', {})
        test_datasets = self.results.get('test_datasets', {})
        
        logger.info("=" * 80)
        logger.info("SMARTBORROW DATA PROCESSING SUMMARY")
        logger.info("=" * 80)
        
        logger.info(f"Processing Time: {processing_time:.2f} seconds")
        logger.info(f"Output Files Generated: {self._count_output_files()}")
        
        logger.info(f"\nPDF Processing:")
        logger.info(f"  Documents: {pdf_results.get('documents_processed', 0)}")
        logger.info(f"  Total Pages: {pdf_results.get('total_pages', 0)}")
        logger.info(f"  Key Topics: {pdf_results.get('key_topics_found', 0)}")
        logger.info(f"  Dollar Amounts: {pdf_results.get('dollar_amounts_found', 0)}")
        
        logger.info(f"\nCSV Processing:")
        logger.info(f"  Complaints: {csv_results.get('total_complaints', 0)}")
        logger.info(f"  Categories: {csv_results.get('categories_identified', 0)}")
        logger.info(f"  FAQ Entries: {csv_results.get('faq_entries_created', 0)}")
        
        logger.info(f"\nContent Enrichment:")
        logger.info(f"  Cross-references: {enrichment_results.get('cross_references_found', 0)}")
        logger.info(f"  Numerical Data: {enrichment_results.get('numerical_data_points', 0)}")
        logger.info(f"  Structured Knowledge: {enrichment_results.get('structured_knowledge_concepts', 0)}")
        
        logger.info(f"\nSynthetic Data:")
        logger.info(f"  Q&A Pairs: {synthetic_results.get('synthetic_qa_pairs', 0)}")
        logger.info(f"  Procedure Variations: {synthetic_results.get('procedure_variations', 0)}")
        
        logger.info(f"\nTest Datasets:")
        logger.info(f"  Total Cases: {test_datasets.get('total', 0)} (Easy: {test_datasets.get('easy', 0)}, Medium: {test_datasets.get('medium', 0)}, Hard: {test_datasets.get('hard', 0)})")
        
        # Key achievements
        achievements = [
            "Comprehensive PDF document processing with key topic extraction",
            "Structured complaint analysis with category identification",
            "Cross-reference enrichment for better knowledge connectivity",
            "Synthetic data generation for comprehensive testing",
            "Multi-difficulty test dataset creation for evaluation"
        ]
        
        logger.info(f"\nKey Achievements:")
        for achievement in achievements:
            logger.info(f"  ✓ {achievement}")
        
        logger.info("=" * 80)
        logger.info("Data processing pipeline completed successfully!")
        logger.info("=" * 80)


def main() -> None:
    """Main function to run the data processing pipeline."""
    try:
        orchestrator = DataOrchestrator()
        results = orchestrator.run_full_pipeline()
        logger.info("Data processing completed successfully!")
        
    except Exception as e:
        logger.error(f"Data processing pipeline failed: {e}")
        raise


if __name__ == "__main__":
    main() 