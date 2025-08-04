"""
SmartBorrow: AI-Powered Student Loan Intelligence Platform
==========================================================

A comprehensive AI system for student loan analysis, built for AIE7 certification.
Demonstrates advanced RAG, multi-agent systems, evaluation, and production deployment.

Modules:
--------
- core: Core business logic and data models
- rag: Retrieval Augmented Generation components (Sessions 3-4)
- agents: AI agent implementations (Sessions 5-6)  
- evaluation: Synthetic data generation and RAGAS evaluation (Sessions 7-8)
- retrieval: Advanced retrieval methods (Session 9)
- ui: User interface components (Streamlit, API)
- utils: Utility functions and helpers
- api: FastAPI backend implementation
"""

__version__ = "0.1.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

# Core imports for easy access
from .core.models import (
    LoanApplication,
    BorrowerProfile,
    RiskAssessment,
    LoanRecommendation
)

from .core.config import Settings, get_settings

__all__ = [
    "LoanApplication", 
    "BorrowerProfile", 
    "RiskAssessment", 
    "LoanRecommendation",
    "Settings",
    "get_settings"
]
