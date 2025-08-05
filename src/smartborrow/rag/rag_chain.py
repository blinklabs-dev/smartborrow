"""
RAG Chain for SmartBorrow

LangChain LCEL chain for question answering using processed
Q&A pairs and numerical data context with source citation.
"""

import os
import logging
from typing import List, Dict, Any, Optional
from langchain.schema import Document
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, PromptTemplate
from langchain.schema.runnable import RunnablePassthrough
from langchain.schema.output_parser import StrOutputParser
from dotenv import load_dotenv
from langchain.chains import LLMChain

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class SmartBorrowRAGChain:
    """RAG chain for SmartBorrow question answering"""
    
    def __init__(self):
        """Initialize RAG chain with comprehensive prompts"""
        self.llm = ChatOpenAI(
            model_name=os.getenv("OPENAI_MODEL_NAME", "gpt-3.5-turbo"),
            temperature=0.1,
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
        
        # Initialize chains with comprehensive prompts
        self.qa_chain = self._create_qa_chain()
        self.qa_with_sources_chain = self._create_qa_with_sources_chain()
        
        # Initialize other components
        self.numerical_context_chain = self._create_numerical_context_chain()
        self.confidence_chain = self._create_confidence_chain()
    
    def _create_qa_prompt(self, question: str, context: str) -> str:
        """Create an optimized QA prompt for best performance/quality balance"""
        return f"""You are a financial aid expert. Answer this question clearly and accurately:

Context: {context}
Question: {question}

Provide a clear, well-formatted answer with:
- Direct response to the question
- Key details and requirements
- Important notes if relevant

IMPORTANT FORMATTING:
- Use bullet points (•) for lists with each bullet on a new line
- Use bold text (**text**) for important information
- Add line breaks between sections
- Structure your response with clear paragraphs
- Make it easy to read and scan
- End with "**Sources:**" in bold on a new line

Avoid template placeholders like {{rate}}. Use actual information or say "not specified".

Answer:"""

    def _create_qa_with_sources_prompt(self, question: str, context: str) -> str:
        """Create an optimized QA prompt with sources for best performance/quality balance"""
        return f"""You are a financial aid expert. Answer this question clearly and accurately:

Context: {context}
Question: {question}

Provide a clear, well-formatted answer with:
- Direct response to the question
- Key details and requirements
- Important notes if relevant

IMPORTANT FORMATTING:
- Use bullet points (•) for lists with each bullet on a new line
- Use bold text (**text**) for important information
- Add line breaks between sections
- Structure your response with clear paragraphs
- Make it easy to read and scan
- End with "**Sources:**" in bold on a new line

Avoid template placeholders like {{rate}}. Use actual information or say "not specified".

Answer:"""
    
    def _create_numerical_context_prompt(self) -> ChatPromptTemplate:
        """Create prompt for numerical data context"""
        template = """You are analyzing numerical data for SmartBorrow. 

Context: {context}

Extract and summarize the key numerical information (amounts, rates, limits, dates) from the context. 
Format the information clearly and include the units where applicable.

Numerical Summary:"""

        return ChatPromptTemplate.from_template(template)
    
    def _create_qa_chain(self):
        """Create QA chain with comprehensive prompts"""
        return self.llm
    
    def _create_qa_with_sources_chain(self):
        """Create QA with sources chain with comprehensive prompts"""
        return self.llm
    
    def _create_numerical_context_chain(self):
        """Create numerical context chain"""
        return self.llm
    
    def _create_confidence_chain(self):
        """Create confidence assessment chain"""
        return self.llm
    
    def answer_question(self, 
                       question: str, 
                       documents: List[Document],
                       include_sources: bool = True) -> Dict[str, Any]:
        """Answer question using comprehensive prompts with proper interface"""
        try:
            if not documents:
                return {
                    "answer": "I don't have enough information to answer this question. Please try rephrasing or ask about a different topic.",
                    "sources": [],
                    "confidence": "low"
                }
            
            # Prepare context from documents
            context = self._prepare_context(documents)
            
            # Get numerical context if relevant
            numerical_context = self._extract_numerical_context(documents)
            
            # Combine context
            full_context = context
            if numerical_context:
                full_context += f"\n\nNumerical Data Context:\n{numerical_context}"
            
            # Create comprehensive prompt
            if include_sources:
                prompt = self._create_qa_with_sources_prompt(question, full_context)
            else:
                prompt = self._create_qa_prompt(question, full_context)
            
            # Generate response using LLM
            response = self.llm.invoke(prompt)
            
            # Extract sources
            sources = self._extract_sources(documents)
            
            # Determine confidence based on document relevance
            confidence = self._determine_confidence(documents, question)
            
            # Clean up any template placeholders
            cleaned_response = self._clean_template_placeholders(response.content)
            
            return {
                "answer": cleaned_response,
                "sources": sources,
                "confidence": confidence,
                "documents_used": len(documents)
            }
            
        except Exception as e:
            logger.error(f"Error in answer_question: {e}")
            return {
                "answer": "I encountered an error while processing your question. Please try again.",
                "sources": [],
                "confidence": "error"
            }
    
    def _prepare_context(self, documents: List[Document]) -> str:
        """Prepare comprehensive context from documents"""
        if not documents:
            return ""
        
        # Sort documents by relevance score if available
        sorted_docs = sorted(documents, key=lambda x: getattr(x, 'metadata', {}).get('score', 0), reverse=True)
        
        context_parts = []
        max_context_length = 6000  # Increased for more comprehensive context
        current_length = 0
        
        for doc in sorted_docs:
            # Extract comprehensive information from document
            content = doc.page_content
            metadata = doc.metadata
            
            # Add metadata information for better context
            metadata_info = []
            if metadata.get('document_type'):
                metadata_info.append(f"Type: {metadata['document_type']}")
            if metadata.get('category'):
                metadata_info.append(f"Category: {metadata['category']}")
            if metadata.get('confidence'):
                metadata_info.append(f"Confidence: {metadata['confidence']}")
            
            # Create comprehensive document entry
            doc_entry = f"Document Content:\n{content}"
            if metadata_info:
                doc_entry += f"\nMetadata: {', '.join(metadata_info)}"
            
            # Check if adding this document would exceed context limit
            if current_length + len(doc_entry) > max_context_length:
                break
            
            context_parts.append(doc_entry)
            current_length += len(doc_entry)
        
        return "\n\n---\n\n".join(context_parts)
    
    def _extract_numerical_context(self, documents: List[Document]) -> str:
        """Extract comprehensive numerical context from documents"""
        numerical_data = []
        
        for doc in documents:
            content = doc.page_content
            metadata = doc.metadata
            
            # Extract numerical information
            import re
            
            # Find amounts, percentages, dates, etc.
            amounts = re.findall(r'\$[\d,]+(?:\.\d{2})?', content)
            percentages = re.findall(r'\d+(?:\.\d+)?%', content)
            years = re.findall(r'20\d{2}', content)
            rates = re.findall(r'\d+(?:\.\d+)?%?\s*(?:rate|interest)', content, re.IGNORECASE)
            
            if amounts or percentages or years or rates:
                numerical_entry = f"Document: {metadata.get('document_type', 'Unknown')}"
                if amounts:
                    numerical_entry += f"\nAmounts: {', '.join(amounts)}"
                if percentages:
                    numerical_entry += f"\nPercentages: {', '.join(percentages)}"
                if years:
                    numerical_entry += f"\nYears: {', '.join(years)}"
                if rates:
                    numerical_entry += f"\nRates: {', '.join(rates)}"
                
                numerical_data.append(numerical_entry)
        
        if numerical_data:
            return "Numerical Data Summary:\n" + "\n\n".join(numerical_data)
        return ""
    
    def _extract_sources(self, documents: List[Document]) -> List[Dict[str, Any]]:
        """Extract source information from documents"""
        sources = []
        
        for doc in documents:
            metadata = doc.metadata
            source_info = {
                "document_type": metadata.get('document_type', 'unknown'),
                "category": metadata.get('category', 'unknown'),
                "source_type": metadata.get('source_type', 'unknown'),
                "content_type": metadata.get('content_type', 'general'),
                "concept": metadata.get('concept', ''),
                "confidence": metadata.get('confidence', 0.8),
                "content": doc.page_content  # Add the actual document content
            }
            
            # Add specific metadata based on document type
            if metadata.get('document_type') == 'knowledge_base':
                source_info["concept"] = metadata.get('concept', '')
                source_info["source_documents"] = metadata.get('source_documents', [])
            
            elif metadata.get('document_type') == 'qa_pairs':
                source_info["confidence"] = metadata.get('confidence', 0.8)
                source_info["variations"] = metadata.get('variations', [])
            
            elif metadata.get('document_type') == 'complaints':
                source_info["complaint_count"] = metadata.get('complaint_count', 0)
                source_info["percentage"] = metadata.get('percentage', 0)
            
            sources.append(source_info)
        
        return sources
    
    def _determine_confidence(self, documents: List[Document], question: str) -> str:
        """Determine confidence level based on document relevance"""
        if not documents:
            return "low"
        
        # Check for exact matches in content
        question_lower = question.lower()
        exact_matches = 0
        
        for doc in documents:
            content_lower = doc.page_content.lower()
            if any(word in content_lower for word in question_lower.split()):
                exact_matches += 1
        
        # Check metadata relevance
        metadata_matches = 0
        for doc in documents:
            metadata = doc.metadata
            if metadata.get('category') and any(word in metadata['category'].lower() for word in question_lower.split()):
                metadata_matches += 1
        
        # Determine confidence
        total_docs = len(documents)
        if exact_matches >= total_docs * 0.7 or metadata_matches >= total_docs * 0.8:
            return "high"
        elif exact_matches >= total_docs * 0.3 or metadata_matches >= total_docs * 0.5:
            return "medium"
        else:
            return "low"
    
    def answer_with_filtering(self, 
                            question: str,
                            documents: List[Document],
                            document_types: Optional[List[str]] = None,
                            categories: Optional[List[str]] = None) -> Dict[str, Any]:
        """Answer question with document filtering"""
        # Filter documents if filters are provided
        filtered_docs = documents
        
        if document_types:
            filtered_docs = [doc for doc in filtered_docs 
                           if doc.metadata.get('document_type') in document_types]
        
        if categories:
            filtered_docs = [doc for doc in filtered_docs 
                           if doc.metadata.get('category') in categories]
        
        if not filtered_docs:
            return {
                "answer": f"No relevant documents found for the specified filters. Document types: {document_types}, Categories: {categories}",
                "sources": [],
                "confidence": "low",
                "filtered": True
            }
        
        return self.answer_question(question, filtered_docs, include_sources=True)
    
    def get_numerical_summary(self, documents: List[Document]) -> str:
        """Get a summary of numerical data from documents"""
        try:
            numerical_context = self._extract_numerical_context(documents)
            
            if not numerical_context:
                return "No numerical data found in the retrieved documents."
            
            # Use modern LCEL for numerical summary
            numerical_chain = self.numerical_context_prompt | self.llm | StrOutputParser()
            response = numerical_chain.invoke({"context": numerical_context})
            
            return response
            
        except Exception as e:
            logger.error(f"Error in get_numerical_summary: {e}")
            return "Error extracting numerical summary."
    
    def _clean_template_placeholders(self, text: str) -> str:
        """Clean up template placeholders from response text"""
        import re
        
        # Common template placeholders to replace
        placeholder_replacements = {
            r'\{rate\}': 'the current rate',
            r'\{amount\}': 'the specific amount',
            r'\{year\}': 'the current year',
            r'\{percentage\}': 'the percentage',
            r'\{limit\}': 'the limit',
            r'\{value\}': 'the value',
            r'\{date\}': 'the date',
            r'\{time\}': 'the time'
        }
        
        cleaned_text = text
        
        for placeholder, replacement in placeholder_replacements.items():
            cleaned_text = re.sub(placeholder, replacement, cleaned_text, flags=re.IGNORECASE)
        
        # If we still have any remaining {something} patterns, replace them
        cleaned_text = re.sub(r'\{[^}]+\}', 'the specific value', cleaned_text)
        
        return cleaned_text

def main() -> None:
    """Test the RAG chain"""
    from smartborrow.rag.document_loader import SmartBorrowDocumentLoader
    from smartborrow.rag.vector_store import SmartBorrowVectorStore
    
    # Load documents
    loader = SmartBorrowDocumentLoader()
    processed_docs = loader.load_processed_data()
    documents = loader.create_langchain_documents(processed_docs)
    
    # Create vector store
    vectorstore = SmartBorrowVectorStore()
    vs = vectorstore.create_vectorstore(documents)
    
    # Create RAG chain
    rag_chain = SmartBorrowRAGChain()
    
    # Test questions
    test_questions = [
        "What is the maximum Pell Grant amount?",
        "How do I qualify for a Pell Grant?",
        "What are the current interest rates for Direct Loans?",
        "What are the most common student loan complaints?"
    ]
    
    for question in test_questions:
        logger.info("\n{'='*60}")
        logger.info("Question: {question}")
        logger.info("{'='*60}")
        
        # Get relevant documents
        relevant_docs = vectorstore.similarity_search(question, k=3)
        
        # Answer question
        result = rag_chain.answer_question(question, relevant_docs)
        
        logger.info("Answer: {result['answer']}")
        logger.info("Confidence: {result['confidence']}")
        logger.info("Documents used: {result['documents_used']}")
        logger.info("Sources: {len(result['sources'])}")

if __name__ == "__main__":
    main() 