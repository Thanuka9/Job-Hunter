import os
import pypdf
import docx
from bs4 import BeautifulSoup
import trafilatura
import httpx
from typing import Optional

class ParserService:
    @staticmethod
    def parse_pdf(file_path: str) -> str:
        text = ""
        with open(file_path, "rb") as f:
            reader = pypdf.PdfReader(f)
            for page in reader.pages:
                text += page.extract_text() + "\n"
        return text

    @staticmethod
    def parse_docx(file_path: str) -> str:
        doc = docx.Document(file_path)
        text = "\n".join([para.text for para in doc.paragraphs])
        return text

    @staticmethod
    async def parse_url(url: str) -> str:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            if response.status_code == 200:
                downloaded = trafilatura.extract(response.text)
                return downloaded if downloaded else ""
        return ""

    @staticmethod
    def parse_markdown(file_path: str) -> str:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
