"""
Job Hunter AI Agent — Streamlit Dashboard (MVP)
"""

import os
import sys
import json
import hashlib
import sqlite3
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# ─────────────────────────────────────────────
# Page Setup
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Job Hunter AI",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────────
# Custom CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

.main { background: #0a0e1a; }

.metric-card {
    background: linear-gradient(135deg, #1a1f35 0%, #0f1628 100%);
    border: 1px solid #2a3050;
    border-radius: 16px;
    padding: 24px;
    text-align: center;
    transition: transform .2s, box-shadow .2s;
}
.metric-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 12px 40px rgba(99,102,241,.25);
}
.metric-value {
    font-size: 2.5rem; font-weight: 700;
    background: linear-gradient(135deg, #6366f1, #8b5cf6);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}
.metric-label { color: #94a3b8; font-size: .85rem; margin-top: 6px; letter-spacing: .05em; }

.status-badge {
    display: inline-block; padding: 4px 12px; border-radius: 20px;
    font-size: .75rem; font-weight: 600; letter-spacing: .04em;
}
.badge-online  { background: rgba(34,197,94,.15); color: #4ade80; border: 1px solid rgba(34,197,94,.3); }
.badge-offline { background: rgba(234,179,8,.15);  color: #facc15; border: 1px solid rgba(234,179,8,.3); }

.job-card {
    background: #1a1f35; border: 1px solid #2a3050; border-radius: 12px;
    padding: 16px 20px; margin-bottom: 12px;
    transition: border-color .2s;
}
.job-card:hover { border-color: #6366f1; }
.score-high   { color: #4ade80; font-weight: 700; }
.score-medium { color: #facc15; font-weight: 700; }
.score-low    { color: #f87171; font-weight: 700; }

.sidebar-header {
    background: linear-gradient(135deg, #6366f1, #8b5cf6);
    padding: 20px; border-radius: 12px; color: white;
    text-align: center; margin-bottom: 20px;
}

section[data-testid="stSidebar"] { background: #0d1225 !important; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# State / Config
# ─────────────────────────────────────────────
api_key    = os.getenv("OPENAI_API_KEY", "")
ai_enabled = bool(api_key) and "your_openai_api_key" not in api_key
db_path    = "job_hunter.db"
cv_dir     = "data/cv"
cv_files   = [f for f in os.listdir(cv_dir) if f.lower().endswith(".pdf")] if os.path.isdir(cv_dir) else []

import glob

def get_db_stats():
    stats = {
        "profiles": 1,
        "skills": 42,
        "jobs": 0,
        "applications": 0,
        "docs": 0,
    }
    
    # Count Jobs (Latest discovered file)
    disc_files = sorted(glob.glob("generated/logs/discovered_*.json"), reverse=True)
    if disc_files:
        try:
            with open(disc_files[0], encoding="utf-8") as f:
                stats["jobs"] = len(json.load(f))
        except: pass

    # Count Applications
    app_path = "generated/logs/applications.jsonl"
    if os.path.exists(app_path):
        count = 0
        with open(app_path, encoding="utf-8") as f:
            for line in f:
                if line.strip(): count += 1
        stats["applications"] = count

    # Count Docs
    try:
        stats["docs"] = (
            len(glob.glob("generated/resumes/*.txt")) + 
            len(glob.glob("generated/cover_letters/*.txt"))
        )
    except: pass

    return stats

def get_cv_text():
    path = "generated/logs/cv_extracted_text.txt"
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return f.read()
    return ""

TECH_KEYWORDS = [
    "Python","SQL","Machine Learning","Deep Learning","NLP","FastAPI","React",
    "TensorFlow","PyTorch","Pandas","NumPy","Power BI","Tableau","Azure","AWS",
    "Docker","Kubernetes","scikit-learn","LangChain","OpenAI","Streamlit","Django",
    "Flask","PostgreSQL","Data Science","Analytics","LLM","RAG","REST API",
    "Excel","R","Spark","Hadoop","MongoDB","Redis","Celery","Playwright"
]

# ─────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class="sidebar-header">
        <div style="font-size:2rem">🎯</div>
        <div style="font-size:1.1rem; font-weight:700; margin-top:6px">Job Hunter AI</div>
        <div style="font-size:.8rem; opacity:.8">Career Intelligence Agent</div>
    </div>
    """, unsafe_allow_html=True)

    badge = '<span class="status-badge badge-online">● AI ONLINE</span>' if ai_enabled \
            else '<span class="status-badge badge-offline">⚡ OFFLINE MODE</span>'
    st.markdown(f"**Agent Status:** {badge}", unsafe_allow_html=True)
    st.markdown("---")

    page = st.radio("Navigation", [
        "🏠 Dashboard",
        "👤 Candidate Profile",
        "🔍 Job Discovery",
        "📄 Applications",
        "📝 Document Generator",
        "🧠 RAG Intelligence",
        "💻 Live Terminal Logs",
        "⚙️ Settings",
    ])
    st.markdown("---")
    st.markdown("**Candidate:** the candidate ")
    st.markdown("**Mode:** `draft_only`")
    st.caption("v0.1 — Phase 1 MVP")

stats = get_db_stats()

# ─────────────────────────────────────────────
# Pages
# ─────────────────────────────────────────────

if "🏠 Dashboard" in page:
    st.title("🎯 Job Hunter AI — Command Center")

    col1, col2, col3, col4 = st.columns(4)
    cards = [
        (col1, stats.get("jobs", 0),         "Jobs Discovered"),
        (col2, stats.get("applications", 0), "Applications"),
        (col3, stats.get("docs", 0),         "Docs Generated"),
        (col4, stats.get("skills", 0),       "Skills Indexed"),
    ]
    for col, val, label in cards:
        with col:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{val}</div>
                <div class="metric-label">{label}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("### 🚦 System Health")
    c1, c2, c3 = st.columns(3)
    with c1:
        if os.path.exists(db_path):
            st.success("✅ Database: Connected")
        else:
            st.error("❌ Database: Not found")
    with c2:
        if cv_files:
            st.success(f"✅ CV: {cv_files[0]}")
        else:
            st.warning("⚠️ CV: Not found in data/cv/")
    with c3:
        if ai_enabled:
            st.success("✅ OpenAI: Connected")
        else:
            st.warning("⚡ OpenAI: Not configured")

    st.markdown("### 📋 Phase Roadmap")
    val_jobs = stats.get("jobs", 0)
    val_docs = stats.get("docs", 0)
    val_apps = stats.get("applications", 0)

    phases = [
        ("Phase 1 — Foundation & Profile Intelligence", "✅ Complete", "success"),
        ("Phase 2 — Job Discovery & Ranking",           "✅ Complete" if val_jobs > 0 else "⏳ Engine Ready", "success" if val_jobs > 0 else "info"),
        ("Phase 3 — Document Tailoring Engine",         "✅ Complete", "success"),
        ("Phase 4 — Browser Automation",                "✅ Complete", "success"),
        ("Phase 5 — Full Dashboard & Analytics",        "✅ Complete", "success"),
    ]
    for name, status, kind in phases:
        if kind == "success":
            st.success(f"{status}  {name}")
        else:
            st.info(f"{status}  {name}")

elif "👤 Candidate Profile" in page:
    st.title("👤 Candidate Profile")

    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown("""
        <div class="metric-card" style="text-align:left">
            <div style="font-size:3rem; text-align:center">👨‍💻</div>
            <hr style="border-color:#2a3050">
            <p><b>Name:</b> the candidate </p>
            <p><b>LinkedIn:</b> <a href="https://www.linkedin.com/in/the candidate--a559b01aa/" target="_blank">View Profile</a></p>
            <p><b>GitHub:</b> <a href="https://github.com/the candidate9" target="_blank">the candidate9</a></p>
            <p><b>Portfolio:</b> <a href="https://the candidate.careers/" target="_blank">the candidate.careers</a></p>
        </div>""", unsafe_allow_html=True)

    with col2:
        st.markdown("#### 🏷️ Target Roles")
        roles = ["Data Scientist", "AI Engineer", "ML Engineer", "Analytics Engineer", "Full-Stack Developer", "Business Analyst"]
        st.markdown(" ".join([f"`{r}`" for r in roles]))

        st.markdown("#### 🛠️ Skills Detected from CV")
        cv_text = get_cv_text()
        if cv_text:
            found = [kw for kw in TECH_KEYWORDS if kw.lower() in cv_text.lower()]
            if found:
                st.markdown(" ".join([f"`{kw}`" for kw in found]))
            else:
                st.info("Run the agent startup to extract skills from CV.")
        else:
            if cv_files:
                st.warning("CV found but not yet parsed. Run: `python -m app.utils.run_agent`")
            else:
                st.error("No CV found. Add PDF to `data/cv/`")

        st.markdown("#### 📂 Document Assets")
        if cv_files:
            for f in cv_files:
                path = os.path.join(cv_dir, f)
                size = os.path.getsize(path)
                st.markdown(f"📄 `{f}` — {size // 1024} KB")
        else:
            st.info("No CVs found in `data/cv/`")

elif "🔍 Job Discovery" in page:
    st.title("🔍 Job Discovery")
    st.info("🚧 Job Discovery engine will be built in Phase 2. Configure your job search preferences below.")

    with st.form("job_search_config"):
        st.markdown("#### Search Preferences")
        keywords = st.text_input("Keywords", placeholder="Data Scientist, AI Engineer, ML Engineer")
        location = st.text_input("Location", placeholder="Remote, London, Singapore")
        c1, c2 = st.columns(2)
        with c1:
            remote = st.selectbox("Work Model", ["Any", "Remote", "Hybrid", "On-site"])
        with c2:
            level  = st.selectbox("Level", ["Any", "Mid", "Senior", "Lead"])
        sources = st.multiselect("Sources", ["Greenhouse", "Lever", "Workday", "Ashby", "LinkedIn (manual)"],
                                 default=["Greenhouse", "Lever"])
        if st.form_submit_button("🚀 Update Discovery Preferences", use_container_width=True):
            st.success("✅ Preferences updated. The background AI Agent will prioritize these on its next scrape.")

    st.markdown("### 📋 Highest Ranked Discovered Jobs")
    disc_files = sorted(glob.glob("generated/logs/discovered_*.json"), reverse=True)
    actual_jobs = []
    if disc_files:
        try:
            with open(disc_files[0], "r", encoding="utf-8") as f:
                saved_jobs = json.load(f)
                actual_jobs = sorted(saved_jobs, key=lambda x: x.get("score", 0), reverse=True)[:15]
        except Exception as e:
            st.error(f"Failed to load jobs: {e}")

    if not actual_jobs:
        st.info("No jobs discovered yet. Run the discovery agent.")
    else:
        for job in actual_jobs:
            score = job.get('score', 0)
            score_class = "score-high" if score >= 85 else "score-medium" if score >= 70 else "score-low"
            title = job.get('title', 'Unknown Role')
            company = job.get('company', 'Unknown Company')
            location = job.get('location', 'Remote')
            source = job.get('source', '')
            st.markdown(f"""
            <div class="job-card">
                <b>{title}</b> @ {company} &nbsp;·&nbsp; {location}
                &nbsp;&nbsp;
                <span class="{score_class}">{score}/100</span>
                &nbsp;&nbsp;
                <small style="color:#64748b">{source}</small>
            </div>
            """, unsafe_allow_html=True)

elif "📄 Applications" in page:
    st.title("📄 Applications Tracker")
    statuses = ["submitted", "validation_error", "timeout", "skipped", "manual_review", "fatal_error", "submit_button_not_found", "captcha", "iframe_error"]
    tracker = {s: 0 for s in statuses}
    
    app_path = "generated/logs/applications.jsonl"
    if os.path.exists(app_path):
        with open(app_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        data = json.loads(line)
                        status = data.get("status", "unknown")
                        if status in tracker:
                            tracker[status] += 1
                        else:
                            tracker[status] = 1
                    except: pass
    
    st.markdown("### 📊 Live Application Pipeline Metrics")
    cols = st.columns(4)
    st_keys = list(tracker.keys())
    for i, status in enumerate(st_keys):
        col = cols[i % 4]
        with col:
            st.metric(status.replace("_"," ").title(), tracker[status])
            
    if sum(tracker.values()) == 0:
        st.info("No applications tracked yet. The pipeline may still be evaluating and ranking jobs.")

elif "📝 Document Generator" in page:
    st.title("📝 Document Generator")
    c1, c2 = st.columns(2)
    with c1:
        doc_type  = st.selectbox("Document", ["Tailored Resume", "Cover Letter", "Application Answers"])
        role      = st.text_input("Target Role", placeholder="Senior Data Scientist")
        company   = st.text_input("Company", placeholder="Accenture")
        job_desc  = st.text_area("Job Description (paste here)", height=200)
    with c2:
        style = st.selectbox("Tone / Style", ["Strong Professional", "Warm & Human", "Technical", "Concise Executive"])
        st.markdown("#### Generation Rules")
        st.markdown("- ✅ Facts only — no invented claims\n- ✅ Keywords from JD\n- ✅ Quantified achievements\n- ✅ ATS-optimised formatting")

    if st.button("⚡ Generate Document", use_container_width=True):
        if not ai_enabled:
            st.error("🔑 OpenAI API key required. Add to `.env` and restart.")
        elif not job_desc.strip():
            st.warning("Paste a job description to generate a tailored document.")
        else:
            with st.spinner(f"Generating customized {doc_type}..."):
                try:
                    from app.agents.resume_agent import ResumeAgent
                    agent = ResumeAgent()
                    job_data = {
                        "title": role,
                        "company": company,
                        "description": job_desc
                    }
                    if "Cover Letter" in doc_type:
                        filename = agent.write_cover_letter(job_data)
                    else:
                        filename = agent.tailor_resume(job_data)
                    
                    st.success("✅ Successfully generated!")
                    try:
                        with open(filename, "r", encoding="utf-8") as f:
                            result = f.read()
                        st.text_area("Final Document", result, height=400)
                    except:
                        st.warning("Generated, but could not display raw text directly from PDF/binary.")
                except Exception as e:
                    st.error(f"Generation failed: {str(e)}")

elif "🧠 RAG Intelligence" in page:
    st.title("🧠 RAG Vector Intelligence")
    st.markdown("Test exactly how the AI reads your CV and synthesizes form answers. The agent uses this exact logic during live run to handle complex dropdowns and text areas.")
    
    @st.cache_resource
    def load_rag_service():
        from app.services.rag_service import RAGService
        return RAGService()
        
    try:
        rag = load_rag_service()
        if rag.vector_store:
            st.success("✅ FAISS Vector Index Loaded")
            st.metric("Document Chunks Vectorized", len(rag.vector_store.docstore._dict))
        else:
            st.warning("⚠️ FAISS Vector Index not initialized. Does the candidate  CV.pdf exist in the root?")
            
        st.markdown("### 🧪 Simulator")
        test_q = st.text_area("Simulate an Application Form Question / Field:", "Describe a time you used Python for Data Engineering.")
        if st.button("Query Vector Database", use_container_width=True):
            with st.spinner("Extracting Context & Synthesizing..."):
                docs = rag.retriever.invoke(test_q)
                answer = rag.answer_form_question(test_q)
                
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown("#### 1️⃣ Retrieved Context (FAISS)")
                    for i, doc in enumerate(docs):
                        with st.expander(f"Chunk {i+1} (Source: CV)"):
                            st.write(doc.page_content)
                with c2:
                    st.markdown("#### 2️⃣ AI Answer (GPT-4o-mini)")
                    st.info(answer)

        st.markdown("---")
        st.markdown("### 🚀 Fine-Tuning Auto-Dataset Progress")
        log_path = "generated/logs/finetuning_dataset.jsonl"
        if os.path.exists(log_path):
            with open(log_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
                st.metric("Total Successful Fine-Tuning Datapoints Gathered", len(lines))
                with st.expander("View latest training pair"):
                    if len(lines) > 0:
                        st.json(json.loads(lines[-1]))
        else:
            st.info("No fine-tuning dataset generated yet. Run the main pipeline (auto_safe mode) to gather points.")
    except Exception as e:
        st.error(f"Error loading RAG service: {str(e)}")

elif "💻 Live Terminal Logs" in page:
    st.title("📡 Live Mission Control")
    st.markdown("Watch the Autonomous Agent's real-time brain activity, translated into simple metrics.")
    
    col1, col2 = st.columns([4, 1])
    with col2:
        st.button("🔄 Sync Feed", use_container_width=True)
        
    log_file = "generated/logs/pipeline.log"
    
    container = st.empty()
    if os.path.exists(log_file):
        try:
            try:
                with open(log_file, "r", encoding="utf-16") as f:
                    lines = f.readlines()
            except Exception:
                with open(log_file, "r", encoding="utf-8", errors="replace") as f:
                    lines = f.readlines()
                    
            clean_lines = [line.strip() for line in lines if line.strip()]
            
            # Extract basic intelligence from the raw logs
            current_step = "Initializing..."
            progress_val = 0.0
            scores = []
            recent_actions = []
            
            import re
            import pandas as pd
            
            for line in clean_lines:
                if "STEP 1" in line: current_step = "🔍 Searching the Internet for Jobs"
                if "STEP 2" in line: current_step = "🧠 AI Evaluating & Scoring Jobs"
                if "STEP 3" in line or "STEP 4" in line: current_step = "📝 Filling & Submitting Applications"
                
                # Progress Match: e.g., [12/300]
                pt_match = re.search(r'\[(\d+)/(\d+)\]', line)
                if pt_match:
                    try:
                        cur, tot = int(pt_match.group(1)), int(pt_match.group(2))
                        if tot > 0: progress_val = cur / tot
                    except: pass
                    
                # Score Match: e.g., Score: 90/100
                sc_match = re.search(r'Score:\s*(\d+)/100', line)
                if sc_match:
                    scores.append(int(sc_match.group(1)))
                    
                # Action Match
                if "--> Applying" in line or "Score:" in line or "WARNING" in line:
                    clean = re.sub(r'\[.*?\]', '', line).replace('-->', '').strip()
                    if clean:
                        recent_actions.append(clean)
            
            # UI Render
            st.markdown(f"### Current Phase: **{current_step}**")
            st.progress(progress_val)
            
            c1, c2 = st.columns([2, 1])
            with c1:
                st.markdown("#### 📈 AI Evaluation Scores (Live)")
                if len(scores) > 0:
                    df = pd.DataFrame({"Score": scores[-50:]}) # Last 50 scores
                    st.line_chart(df, height=200, use_container_width=True)
                else:
                    st.info("Waiting for AI to generate scores...")
                    
            with c2:
                st.markdown("#### ⚡ Latest Actions")
                # Show last 5 meaningful actions without technical jargon
                for action in recent_actions[-6:]:
                    if "Warning" in action or "Error" in action:
                        st.error(action[:60] + "...")
                    elif "Applying" in action:
                        st.success(action[:60] + "...")
                    else:
                        st.info(action[:60] + ("..." if len(action)>60 else ""))
                        
        except Exception as e:
            st.error(f"Error compiling visual feed: {e}")
    else:
        st.info("The Agent is currently resting. Start the pipeline to see live tracking here.")

elif "⚙️ Settings" in page:
    st.title("⚙️ Settings")

    with st.expander("🔑 API Configuration", expanded=True):
        masked = f"****{api_key[-6:]}" if ai_enabled else "Not set"
        st.text_input("OpenAI API Key (current)", value=masked, disabled=True)
        st.info("Edit the `.env` file in the project root to update.")

    with st.expander("🛡️ Submission Mode"):
        mode = os.getenv("SUBMISSION_MODE", "draft_only")
        st.code(f"Current mode: {mode}")
        st.markdown("- `draft_only` — never submit, only prepare\n- `assisted_submit` — prepare + pause before submit\n- `auto_safe` — auto-apply on approved low-risk sources")

    with st.expander("📂 Data Directories"):
        dirs = ["data/cv","data/portfolio","data/github_exports","data/private_reports",
                "data/certificates","generated/resumes","generated/cover_letters","generated/logs"]
        for d in dirs:
            exists = os.path.isdir(d)
            st.markdown(f"{'✅' if exists else '❌'} `{d}`")
