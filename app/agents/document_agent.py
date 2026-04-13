import json
from app.services.llm_service import LLMService

class DocumentAgent:
    def __init__(self):
        self.llm = LLMService()

    def extract_profile_data(self, text: str) -> dict:
        system_prompt = """
        You are an expert AI Resume Parser. Your goal is to extract structured information from a candidate's resume or profile text.
        Extract the following fields:
        - full_name
        - email
        - phone
        - location
        - linkedin_url
        - github_url
        - portfolio_url
        - summary (a professional summary)
        - skills (list of skills categorized by: Languages, Frameworks, Tools, Soft Skills, etc.)
        - years_experience (numerical)
        - projects (list of projects with name, description, tools, and impact)
        - experience (list of work experience with title, company, dates, and bullet points)
        
        If a field is not found, leave it as null.
        Respond ONLY with a valid JSON object.
        """
        
        prompt = f"Extract structured data from the following text:\n\n{text}"
        
        response = self.llm.get_structured_completion(prompt, system_prompt)
        return json.loads(response)

    def extract_evidence_snippets(self, text: str) -> list:
        system_prompt = """
        You are an evidence extraction agent. Your goal is to find "evidence snippets" from the candidate's background.
        An evidence snippet is a specific, quantifiable achievement or a strong statement of impact.
        Examples:
        - "Reduced processing time by 40% using optimized Python scripts."
        - "Led a team of 5 to deliver a revenue-critical dashboard in 2 months."
        
        Extract as many as you can find.
        Respond ONLY with a JSON list of snippets.
        """
        
        prompt = f"Find evidence snippets in the following text:\n\n{text}"
        
        response = self.llm.get_structured_completion(prompt, system_prompt)
        return json.loads(response)
