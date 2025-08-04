# SmartBorrow Data Processing

Comprehensive data processing for SmartBorrow using the 5 files in `data/raw/`.

## Overview

This module provides intelligent data processing for SmartBorrow, focusing on deep processing of limited but high-quality data sources. The pipeline processes 4 PDF documents and 1 CSV file to create rich, structured knowledge for better retrieval and understanding.

## Data Sources

### PDF Documents (4 files)
- `The_Federal_Pell_Grant_Program.pdf` - Pell Grant guidelines and procedures
- `The_Direct_Loan_Program.pdf` - Direct Loan program information
- `Applications_and_Verification_Guide.pdf` - Application and verification processes
- `Academic_Calenders_Cost_of_Attendance_and_Packaging.pdf` - Academic calendar and cost information

### CSV Data (1 file)
- `complaints.csv` - Student loan complaint data with narratives and metadata

## Processing Pipeline

### 1. PDF Processor (`pdf_processor.py`)

**Purpose**: Extract comprehensive information from PDF documents

**Features**:
- Text extraction with page-by-page processing
- Metadata extraction (document type, sections, page numbers)
- Key information identification (procedures, requirements, dollar amounts, dates)
- Rich metadata creation for better retrieval
- Section identification and topic extraction

**Output**:
- Extracted text files
- Metadata JSON files
- Processing summary with statistics

### 2. CSV Processor (`csv_processor.py`)

**Purpose**: Analyze complaint patterns and create FAQ-style data

**Features**:
- Complaint categorization by type (payment issues, servicer problems, etc.)
- Common keyword and pain point extraction
- FAQ generation from common complaints
- Pattern analysis and trend identification
- Response time analysis

**Output**:
- Complaint categories with analysis
- FAQ entries derived from complaints
- Overall complaint analysis and statistics

### 3. Content Enricher (`content_enricher.py`)

**Purpose**: Cross-reference information and build structured knowledge

**Features**:
- Cross-reference information between PDFs
- Extract numerical data (interest rates, limits, deadlines)
- Build structured knowledge from unstructured PDFs
- Create connections between related concepts
- Identify relationships between documents

**Output**:
- Cross-reference mappings
- Numerical data extraction
- Structured knowledge base
- Connection summaries

### 4. Synthetic Expander (`synthetic_expander.py`)

**Purpose**: Generate additional data and test datasets

**Features**:
- Generate additional Q&A pairs from PDF content
- Create variations of procedures and requirements
- Expand complaint categories with similar scenarios
- Build test datasets from existing content
- Create synthetic training data

**Output**:
- Synthetic Q&A pairs
- Procedure and requirement variations
- Expanded complaint categories
- Test datasets (easy, medium, hard)

## Usage

### Quick Start

Run the complete pipeline:

```bash
cd src/smartborrow/data
python orchestrator.py
```

### Individual Processors

Run individual processors:

```python
# PDF Processing
from smartborrow.data.pdf_processor import PDFProcessor
processor = PDFProcessor()
all_metadata, summary = processor.process_all_pdfs()

# CSV Processing
from smartborrow.data.csv_processor import CSVProcessor
processor = CSVProcessor()
categories, faq_entries, analysis = processor.process_complaints()

# Content Enrichment
from smartborrow.data.content_enricher import ContentEnricher
enricher = ContentEnricher()
cross_refs, numerical_data, structured_knowledge, connections = enricher.enrich_content()

# Synthetic Expansion
from smartborrow.data.synthetic_expander import SyntheticExpander
expander = SyntheticExpander()
qa_pairs, variations, categories, test_datasets = expander.expand_content()
```

## Output Structure

All processed data is saved to `data/processed/`:

```
data/processed/
├── *_metadata.json          # PDF metadata
├── *_text.txt              # Extracted PDF text
├── complaint_categories.json # Complaint analysis
├── complaint_faqs.json      # Generated FAQs
├── complaint_analysis.json  # Overall complaint stats
├── cross_references.json    # Document cross-references
├── numerical_data.json      # Extracted numerical data
├── structured_knowledge.json # Structured knowledge base
├── connections_summary.json # Connection analysis
├── synthetic_qa_pairs.json  # Generated Q&A pairs
├── procedure_variations.json # Procedure variations
├── expanded_categories.json # Expanded complaint categories
├── test_datasets.json       # Test datasets
└── pdf_processing_summary.json # PDF processing summary
```

## Key Features

### Deep Processing Focus
- Extracts rich metadata from limited sources
- Identifies key topics and concepts
- Creates structured knowledge from unstructured data
- Builds comprehensive FAQ systems

### Cross-Referencing
- Links information between documents
- Identifies related concepts and procedures
- Creates knowledge graphs from PDF content
- Maps numerical data across documents

### Synthetic Data Generation
- Creates additional Q&A pairs
- Generates procedure variations
- Expands complaint scenarios
- Builds test datasets for evaluation

### Comprehensive Analysis
- Analyzes complaint patterns and trends
- Identifies common pain points
- Extracts numerical data (amounts, dates, rates)
- Creates structured knowledge bases

## Dependencies

Install required dependencies:

```bash
pip install -r requirements.txt
```

Key dependencies:
- `PyPDF2` - PDF text extraction
- `pdfplumber` - Advanced PDF processing
- `pandas` - CSV data analysis
- `numpy` - Numerical operations

## Configuration

The processors use default paths but can be configured:

```python
# Custom paths
processor = PDFProcessor(raw_data_path="custom/raw/path")
processor = CSVProcessor(raw_data_path="custom/raw/path")
```

## Performance

The pipeline is designed for:
- **Efficiency**: Processes 5 files in under 2 minutes
- **Accuracy**: Deep analysis of content with high precision
- **Scalability**: Modular design for easy extension
- **Reliability**: Comprehensive error handling and logging

## Extensibility

The modular design allows easy extension:

1. **Add new document types**: Extend PDF processor for new formats
2. **New analysis types**: Add processors for different data sources
3. **Custom enrichment**: Create specialized content enrichers
4. **Additional synthetic data**: Extend the synthetic expander

## Troubleshooting

### Common Issues

1. **PDF Processing Errors**: Ensure PDFs are not password-protected
2. **Missing Dependencies**: Install all requirements with `pip install -r requirements.txt`
3. **Path Issues**: Verify data files are in `data/raw/` directory
4. **Memory Issues**: Large PDFs may require more memory

### Debug Mode

Enable detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Contributing

To extend the data processing:

1. Follow the existing module structure
2. Add comprehensive error handling
3. Include detailed logging
4. Create appropriate data classes
5. Add unit tests for new functionality

## License

This module is part of the SmartBorrow project and follows the same licensing terms. 