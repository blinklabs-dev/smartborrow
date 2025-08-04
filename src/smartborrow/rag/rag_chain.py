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

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class SmartBorrowRAGChain:
    """RAG chain for SmartBorrow question answering"""
    
    def __init__(self, 
                 model_name: str = "gpt-3.5-turbo",
                 temperature: float = 0.1,
                 max_tokens: int = 1000) -> None:
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        # Initialize LLM with timeout and retry settings
        self.llm = ChatOpenAI(
            model_name=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            request_timeout=30,  # 30 second timeout
            max_retries=2  # Retry failed requests
        )
        
        # Create prompts
        self.qa_prompt = self._create_qa_prompt()
        self.qa_with_sources_prompt = self._create_qa_with_sources_prompt()
        self.numerical_context_prompt = self._create_numerical_context_prompt()
        
        # Create chains using modern LCEL approach
        self.qa_chain = self._create_qa_chain()
        self.qa_with_sources_chain = self._create_qa_with_sources_chain()
    
    def _create_qa_prompt(self) -> ChatPromptTemplate:
        """Create QA prompt template"""
        template = """You are a helpful assistant for SmartBorrow, a student loan and financial aid information system. 
You have access to comprehensive information about federal student loans, Pell Grants, application processes, and common issues.

Use the following context to answer the question. If you cannot find the answer in the context, say so.

IMPORTANT: 
- Provide specific, concrete answers with actual numbers and values
- Do NOT use template placeholders like {{rate}}, {{amount}}, {{year}}, etc.
- If specific numbers are not available in the context, say "The specific rate/amount is not provided in the available information"
- Always give complete, actionable answers

Context:
{context}

Question: {question}

Answer the question based on the context provided. Be specific and accurate. If the question asks for numerical data (like amounts, rates, limits), provide the exact values from the context. If exact values are not available, clearly state what information is available and what is not.

Answer:"""

        return ChatPromptTemplate.from_template(template)
    
    def _create_qa_with_sources_prompt(self) -> ChatPromptTemplate:
        """Create QA with sources prompt template"""
        template = """You are a helpful assistant for SmartBorrow, a student loan and financial aid information system.

Use the following context to answer the question. For complex questions, break them down and address each part systematically.

IMPORTANT: 
- Provide specific, concrete answers with actual numbers and values
- Do NOT use template placeholders like {{rate}}, {{amount}}, {{year}}, etc.
- If specific numbers are not available in the context, say "The specific rate/amount is not provided in the available information"
- Always give complete, actionable answers

Context:
{context}

Question: {question}

Instructions:
1. For complex questions, break them down into parts and address each systematically
2. Use specific information from the context to answer each part
3. If the context doesn't contain enough information, acknowledge this but provide what you can
4. For multi-part questions, structure your answer clearly with sections
5. If the question asks for numerical data, provide exact values from the context
6. Be comprehensive and address all aspects of the question
7. Stay faithful to the context while being helpful and informative
8. NEVER use template placeholders - provide actual values or clearly state when they're not available

Answer:"""

        return ChatPromptTemplate.from_template(template)
    
    def _create_numerical_context_prompt(self) -> ChatPromptTemplate:
        """Create prompt for numerical data context"""
        template = """You are analyzing numerical data for SmartBorrow. 

Context: {context}

Extract and summarize the key numerical information (amounts, rates, limits, dates) from the context. 
Format the information clearly and include the units where applicable.

Numerical Summary:"""

        return ChatPromptTemplate.from_template(template)
    
    def _create_qa_chain(self) -> None:
        """Create basic QA chain using modern LCEL"""
        return self.qa_prompt | self.llm | StrOutputParser()
    
    def _create_qa_with_sources_chain(self) -> None:
        """Create QA chain with source citation using modern LCEL"""
        return self.qa_with_sources_prompt | self.llm | StrOutputParser()
    
    def answer_question(self, 
                       question: str, 
                       documents: List[Document],
                       include_sources: bool = True) -> Dict[str, Any]:
        """Answer a question using retrieved documents"""
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
            
            # Generate answer using modern LCEL
            if include_sources:
                response = self.qa_with_sources_chain.invoke({
                    "context": full_context,
                    "question": question
                })
            else:
                response = self.qa_chain.invoke({
                    "context": full_context,
                    "question": question
                })
            
            # Extract sources
            sources = self._extract_sources(documents)
            
            # Determine confidence based on document relevance
            confidence = self._determine_confidence(documents, question)
            
            # Clean up any template placeholders that might have slipped through
            cleaned_response = self._clean_template_placeholders(response)
            
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
        """Prepare context from documents"""
        context_parts = []
        
        for i, doc in enumerate(documents):
            # Add document content with metadata
            content = doc.page_content
            metadata = doc.metadata
            
            # Add metadata info if available
            metadata_info = []
            if metadata.get('document_type'):
                metadata_info.append(f"Type: {metadata['document_type']}")
            if metadata.get('category'):
                metadata_info.append(f"Category: {metadata['category']}")
            if metadata.get('concept'):
                metadata_info.append(f"Concept: {metadata['concept']}")
            
            if metadata_info:
                content = f"[{' | '.join(metadata_info)}]\n{content}"
            
            context_parts.append(f"Document {i+1}:\n{content}")
        
        return "\n\n".join(context_parts)
    
    def _extract_numerical_context(self, documents: List[Document]) -> str:
        """Extract numerical data context from documents"""
        numerical_data = []
        
        for doc in documents:
            metadata = doc.metadata
            
            # Check for numerical data in metadata
            if metadata.get('value') and metadata.get('unit'):
                numerical_data.append(f"{metadata['value']} ({metadata['unit']})")
            
            # Check for numerical data in content
            content = doc.page_content.lower()
            if any(keyword in content for keyword in ['$', 'percent', 'rate', 'amount', 'limit']):
                # Extract numerical information from content
                lines = doc.page_content.split('\n')
                for line in lines:
                    if any(keyword in line.lower() for keyword in ['$', 'percent', 'rate', 'amount', 'limit']):
                        numerical_data.append(line.strip())
        
        if numerical_data:
            return "\n".join(numerical_data[:10])  # Limit to first 10
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