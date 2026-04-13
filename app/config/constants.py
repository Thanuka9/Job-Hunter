import os
from dotenv import load_dotenv

load_dotenv()

# Candidate Information
CANDIDATE_NAME = os.getenv("CANDIDATE_NAME", "Your Name")
CANDIDATE_EMAIL = os.getenv("CANDIDATE_EMAIL", "your.email@example.com")
CANDIDATE_PHONE = os.getenv("CANDIDATE_PHONE", "+00 000 000 000")
LINKEDIN_URL = os.getenv("LINKEDIN_URL", "https://www.linkedin.com/in/yourid/")
GITHUB_URL = os.getenv("GITHUB_URL", "https://github.com/yourusername")
PORTFOLIO_URL = os.getenv("PORTFOLIO_URL", "https://yourportfolio.careers/")

# Pipeline Defaults
DEFAULT_MAX_JOBS = int(os.getenv("MAX_JOBS", "50"))
DEFAULT_MIN_SCORE = int(os.getenv("MIN_SCORE", "65"))

# Paths
PROJECT_ROOT = os.getenv("PROJECT_ROOT", os.getcwd())
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
GENERATED_DIR = os.path.join(PROJECT_ROOT, "generated")

CV_PATH = os.path.join(PROJECT_ROOT, "the candidate  CV.pdf")
# Fallback to older path if needed
if not os.path.exists(CV_PATH):
    CV_PATH = os.path.join(DATA_DIR, "cv", "the candidate  CV.pdf")
