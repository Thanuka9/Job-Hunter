import os
import json
import logging
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pydantic import BaseModel, Field
from typing import Dict, Any

logger = logging.getLogger("RAGService")

class RAGService:
    """
    RAG & LangChain Service for Production-Grade Querying
    Reads the user's PDF CV, splits it, creates a FAISS vector index, 
    and exposes LangChain-based retrieval logic for application questions.
    """
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(RAGService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
        
    def __init__(self):
        if self._initialized:
            return
            
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        self.vector_store = None
        self.retriever = None
        
        self._initialize_index()
        self._initialized = True
        
    def _initialize_index(self):
        index_dir = "data/faiss_index"
        data_dirs = ["data/cv", "data/portfolio", "data/github_exports"]
        try:
            # Check if persistent Vector DB exists
            if os.path.exists(index_dir):
                logger.info(f"  [RAG] Loading existing FAISS Vector DB from {index_dir}")
                self.vector_store = FAISS.load_local(index_dir, self.embeddings, allow_dangerous_deserialization=True)
                self.retriever = self.vector_store.as_retriever(search_kwargs={"k": 5})
                return
                
            logger.info("  [RAG] Scanning for multi-modal files to build new FAISS Vector DB...")
            all_documents = []
            
            for directory in data_dirs:
                if not os.path.isdir(directory):
                    continue
                for file in os.listdir(directory):
                    file_path = os.path.join(directory, file)
                    try:
                        if file.lower().endswith(".pdf"):
                            loader = PyPDFLoader(file_path)
                            all_documents.extend(loader.load())
                        elif file.lower().endswith((".txt", ".md")):
                            from langchain_community.document_loaders import TextLoader
                            loader = TextLoader(file_path, encoding='utf-8')
                            all_documents.extend(loader.load())
                    except Exception as fe:
                        logger.warning(f"  [RAG Warning] Failed to parse {file}: {fe}")
            
            if not all_documents:
                logger.warning(f"  [RAG] No CV, Portfolio, or Github documents found to index.")
                return
            
            # Use smaller chunks for more precise document retrieval
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
            splits = text_splitter.split_documents(all_documents)
            
            self.vector_store = FAISS.from_documents(splits, self.embeddings)
            
            # Persist the vector DB to disk!
            os.makedirs(index_dir, exist_ok=True)
            self.vector_store.save_local(index_dir)
            
            self.retriever = self.vector_store.as_retriever(search_kwargs={"k": 5})
            logger.info(f"  [RAG] Index initialized and saved with {len(splits)} chunks from all files.")
        except Exception as e:
            logger.error(f"  [RAG Error] Error initializing FAISS index: {e}")
            
    def answer_form_question(self, question: str, job_context: str = "") -> str:
        """
        Uses LangChain RAG pipeline to answer a specific application form question.
        Returns a concise string.
        """
        if not self.retriever:
            return "N/A"
            
        template = """You are an AI assistant answering job application questions on behalf of the candidate .
        Use the following pieces of retrieved context from his actual CV to answer the question.
        If the answer is not in the context, use your best logical judgment based on his general profile or output "N/A".
        Keep the answer concise, professional, and directly addressing the question.
        
        Context from CV:
        {context}
        
        Additional Job Context (if relevant):
        {job_context}
        
        Question: {question}
        
        Answer:"""
        
        prompt = PromptTemplate.from_template(template)
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        
        def format_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs)
            
        rag_chain = (
            {"context": self.retriever | format_docs, "question": RunnablePassthrough(), "job_context": lambda _: job_context}
            | prompt
            | llm
            | StrOutputParser()
        )
        
        return rag_chain.invoke(question)

    def extract_and_solve_form(self, form_fields: list, candidate_info: dict) -> dict:
        """
        Takes raw form fields extracted from JS and solves them using LangChain Structured Outputs.
        Includes RAG context from the CV to intelligently synthesize long-form text answers.
        """
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        
        # Gather potentially complex open-ended questions to retrieve RAG context
        complex_questions = [f["label"] for f in form_fields if f["type"].startswith("textarea") or (f["type"].startswith("input") and "how" in f["label"].lower())]
        rag_context = ""
        
        if self.retriever and complex_questions:
            try:
                # Query RAG for the longest/most complex question
                query = " ".join(complex_questions[:2])
                docs = self.retriever.invoke(query)
                rag_context = "\n\n".join([doc.page_content for doc in docs])
            except Exception as e:
                logger.error(f"  [RAG Error] Failed to retrieve context: {e}")
        
        system_msg = "You are an AI assistant automating a job application. Evaluate the unfilled form fields and determine the correct answer for each based strictly on the candidate's profile and CV context. Respond ONLY with a valid JSON dictionary."
        
        prompt_text = f"Candidate Profile Summary:\n{json.dumps(candidate_info, indent=2)}\n\n"
        if rag_context:
            prompt_text += f"Retrieved CV Context (for reference):\n{rag_context}\n\n"
            
        prompt_text += "Form Fields to fill:\n"
        
        for f in form_fields:
            prompt_text += f"- ID: {f.get('id', 'group')} | Type: {f['type']} | Label: {f['label']}\n"
            if f.get('options'):
                prompt_text += f"  Options: {f['options']}\n"
            if f.get('radio_options'):
                prompt_text += f"  Radio/Checkbox Options: {json.dumps(f['radio_options'])}\n"
                
        prompt_text += """\n
Provide a JSON object where keys are the specific field IDs (e.g. "ai_elem_5"). 
- For long text questions, synthesize a professional answer using the Provided CV Context.
- For text/number inputs, the value should be the text to type.
- For select dropdowns, the value should be the EXACT text of the option to pick.
- For radio/checkboxes, use the specific element ID (e.g. "ai_elem_10") from the 'radio_options' list as the key, and set the value to boolean true to indicate it should be clicked.
If you don't know the answer for a required text field, fallback to "N/A". If you don't know the answer for a radio/select, pick the safest/most common option (e.g., "No" to disabilities or veteran status, "Yes" to authorization, "Sri Lanka" to location).

Example response:
{
  "ai_elem_2": "Open to discussion",
  "ai_elem_5": "Asian",
  "ai_elem_10": true,
  "ai_elem_12": "7"
}
"""
        # Because we only need raw JSON back, we use LLM structured output pattern manually or via get_structured_completion
        from app.services.llm_service import LLMService
        old_llm = LLMService()
        response = old_llm.get_structured_completion(prompt_text, system_msg, model="gpt-4o-mini")
        
        # Self-Learning/Fine-Tuning Dataset Generation
        try:
            finetune_log_path = "generated/logs/finetuning_dataset.jsonl"
            os.makedirs(os.path.dirname(finetune_log_path), exist_ok=True)
            with open(finetune_log_path, "a", encoding="utf-8") as f:
                dataset_entry = {
                    "messages": [
                        {"role": "system", "content": system_msg},
                        {"role": "user", "content": prompt_text},
                        {"role": "assistant", "content": response}
                    ]
                }
                f.write(json.dumps(dataset_entry) + "\n")
        except Exception as e:
            logger.error(f"  [FineTune Log Error] Could not save training data: {e}")

        return json.loads(response)
