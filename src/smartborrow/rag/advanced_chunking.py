#!/usr/bin/env python3
"""
Advanced Chunking Strategies for SmartBorrow

Implements multiple chunking techniques for optimal document processing:
- Semantic chunking
- Hierarchical chunking  
- Overlap chunking
- Metadata-aware chunking
"""

import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from langchain.text_splitter import RecursiveCharacterTextSplitter, TokenTextSplitter
from langchain.schema import Document

@dataclass
class ChunkingConfig:
    """Configuration for advanced chunking strategies"""
    chunk_size: int = 1000
    chunk_overlap: int = 200
    semantic_threshold: float = 0.7
    hierarchical_levels: int = 3
    preserve_metadata: bool = True

class AdvancedChunker:
    """Advanced chunking with multiple strategies"""
    
    def __init__(self, config: ChunkingConfig = ChunkingConfig()):
        self.config = config
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=config.chunk_size,
            chunk_overlap=config.chunk_overlap,
            separators=["\n\n", "\n", ". ", "! ", "? ", " ", ""]
        )
        self.token_splitter = TokenTextSplitter(
            chunk_size=config.chunk_size,
            chunk_overlap=config.chunk_overlap
        )
    
    def semantic_chunking(self, text: str) -> List[Document]:
        """Semantic chunking based on meaning boundaries"""
        # Split by semantic units (paragraphs, sections)
        semantic_units = self._extract_semantic_units(text)
        chunks = []
        
        for unit in semantic_units:
            if len(unit) > self.config.chunk_size:
                # Further split large units
                sub_chunks = self.text_splitter.split_text(unit)
                for i, chunk in enumerate(sub_chunks):
                    chunks.append(Document(
                        page_content=chunk,
                        metadata={
                            "chunk_type": "semantic",
                            "chunk_index": i,
                            "original_length": len(unit)
                        }
                    ))
            else:
                chunks.append(Document(
                    page_content=unit,
                    metadata={"chunk_type": "semantic"}
                ))
        
        return chunks
    
    def hierarchical_chunking(self, text: str) -> List[Document]:
        """Hierarchical chunking with multiple levels"""
        # Extract document structure
        sections = self._extract_sections(text)
        chunks = []
        
        for section in sections:
            # Level 1: Section level
            section_chunk = Document(
                page_content=section["content"],
                metadata={
                    "chunk_type": "hierarchical",
                    "level": 1,
                    "section_title": section.get("title", ""),
                    "section_type": section.get("type", "content")
                }
            )
            chunks.append(section_chunk)
            
            # Level 2: Paragraph level
            paragraphs = self._extract_paragraphs(section["content"])
            for i, para in enumerate(paragraphs):
                if len(para) > 100:  # Only chunk substantial paragraphs
                    para_chunk = Document(
                        page_content=para,
                        metadata={
                            "chunk_type": "hierarchical",
                            "level": 2,
                            "section_title": section.get("title", ""),
                            "paragraph_index": i
                        }
                    )
                    chunks.append(para_chunk)
            
            # Level 3: Sentence level for key information
            sentences = self._extract_sentences(section["content"])
            for i, sentence in enumerate(sentences):
                if self._is_key_sentence(sentence):
                    sentence_chunk = Document(
                        page_content=sentence,
                        metadata={
                            "chunk_type": "hierarchical",
                            "level": 3,
                            "section_title": section.get("title", ""),
                            "sentence_index": i,
                            "key_sentence": True
                        }
                    )
                    chunks.append(sentence_chunk)
        
        return chunks
    
    def overlap_chunking(self, text: str) -> List[Document]:
        """Overlap chunking for better context preservation"""
        # Use sliding window approach
        chunks = []
        words = text.split()
        window_size = self.config.chunk_size // 4  # Approximate word count
        
        for i in range(0, len(words), window_size // 2):  # 50% overlap
            chunk_words = words[i:i + window_size]
            chunk_text = " ".join(chunk_words)
            
            if len(chunk_text) > 50:  # Minimum chunk size
                chunks.append(Document(
                    page_content=chunk_text,
                    metadata={
                        "chunk_type": "overlap",
                        "window_start": i,
                        "window_end": i + window_size,
                        "overlap_ratio": 0.5
                    }
                ))
        
        return chunks
    
    def metadata_aware_chunking(self, text: str, metadata: Dict[str, Any]) -> List[Document]:
        """Chunking that preserves and enhances metadata"""
        # Extract document type and apply specialized chunking
        doc_type = metadata.get("document_type", "general")
        
        if doc_type == "financial_aid":
            return self._financial_aid_chunking(text, metadata)
        elif doc_type == "loan_information":
            return self._loan_info_chunking(text, metadata)
        elif doc_type == "application_process":
            return self._application_chunking(text, metadata)
        else:
            return self.semantic_chunking(text)
    
    def _financial_aid_chunking(self, text: str, metadata: Dict[str, Any]) -> List[Document]:
        """Specialized chunking for financial aid documents"""
        chunks = []
        
        # Extract key financial information
        amounts = re.findall(r'\$[\d,]+(?:\.\d{2})?', text)
        percentages = re.findall(r'\d+(?:\.\d+)?%', text)
        dates = re.findall(r'\d{1,2}/\d{1,2}/\d{4}', text)
        
        # Create chunks with financial context
        semantic_chunks = self.semantic_chunking(text)
        
        for chunk in semantic_chunks:
            # Enhance metadata with financial information
            enhanced_metadata = chunk.metadata.copy()
            enhanced_metadata.update({
                "financial_amounts": amounts,
                "percentages": percentages,
                "dates": dates,
                "document_type": "financial_aid",
                "chunk_strategy": "financial_specialized"
            })
            
            chunks.append(Document(
                page_content=chunk.page_content,
                metadata=enhanced_metadata
            ))
        
        return chunks
    
    def _loan_info_chunking(self, text: str, metadata: Dict[str, Any]) -> List[Document]:
        """Specialized chunking for loan information"""
        chunks = []
        
        # Extract loan-specific information
        loan_types = re.findall(r'(?:Direct|Subsidized|Unsubsidized|PLUS|Private)\s+Loan', text, re.IGNORECASE)
        interest_rates = re.findall(r'interest rate[s]?\s+(?:of\s+)?(\d+(?:\.\d+)?%)', text, re.IGNORECASE)
        
        semantic_chunks = self.semantic_chunking(text)
        
        for chunk in semantic_chunks:
            enhanced_metadata = chunk.metadata.copy()
            enhanced_metadata.update({
                "loan_types": loan_types,
                "interest_rates": interest_rates,
                "document_type": "loan_information",
                "chunk_strategy": "loan_specialized"
            })
            
            chunks.append(Document(
                page_content=chunk.page_content,
                metadata=enhanced_metadata
            ))
        
        return chunks
    
    def _application_chunking(self, text: str, metadata: Dict[str, Any]) -> List[Document]:
        """Specialized chunking for application processes"""
        chunks = []
        
        # Extract step-by-step information
        steps = re.findall(r'(?:Step|Step\s+\d+)[:.]?\s*(.+?)(?=\n|$)', text, re.IGNORECASE)
        requirements = re.findall(r'(?:required|need|must|should)[:.]?\s*(.+?)(?=\n|$)', text, re.IGNORECASE)
        
        semantic_chunks = self.semantic_chunking(text)
        
        for chunk in semantic_chunks:
            enhanced_metadata = chunk.metadata.copy()
            enhanced_metadata.update({
                "process_steps": steps,
                "requirements": requirements,
                "document_type": "application_process",
                "chunk_strategy": "application_specialized"
            })
            
            chunks.append(Document(
                page_content=chunk.page_content,
                metadata=enhanced_metadata
            ))
        
        return chunks
    
    def _extract_semantic_units(self, text: str) -> List[str]:
        """Extract semantic units from text"""
        # Split by paragraphs and sections
        units = re.split(r'\n\s*\n', text)
        return [unit.strip() for unit in units if unit.strip()]
    
    def _extract_sections(self, text: str) -> List[Dict[str, Any]]:
        """Extract document sections"""
        sections = []
        lines = text.split('\n')
        current_section = {"content": "", "title": "", "type": "content"}
        
        for line in lines:
            if re.match(r'^[A-Z][A-Z\s]+$', line.strip()):  # Section header
                if current_section["content"]:
                    sections.append(current_section)
                current_section = {
                    "content": line + "\n",
                    "title": line.strip(),
                    "type": "section"
                }
            else:
                current_section["content"] += line + "\n"
        
        if current_section["content"]:
            sections.append(current_section)
        
        return sections
    
    def _extract_paragraphs(self, text: str) -> List[str]:
        """Extract paragraphs from text"""
        paragraphs = re.split(r'\n\s*\n', text)
        return [p.strip() for p in paragraphs if p.strip()]
    
    def _extract_sentences(self, text: str) -> List[str]:
        """Extract sentences from text"""
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _is_key_sentence(self, sentence: str) -> bool:
        """Determine if sentence contains key information"""
        key_indicators = [
            r'\$[\d,]+',  # Money amounts
            r'\d+%',      # Percentages
            r'(?:important|key|critical|essential)',  # Important words
            r'(?:deadline|due date|limit)',  # Time-sensitive info
            r'(?:maximum|minimum|required)',  # Requirements
        ]
        
        return any(re.search(pattern, sentence, re.IGNORECASE) for pattern in key_indicators)

# Factory function for easy usage
def create_advanced_chunker(config: Optional[ChunkingConfig] = None) -> AdvancedChunker:
    """Create an advanced chunker with optional configuration"""
    if config is None:
        config = ChunkingConfig()
    return AdvancedChunker(config) 