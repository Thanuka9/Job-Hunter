from app.db.base import Base
from app.db.session import engine
from app.models.candidate_profile import CandidateProfile, CandidateSkill
from app.models.document_asset import DocumentAsset
from app.models.job_posting import JobPosting, JobScore
from app.models.application import Application, GeneratedDocument
from app.models.audit_log import AuditLog

def init_db():
    # Import all models here to ensure they are registered on Base
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    print("Initializing the database...")
    init_db()
    print("Database initialized successfully.")
