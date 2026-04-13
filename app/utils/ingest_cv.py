import os
from app.db.session import SessionLocal
from app.agents.profile_agent import ProfileAgent
from dotenv import load_dotenv

load_dotenv()

def main():
    db = SessionLocal()
    try:
        agent = ProfileAgent(db)
        cv_dir = os.path.join("data", "cv")
        files = [f for f in os.listdir(cv_dir) if f.endswith(".pdf")]
        
        if not files:
            print("No CV found in data/cv")
            return
            
        cv_path = os.path.join(cv_dir, files[0])
        print(f"Ingesting CV: {cv_path}")
        
        # Check if OPENAI_API_KEY is set
        if not os.getenv("OPENAI_API_KEY") or "your_openai_api_key" in os.getenv("OPENAI_API_KEY"):
            print("ERROR: Please set a valid OPENAI_API_KEY in the .env file.")
            return

        profile = agent.ingest_cv(cv_path)
        print(f"Successfully ingested profile for: {profile.full_name}")
        print(f"Email: {profile.email}")
        print(f"Skills extracted: {db.query(CandidateSkill).filter(CandidateSkill.candidate_id == profile.id).count()}")
        
    finally:
        db.close()

if __name__ == "__main__":
    from app.models.candidate_profile import CandidateSkill # Import for count query
    main()
