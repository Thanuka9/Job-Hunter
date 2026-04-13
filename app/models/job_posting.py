from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base

class JobPosting(Base):
    __tablename__ = "job_postings"

    id = Column(Integer, primary_key=True, index=True)
    external_job_id = Column(String, nullable=True)
    source_name = Column(String) # Greenhouse, Lever, LinkedIn, etc.
    source_url = Column(String)
    company_name = Column(String, index=True)
    title = Column(String, index=True)
    location = Column(String, nullable=True)
    job_type = Column(String, nullable=True) # Full-time, Contract, etc.
    workplace_type = Column(String, nullable=True) # Remote, On-site, Hybrid
    salary_text = Column(String, nullable=True)
    description_text = Column(Text)
    description_hash = Column(String, index=True)
    discovered_at = Column(DateTime, default=datetime.utcnow)
    application_url = Column(String, nullable=True)
    status = Column(String, default="discovered") # discovered, ranked, ignored

    scores = relationship("JobScore", back_populates="job")
    applications = relationship("Application", back_populates="job")

class JobScore(Base):
    __tablename__ = "job_scores"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("job_postings.id"))
    candidate_id = Column(Integer, ForeignKey("candidate_profiles.id"))
    overall_score = Column(Float)
    title_score = Column(Float)
    skills_score = Column(Float)
    seniority_score = Column(Float)
    location_score = Column(Float)
    portfolio_score = Column(Float)
    notes_json = Column(Text, nullable=True)
    apply_recommendation = Column(String) # strong apply, apply after review, optional, skip

    job = relationship("JobPosting", back_populates="scores")
