from sqlalchemy import Column, Integer, String, Text, DateTime, Float, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base

class CandidateProfile(Base):
    __tablename__ = "candidate_profiles"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, index=True)
    email = Column(String, index=True)
    phone = Column(String, nullable=True)
    location = Column(String, nullable=True)
    linkedin_url = Column(String, nullable=True)
    github_url = Column(String, nullable=True)
    portfolio_url = Column(String, nullable=True)
    target_roles = Column(Text, nullable=True) # JSON or Comma separated
    preferred_locations = Column(Text, nullable=True)
    remote_preference = Column(String, nullable=True)
    salary_min = Column(Float, nullable=True)
    salary_max = Column(Float, nullable=True)
    visa_notes = Column(Text, nullable=True)
    work_authorization_notes = Column(Text, nullable=True)
    years_experience = Column(Float, nullable=True)
    summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    skills = relationship("CandidateSkill", back_populates="candidate")

class CandidateSkill(Base):
    __tablename__ = "candidate_skills"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidate_profiles.id"))
    skill_name = Column(String, index=True)
    category = Column(String, nullable=True) # Languages, Frameworks, Tools, etc.
    confidence = Column(Float, default=1.0)
    source_document_id = Column(Integer, ForeignKey("document_assets.id"), nullable=True)

    candidate = relationship("CandidateProfile", back_populates="skills")
