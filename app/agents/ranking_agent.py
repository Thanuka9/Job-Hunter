"""
Ranking Agent
Scores each discovered job against Thanuka's profile using GPT-4o.
"""

import json
import os
from typing import Dict, List, Optional
from app.services.llm_service import LLMService
from app.config.constants import CANDIDATE_NAME, LINKEDIN_URL, GITHUB_URL, PORTFOLIO_URL, CV_PATH
from app.models.job_posting import JobPosting, JobScore

CANDIDATE_SUMMARY = f"""
Name: {CANDIDATE_NAME}
Title: AI Engineer | Data Scientist | Full-Stack Developer
Experience: 7+ years (healthcare analytics, ML, full-stack)
Current Role: Assistant Manager, Collective RCM (healthcare revenue cycle)
Education: Master of Business Analytics (University of Colombo), BSc Computer Systems & Networking (Greenwich)

Core Skills:
- Python (Pandas, NumPy, Scikit-learn, TensorFlow, Flask)
- SQL (MySQL, PostgreSQL), REST APIs, HTML/CSS/JavaScript
- Machine Learning: Regression, Classification, Clustering, Ensemble Learning, NLP (TF-IDF, SVD, VADER)
- Data Engineering: ETL Pipelines, Large-scale data handling (~7M+ records)
- Visualisation: Power BI, Matplotlib, Plotly, Dashboard Development
- Tools: Git, SQLAlchemy, Streamlit

Key Projects:
- ReviewRadar AI: NLP sentiment pipeline on 7M records, ensemble modeling
- Predictive Payment Analysis: ML models (Random Forest, Neural Networks) for healthcare payment prediction
- Collective Intranet System: Full-stack Flask app with 2FA, RBAC, and KPI dashboards

Certifications: Google Data Analytics Professional, CCNA, Diploma in Telecom

Preferences: Remote or Hybrid preferred. Open to Mid-Senior roles. Healthcare, fintech, SaaS, AI/ML domain preferred. Highly prioritize roles in Sri Lanka, Dubai, and Singapore.
"""


class RankingAgent:

    def __init__(self, db=None):
        self.llm = LLMService()
        self.db  = db

    # Locations that get a hard priority boost AFTER GPT scoring
    PRIORITY_LOCATIONS = [
        "sri lanka", "colombo", "kandy", "galle",
        "dubai", "uae", "abu dhabi", "sharjah",
        "singapore",
    ]

    def score_job(self, job: Dict) -> Dict:
        """Score a single job against Thanuka's profile. Returns job + scores."""
        system_prompt = """
You are a career matching expert. Score how well a job fits a candidate's profile.
Score each dimension out of the given weight and return JSON only.

IMPORTANT PRIORITY RULE:
- If the job is located in Sri Lanka, Dubai/UAE, or Singapore — award the MAXIMUM location_score (10).
  These are the candidate's top priority markets and beat any other location.
- Remote roles also get maximum location_score.

Scoring dimensions (max points shown):
- title_score: 20      (how well the job title aligns)
- skills_score: 25     (how many required skills the candidate has)
- seniority_score: 15  (seniority level fit)
- location_score: 10   (10 = Sri Lanka / Dubai / Singapore / Remote; 5 = other Asia; 2 = Western)
- portfolio_score: 10  (how relevant their projects are)
- domain_score: 10     (industry/domain fit)
- feasibility_score: 5 (ease of application, likelihood of ATS passing)
- strategic_score: 5   (company prestige and growth opportunity)

Return schema:
{
  "title_score": <0-20>,
  "skills_score": <0-25>,
  "seniority_score": <0-15>,
  "location_score": <0-10>,
  "portfolio_score": <0-10>,
  "domain_score": <0-10>,
  "feasibility_score": <0-5>,
  "strategic_score": <0-5>,
  "overall_score": <sum of above>,
  "recommendation": "<strong apply|apply after review|optional|skip>",
  "fit_reasons": ["<reason1>", "<reason2>"],
  "gaps": ["<gap1>"]
}
"""
        job_text = f"""
Job Title: {job['title']}
Company: {job['company_name']}
Location: {job.get('location', 'Unknown')} ({job.get('workplace_type', 'Unknown')})
Source: {job.get('source_name', 'Unknown')}
Description (first 1500 chars): {job.get('description_text', '')[:1500]}
"""
        prompt = f"""
CANDIDATE PROFILE:
{CANDIDATE_SUMMARY}

JOB POSTING:
{job_text}

Score this job fit and return ONLY valid JSON matching the schema above.
Remember: Sri Lanka / Dubai / Singapore / Remote = MAXIMUM location_score.
"""
        try:
            response = self.llm.get_structured_completion(prompt, system_prompt, model="gpt-4o-mini")
            scores = json.loads(response)
            result = {**job, **scores}

            # Hard post-score boost for priority locations
            loc = (job.get("location", "") + " " + job.get("source_name", "")).lower()
            workplace = job.get("workplace_type", "").lower()
            is_priority = (
                any(pl in loc for pl in self.PRIORITY_LOCATIONS)
                or workplace == "remote"
                or job.get("source_name") == "TopJobs"  # TopJobs is always Sri Lanka
            )
            if is_priority:
                boost = 15  # Hard +15 points for priority regions
                result["overall_score"] = min(100, result.get("overall_score", 0) + boost)
                result.setdefault("fit_reasons", []).insert(0, "Priority location: Sri Lanka / Dubai / Singapore / Remote")

            return result
        except Exception as e:
            # Fallback scores on error
            return {**job, "overall_score": 0, "recommendation": "skip", "fit_reasons": [], "gaps": [str(e)]}

    def rank_jobs(self, jobs: List[Dict], min_score: int = 60) -> List[Dict]:
        """Score and rank all jobs, filter by minimum score."""
        print(f"  [Ranking] Scoring {len(jobs)} jobs against profile...")
        scored = []
        total = len(jobs)
        for i, job in enumerate(jobs, 1):
            # Check DB for existing score
            if self.db:
                existing_score = self.db.query(JobScore).join(JobPosting).filter(
                    JobPosting.description_hash == job.get("description_hash")
                ).first()
                if existing_score:
                    # Map DB record back to result format
                    job["overall_score"] = existing_score.overall_score
                    job["fit_reasons"] = json.loads(existing_score.notes_json) if existing_score.notes_json else []
                    job["recommendation"] = existing_score.apply_recommendation
                    scored.append(job)
                    print(f"    [{i}/{total}] {job['company_name']} — {job['title'][:50]} | Cached Score: {job['overall_score']}/100")
                    continue

            result = self.score_job(job)
            score  = result.get("overall_score", 0)
            rec    = result.get("recommendation", "skip")
            print(f"    [{i}/{total}] {job['company_name']} — {job['title'][:50]} | Score: {score}/100 | {rec}")
            if score >= min_score:
                scored.append(result)

        scored.sort(key=lambda x: x.get("overall_score", 0), reverse=True)
        return scored
