"""
Job Hunter AI Agent - Startup Runner
Runs all available system checks and ingests the CV (with or without OpenAI).
"""

import os
import sys
import json
import hashlib
import traceback
from dotenv import load_dotenv

load_dotenv()

# Helpers
def ok(msg):     print(f"  [OK]   {msg}")
def warn(msg):   print(f"  [WARN] {msg}")
def err(msg):    print(f"  [ERR]  {msg}")
def info(msg):   print(f"  [-->]  {msg}")
def header(msg): print(f"\n{'='*55}\n  {msg}\n{'='*55}")

# 1. Environment Check
header("1 / 5  Environment Check")

api_key     = os.getenv("OPENAI_API_KEY", "")
db_url      = os.getenv("DATABASE_URL", "sqlite:///./job_hunter.db")
ai_enabled  = bool(api_key) and "your_openai_api_key" not in api_key

ok(f"Project root   : D:\\Job Hunter")
ok(f"Database URL   : {db_url}")

if ai_enabled:
    ok(f"OpenAI API key : ****{api_key[-6:]} (AI features ENABLED)")
else:
    warn("OpenAI API key : NOT SET - AI extraction will be skipped")
    info("To enable AI, add your key to .env -> OPENAI_API_KEY=sk-...")

# 2. Package Check
header("2 / 5  Package Check")
REQUIRED = ["fastapi", "sqlalchemy", "pypdf", "docx", "openai", "httpx", "streamlit"]
for pkg in REQUIRED:
    try:
        __import__(pkg)
        ok(pkg)
    except ImportError:
        err(f"{pkg}  - run: pip install {pkg}")

# 3. Database Initialisation
header("3 / 5  Database Initialisation")

try:
    from app.db.init_db import init_db
    init_db()
    ok("All tables created / verified in job_hunter.db")
except Exception as e:
    err(f"DB init failed: {e}")
    traceback.print_exc()

# 4. CV Parsing
header("4 / 5  CV Parsing")

cv_dir   = os.path.join("data", "cv")
cv_files = [f for f in os.listdir(cv_dir) if f.lower().endswith(".pdf")]

if not cv_files:
    err("No PDF found in data/cv/  - place your CV there and re-run.")
else:
    cv_path = os.path.join(cv_dir, cv_files[0])
    ok(f"Found CV: {cv_files[0]}")

    try:
        import pypdf
        with open(cv_path, "rb") as f:
            reader = pypdf.PdfReader(f)
            pages  = len(reader.pages)
            text   = "\n".join(p.extract_text() or "" for p in reader.pages)

        sha256 = hashlib.sha256(open(cv_path, "rb").read()).hexdigest()[:12]
        ok(f"Extracted {pages} page(s) - {len(text)} characters - SHA256: {sha256}...")

        # Quick local keyword extraction (no AI needed)
        keywords = []
        tech_words = [
            "Python","SQL","Machine Learning","Deep Learning","NLP","FastAPI",
            "React","TensorFlow","PyTorch","Pandas","NumPy","Power BI",
            "Tableau","Azure","AWS","Docker","Kubernetes","scikit-learn",
            "LangChain","OpenAI","Streamlit","Django","Flask","PostgreSQL",
            "Data Science","Analytics","AI","ML","Full-Stack","REST API"
        ]
        for kw in tech_words:
            if kw.lower() in text.lower():
                keywords.append(kw)

        print("\n  Skills detected in CV (keyword scan):")
        for i in range(0, len(keywords), 6):
            print("    " + "  |  ".join(keywords[i:i+6]))

        # Save extracted text for AI step
        os.makedirs("generated/logs", exist_ok=True)
        with open("generated/logs/cv_extracted_text.txt", "w", encoding="utf-8") as f:
            f.write(text)
        ok("Raw CV text saved -> generated/logs/cv_extracted_text.txt")

        if ai_enabled:
            info("Running AI profile extraction via OpenAI GPT-4o...")
            from app.db.session import SessionLocal
            from app.agents.profile_agent import ProfileAgent
            db = SessionLocal()
            try:
                agent = ProfileAgent(db)
                profile = agent.ingest_cv(cv_path)
                ok(f"Profile built:  {profile.full_name}")
                ok(f"Email:          {profile.email}")
                ok(f"Location:       {profile.location}")
                ok(f"Experience:     {profile.years_experience} years")
                from app.models.candidate_profile import CandidateSkill
                count = db.query(CandidateSkill).filter(CandidateSkill.candidate_id == profile.id).count()
                ok(f"Skills stored:  {count}")
            finally:
                db.close()
        else:
            warn("Skipping AI extraction (no API key). Keyword scan complete above.")

    except Exception as e:
        err(f"CV parsing failed: {e}")
        traceback.print_exc()

# 5. System Status
header("5 / 5  System Status")

checks = {
    "Database (SQLite)":    os.path.exists("job_hunter.db"),
    "CV in data/cv/":       bool(cv_files) if "cv_files" in dir() else False,
    "Output dirs exist":    all(os.path.isdir(d) for d in ["generated/resumes","generated/cover_letters","generated/logs"]),
    "AI features enabled":  ai_enabled,
    ".env configured":      os.path.exists(".env"),
}

for label, status in checks.items():
    if status: ok(label)
    else:      warn(f"{label}  (not ready)")

print(f"\n{'='*55}")
if ai_enabled:
    print("  [OK] Job Hunter AI Agent is fully operational!")
    print("  Run the dashboard:  streamlit run dashboard/streamlit_app.py")
else:
    print("  [OFFLINE] Job Hunter is running in OFFLINE mode.")
    print("  Add OPENAI_API_KEY to .env to enable AI features.")
print(f"{'='*55}\n")
