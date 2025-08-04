"""
RAG Service for SmartBorrow

Main RAGService class coordinating document loading, vector store,
and RAG chain for comprehensive question answering.
"""

import os
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from dataclasses import asdict
from langchain.schema import Document

from .document_loader import SmartBorrowDocumentLoader
from .vector_store import SmartBorrowVectorStore, SmartBorrowRetriever
from .rag_chain import SmartBorrowRAGChain

logger = logging.getLogger(__name__)

class RAGService:
    """Main RAG service for SmartBorrow"""
    
    def __init__(self, 
                 processed_data_path: str = "data/processed",
                 vectorstore_path: str = "data/faiss",
                 model_name: str = "gpt-3.5-turbo",
                 rebuild_vectorstore: bool = False) -> None:
        self.processed_data_path = Path(processed_data_path)
        self.vectorstore_path = Path(vectorstore_path)
        self.model_name = model_name
        self.rebuild_vectorstore = rebuild_vectorstore
        
        # Initialize components
        self.document_loader = SmartBorrowDocumentLoader(processed_data_path)
        self.vectorstore = SmartBorrowVectorStore(vectorstore_path)
        self.rag_chain = SmartBorrowRAGChain(model_name)
        self.retriever = None
        
        # Advanced retrieval components - initialize lazily to avoid circular import
        self.advanced_rag_service = None
        
        # Service state
        self.is_initialized = False
        self.stats = {}
    
    def initialize(self) -> bool:
        """Initialize the RAG service"""
        try:
            logger.info("Initializing SmartBorrow RAG Service...")
            
            # Check if vector store exists and should be rebuilt
            if self.rebuild_vectorstore or not self.vectorstore.load_existing_vectorstore():
                logger.info("Building new vector store from processed data...")
                
                # Load documents
                processed_docs = self.document_loader.load_processed_data()
                if not processed_docs:
                    logger.error("No processed documents found")
                    return False
                
                # Create LangChain documents
                documents = self.document_loader.create_langchain_documents(processed_docs)
                
                # Create vector store
                self.vectorstore.create_vectorstore(documents)
                
                # Get document summary
                self.stats = self.document_loader.get_document_summary(documents)
                
                logger.info(f"Vector store created with {len(documents)} documents")
            else:
                logger.info("Loaded existing vector store")
                # Get stats from existing vector store
                self.stats = self.vectorstore.get_vectorstore_stats()
            
            # Create retriever
            self.retriever = SmartBorrowRetriever(self.vectorstore)
            
            self.is_initialized = True
            logger.info("RAG Service initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing RAG service: {e}")
            return False
    
    def smart_search(self, 
                    question: str,
                    search_type: str = "hybrid",
                    document_types: Optional[List[str]] = None,
                    categories: Optional[List[str]] = None,
                    k: int = 5,
                    include_sources: bool = True,
                    format_response: bool = True) -> Dict[str, Any]:
        """Enhanced smart search with multiple retrieval strategies"""
        if not self.is_initialized:
            logger.error("RAG service not initialized. Call initialize() first.")
            return {
                "answer": "RAG service not initialized. Please initialize the service first.",
                "sources": [],
                "confidence": "error",
                "error": "Service not initialized"
            }
        
        try:
            logger.info(f"Processing smart search: {question} (type: {search_type})")
            
            # Determine retrieval strategy based on search type
            if search_type == "hybrid":
                result = self._hybrid_search(question, document_types, categories, k, include_sources)
            elif search_type == "semantic":
                result = self._semantic_search(question, document_types, categories, k, include_sources)
            elif search_type == "keyword":
                result = self._keyword_search(question, document_types, categories, k, include_sources)
            elif search_type == "numerical":
                result = self._numerical_search(question, document_types, categories, k, include_sources)
            else:
                result = self._standard_search(question, document_types, categories, k, include_sources)
            
            # Format response if requested
            if format_response and result.get("answer"):
                result["answer"] = self._format_answer(result["answer"], result.get("sources", []))
            
            # Add search metadata
            result.update({
                "query": question,
                "search_type": search_type,
                "document_types_filtered": document_types,
                "categories_filtered": categories,
                "k": k,
                "formatted": format_response
            })
            
            logger.info(f"Smart search completed. Confidence: {result['confidence']}")
            return result
            
        except Exception as e:
            logger.error(f"Error in smart search: {e}")
            return {
                "answer": "I encountered an error while processing your question. Please try again.",
                "sources": [],
                "confidence": "error",
                "error": str(e)
            }
    
    def _hybrid_search(self, question: str, document_types: Optional[List[str]], 
                      categories: Optional[List[str]], k: int, include_sources: bool) -> Dict[str, Any]:
        """Hybrid search combining multiple retrieval strategies"""
        # Get documents using different strategies
        semantic_docs = self.retriever.get_relevant_documents(question, k=k*2)
        keyword_docs = self._get_keyword_documents(question, k=k)
        numerical_docs = self._get_numerical_documents(question, k=k)
        
        # Combine and deduplicate documents
        all_docs = semantic_docs + keyword_docs + numerical_docs
        unique_docs = self._deduplicate_documents(all_docs)
        
        # Score and rank documents
        scored_docs = self._score_documents(unique_docs, question)
        top_docs = scored_docs[:k]
        
        # Generate answer
        result = self.rag_chain.answer_question(question, top_docs, include_sources)
        
        # Add hybrid metadata
        result["retrieval_method"] = "hybrid"
        result["semantic_docs"] = len(semantic_docs)
        result["keyword_docs"] = len(keyword_docs)
        result["numerical_docs"] = len(numerical_docs)
        
        return result
    
    def _semantic_search(self, question: str, document_types: Optional[List[str]], 
                        categories: Optional[List[str]], k: int, include_sources: bool) -> Dict[str, Any]:
        """Semantic search using vector similarity"""
        # Get relevant documents with increased k for better recall
        question_complexity = len(question.split()) > 8
        if question_complexity:
            retrieval_k = min(k * 3, 25)
        else:
            retrieval_k = min(k * 2, 20)
        
        if document_types or categories:
            relevant_docs = self.retriever.get_relevant_documents(
                query=question,
                document_types=document_types,
                categories=categories,
                k=retrieval_k
            )
        else:
            relevant_docs = self.retriever.get_relevant_documents(
                query=question,
                k=retrieval_k
            )
        
        # Limit to requested k for final result
        relevant_docs = relevant_docs[:k]
        
        # Answer the question
        result = self.rag_chain.answer_question(
            question=question,
            documents=relevant_docs,
            include_sources=include_sources
        )
        
        result["retrieval_method"] = "semantic"
        return result
    
    def _keyword_search(self, question: str, document_types: Optional[List[str]], 
                       categories: Optional[List[str]], k: int, include_sources: bool) -> Dict[str, Any]:
        """Keyword-based search"""
        # Extract keywords from question
        keywords = self._extract_keywords(question)
        
        # Get documents matching keywords
        keyword_docs = self._get_keyword_documents(question, k=k*2)
        
        # Score and rank
        scored_docs = self._score_documents(keyword_docs, question)
        top_docs = scored_docs[:k]
        
        # Generate answer
        result = self.rag_chain.answer_question(question, top_docs, include_sources)
        
        result["retrieval_method"] = "keyword"
        result["keywords_used"] = keywords
        return result
    
    def _numerical_search(self, question: str, document_types: Optional[List[str]], 
                         categories: Optional[List[str]], k: int, include_sources: bool) -> Dict[str, Any]:
        """Search focused on numerical data"""
        # Get numerical documents
        numerical_docs = self._get_numerical_documents(question, k=k*2)
        
        # Add numerical context
        result = self.rag_chain.answer_question(question, numerical_docs[:k], include_sources)
        
        # Add numerical summary
        numerical_summary = self.rag_chain.get_numerical_summary(numerical_docs)
        result["numerical_summary"] = numerical_summary
        
        result["retrieval_method"] = "numerical"
        return result
    
    def _standard_search(self, question: str, document_types: Optional[List[str]], 
                        categories: Optional[List[str]], k: int, include_sources: bool) -> Dict[str, Any]:
        """Standard search (original query method)"""
        # Get relevant documents with increased k for better recall
        # For complex questions, get even more documents
        question_complexity = len(question.split()) > 8  # Simple heuristic for complexity
        if question_complexity:
            retrieval_k = min(k * 3, 25)  # More documents for complex questions
        else:
            retrieval_k = min(k * 2, 20)  # Standard retrieval
        
        if document_types or categories:
            # Use filtered retrieval
            relevant_docs = self.retriever.get_relevant_documents(
                query=question,
                document_types=document_types,
                categories=categories,
                k=retrieval_k
            )
        else:
            # Use standard retrieval
            relevant_docs = self.retriever.get_relevant_documents(
                query=question,
                k=retrieval_k
            )
        
        # Limit to requested k for final result
        relevant_docs = relevant_docs[:k]
        
        # Answer the question
        result = self.rag_chain.answer_question(
            question=question,
            documents=relevant_docs,
            include_sources=include_sources
        )
        
        result["retrieval_method"] = "standard"
        return result
    
    def _get_keyword_documents(self, question: str, k: int) -> List[Document]:
        """Get documents using keyword matching"""
        keywords = self._extract_keywords(question)
        keyword_docs = []
        
        for keyword in keywords:
            docs = self.vectorstore.similarity_search(keyword, k=k//len(keywords))
            keyword_docs.extend(docs)
        
        return keyword_docs
    
    def _get_numerical_documents(self, question: str, k: int) -> List[Document]:
        """Get documents with numerical data"""
        # Search for documents with numerical content
        numerical_terms = ["amount", "rate", "limit", "percent", "$", "dollar", "cost", "price"]
        
        numerical_docs = []
        for term in numerical_terms:
            if term.lower() in question.lower():
                docs = self.vectorstore.similarity_search(term, k=k//len(numerical_terms))
                numerical_docs.extend(docs)
        
        return numerical_docs
    
    def _extract_keywords(self, question: str) -> List[str]:
        """Extract important keywords from question"""
        # Simple keyword extraction
        stop_words = {"what", "is", "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by"}
        words = question.lower().split()
        keywords = [word for word in words if word not in stop_words and len(word) > 2]
        return keywords[:5]  # Limit to top 5 keywords
    
    def _deduplicate_documents(self, documents: List[Document]) -> List[Document]:
        """Remove duplicate documents based on content"""
        seen = set()
        unique_docs = []
        
        for doc in documents:
            content_hash = hash(doc.page_content[:100])  # Hash first 100 chars
            if content_hash not in seen:
                seen.add(content_hash)
                unique_docs.append(doc)
        
        return unique_docs
    
    def _score_documents(self, documents: List[Document], question: str) -> List[Document]:
        """Score and rank documents by relevance"""
        scored_docs = []
        
        for doc in documents:
            score = self._calculate_relevance_score(doc, question)
            doc.metadata["relevance_score"] = score
            scored_docs.append(doc)
        
        # Sort by score (highest first)
        scored_docs.sort(key=lambda x: x.metadata.get("relevance_score", 0), reverse=True)
        return scored_docs
    
    def _calculate_relevance_score(self, document: Document, question: str) -> float:
        """Calculate relevance score for a document"""
        score = 0.0
        
        # Content overlap
        question_words = set(question.lower().split())
        content_words = set(document.page_content.lower().split())
        overlap = len(question_words.intersection(content_words))
        score += overlap * 0.1
        
        # Metadata relevance
        metadata = document.metadata
        if metadata.get("category"):
            category_words = set(metadata["category"].lower().split())
            category_overlap = len(question_words.intersection(category_words))
            score += category_overlap * 0.2
        
        # Document type relevance
        if metadata.get("document_type") == "qa_pairs":
            score += 0.3  # Q&A pairs are highly relevant
        elif metadata.get("document_type") == "knowledge_base":
            score += 0.2  # Knowledge base is relevant
        
        return score
    
    def _format_answer(self, answer: str, sources: List[Dict[str, Any]]) -> str:
        """Format the answer for better presentation"""
        if not answer:
            return answer
        
        # Add source citations if available
        if sources:
            formatted_answer = answer + "\n\n**Sources:**\n"
            for i, source in enumerate(sources[:3], 1):  # Limit to 3 sources
                source_type = source.get("document_type", "Document")
                category = source.get("category", "")
                formatted_answer += f"{i}. {source_type}"
                if category:
                    formatted_answer += f" ({category})"
                formatted_answer += "\n"
        
        else:
            formatted_answer = answer
        
        return formatted_answer
    
    def query(self, 
              question: str,
              document_types: Optional[List[str]] = None,
              categories: Optional[List[str]] = None,
              k: int = 5,
              include_sources: bool = True) -> Dict[str, Any]:
        """Query the RAG system (legacy method)"""
        return self.smart_search(question, "standard", document_types, categories, k, include_sources)
    
    def query_with_numerical_context(self, 
                                   question: str,
                                   document_types: Optional[List[str]] = None,
                                   categories: Optional[List[str]] = None,
                                   k: int = 5) -> Dict[str, Any]:
        """Query with additional numerical context"""
        # Get standard query result
        result = self.query(question, document_types, categories, k, include_sources=True)
        
        if result.get("error"):
            return result
        
        # Get relevant documents for numerical context
        relevant_docs = self.retriever.get_relevant_documents(
            query=question,
            document_types=document_types,
            categories=categories,
            k=k
        )
        
        # Add numerical summary
        numerical_summary = self.rag_chain.get_numerical_summary(relevant_docs)
        result["numerical_summary"] = numerical_summary
        
        return result
    
    def get_similar_questions(self, question: str, k: int = 5) -> List[Dict[str, Any]]:
        """Get similar questions from the Q&A pairs"""
        if not self.is_initialized:
            return []
        
        try:
            # Search for Q&A pairs specifically
            qa_docs = self.vectorstore.filter_by_document_type("qa_pairs")
            
            # Get similar documents
            similar_docs = self.vectorstore.similarity_search(
                query=question,
                k=k,
                filter_dict={"document_type": "qa_pairs"}
            )
            
            similar_questions = []
            for doc in similar_docs:
                # Extract question from content
                content = doc.page_content
                if "Question:" in content:
                    question_part = content.split("Question:")[1].split("\n\n")[0].strip()
                    similar_questions.append({
                        "question": question_part,
                        "similarity_score": doc.metadata.get("similarity_score", 0.0),
                        "category": doc.metadata.get("category", "unknown"),
                        "confidence": doc.metadata.get("confidence", 0.8)
                    })
            
            return similar_questions
            
        except Exception as e:
            logger.error(f"Error getting similar questions: {e}")
            return []
    
    def get_complaint_insights(self, topic: str) -> Dict[str, Any]:
        """Get insights about complaints related to a topic"""
        if not self.is_initialized:
            return {"error": "Service not initialized"}
        
        try:
            # Search for complaint-related documents
            complaint_docs = self.vectorstore.similarity_search(
                query=topic,
                k=10,
                filter_dict={"document_type": {"$in": ["complaints", "faqs"]}}
            )
            
            insights = {
                "topic": topic,
                "total_complaints_found": len(complaint_docs),
                "categories": {},
                "common_issues": [],
                "sample_complaints": []
            }
            
            for doc in complaint_docs:
                metadata = doc.metadata
                category = metadata.get("category", "unknown")
                
                if category not in insights["categories"]:
                    insights["categories"][category] = {
                        "count": 0,
                        "percentage": 0,
                        "common_keywords": []
                    }
                
                insights["categories"][category]["count"] += 1
                
                # Extract common keywords if available
                if metadata.get("common_keywords"):
                    insights["categories"][category]["common_keywords"].extend(
                        metadata["common_keywords"][:5]
                    )
                
                # Add sample complaints
                if len(insights["sample_complaints"]) < 3:
                    insights["sample_complaints"].append(doc.page_content[:200] + "...")
            
            # Calculate percentages
            total = sum(cat["count"] for cat in insights["categories"].values())
            for category in insights["categories"]:
                insights["categories"][category]["percentage"] = (
                    insights["categories"][category]["count"] / total * 100
                )
            
            return insights
            
        except Exception as e:
            logger.error(f"Error getting complaint insights: {e}")
            return {"error": str(e)}
    
    def get_knowledge_summary(self, concept: str) -> Dict[str, Any]:
        """Get a summary of knowledge about a specific concept"""
        if not self.is_initialized:
            return {"error": "Service not initialized"}
        
        try:
            # Search for knowledge base documents about the concept
            knowledge_docs = self.vectorstore.similarity_search(
                query=concept,
                k=5,
                filter_dict={"document_type": "knowledge_base"}
            )
            
            summary = {
                "concept": concept,
                "definition": "",
                "requirements": [],
                "procedures": [],
                "numerical_data": [],
                "source_documents": []
            }
            
            for doc in knowledge_docs:
                metadata = doc.metadata
                content = doc.page_content
                
                # Extract definition
                if metadata.get("content_type") == "definition":
                    summary["definition"] = content
                
                # Extract requirements
                elif metadata.get("content_type") == "requirement":
                    summary["requirements"].append(content)
                
                # Extract procedures
                elif metadata.get("content_type") == "procedure":
                    summary["procedures"].append(content)
                
                # Extract numerical data
                elif metadata.get("content_type") == "numerical_data":
                    summary["numerical_data"].append(content)
                
                # Collect source documents
                if metadata.get("source_documents"):
                    summary["source_documents"].extend(metadata["source_documents"])
            
            # Remove duplicates
            summary["source_documents"] = list(set(summary["source_documents"]))
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting knowledge summary: {e}")
            return {"error": str(e)}
    
    def get_service_stats(self) -> Dict[str, Any]:
        """Get statistics about the RAG service"""
        if not self.is_initialized:
            return {"error": "Service not initialized"}
        
        return {
            "is_initialized": self.is_initialized,
            "model_name": self.model_name,
            "vectorstore_stats": self.stats,
            "processed_data_path": str(self.processed_data_path),
            "vectorstore_path": str(self.vectorstore_path)
        }
    
    def query_with_advanced_retrieval(self, 
                                      question: str,
                                      use_hybrid: bool = True,
                                      use_faq: bool = True,
                                      use_complaints: bool = True) -> Dict[str, Any]:
        """Query using advanced hybrid retrieval"""
        if not self.is_initialized:
            logger.error("RAG service not initialized. Call initialize() first.")
            return {
                "answer": "RAG service not initialized. Please initialize the service first.",
                "sources": [],
                "confidence": "error",
                "error": "Service not initialized"
            }
        
        try:
            logger.info(f"Processing query with advanced retrieval: {question}")
            
            # Initialize advanced RAG service lazily
            if self.advanced_rag_service is None:
                from ..retrieval.advanced_rag_service import AdvancedRAGService
                self.advanced_rag_service = AdvancedRAGService(self.processed_data_path)
            
            # Use advanced RAG service for hybrid retrieval
            result = self.advanced_rag_service.query_with_hybrid_retrieval(
                question, use_faq, use_complaints
            )
            
            # Extract the best answer from hybrid results
            hybrid_data = result.get('hybrid_retrieval', {})
            standard_data = result.get('standard_rag', {})
            
            # Determine which answer to use based on combined score
            hybrid_score = hybrid_data.get('combined_score', 0)
            standard_confidence = standard_data.get('confidence', 'medium')
            
            if hybrid_score > 0.5:
                # Use hybrid retrieval results
                answer = self._format_hybrid_answer(hybrid_data)
                sources = self._extract_hybrid_sources(hybrid_data)
                confidence = "high" if hybrid_score > 0.7 else "medium"
            else:
                # Fall back to standard RAG
                answer = standard_data.get('answer', 'No answer available')
                sources = standard_data.get('sources', [])
                confidence = standard_confidence
            
            return {
                "answer": answer,
                "sources": sources,
                "confidence": confidence,
                "retrieval_method": hybrid_data.get('retrieval_method', 'standard'),
                "combined_score": hybrid_score,
                "response_time": result.get('response_time', 0),
                "hybrid_data": hybrid_data,
                "standard_data": standard_data
            }
            
        except Exception as e:
            logger.error(f"Error in advanced retrieval query: {e}")
            return {
                "answer": f"Error processing query: {str(e)}",
                "sources": [],
                "confidence": "error",
                "error": str(e)
            }
    
    def _format_hybrid_answer(self, hybrid_data: Dict[str, Any]) -> str:
        """Format hybrid retrieval results into a coherent answer"""
        answer_parts = []
        
        # Add knowledge-based answer
        knowledge_results = hybrid_data.get('knowledge_results', {})
        if knowledge_results.get('related_concepts'):
            concepts = knowledge_results['related_concepts'][:2]  # Top 2 concepts
            for concept in concepts:
                if concept.get('definition'):
                    answer_parts.append(f"Based on {concept['concept']}: {concept['definition'][:200]}...")
        
        # Add numerical data
        numerical_results = hybrid_data.get('numerical_results', {})
        if numerical_results.get('all_matches'):
            matches = numerical_results['all_matches'][:3]  # Top 3 matches
            for match in matches:
                if hasattr(match, 'value') and hasattr(match, 'context'):
                    answer_parts.append(f"Numerical data: {match.value} - {match.context[:100]}...")
        
        # Add FAQ insights
        faq_results = hybrid_data.get('faq_results', {})
        if faq_results.get('matches'):
            top_faq = faq_results['matches'][0]
            if top_faq.get('answer'):
                answer_parts.append(f"FAQ insight: {top_faq['answer'][:200]}...")
        
        if answer_parts:
            return " ".join(answer_parts)
        else:
            return "No specific information found for this query."
    
    def _extract_hybrid_sources(self, hybrid_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract sources from hybrid retrieval results"""
        sources = []
        
        # Add knowledge sources
        knowledge_results = hybrid_data.get('knowledge_results', {})
        for concept in knowledge_results.get('related_concepts', []):
            sources.append({
                'type': 'knowledge',
                'concept': concept.get('concept', ''),
                'similarity': concept.get('similarity', 0),
                'content': concept.get('definition', '')[:100] + "..."
            })
        
        # Add numerical sources
        numerical_results = hybrid_data.get('numerical_results', {})
        for match in numerical_results.get('all_matches', [])[:5]:
            if hasattr(match, 'value') and hasattr(match, 'context'):
                sources.append({
                    'type': 'numerical',
                    'value': match.value,
                    'category': match.category,
                    'confidence': match.confidence,
                    'content': match.context[:100] + "..."
                })
        
        # Add FAQ sources
        faq_results = hybrid_data.get('faq_results', {})
        for faq in faq_results.get('matches', [])[:3]:
            sources.append({
                'type': 'faq',
                'question': faq.get('question', ''),
                'relevance_score': faq.get('relevance_score', 0),
                'content': faq.get('answer', '')[:100] + "..."
            })
        
        return sources
    
    def compare_retrieval_methods(self, question: str) -> Dict[str, Any]:
        """Compare different retrieval methods for a question"""
        if self.advanced_rag_service is None:
            from ..retrieval.advanced_rag_service import AdvancedRAGService
            self.advanced_rag_service = AdvancedRAGService(self.processed_data_path)
        return self.advanced_rag_service.compare_retrieval_methods(question)
    
    def run_ab_test(self, question: str, method_a: str = "hybrid", method_b: str = "standard") -> Dict[str, Any]:
        """Run A/B test between retrieval methods"""
        if self.advanced_rag_service is None:
            from ..retrieval.advanced_rag_service import AdvancedRAGService
            self.advanced_rag_service = AdvancedRAGService(self.processed_data_path)
        result = self.advanced_rag_service.run_ab_test(question, method_a, method_b)
        return asdict(result)
    
    def get_advanced_stats(self) -> Dict[str, Any]:
        """Get advanced retrieval statistics"""
        if self.advanced_rag_service is None:
            from ..retrieval.advanced_rag_service import AdvancedRAGService
            self.advanced_rag_service = AdvancedRAGService(self.processed_data_path)
        return self.advanced_rag_service.get_performance_summary()
    
    def rebuild_knowledge_base(self) -> bool:
        """Rebuild the entire knowledge base"""
        try:
            logger.info("Rebuilding knowledge base...")
            
            # Delete existing vector store
            self.vectorstore.delete_collection()
            
            # Reinitialize
            self.rebuild_vectorstore = True
            return self.initialize()
            
        except Exception as e:
            logger.error(f"Error rebuilding knowledge base: {e}")
            return False

def main() -> None:
    """Test the RAG service"""
    # Initialize service
    rag_service = RAGService()
    
    if not rag_service.initialize():
        logger.info("Failed to initialize RAG service")
        return
    
    # Test queries
    test_queries = [
        "What is the maximum Pell Grant amount?",
        "How do I qualify for a Pell Grant?",
        "What are the current interest rates for Direct Loans?",
        "What are the most common student loan complaints?"
    ]
    
    for query in test_queries:
        logger.info("\n{'='*80}")
        logger.info("Query: {query}")
        logger.info("{'='*80}")
        
        # Get answer
        result = rag_service.smart_search(query, "hybrid")
        
        logger.info("Answer: {result['answer']}")
        logger.info("Confidence: {result['confidence']}")
        logger.info("Documents used: {result['documents_used']}")
        logger.info("Sources: {len(result['sources'])}")
    
    # Get service stats
    stats = rag_service.get_service_stats()
    logger.info("\nService Stats: {stats}")

if __name__ == "__main__":
    main() 