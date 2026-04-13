from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime
from app.db.base import Base

class DocumentAsset(Base):
    __tablename__ = "document_assets"

    id = Column(Integer, primary_key=True, index=True)
    file_name = Column(String)
    file_path = Column(String)
    file_type = Column(String) # pdf, docx, md, etc.
    sha256 = Column(String, unique=True)
    source_type = Column(String) # cv, portfolio, github, private_report, certificate
    extracted_text = Column(Text, nullable=True)
    parsed_json = Column(Text, nullable=True) # JSON string
    relevance_tags = Column(Text, nullable=True) # Comma separated
    created_at = Column(DateTime, default=datetime.utcnow)
