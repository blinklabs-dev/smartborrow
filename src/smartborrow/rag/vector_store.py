"""
Vector Store for SmartBorrow RAG System

ChromaDB vector store using OpenAI embeddings to store
processed documents with rich metadata.
"""

import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from langchain.schema import Document
from langchain_openai import OpenAIEmbeddings
from langchain.schema.retriever import BaseRetriever
from langchain_community.vectorstores import FAISS
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class SmartBorrowVectorStore:
    """FAISS vector store for SmartBorrow documents"""
    
    def __init__(self, 
                 persist_directory: str = "data/faiss",
                 embedding_model: str = "text-embedding-ada-002") -> None:
        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        
        # Initialize embeddings
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        
        self.embeddings = OpenAIEmbeddings(
            model=embedding_model,
            openai_api_key=api_key
        )
        
        self.vectorstore = None
        self.retriever = None
    
    def create_vectorstore(self, documents: List[Document]) -> FAISS:
        """Create FAISS vector store from documents"""
        try:
            logger.info(f"Creating vector store with {len(documents)} documents")
            
            # Create vector store
            self.vectorstore = FAISS.from_documents(
                documents=documents,
                embedding=self.embeddings
            )
            
            # Save the vector store
            self.vectorstore.save_local(str(self.persist_directory))
            
            # Create retriever
            self.retriever = self.vectorstore.as_retriever(
                search_type="similarity",
                search_kwargs={"k": 5}
            )
            
            logger.info(f"Vector store created successfully at {self.persist_directory}")
            return self.vectorstore
            
        except Exception as e:
            logger.error(f"Error creating vector store: {e}")
            raise
    
    def load_existing_vectorstore(self) -> FAISS:
        """Load existing vector store from disk"""
        try:
            if not self.persist_directory.exists():
                logger.warning("No existing vector store found")
                return None
            
            self.vectorstore = FAISS.load_local(
                folder_path=str(self.persist_directory),
                embeddings=self.embeddings,
                allow_dangerous_deserialization=True
            )
            
            # Create retriever
            self.retriever = self.vectorstore.as_retriever(
                search_type="similarity",
                search_kwargs={"k": 5}
            )
            
            logger.info("Loaded existing vector store")
            return self.vectorstore
            
        except Exception as e:
            logger.error(f"Error loading vector store: {e}")
            return None
    
    def similarity_search(self, 
                        query: str, 
                        k: int = 5,
                        filter_dict: Optional[Dict[str, Any]] = None) -> List[Document]:
        """Perform similarity search with optional filtering"""
        if not self.vectorstore:
            logger.error("Vector store not initialized")
            return []
        
        try:
            results = self.vectorstore.similarity_search(
                query=query,
                k=k,
                filter=filter_dict
            )
            
            logger.info(f"Found {len(results)} similar documents for query: {query[:50]}...")
            return results
            
        except Exception as e:
            logger.error(f"Error in similarity search: {e}")
            return []
    
    def similarity_search_with_score(self, 
                                   query: str, 
                                   k: int = 5,
                                   filter_dict: Optional[Dict[str, Any]] = None) -> List[Tuple[Document, float]]:
        """Perform similarity search with scores"""
        if not self.vectorstore:
            logger.error("Vector store not initialized")
            return []
        
        try:
            results = self.vectorstore.similarity_search_with_score(
                query=query,
                k=k,
                filter=filter_dict
            )
            
            logger.info(f"Found {len(results)} similar documents with scores for query: {query[:50]}...")
            return results
            
        except Exception as e:
            logger.error(f"Error in similarity search with score: {e}")
            return []
    
    def get_retriever(self, 
                     search_type: str = "similarity",
                     search_kwargs: Optional[Dict[str, Any]] = None) -> BaseRetriever:
        """Get a retriever with custom search parameters"""
        if not self.vectorstore:
            logger.error("Vector store not initialized")
            return None
        
        if search_kwargs is None:
            search_kwargs = {"k": 5}
        
        return self.vectorstore.as_retriever(
            search_type=search_type,
            search_kwargs=search_kwargs
        )
    
    def filter_by_document_type(self, document_type: str) -> List[Document]:
        """Get documents filtered by document type"""
        if not self.vectorstore:
            logger.error("Vector store not initialized")
            return []
        
        try:
            # Get all documents and filter by metadata
            all_docs = self.vectorstore.get()
            filtered_docs = []
            
            for doc in all_docs['documents']:
                metadata = all_docs['metadatas'][all_docs['documents'].index(doc)]
                if metadata.get('document_type') == document_type:
                    filtered_docs.append(Document(
                        page_content=doc,
                        metadata=metadata
                    ))
            
            logger.info(f"Found {len(filtered_docs)} documents of type: {document_type}")
            return filtered_docs
            
        except Exception as e:
            logger.error(f"Error filtering by document type: {e}")
            return []
    
    def filter_by_category(self, category: str) -> List[Document]:
        """Get documents filtered by category"""
        if not self.vectorstore:
            logger.error("Vector store not initialized")
            return []
        
        try:
            # Get all documents and filter by metadata
            all_docs = self.vectorstore.get()
            filtered_docs = []
            
            for doc in all_docs['documents']:
                metadata = all_docs['metadatas'][all_docs['documents'].index(doc)]
                if metadata.get('category') == category:
                    filtered_docs.append(Document(
                        page_content=doc,
                        metadata=metadata
                    ))
            
            logger.info(f"Found {len(filtered_docs)} documents of category: {category}")
            return filtered_docs
            
        except Exception as e:
            logger.error(f"Error filtering by category: {e}")
            return []
    
    def get_vectorstore_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store"""
        if not self.vectorstore:
            return {"error": "Vector store not initialized"}
        
        try:
            # For FAISS, we need to use different methods to get stats
            # FAISS doesn't have a 'get' method like ChromaDB
            stats = {
                'total_documents': 0,
                'document_types': {},
                'categories': {},
                'source_types': {},
                'vectorstore_type': 'FAISS'
            }
            
            # Try to get document count using FAISS methods
            try:
                if hasattr(self.vectorstore, 'index'):
                    stats['total_documents'] = self.vectorstore.index.ntotal
            except:
                pass
            
            # For FAISS, we can't easily get metadata without additional storage
            # This is a limitation of FAISS - it only stores vectors, not metadata
            # We'll return basic stats for now
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting vector store stats: {e}")
            return {"error": str(e)}
    
    def delete_collection(self) -> None:
        """Delete the current collection"""
        if self.vectorstore:
            try:
                self.vectorstore.delete_collection()
                logger.info("Collection deleted successfully")
            except Exception as e:
                logger.error(f"Error deleting collection: {e}")
    
    def add_documents(self, documents: List[Document]) -> None:
        """Add new documents to the vector store"""
        if not self.vectorstore:
            logger.error("Vector store not initialized")
            return
        
        try:
            self.vectorstore.add_documents(documents)
            self.vectorstore.persist()
            logger.info(f"Added {len(documents)} new documents to vector store")
        except Exception as e:
            logger.error(f"Error adding documents: {e}")

class SmartBorrowRetriever:
    """Enhanced retriever with filtering capabilities"""
    
    def __init__(self, vectorstore: SmartBorrowVectorStore) -> None:
        self.vectorstore = vectorstore
        self.base_retriever = vectorstore.get_retriever()
    
    def get_relevant_documents(self, 
                             query: str,
                             document_types: Optional[List[str]] = None,
                             categories: Optional[List[str]] = None,
                             k: int = 5) -> List[Document]:
        """Get relevant documents with optional filtering"""
        try:
            # For FAISS, we'll do simple similarity search without filtering
            # since FAISS doesn't support metadata filtering like ChromaDB
            results = self.vectorstore.similarity_search(
                query=query,
                k=k
            )
            
            logger.info(f"Retrieved {len(results)} documents for query: {query[:50]}...")
            return results
            
        except Exception as e:
            logger.error(f"Error in get_relevant_documents: {e}")
            return []
    
    def get_relevant_documents_with_scores(self, 
                                          query: str,
                                          document_types: Optional[List[str]] = None,
                                          categories: Optional[List[str]] = None,
                                          k: int = 5) -> List[Tuple[Document, float]]:
        """Get relevant documents with scores"""
        try:
            # For FAISS, we'll do simple similarity search with scores
            results = self.vectorstore.similarity_search_with_score(
                query=query,
                k=k
            )
            
            logger.info(f"Retrieved {len(results)} documents with scores for query: {query[:50]}...")
            return results
            
        except Exception as e:
            logger.error(f"Error in get_relevant_documents_with_scores: {e}")
            return []

def main() -> None:
    """Test the vector store"""
    from smartborrow.rag.document_loader import SmartBorrowDocumentLoader
    
    # Load documents
    loader = SmartBorrowDocumentLoader()
    processed_docs = loader.load_processed_data()
    documents = loader.create_langchain_documents(processed_docs)
    
    # Create vector store
    vectorstore = SmartBorrowVectorStore()
    vs = vectorstore.create_vectorstore(documents)
    
    # Test search
    query = "What is the maximum Pell Grant amount?"
    results = vectorstore.similarity_search(query, k=3)
    
    logger.info("Search results for: {query}")
    for i, doc in enumerate(results):
        logger.info("\nResult {i+1}:")
        logger.info("Content: {doc.page_content[:200]}...")
        logger.info("Metadata: {doc.metadata}")
    
    # Get stats
    stats = vectorstore.get_vectorstore_stats()
    logger.info("\nVector store stats: {stats}")

if __name__ == "__main__":
    main() 