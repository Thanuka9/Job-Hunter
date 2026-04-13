import os
import openai
from dotenv import load_dotenv

load_dotenv()

class LLMService:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables.")
        self.client = openai.OpenAI(api_key=self.api_key)

    def get_completion(self, prompt: str, system_prompt: str = "You are a helpful assistant.", model: str = "gpt-4o") -> str:
        response = self.client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1
        )
        return response.choices[0].message.content

    def get_structured_completion(self, prompt: str, system_prompt: str = "You are a helpful assistant.", model: str = "gpt-4o", response_format: dict = None) -> str:
        # For simple JSON mode, ensure system prompt mentions JSON
        response = self.client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": f"{system_prompt} Respond strictly in valid JSON format."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.1
        )
        return response.choices[0].message.content
