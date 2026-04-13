from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime
from app.db.base import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String) # submission, error, manual_override, document_generation
    reference_id = Column(String, nullable=True) # ID of related entity
    event_payload = Column(Text, nullable=True) # JSON details
    screenshot_path = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
