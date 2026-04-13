"""
Resume & Cover Letter Agent
Generates tailored documents for each job using GPT-4o.
"""

import os
import json
from datetime import datetime
from app.services.llm_service import LLMService
from app.config.constants import CANDIDATE_NAME, CANDIDATE_EMAIL, CANDIDATE_PHONE, LINKEDIN_URL, GITHUB_URL, PORTFOLIO_URL, CV_PATH

def get_cv_content():
    """Dynamically load CV text from the configured path."""
    from generated.logs.cv_extracted_text.txt import CV_TEXT_FILE # Try to use extracted text first
    path = "generated/logs/cv_extracted_text.txt"
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    
    # Simple fallback placeholder for GitHub code safety
    return "Candidate Career History Context (Loaded from local CV PDF/Vector DB)"

CV_CONTENT = get_cv_content()


class ResumeAgent:

    def __init__(self):
        self.llm = LLMService()
        os.makedirs("generated/resumes", exist_ok=True)
        os.makedirs("generated/cover_letters", exist_ok=True)
        os.makedirs("generated/answers", exist_ok=True)

    def tailor_resume(self, job: dict) -> str:
        """Use the user-provided PDF CV for uploading, falling back to text generation if missing."""
        if os.path.exists(CV_PATH):
            return CV_PATH

        system_prompt = """
        You are an expert resume writer. Your task is to tailor a candidate's resume for a specific job posting.
        Rules (STRICT):
        - Never invent qualifications, skills, or experience not in the original CV
        - Keep all facts accurate — same companies, dates, and titles
        - Reorder and emphasize bullet points to match the job requirements
        - Use keywords from the job description naturally
        - Make bullet points specific, quantified, and impactful
        - Keep it clean, ATS-friendly, professional
        Output: a complete, formatted plain-text resume ready to copy-paste or save as a text file.
        No markdown. No code blocks. Just the resume text.
        """
        prompt = f"""
        Tailor this resume for the following job. Reorder priorities, insert relevant keywords, emphasize matching skills.
        DO NOT add any qualifications not in the original resume.
        
        JOB:
        Title: {job['title']}
        Company: {job['company_name']}
        Location: {job.get('location', '')} | {job.get('workplace_type', '')}
        Description: {job.get('description_text', '')[:2000]}
        
        ORIGINAL RESUME:
        {CV_CONTENT}
        
        Key fit reasons to emphasize: {', '.join(job.get('fit_reasons', []))}
        
        Output the complete tailored resume now:
        """
        content = self.llm.get_completion(prompt, system_prompt, model="gpt-4o")

        # Save to file
        safe_company = "".join(c if c.isalnum() else "_" for c in job["company_name"])
        safe_title   = "".join(c if c.isalnum() else "_" for c in job["title"])[:40]
        filename = f"generated/resumes/{safe_company}_{safe_title}.txt"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)

        return filename

    def write_cover_letter(self, job: dict) -> str:
        """Generate a tailored cover letter (Cached)."""
        safe_company = "".join(c if c.isalnum() else "_" for c in job["company_name"])
        safe_title   = "".join(c if c.isalnum() else "_" for c in job["title"])[:40]
        filename = f"generated/cover_letters/{safe_company}_{safe_title}.txt"

        if os.path.exists(filename):
            return filename

        system_prompt = """
You are an expert cover letter writer. Write a compelling, specific, and honest cover letter.
Rules:
- Reference real projects and achievements from the candidate's background
- Personalize to the company and role — show you know what they do
- Be concise (300-400 words max)
- No generic phrases like "I am writing to express my interest"
- Show business value clearly
- Never claim experience or skills not in the CV
- Professional but warm tone
Output: Complete cover letter text. No markdown, no code blocks.
"""
        prompt = f"""
Write a tailored cover letter for Thanuka applying to this job.

JOB:
Title: {job['title']}
Company: {job['company_name']}
Location: {job.get('location', '')} | {job.get('workplace_type', '')}
Description: {job.get('description_text', '')[:2000]}
Fit Reasons: {', '.join(job.get('fit_reasons', []))}
Gaps to acknowledge: {', '.join(job.get('gaps', []))}

CANDIDATE:
{CV_CONTENT[:2000]}

Write the cover letter now. Start with "Dear Hiring Team" or the specific team name if inferable.
"""
        content = self.llm.get_completion(prompt, system_prompt, model="gpt-4o")

        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)

        return filename

    def generate_answers(self, job: dict) -> dict:
        """Generate stock answers for common application questions (Cached)."""
        safe_company = "".join(c if c.isalnum() else "_" for c in job["company_name"])
        safe_title   = "".join(c if c.isalnum() else "_" for c in job["title"])[:40]
        filename = f"generated/answers/{safe_company}_{safe_title}.json"

        if os.path.exists(filename):
            with open(filename, "r", encoding="utf-8") as f:
                try:
                    return json.load(f)
                except Exception:
                    pass # Fall back to generating if corrupt

        system_prompt = """
You are an expert career coach generating application answers for a candidate.
Rules: answers must be truthful, based only on verified background, professional, and specific.
Return JSON with question-answer pairs.
"""
        prompt = f"""
Generate answers to these common application questions for this job application.
Keep answers factual and based on Thanuka's real background only.

JOB: {job['title']} at {job['company_name']}

Questions to answer:
1. Tell us about yourself (200 words max)
2. Why do you want this role? (150 words max)
3. Why do you want to work at {job['company_name']}? (150 words max)
4. Describe a relevant project you are proud of (200 words max)
5. What is your experience with the key skills for this role? (150 words max)

CANDIDATE BACKGROUND:
{CV_CONTENT[:2000]}

Return JSON: {{"q1": "...", "q2": "...", "q3": "...", "q4": "...", "q5": "..."}}
"""
        try:
            response = self.llm.get_structured_completion(prompt, system_prompt, model="gpt-4o-mini")
            answers  = json.loads(response)
        except Exception:
            answers = {}

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(answers, f, indent=2)

        return answers
