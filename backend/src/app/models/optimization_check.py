from sqlalchemy import Column, Integer, String, Float, Date, JSON

from ..core.database import Base

class OptimizationCheck(Base):
    __tablename__ = "optimization_checks"

    id = Column(String, primary_key=True, index=True)
    slug = Column(String, unique=True, index=True, nullable=False)
    title = Column(String, nullable=False)
    category = Column(String, index=True)
    subcategory = Column(String, index=True)
    impact_level = Column(String)
    complexity = Column(String)
    estimated_savings_pct = Column(Float)
    effort_minutes = Column(Integer)
    prerequisites = Column(JSON)  # Storing list as JSON
    tags = Column(JSON)  # Storing list as JSON
    last_reviewed = Column(Date)
    status = Column(String)
    version = Column(Integer)
    description = Column(String)
    how_to_implement = Column(String)
    code_snippet = Column(String)
    success_indicators = Column(String)
    when_to_use = Column(String)
