"""Configuration management for SmartBorrow AI Platform.

This module provides centralized configuration management using Pydantic Settings
for type-safe environment variable handling and validation.
"""

import logging

logger = logging.getLogger(__name__)

import os
from functools import lru_cache
from typing import Optional, List, Dict, Any
from pydantic_settings import BaseSettings
from pydantic import Field, ConfigDict, validator


class Settings(BaseSettings):
    """Application settings loaded from environment variables.
    
    Provides type-safe configuration management with automatic validation
    and environment variable loading. All settings can be overridden
    via environment variables or .env file.
    """
    
    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",  # Allows extra fields in .env without errors
        validate_default=True
    )
    
    # Application Configuration
    app_name: str = Field(
        default="SmartBorrow AI Platform",
        description="Application name"
    )
    environment: str = Field(
        default="development",
        alias="ENVIRONMENT",
        description="Application environment (development, staging, production)"
    )
    debug: bool = Field(
        default=True,
        alias="DEBUG",
        description="Enable debug mode"
    )
    
    # API Keys and External Services
    openai_api_key: Optional[str] = Field(
        default=None,
        alias="OPENAI_API_KEY",
        description="OpenAI API key for LLM access"
    )
    anthropic_api_key: Optional[str] = Field(
        default=None,
        alias="ANTHROPIC_API_KEY",
        description="Anthropic API key for Claude access"
    )
    cohere_api_key: Optional[str] = Field(
        default=None,
        alias="COHERE_API_KEY",
        description="Cohere API key for embeddings"
    )
    langchain_api_key: Optional[str] = Field(
        default=None,
        alias="LANGCHAIN_API_KEY",
        description="LangChain API key for tracing"
    )
    
    # LangSmith Configuration
    langchain_tracing_v2: bool = Field(
        default=True,
        alias="LANGCHAIN_TRACING_V2",
        description="Enable LangSmith tracing"
    )
    langchain_endpoint: Optional[str] = Field(
        default=None,
        alias="LANGCHAIN_ENDPOINT",
        description="LangSmith endpoint URL"
    )
    langchain_project: str = Field(
        default="smartborrow-aie7",
        alias="LANGCHAIN_PROJECT",
        description="LangSmith project name"
    )
    
    # Vector Database Configuration
    chroma_db_impl: Optional[str] = Field(
        default=None,
        alias="CHROMA_DB_IMPL",
        description="ChromaDB implementation type"
    )
    chroma_persist_directory: str = Field(
        default="./data/chromadb",
        alias="CHROMA_PERSIST_DIRECTORY",
        description="ChromaDB persistence directory"
    )
    qdrant_url: Optional[str] = Field(
        default=None,
        alias="QDRANT_URL",
        description="Qdrant vector database URL"
    )
    qdrant_api_key: Optional[str] = Field(
        default=None,
        alias="QDRANT_API_KEY",
        description="Qdrant API key"
    )
    
    # Financial Data APIs
    alpha_vantage_api_key: Optional[str] = Field(
        default=None,
        alias="ALPHA_VANTAGE_API_KEY",
        description="Alpha Vantage API key for financial data"
    )
    
    # Logging Configuration
    log_level: str = Field(
        default="INFO",
        alias="LOG_LEVEL",
        description="Logging level (DEBUG, INFO, WARNING, ERROR)"
    )
    log_format: Optional[str] = Field(
        default=None,
        alias="LOG_FORMAT",
        description="Custom log format string"
    )
    
    # API Configuration
    api_host: str = Field(
        default="0.0.0.0",
        alias="API_HOST",
        description="API server host"
    )
    api_port: int = Field(
        default=8000,
        alias="API_PORT",
        description="API server port",
        ge=1,
        le=65535
    )
    api_reload: Optional[bool] = Field(
        default=None,
        alias="API_RELOAD",
        description="Enable API auto-reload"
    )
    
    # Streamlit Configuration
    streamlit_server_port: Optional[int] = Field(
        default=None,
        alias="STREAMLIT_SERVER_PORT",
        description="Streamlit server port",
        ge=1,
        le=65535
    )
    streamlit_server_address: Optional[str] = Field(
        default=None,
        alias="STREAMLIT_SERVER_ADDRESS",
        description="Streamlit server address"
    )
    
    # Model Configuration
    default_llm_model: str = Field(
        default="gpt-4-turbo-preview",
        alias="DEFAULT_LLM_MODEL",
        description="Default LLM model for text generation"
    )
    default_embedding_model: str = Field(
        default="text-embedding-3-small",
        alias="DEFAULT_EMBEDDING_MODEL",
        description="Default embedding model"
    )
    default_rerank_model: Optional[str] = Field(
        default=None,
        alias="DEFAULT_RERANK_MODEL",
        description="Default reranking model"
    )
    default_temperature: float = Field(
        default=0.1,
        alias="DEFAULT_TEMPERATURE",
        description="Default temperature for LLM generation",
        ge=0.0,
        le=2.0
    )
    default_max_tokens: int = Field(
        default=4000,
        alias="DEFAULT_MAX_TOKENS",
        description="Default max tokens for LLM generation",
        ge=1,
        le=32000
    )
    default_top_p: Optional[float] = Field(
        default=None,
        alias="DEFAULT_TOP_P",
        description="Default top-p for LLM generation",
        ge=0.0,
        le=1.0
    )
    
    # RAG Configuration
    default_chunk_size: int = Field(
        default=1000,
        alias="DEFAULT_CHUNK_SIZE",
        description="Default chunk size for document processing",
        ge=100,
        le=10000
    )
    default_chunk_overlap: int = Field(
        default=200,
        alias="DEFAULT_CHUNK_OVERLAP",
        description="Default chunk overlap for document processing",
        ge=0,
        le=5000
    )
    default_retrieval_k: int = Field(
        default=5,
        alias="DEFAULT_RETRIEVAL_K",
        description="Default number of documents to retrieve",
        ge=1,
        le=100
    )
    default_rerank_k: Optional[int] = Field(
        default=None,
        alias="DEFAULT_RERANK_K",
        description="Default number of documents to rerank",
        ge=1,
        le=100
    )
    enable_hybrid_search: Optional[bool] = Field(
        default=None,
        alias="ENABLE_HYBRID_SEARCH",
        description="Enable hybrid search functionality"
    )
    
    # Evaluation Configuration
    ragas_sample_size: Optional[int] = Field(
        default=None,
        alias="RAGAS_SAMPLE_SIZE",
        description="Sample size for RAGAS evaluation",
        ge=1,
        le=10000
    )
    ragas_timeout: Optional[int] = Field(
        default=None,
        alias="RAGAS_TIMEOUT",
        description="Timeout for RAGAS evaluation in seconds",
        ge=1,
        le=3600
    )
    synthetic_data_size: Optional[int] = Field(
        default=None,
        alias="SYNTHETIC_DATA_SIZE",
        description="Size of synthetic data to generate",
        ge=1,
        le=100000
    )
    
    @validator('environment')
    def validate_environment(cls, v: str) -> str:
        """Validate environment setting."""
        valid_environments = ['development', 'staging', 'production', 'test']
        if v not in valid_environments:
            raise ValueError(f'Environment must be one of: {valid_environments}')
        return v
    
    @validator('log_level')
    def validate_log_level(cls, v: str) -> str:
        """Validate log level setting."""
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f'Log level must be one of: {valid_levels}')
        return v.upper()
    
    def get_model_config(self) -> Dict[str, Any]:
        """Get model configuration as dictionary."""
        return {
            'model_name': self.default_llm_model,
            'temperature': self.default_temperature,
            'max_tokens': self.default_max_tokens,
            'top_p': self.default_top_p,
        }
    
    def get_rag_config(self) -> Dict[str, Any]:
        """Get RAG configuration as dictionary."""
        return {
            'chunk_size': self.default_chunk_size,
            'chunk_overlap': self.default_chunk_overlap,
            'retrieval_k': self.default_retrieval_k,
            'rerank_k': self.default_rerank_k,
            'enable_hybrid_search': self.enable_hybrid_search,
        }
    
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment.lower() == 'production'
    
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment.lower() == 'development'


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings.
    
    Returns:
        Settings: Application configuration object
        
    Note:
        Uses LRU cache to avoid repeated environment variable parsing.
    """
    return Settings()


def get_model_config() -> Dict[str, Any]:
    """Get model configuration.
    
    Returns:
        Dict[str, Any]: Model configuration dictionary
    """
    return get_settings().get_model_config()


def get_rag_config() -> Dict[str, Any]:
    """Get RAG configuration.
    
    Returns:
        Dict[str, Any]: RAG configuration dictionary
    """
    return get_settings().get_rag_config()
