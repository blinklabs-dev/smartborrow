"""Core data models for SmartBorrow AI Platform."""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, field_validator, ConfigDict


class LoanType(str, Enum):
    """Types of student loans."""
    FEDERAL_SUBSIDIZED = "federal_subsidized"
    FEDERAL_UNSUBSIDIZED = "federal_unsubsidized"
    FEDERAL_PLUS = "federal_plus"
    PRIVATE = "private"


class LoanStatus(str, Enum):
    """Loan application status."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    UNDER_REVIEW = "under_review"


class RiskLevel(str, Enum):
    """Risk assessment levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class BorrowerProfile(BaseModel):
    """Student borrower profile information."""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "borrower_id": "BOR123456",
                "age": 22,
                "credit_score": 720,
                "annual_income": "35000",
                "employment_status": "part_time",
                "education_level": "undergraduate",
                "major": "Computer Science",
                "school_name": "State University",
                "graduation_date": "2024-05-15T00:00:00",
                "existing_debt": "5000"
            }
        }
    )
    
    borrower_id: str = Field(..., description="Unique borrower identifier")
    age: int = Field(..., ge=17, le=65, description="Borrower age")
    credit_score: Optional[int] = Field(None, ge=300, le=850, description="Credit score")
    annual_income: Decimal = Field(..., ge=0, description="Annual income in USD")
    employment_status: str = Field(..., description="Current employment status")
    education_level: str = Field(..., description="Highest education level")
    major: str = Field(..., description="Field of study")
    school_name: str = Field(..., description="Educational institution")
    graduation_date: datetime = Field(..., description="Expected/actual graduation date")
    existing_debt: Decimal = Field(default=Decimal("0"), ge=0, description="Existing debt amount")


class LoanApplication(BaseModel):
    """Student loan application."""
    
    application_id: str = Field(..., description="Unique application identifier")
    borrower_profile: BorrowerProfile = Field(..., description="Borrower information")
    loan_type: LoanType = Field(..., description="Type of loan requested")
    requested_amount: Decimal = Field(..., gt=0, description="Requested loan amount")
    loan_term_months: int = Field(..., gt=0, le=360, description="Loan term in months")
    purpose: str = Field(..., description="Purpose of the loan")
    cosigner_available: bool = Field(default=False, description="Cosigner availability")
    application_date: datetime = Field(default_factory=datetime.now, description="Application submission date")
    status: LoanStatus = Field(default=LoanStatus.PENDING, description="Application status")
    
    @field_validator('loan_term_months')
    @classmethod
    def validate_loan_term(cls, v: int) -> int:
        """Validate loan term is in common increments."""
        if v % 12 != 0:
            raise ValueError('Loan term should be in 12-month increments')
        return v


class RiskAssessment(BaseModel):
    """AI-generated risk assessment for loan application."""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "assessment_id": "RISK123456",
                "application_id": "APP123456",
                "risk_level": "medium",
                "risk_score": 0.35,
                "risk_factors": ["Limited credit history", "Part-time employment"],
                "mitigating_factors": ["Strong academic performance", "STEM major"],
                "recommended_terms": {
                    "interest_rate": 6.5,
                    "max_amount": 25000,
                    "required_cosigner": False
                },
                "confidence_score": 0.87,
                "model_version": "smartborrow-v1.0"
            }
        }
    )
    
    assessment_id: str = Field(..., description="Unique assessment identifier")
    application_id: str = Field(..., description="Associated application ID")
    risk_level: RiskLevel = Field(..., description="Overall risk level")
    risk_score: float = Field(..., ge=0.0, le=1.0, description="Numerical risk score (0-1)")
    risk_factors: List[str] = Field(..., description="Identified risk factors")
    mitigating_factors: List[str] = Field(default_factory=list, description="Positive factors")
    recommended_terms: Dict[str, Any] = Field(..., description="Recommended loan terms")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="AI confidence in assessment")
    assessment_date: datetime = Field(default_factory=datetime.now, description="Assessment date")
    model_version: str = Field(..., description="AI model version used")


class LoanRecommendation(BaseModel):
    """AI-generated loan recommendations."""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "recommendation_id": "REC123456",
                "borrower_id": "BOR123456",
                "recommended_loans": [
                    {
                        "loan_type": "federal_subsidized",
                        "max_amount": 5500,
                        "interest_rate": 5.5,
                        "benefits": ["Interest paid by government during school"]
                    }
                ],
                "personalized_advice": "Based on your profile, federal loans offer the best terms...",
                "alternative_options": ["Work-study programs", "Scholarships", "Grants"],
                "next_steps": ["Complete FAFSA", "Contact financial aid office"]
            }
        }
    )
    
    recommendation_id: str = Field(..., description="Unique recommendation identifier")
    borrower_id: str = Field(..., description="Associated borrower ID")
    recommended_loans: List[Dict[str, Any]] = Field(..., description="List of recommended loan products")
    personalized_advice: str = Field(..., description="Personalized financial guidance")
    alternative_options: List[str] = Field(default_factory=list, description="Alternative financing options")
    next_steps: List[str] = Field(..., description="Recommended next steps")
    generated_date: datetime = Field(default_factory=datetime.now, description="Recommendation generation date")
    expires_date: datetime = Field(..., description="Recommendation expiration date")
