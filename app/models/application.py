from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base

class Application(Base):
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidate_profiles.id"))
    job_id = Column(Integer, ForeignKey("job_postings.id"))
    source_name = Column(String)
    application_url = Column(String)
    status = Column(String, default="draft") # draft, submitted, rejected, interview, offer
    submission_mode = Column(String) # auto_safe, assisted_submit, manual
    submitted_at = Column(DateTime, nullable=True)
    approval_required = Column(Integer, default=1) # Boolean 0/1
    approval_status = Column(String, nullable=True) # pending, approved, denied
    notes = Column(Text, nullable=True)

    job = relationship("JobPosting", back_populates="applications")

class GeneratedDocument(Base):
    __tablename__ = "generated_documents"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidate_profiles.id"))
    job_id = Column(Integer, ForeignKey("job_postings.id"), nullable=True)
    doc_type = Column(String) # resume, cover_letter, answers
    file_path = Column(String)
    prompt_version = Column(String)
    source_snapshot = Column(Text, nullable=True) # References used for generation
    created_at = Column(DateTime, default=datetime.utcnow)
