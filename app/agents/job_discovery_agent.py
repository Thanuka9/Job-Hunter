"""
Job Discovery Agent
Fetches real jobs from Greenhouse and Lever public APIs.
"""

import httpx
import hashlib
import json
import os
from typing import List, Dict, Optional
from datetime import datetime


# ── Curated company list by ATS ───────────────────────────────────────────────
# These companies use Greenhouse or Lever and are relevant for Data/AI roles
GREENHOUSE_COMPANIES = [
    "airbnb", "dropbox", "hubspot", "zendesk", "mongodb", "elastic",
    "hashicorp", "twilio", "cloudflare", "figma", "notion", "airtable",
    "databricks", "snowflake", "dbt-labs", "segment", "mixpanel",
    "intercom", "gusto", "lattice", "rippling", "brex", "carta",
    "confluent", "supabase", "retool", "census", "mode", "amplitude",
    "heap", "fullstory", "looker", "metabase", "sisense",
    "workato", "mulesoft", "boomi", "informatica", "talend",
    "alteryx", "dataiku", "h2o-ai", "domino-data-lab",
    "thoughtspot", "atscale", "dremio", "starburst",
    "benchling", "veeva", "health-catalyst",
    "babylonhealth", "tempus", "flatiron", "komodo-health",
    "canonical", "jetbrains", "atlassian", "sentry-io",
    "grafana-labs", "pagerduty", "sumo-logic", "new-relic",
    "digitalocean", "linode", "render", "railway",
]

LEVER_COMPANIES = [
    "netflix", "reddit", "discord", "stripe", "braintree", "plaid",
    "affirm", "marqeta", "chime", "robinhood", "coinbase",
    "openai", "anthropic", "cohere", "huggingface", "scale-ai",
    "weights-biases", "mlflow", "determined-ai",
    "palantir", "c3-ai", "datarobot", "rapidai",
    "veritone", "clarifai", "landing-ai",
    "gong", "clari", "chorus-ai", "salesloft", "outreach",
    "carta", "deel", "remote", "rippling-hq",
    "toast", "lightspeed", "square",
    "shopify", "klaviyo", "yotpo", "attentive",
    "benchling", "insitro", "recursion",
]

# Role keywords to match against job titles
RELEVANT_KEYWORDS = [
    "data scientist", "ai engineer", "machine learning", "ml engineer",
    "data engineer", "analytics engineer", "data analyst",
    "business analyst", "business intelligence", "bi developer",
    "python developer", "backend developer", "full stack", "fullstack",
    "software engineer", "applied scientist", "research scientist",
    "nlp engineer", "computer vision", "llm", "generative ai",
    "deep learning", "data platform", "data infrastructure",
    "analytics", "insights", "decision science",
]

# Keywords that disqualify a role
EXCLUDE_KEYWORDS = [
    "senior director", "vp of", "vice president", "c-level", "cto", "cdo",
    "principal engineer", "distinguished", "staff engineer",
    "intern", "graduate", "entry level", "0-1 year",
    "sales engineer", "customer success", "account executive",
    "hardware", "embedded", "firmware", "mechanical", "electrical",
    "devops only", "site reliability", "network engineer",
]


class JobDiscoveryAgent:

    def __init__(self):
        self.client = httpx.Client(timeout=15, follow_redirects=True)
        self.headers = {
            "User-Agent": "Mozilla/5.0 (compatible; JobHunterBot/1.0; +https://thanukaellepola.careers/)",
            "Accept": "application/json",
        }

    # ── Greenhouse ────────────────────────────────────────────────────────────
    def fetch_greenhouse(self, company_id: str) -> List[Dict]:
        url = f"https://boards-api.greenhouse.io/v1/boards/{company_id}/jobs?content=true"
        try:
            r = self.client.get(url, headers=self.headers)
            if r.status_code != 200:
                return []
            data = r.json()
            jobs = []
            for job in data.get("jobs", []):
                title = job.get("title", "")
                if not self._is_relevant(title):
                    continue
                jobs.append({
                    "external_job_id": str(job.get("id")),
                    "source_name":     "Greenhouse",
                    "source_url":      job.get("absolute_url", ""),
                    "application_url": job.get("absolute_url", ""),
                    "company_name":    self._clean_company(company_id),
                    "title":           title,
                    "location":        self._extract_location(job),
                    "job_type":        "Full-time",
                    "workplace_type":  self._detect_remote(title, job.get("content", "")),
                    "description_text": self._strip_html(job.get("content", "")),
                    "salary_text":     None,
                    "discovered_at":   datetime.utcnow().isoformat(),
                })
            return jobs
        except Exception as e:
            return []

    # ── Lever ─────────────────────────────────────────────────────────────────
    def fetch_lever(self, company_id: str) -> List[Dict]:
        url = f"https://api.lever.co/v0/postings/{company_id}?mode=json"
        try:
            r = self.client.get(url, headers=self.headers)
            if r.status_code != 200:
                return []
            jobs = []
            for job in r.json():
                title = job.get("text", "")
                if not self._is_relevant(title):
                    continue
                categories = job.get("categories", {})
                location   = categories.get("location", "") or job.get("workplaceType", "")
                content    = " ".join([
                    job.get("descriptionPlain", ""),
                    " ".join(l.get("content", "") for l in job.get("lists", [])),
                    job.get("additionalPlain", ""),
                ])
                jobs.append({
                    "external_job_id": job.get("id"),
                    "source_name":     "Lever",
                    "source_url":      job.get("hostedUrl", ""),
                    "application_url": job.get("applyUrl", job.get("hostedUrl", "")),
                    "company_name":    self._clean_company(company_id),
                    "title":           title,
                    "location":        location,
                    "job_type":        "Full-time",
                    "workplace_type":  job.get("workplaceType", self._detect_remote(title, content)),
                    "description_text": content.strip(),
                    "salary_text":     None,
                    "discovered_at":   datetime.utcnow().isoformat(),
                })
            return jobs
        except Exception as e:
            return []

    # ── TopJobs Sri Lanka ─────────────────────────────────────────────────────
    def fetch_topjobs(self) -> List[Dict]:
        """Fetch software/IT jobs from TopJobs.lk (Sri Lanka)."""
        import uuid
        try:
            from bs4 import BeautifulSoup
            url = "https://www.topjobs.lk/applicant/vacancybyfunctionalarea.jsp?FA=SDQ&jst=OPEN"
            import httpx
            with httpx.Client(verify=False, timeout=15) as client:
                r = client.get(url)
            
            soup = BeautifulSoup(r.text, 'html.parser')
            rows = soup.find_all('tr', id=lambda x: x and x.startswith('tr'))
            
            jobs = []
            for row in rows[:50]:  # Cap at top 50 recents to prevent massive iframe traversal costs
                title_elem = row.find('h2')
                if not title_elem:
                    continue
                title = title_elem.text.strip()
                
                # Check keyword relevance 
                if not self._is_relevant(title):
                    continue

                company_elem = row.find('h1')
                company = company_elem.text.strip() if company_elem else "TopJobs Employer"
                
                jc_elem = row.find('span', id=lambda x: x and x.startswith('hdnJC'))
                ec_elem = row.find('span', id=lambda x: x and x.startswith('hdnEC'))
                ac_elem = row.find('span', id=lambda x: x and x.startswith('hdnAC'))
                
                if jc_elem and ec_elem and ac_elem:
                    jc = jc_elem.text.strip()
                    ec = ec_elem.text.strip()
                    ac = ac_elem.text.strip()
                    job_url = f"https://www.topjobs.lk/employer/JobAdvertismentServlet?rid=0&ac={ac}&jc={jc}&ec={ec}"
                else:
                    job_url = url
                
                desc_col = row.find('td', width="35%")
                short_desc = desc_col.text.strip() if desc_col else ""
                
                jobs.append({
                    "external_job_id": jc_elem.text.strip() if jc_elem else str(uuid.uuid4())[:8],
                    "source_name":     "TopJobs",
                    "source_url":      job_url,
                    "application_url": job_url,
                    "company_name":    company,
                    "title":           title,
                    "location":        "Sri Lanka (Estimated)",
                    "job_type":        "Full-time",
                    "workplace_type":  self._detect_remote(title, short_desc),
                    "description_text": f"{title} at {company}. {short_desc}\n\nSee full advert: {job_url}",
                    "salary_text":     None,
                    "discovered_at":   datetime.utcnow().isoformat(),
                })
            return jobs
        except Exception as e:
            print(f"TopJobs scrape error: {e}")
            return []

    # ── Helpers ───────────────────────────────────────────────────────────────
    def _is_relevant(self, title: str) -> bool:
        t = title.lower()
        if any(excl in t for excl in EXCLUDE_KEYWORDS):
            return False
        return any(kw in t for kw in RELEVANT_KEYWORDS)

    def _detect_remote(self, title: str, content: str) -> str:
        combo = (title + " " + content).lower()
        if "remote" in combo:
            return "Remote"
        if "hybrid" in combo:
            return "Hybrid"
        return "On-site"

    def _extract_location(self, job: dict) -> str:
        offices = job.get("offices", [])
        if offices:
            return offices[0].get("name", "")
        return ""

    @staticmethod
    def _clean_company(company_id: str) -> str:
        return company_id.replace("-", " ").replace("_", " ").title()

    @staticmethod
    def _strip_html(html: str) -> str:
        import re
        clean = re.sub(r"<[^>]+>", " ", html)
        clean = re.sub(r"\s+", " ", clean)
        return clean.strip()

    def discover_all(self, max_per_source: Optional[int] = None) -> List[Dict]:
        """Fetch jobs from all configured sources with caching."""
        cache_file = "generated/logs/discovery_cache.json"
        os.makedirs("generated/logs", exist_ok=True)
        
        # Check cache (1 hour)
        if os.path.exists(cache_file):
            mtime = os.path.getmtime(cache_file)
            if (datetime.now().timestamp() - mtime) < 3600: 
                with open(cache_file, "r", encoding="utf-8") as f:
                    print("  [Discovery] Using cached results (less than 1 hour old)...")
                    return json.load(f)

        all_jobs = []
        print(f"  [Discovery] Scanning {len(GREENHOUSE_COMPANIES)} Greenhouse boards...")
        for company in GREENHOUSE_COMPANIES:
            jobs = self.fetch_greenhouse(company)
            if jobs:
                print(f"    [+] {self._clean_company(company)}: {len(jobs)} relevant jobs")
                all_jobs.extend(jobs)

        print(f"  [Discovery] Scanning {len(LEVER_COMPANIES)} Lever boards...")
        for company in LEVER_COMPANIES:
            jobs = self.fetch_lever(company)
            if jobs:
                print(f"    [+] {self._clean_company(company)}: {len(jobs)} relevant jobs")
                all_jobs.extend(jobs)

        print(f"  [Discovery] Scanning TopJobs.lk (Sri Lanka)...")
        tj_jobs = self.fetch_topjobs()
        if tj_jobs:
            print(f"    [+] TopJobs: {len(tj_jobs)} relevant jobs")
            all_jobs.extend(tj_jobs)

        # Deduplicate and Hash
        seen = set()
        unique = []
        for j in all_jobs:
            # Create a simple deduplication key
            key = f"{j['company_name'].lower()}::{j['title'].lower()}"
            if key not in seen:
                seen.add(key)
                if "description_hash" not in j:
                    j["description_hash"] = hashlib.md5(j["description_text"].encode()).hexdigest()
                unique.append(j)

        # Save to cache
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(unique, f, indent=2, default=str)

        return unique
