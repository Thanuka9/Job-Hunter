# Job Hunter AI Agent — Full Project Master Prompt and Build Specification

**Project Root:** `.`  
**Owner:** Your Name  
**Primary Goal:** Build a semi-autonomous AI career agent that discovers suitable jobs, ranks them against the candidate profile, generates tailored application materials, fills applications, uploads required documents, and either submits automatically where allowed or stops for final human approval.

---

## 1. Project Objective

Create a production-grade AI agent system that can:

- search job opportunities across multiple job sources
- understand the candidate's background from CV, portfolio, GitHub, local reports, and supporting files
- match jobs against real skills and experience
- tailor resumes and cover letters per role
- answer common job application questions
- upload CV, cover letter, portfolio, and other required files
- track applications and avoid duplicate submissions
- support account-assisted workflows for platforms like LinkedIn
- protect accuracy, privacy, and account safety

This project must be designed as a **hybrid autonomous agent**:

- **Fully automated** for low-risk, compatible application flows
- **Human-in-the-loop** for risky or policy-sensitive platforms such as LinkedIn Easy Apply or sites with strong anti-bot enforcement

---

## 2. Candidate Profile Source of Truth

Use the following candidate assets as the primary truth layer.

### Identity and Links
- **Name:** [Your Name]
- **Project Root:** `.`
- **GitHub:** `https://github.com/yourusername`
- **Portfolio:** `https://yourportfolio.careers/`
- **LinkedIn:** `https://www.linkedin.com/in/yourid/`

### Core Professional Positioning
the candidate is positioned as:
- AI Engineer
- Data Scientist
- Full-Stack Developer
- Analytics-focused technical professional
- Assistant Manager with strong data, systems, and process-improvement background

### Mandatory Candidate Truth Rules
The agent must:
- never invent qualifications, experience, awards, or skills
- never exaggerate years of experience
- never claim tools or work not supported by source documents
- use only verified information extracted from local files, public portfolio pages, GitHub, CV, and user-approved private reports
- flag uncertain items as **needs review**
- keep every application factually consistent

---

## 3. High-Level Product Vision

Build **Job Hunter**, a modular AI job-search and application platform with the following layers:

1. **Profile Intelligence Layer**
2. **Document and Evidence Ingestion Layer**
3. **Job Discovery Layer**
4. **Job Matching and Ranking Layer**
5. **Application Package Generation Layer**
6. **Browser Automation Layer**
7. **Human Approval Layer**
8. **Tracking and Analytics Dashboard**
9. **Safety, Privacy, and Policy Layer**

---

## 4. Critical Design Decision

This system must not be a reckless “auto-apply everywhere” bot.

It must be a **career application intelligence system** that:
- automates job discovery
- automates personalization
- automates document preparation
- automates form filling where appropriate
- requests approval before submitting on sensitive or restricted platforms

This is the preferred design because it is safer, more reliable, easier to maintain, and less likely to trigger account restrictions.

---

## 5. Platforms and Source Categories

### Priority Sources
The agent should support:

- Greenhouse job boards
- Lever job boards
- company careers pages
- Workday pages where feasible
- Ashby job boards where feasible
- direct application pages
- manual review support for LinkedIn job links
- optional user-approved email job alerts

### Supported Candidate Data Sources
The agent should be able to ingest and reason over:

- CV PDFs
- DOCX resumes
- portfolio website content
- GitHub profile and repositories
- local project reports
- private reports placed in approved local directories
- certificates
- reference documents
- transcripts if provided
- writing samples if provided

---

## 6. Handling Private Reports and Local Documents

The agent should be able to review private reports, but only through **user-approved local ingestion**.

### Rule
The agent must not assume access to private online accounts or hidden documents unless:
- they are exported locally into the project folders, or
- they are connected via an approved integration, or
- the user explicitly grants access in the execution environment

### Approved Local Ingestion Folders
Use these folders:

```text
D:\Job Hunter\data\cv
D:\Job Hunter\data\portfolio
D:\Job Hunter\data\github_exports
D:\Job Hunter\data\private_reports
D:\Job Hunter\data\certificates
D:\Job Hunter\data\cover_letter_templates
D:\Job Hunter\data\answers_bank
D:\Job Hunter\data\job_descriptions_archive
```

### Private Report Usage Goals
The agent should:
- extract achievements
- detect keywords
- find measurable outcomes
- identify technical tools used
- identify leadership and business impact statements
- surface evidence snippets that strengthen cover letters and application answers

### Output from Private Reports
For each document, generate:
- document summary
- role relevance tags
- extracted skills
- quantified outcomes
- project names
- notable business or research impact
- candidate evidence snippets for future applications

---

## 7. Product Modes

### Mode A — Discovery Only
- find jobs
- rank jobs
- build shortlist
- generate tailored application drafts
- no submission

### Mode B — Assisted Apply
- fill form fields
- upload files
- prepare responses
- stop before final submit for user approval

### Mode C — Safe Auto Apply
- auto-apply only on approved low-risk sources
- log every submission
- save screenshots and metadata
- skip any site that triggers captcha, suspicious behavior, or unclear compliance status

---

## 8. Recommended Tech Stack

### Backend
- Python 3.11+
- FastAPI
- Pydantic
- SQLAlchemy
- PostgreSQL
- Alembic

### Automation
- Playwright
- browser session management
- secure credential/session handling
- retry logic
- screenshot capture

### AI Layer
- OpenAI API for extraction, ranking, writing, and structured reasoning
- embeddings for semantic job matching
- optional reranker for job-description relevance

### Parsing
- BeautifulSoup
- lxml
- pypdf
- python-docx
- markdown
- trafilatura or readability where needed

### Frontend
- Streamlit for MVP dashboard
or
- React + Next.js for full production UI

### Scheduling and Queues
- Celery or RQ
- Redis
- scheduled job refresh tasks

### Storage
- PostgreSQL for structured data
- local file storage for generated documents
- optional S3-compatible storage later

---

## 9. Folder Structure

```text
D:\Job Hunter
│
├── app
│   ├── main.py
│   ├── config.py
│   ├── dependencies.py
│   ├── logging_config.py
│   │
│   ├── agents
│   │   ├── profile_agent.py
│   │   ├── document_agent.py
│   │   ├── job_discovery_agent.py
│   │   ├── ranking_agent.py
│   │   ├── resume_agent.py
│   │   ├── cover_letter_agent.py
│   │   ├── qa_agent.py
│   │   ├── application_agent.py
│   │   ├── approval_agent.py
│   │   └── tracking_agent.py
│   │
│   ├── services
│   │   ├── llm_service.py
│   │   ├── embeddings_service.py
│   │   ├── parser_service.py
│   │   ├── browser_service.py
│   │   ├── linkedin_service.py
│   │   ├── greenhouse_service.py
│   │   ├── lever_service.py
│   │   ├── workday_service.py
│   │   ├── github_service.py
│   │   ├── portfolio_service.py
│   │   └── document_generation_service.py
│   │
│   ├── models
│   │   ├── candidate_profile.py
│   │   ├── job_posting.py
│   │   ├── application.py
│   │   ├── document_asset.py
│   │   ├── generated_document.py
│   │   └── audit_log.py
│   │
│   ├── prompts
│   │   ├── profile_extraction.md
│   │   ├── job_matcher.md
│   │   ├── cover_letter_writer.md
│   │   ├── resume_tailor.md
│   │   ├── application_answers.md
│   │   └── safety_rules.md
│   │
│   ├── api
│   │   ├── routes_profile.py
│   │   ├── routes_jobs.py
│   │   ├── routes_applications.py
│   │   ├── routes_documents.py
│   │   └── routes_admin.py
│   │
│   ├── db
│   │   ├── base.py
│   │   ├── session.py
│   │   └── init_db.py
│   │
│   └── utils
│       ├── dedupe.py
│       ├── file_hash.py
│       ├── validators.py
│       ├── keyword_tools.py
│       └── date_utils.py
│
├── data
│   ├── cv
│   ├── portfolio
│   ├── github_exports
│   ├── private_reports
│   ├── certificates
│   ├── cover_letter_templates
│   ├── answers_bank
│   └── job_descriptions_archive
│
├── generated
│   ├── resumes
│   ├── cover_letters
│   ├── answers
│   ├── screenshots
│   ├── logs
│   └── application_exports
│
├── dashboard
│   └── streamlit_app.py
│
├── tests
│   ├── test_parsers.py
│   ├── test_ranking.py
│   ├── test_generation.py
│   └── test_apply_flows.py
│
├── .env
├── requirements.txt
├── README.md
└── MASTER_PROMPT.md
```

---

## 10. Core Database Entities

### candidate_profiles
Fields:
- id
- full_name
- email
- phone
- location
- linkedin_url
- github_url
- portfolio_url
- target_roles
- preferred_locations
- remote_preference
- salary_min
- salary_max
- visa_notes
- work_authorization_notes
- years_experience
- summary
- created_at
- updated_at

### candidate_skills
- id
- candidate_id
- skill_name
- category
- confidence
- source_document_id

### document_assets
- id
- file_name
- file_path
- file_type
- sha256
- source_type
- extracted_text
- parsed_json
- relevance_tags
- created_at

### job_postings
- id
- external_job_id
- source_name
- source_url
- company_name
- title
- location
- job_type
- workplace_type
- salary_text
- description_text
- description_hash
- discovered_at
- application_url
- status

### job_scores
- id
- job_id
- candidate_id
- overall_score
- title_score
- skills_score
- seniority_score
- location_score
- portfolio_score
- notes_json
- apply_recommendation

### generated_documents
- id
- candidate_id
- job_id
- doc_type
- file_path
- prompt_version
- source_snapshot
- created_at

### applications
- id
- candidate_id
- job_id
- source_name
- application_url
- status
- submission_mode
- submitted_at
- approval_required
- approval_status
- notes

### audit_logs
- id
- event_type
- reference_id
- event_payload
- screenshot_path
- created_at

---

## 11. Candidate Ingestion Workflow

### Goal
Create a structured candidate intelligence profile from all available documents.

### Inputs
- CV
- portfolio website
- GitHub profile and repo readme files
- local reports
- certificates
- writing samples
- LinkedIn exported data if available

### Output
Build:
- canonical candidate profile
- verified skills graph
- experience timeline
- projects library
- evidence library
- role-fit tags
- achievement bank
- cover-letter phrase bank

### Extraction Requirements
The agent must extract:
- job titles
- organizations
- dates
- technical tools
- project outcomes
- quantified impact
- leadership signals
- research experience
- business analytics expertise
- AI and ML projects
- domain specialization

### Confidence Model
Every extracted fact should have:
- source file
- evidence snippet
- confidence label
- verified or needs-review flag

---

## 12. Job Discovery Logic

### Goal
Find relevant jobs continuously.

### Discovery Strategy
1. Pull public jobs from supported ATS providers.
2. Crawl approved company careers pages.
3. Ingest saved job links from the user.
4. Capture LinkedIn job links for manual or assisted handling.
5. Deduplicate all jobs.
6. Archive descriptions for ranking and evidence generation.

### Filters
Support:
- role families
- keywords
- location
- remote/on-site/hybrid
- experience level
- company type
- salary if available
- visa sponsorship if detectable

### Default Priority Role Families
Start with:
- Data Scientist
- AI Engineer
- Machine Learning Engineer
- Data Analyst
- Business Analyst
- Business Analytics roles
- Full-Stack Developer
- Python Developer
- Analytics Engineer
- Applied AI roles

---

## 13. Job Matching and Scoring Logic

### Scoring Components
Each job should be scored out of 100 using weighted categories:

- title alignment: 20
- skills alignment: 25
- experience alignment: 15
- industry/domain fit: 10
- location/work model fit: 10
- project and portfolio relevance: 10
- application complexity and feasibility: 5
- strategic value of company/role: 5

### Output Decision
- **85–100:** strong apply
- **70–84:** apply after review
- **55–69:** optional or stretch
- **below 55:** skip unless user overrides

### Matching Rules
The agent should:
- favor roles matching AI, analytics, ML, data science, Python, and full-stack experience
- promote jobs where healthcare analytics, process optimization, NLP, dashboards, or enterprise applications are relevant
- detect when a role requires strong CV tailoring
- avoid roles clearly unrelated to verified experience

---

## 14. Resume Tailoring Engine

### Goal
Create targeted resume variants without falsifying content.

### Resume Variant Types
- AI Engineer version
- Data Scientist version
- Business Analytics version
- Full-Stack Developer version
- Generic strong version

### Tailoring Rules
The system must:
- reorder bullets based on role relevance
- emphasize matching projects
- include strong keywords from job descriptions
- preserve truth and chronology
- improve ATS readability
- maintain clean PDF and DOCX export

### Tailoring Prompt Rules
The resume-tailoring agent should:
- keep all claims factual
- use quantified achievements where supported
- emphasize relevant tools named in the job description
- remove less relevant content where appropriate
- preserve readability and professionalism

---

## 15. Cover Letter Engine

### Goal
Generate strong tailored cover letters fast.

### Cover Letter Principles
- personalized to company and role
- references real projects and outcomes
- shows motivation without sounding generic
- concise but specific
- no false claims
- no flattery overload
- clear business value

### Cover Letter Structure
1. Opening with role and motivation
2. Why the background fits
3. Evidence from relevant work/projects
4. Specific value for that employer
5. Polite close

### Style Options
Support:
- formal
- strong professional
- warm and human
- concise executive
- technical

---

## 16. Application Question Answering Engine

### Goal
Generate accurate responses for common application questions.

### Common Questions
- Tell us about yourself
- Why do you want this role?
- Why do you want to work here?
- Describe a project you are proud of
- What is your experience with Python, SQL, ML, dashboards, APIs?
- Salary expectations
- Work authorization
- Notice period
- Links to GitHub/portfolio

### Rules
- answer only from verified profile data
- store reusable answers
- version answers by job family
- allow short, medium, and long response formats
- flag any legal/work-authorization uncertainty for review

---

## 17. Browser Automation Engine

### Primary Tool
Use Playwright.

### Responsibilities
- open application pages
- authenticate if authorized
- fill forms
- upload documents
- select generated answers
- capture screenshots
- detect blockers
- stop for approval when required

### Browser Safety Rules
- slow down interactions to human-like pace
- randomize reasonable wait intervals
- use visible browser mode for sensitive actions
- log every step
- take screenshots before and after submission
- halt on captcha or suspicious activity
- never bypass platform security controls

### Submission Modes
- `auto_safe`
- `assisted_submit`
- `draft_only`

---

## 18. LinkedIn Handling Rules

### Important
LinkedIn should be treated as a high-risk platform for full automation.

### LinkedIn Rules
The system may:
- read user-provided LinkedIn profile URL as a reference
- use LinkedIn data exported or approved by the user
- help write messages and application answers
- open LinkedIn job pages for review
- prefill information for final user review

The system should not:
- aggressively scrape at scale
- perform hidden bot behavior
- try to defeat anti-bot protections
- blindly auto-submit at high volume

### Preferred LinkedIn Workflow
1. User saves a LinkedIn job URL.
2. Agent analyzes the job.
3. Agent prepares CV and cover letter.
4. Agent pre-fills fields if feasible.
5. Agent pauses for final approval.

---

## 19. Approval Layer

### Purpose
Keep the user in control on high-risk or high-importance applications.

### Approval Required For
- LinkedIn
- ambiguous company forms
- roles above a configurable score threshold if a premium application is desired
- applications requiring unique legal declarations
- applications that include custom essay questions
- any step where facts are uncertain

### Approval Screen Should Show
- company
- role
- match score
- key reasons for fit
- selected resume version
- selected cover letter
- generated answers
- warnings
- final action buttons

---

## 20. Tracking and Dashboard

### Dashboard Features
- newly discovered jobs
- shortlisted jobs
- applied jobs
- pending approvals
- application statuses
- generated resumes
- generated cover letters
- duplicate warnings
- source breakdown
- success metrics over time

### Application Status Flow
- discovered
- ranked
- shortlisted
- documents_ready
- awaiting_approval
- submitted
- follow_up_due
- rejected
- interview
- offer
- archived

---

## 21. Security and Privacy

### Requirements
- store secrets in `.env`
- encrypt account credentials where used
- never hardcode passwords
- keep browser session files protected
- redact sensitive logs where needed
- provide manual deletion/export of all stored data
- keep an audit log of generated documents and submissions

### Sensitive Files
Treat these as sensitive:
- CVs
- passport/work authorization docs
- certificates
- personal identity records
- exported job-platform account data

---

## 22. MVP Build Phases

## Phase 1 — Foundation and Profile Intelligence
### Deliverables
- project scaffolding
- database setup
- CV parser
- portfolio parser
- GitHub parser
- private report parser
- candidate profile builder
- evidence bank

### Success Criteria
- system can ingest the candidate’s files
- build structured profile
- store extracted facts with evidence links
- generate a profile summary JSON

---

## Phase 2 — Job Discovery
### Deliverables
- Greenhouse connector
- Lever connector
- generic careers-page parser
- job deduplication
- job archive storage

### Success Criteria
- discover jobs daily
- store full descriptions
- avoid duplicates
- searchable job database available

---

## Phase 3 — Matching and Ranking
### Deliverables
- scoring engine
- keyword extraction
- embeddings-based similarity
- role-family ranking
- shortlist recommendations

### Success Criteria
- each job gets a score, reasons, and recommendation
- shortlist can be filtered by score and role family

---

## Phase 4 — Document Generation
### Deliverables
- resume tailoring engine
- cover letter engine
- application answer engine
- PDF and DOCX output generation

### Success Criteria
- generate tailored resume and cover letter per selected job
- preserve factual accuracy
- support multiple style templates

---

## Phase 5 — Browser Application Automation
### Deliverables
- Playwright automation
- file upload handling
- forms engine
- screenshot logging
- assisted approval flow

### Success Criteria
- fill and prepare real applications on approved sites
- pause before final submit when needed
- log all steps

---

## Phase 6 — Dashboard and Analytics
### Deliverables
- Streamlit or web dashboard
- application tracking
- status pipeline
- summary metrics

### Success Criteria
- view discovered, shortlisted, and submitted jobs
- track outputs and history easily

---

## Phase 7 — Hardening and Production Quality
### Deliverables
- tests
- retry logic
- anti-duplication rules
- better prompts
- policy guardrails
- export/import tools

### Success Criteria
- stable end-to-end workflow
- safe failure handling
- reproducible runs

---

## 23. Step-by-Step Build Order

1. initialize repo and virtual environment
2. create project folders
3. configure `.env` and settings loader
4. set up PostgreSQL and Alembic
5. build document ingestion pipeline
6. parse CV and create candidate JSON profile
7. parse portfolio site content
8. parse GitHub profile and public repositories
9. create evidence bank and achievements bank
10. build ATS job connectors
11. build deduplication layer
12. implement scoring engine
13. create dashboard shortlist view
14. build resume tailoring generator
15. build cover letter generator
16. build application question generator
17. implement Playwright application flows
18. add approval queue
19. add audit logs and screenshots
20. add tests and production hardening

---

## 24. Environment Variables

```env
OPENAI_API_KEY=
DATABASE_URL=
REDIS_URL=
PLAYWRIGHT_HEADLESS=false
JOB_REFRESH_CRON=0 */6 * * *
LINKEDIN_EMAIL=
LINKEDIN_PASSWORD=
ALLOW_LINKEDIN_AUTOFILL=true
ALLOW_LINKEDIN_AUTO_SUBMIT=false
DEFAULT_COUNTRY=Sri Lanka
DEFAULT_TIMEZONE=Asia/Colombo
```

---

## 25. Master System Prompt for the Orchestrator Agent

Copy the following into the orchestrator agent configuration.

```md
You are Job Hunter, an AI job search and application orchestration agent for the candidate .

Your mission is to discover suitable jobs, evaluate fit, generate truthful application materials, and support or automate job applications safely.

You must always follow these rules:

1. Use the candidate’s verified profile as the source of truth.
2. Never invent or exaggerate skills, qualifications, roles, dates, awards, or outcomes.
3. Prefer roles aligned with AI engineering, data science, machine learning, business analytics, Python development, analytics engineering, and relevant full-stack development.
4. Use supporting evidence from CVs, portfolio pages, GitHub repositories, and user-approved local reports.
5. Generate tailored resumes and cover letters for each selected job.
6. Score each job and explain why it is or is not a fit.
7. Never submit an application when platform risk is high unless the configured submission mode allows it and all policy checks pass.
8. For LinkedIn and similarly sensitive platforms, prefer assisted apply mode and stop for final approval.
9. Archive every job description and every generated application artifact.
10. Maintain a complete audit log.
11. Use concise, professional, truthful, role-specific writing.
12. When uncertain, mark the item for review rather than guessing.
13. Avoid duplicate applications.
14. Use human approval for ambiguous legal, salary, relocation, visa, or compliance questions.
15. Protect user privacy and credentials.

Operational flow:
- ingest profile sources
- discover jobs
- deduplicate jobs
- score and rank jobs
- shortlist relevant roles
- generate tailored application package
- fill forms
- request approval where needed
- log status changes

Output expectations:
- structured JSON for backend tasks
- polished business writing for application documents
- concise explanations for decision support
```

---

## 26. Profile Extraction Prompt

```md
You are a profile extraction agent.

Input:
- CV text
- portfolio content
- GitHub profile content
- local reports and supporting documents

Task:
Extract a verified candidate profile for the candidate .

Return:
- personal summary
- role titles
- experience timeline
- technical skills
- business/domain skills
- projects
- quantified achievements
- leadership indicators
- education
- certifications
- links
- evidence snippets
- confidence labels
- needs_review flags

Rules:
- do not invent missing details
- preserve chronology
- attach evidence to all important claims
- distinguish verified facts from inferred relevance
```

---

## 27. Job Matcher Prompt

```md
You are a job matching agent.

Given:
- a structured candidate profile
- a job description
- optional company information

Score the job for the candidate .

Evaluate:
- title fit
- skills fit
- experience fit
- domain fit
- location fit
- project fit
- strategic relevance

Return:
- overall score out of 100
- sub-scores
- reasons for fit
- missing requirements
- risk flags
- apply recommendation
- preferred resume type
- preferred cover letter tone

Rules:
- prefer evidence-backed reasoning
- do not overestimate fit
- separate hard requirements from nice-to-have items
```

---

## 28. Resume Tailoring Prompt

```md
You are a resume tailoring agent.

Task:
Create a targeted resume for the candidate  based on a job description.

You must:
- keep all facts true
- reorder bullets for relevance
- emphasize matching skills and projects
- improve ATS alignment
- maintain a clean professional style
- preserve role chronology

Output:
- updated summary
- updated skills emphasis
- tailored experience bullets
- selected projects section
- ATS keyword suggestions
```

---

## 29. Cover Letter Prompt

```md
You are a cover letter writing agent.

Task:
Write a tailored cover letter for the candidate .

Requirements:
- professional and specific
- references real experience only
- connect the role with the candidate’s AI, analytics, full-stack, and business impact background where relevant
- highlight measurable outcomes when available
- avoid generic filler
- keep tone confident, clear, and human

Output:
- final cover letter
- subject line if needed
- 3 strongest evidence points used
```

---

## 30. Application Answers Prompt

```md
You are an application-answer generation agent.

Task:
Generate accurate job application answers for the candidate  using only verified profile information.

Requirements:
- short, medium, and long options where relevant
- no invented facts
- professional tone
- adapt to the role
- flag uncertain items for review

Output:
- answer set in structured JSON
- review flags
- evidence used
```

---

## 31. Approval Agent Prompt

```md
You are an approval agent.

Task:
Before submission, show a concise review summary.

Display:
- company
- role
- score
- why it matches
- selected resume version
- selected cover letter
- generated answers
- risk warnings
- final action recommendation

Rules:
- do not submit automatically when approval is required
- clearly mark uncertain fields
- ask for a final human action
```

---

## 32. Policy and Safety Rules Prompt

```md
You are the safety and compliance controller for Job Hunter.

Always enforce:
- truthful candidate representation
- no fabricated experience
- no secret bypass of anti-bot protections
- no captcha bypass
- no uncontrolled mass-apply behavior
- no duplicate applications
- stop on suspicious site behavior
- protect credentials
- log high-risk events
- require approval for sensitive platforms and uncertain answers
```

---

## 33. Initial Candidate Data Snapshot

Seed the candidate profile with the following verified starting assumptions, then update from local files.

```json
{
  "name": "the candidate ",
  "portfolio_url": "https://the candidate.careers/",
  "github_url": "https://github.com/the candidate9",
  "linkedin_url": "https://www.linkedin.com/in/the candidate--a559b01aa/",
  "base_location": "Sri Lanka",
  "target_roles": [
    "AI Engineer",
    "Data Scientist",
    "Business Analyst",
    "Business Analytics Specialist",
    "Machine Learning Engineer",
    "Full-Stack Developer",
    "Python Developer",
    "Analytics Engineer"
  ],
  "document_roots": [
    "D:\\Job Hunter\\data\\cv",
    "D:\\Job Hunter\\data\\portfolio",
    "D:\\Job Hunter\\data\\github_exports",
    "D:\\Job Hunter\\data\\private_reports",
    "D:\\Job Hunter\\data\\certificates"
  ]
}
```

---

## 34. First Build Tasks for Anti Gravity

If this project is being created inside Anti Gravity or another agent-building platform, start with this execution order:

### Task 1
Create the project structure exactly as defined above.

### Task 2
Implement:
- config loader
- database connection
- document asset model
- candidate profile model
- job posting model
- application model

### Task 3
Build document ingestion pipelines for:
- PDF
- DOCX
- plain text
- markdown
- HTML content

### Task 4
Create a candidate profile builder that:
- parses CV
- parses portfolio site
- parses GitHub profile
- reads local private reports
- stores extracted evidence

### Task 5
Build ATS connectors:
- Greenhouse
- Lever
- generic careers parser

### Task 6
Build matching engine and shortlist UI.

### Task 7
Build resume tailoring, cover letter generation, and application answer generation.

### Task 8
Build browser automation with assisted approval mode.

### Task 9
Build dashboard and audit logs.

### Task 10
Add tests, hardening, and deployment instructions.

---

## 35. Non-Negotiable Acceptance Criteria

The project is complete only when it can:

- ingest the candidate’s candidate materials from local folders
- build a structured candidate profile
- discover real job postings
- rank jobs against profile fit
- generate tailored resumes and cover letters
- answer job application questions accurately
- fill and prepare job applications
- upload required files
- stop for approval where required
- log every application action
- prevent duplicate applications

---

## 36. Final Developer Notes

This project should be built as a **professional portfolio-grade AI agent system**, not as a shortcut bot.

The final product should demonstrate:
- agent orchestration
- document intelligence
- LLM-powered personalization
- browser automation
- safe workflow design
- real-world business utility

The project should be organized so that later it can support:
- multiple candidate profiles
- multiple job regions
- interview preparation
- outreach automation
- follow-up scheduling
- recruiter CRM features

---

## 37. Recommended Next File

After this file, create these immediately:

1. `README.md`
2. `requirements.txt`
3. `.env.example`
4. `app/main.py`
5. `app/config.py`
6. `app/models/`
7. `app/prompts/`
8. `dashboard/streamlit_app.py`

---

## 38. Final Instruction to the Build Agent

Build the Job Hunter system in phases, complete each phase fully, test it, and preserve production quality. Use modular code, strong typing, clean logs, and reusable prompts. Prioritize truthfulness, safe automation, and application quality over aggressive submission volume.
