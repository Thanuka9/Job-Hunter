"""
Job Hunter Pipeline — Master Orchestrator
Runs: Discover → Rank → Generate Documents → Apply (Auto Mode by default)

Usage:
  python -m app.pipeline

Flags:
  --mode draft_only       Just discover and generate documents, no browser
  --mode assisted         Fill forms, pause for human approval
  --mode auto_safe        Auto-submit on Greenhouse/Lever (default)
  --top N                 Only apply to top N jobs (default: 50)
  --min-score N           Minimum match score to apply (default: 65)
  --discover-only         Only discover and rank, no documents/applications
"""

import os
import sys
import json
import asyncio
import argparse
from datetime import datetime
from dotenv import load_dotenv
from app.db.session import SessionLocal
from app.models.job_posting import JobPosting, JobScore
from app.models.application import Application

load_dotenv()

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


import logging

# Basic logging setup
os.makedirs("generated/logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("generated/logs/pipeline.log", encoding="utf-8")
    ]
)
logger = logging.getLogger("Pipeline")

def sep(label=""): logger.info(f"\n{'='*60}\n  {label}\n{'='*60}")
def ok(msg):  logger.info(f"  [OK]   {msg}")
def info(msg): logger.info(f"  [-->]  {msg}")
def warn(msg): logger.warning(f"  [!!]   {msg}")
def err(msg):  logger.error(f"  [ERR]  {msg}")


def parse_args():
    parser = argparse.ArgumentParser(description="Job Hunter Pipeline")
    parser.add_argument("--mode",          default=os.getenv("SUBMISSION_MODE", "auto_safe"), choices=["draft_only","assisted","auto_safe"])
    parser.add_argument("--top",           type=int, default=int(os.getenv("MAX_JOBS", "50")))
    parser.add_argument("--min-score",     type=int, default=int(os.getenv("MIN_SCORE", "65")))
    parser.add_argument("--discover-only", action="store_true")
    return parser.parse_args()


async def run_pipeline(args):
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

    # ── 1. Discovery ──────────────────────────────────────────────────────────
    sep("STEP 1 / 5  JOB DISCOVERY")
    from app.agents.job_discovery_agent import JobDiscoveryAgent
    discovery = JobDiscoveryAgent()
    jobs = discovery.discover_all(max_per_source=None)
    ok(f"Discovered {len(jobs)} relevant jobs across Greenhouse + Lever + TopJobs")

    if not jobs:
        warn("No jobs found. Check network or expand company list.")
        return

    ok(f"Discovery results loaded/saved to generated/logs/discovery_cache.json")

    # Create DB session
    db = SessionLocal()
    try:
        for j in jobs:
            # Check if job exists
            exists = db.query(JobPosting).filter(JobPosting.description_hash == j["description_hash"]).first()
            if not exists:
                new_job = JobPosting(
                    external_job_id = j["external_job_id"],
                    source_name     = j["source_name"],
                    source_url      = j["source_url"],
                    company_name    = j["company_name"],
                    title           = j["title"],
                    location        = j["location"],
                    job_type        = j["job_type"],
                    workplace_type  = j["workplace_type"],
                    description_text = j["description_text"],
                    description_hash = j["description_hash"],
                    application_url = j["application_url"],
                )
                db.add(new_job)
        db.commit()
    except Exception as dbe:
        err(f"Database error: {dbe}")
    finally:
        db.close()

    # ── 2. Ranking ────────────────────────────────────────────────────────────
    sep("STEP 2 / 5  RANKING & SCORING")
    from app.agents.ranking_agent import RankingAgent
    
    db = SessionLocal()
    ranker = RankingAgent(db=db)
    ranked_jobs = ranker.rank_jobs(jobs, min_score=args.min_score)
    
    # Save scores to DB
    try:
        for rj in ranked_jobs:
            job_rec = db.query(JobPosting).filter(JobPosting.description_hash == rj["description_hash"]).first()
            if job_rec:
                # Check if score already exists
                score_exists = db.query(JobScore).filter(JobScore.job_id == job_rec.id).first()
                if not score_exists:
                    new_score = JobScore(
                        job_id          = job_rec.id,
                        overall_score   = rj["overall_score"],
                        notes_json      = json.dumps(rj.get("fit_reasons", [])),
                        apply_recommendation = rj.get("recommendation", "skip"),
                    )
                    db.add(new_score)
        db.commit()
    except Exception as dbe:
        err(f"Database error saving scores: {dbe}")
    finally:
        db.close()
    shortlist = ranked_jobs[:args.top]

    ok(f"Ranked: {len(ranked_jobs)} jobs score >= {args.min_score}")
    ok(f"Shortlist (top {args.top}):")
    for i, j in enumerate(shortlist, 1):
        rec = j.get("recommendation","")
        print(f"    {i:02d}. [{j.get('overall_score',0):3d}/100] {j['company_name']} — {j['title'][:55]} | {rec}")

    rank_path = f"generated/logs/ranked_{ts}.json"
    with open(rank_path, "w", encoding="utf-8") as f:
        json.dump(shortlist, f, indent=2, default=str)
    ok(f"Saved ranked list to {rank_path}")

    if args.discover_only or not shortlist:
        if not shortlist:
            warn("No jobs met the score threshold. Done.")
        else:
            ok("Discovery-only mode. Stopping here.")
        return

    # ── 3. Document Generation ────────────────────────────────────────────────
    sep("STEP 3 / 5  DOCUMENT GENERATION")
    from app.agents.resume_agent import ResumeAgent
    resume_agent = ResumeAgent()

    job_packages = []
    for job in shortlist:
        company = job["company_name"]
        title   = job["title"]
        info(f"Generating documents for: {company} — {title}")
        try:
            resume_path = resume_agent.tailor_resume(job)
            ok(f"  Resume   -> {resume_path}")
            cl_path     = resume_agent.write_cover_letter(job)
            ok(f"  CovLetter-> {cl_path}")
            answers     = resume_agent.generate_answers(job)
            ok(f"  Answers  -> {len(answers)} questions answered")
            job_packages.append({
                "job":           job,
                "resume_path":   resume_path,
                "cl_path":       cl_path,
                "answers":       answers,
            })
        except Exception as e:
            err(f"  Document generation failed for {company}: {e}")

    ok(f"Generated documents for {len(job_packages)} jobs")

    if args.mode == "draft_only":
        ok("Mode: draft_only — stopping before browser automation.")
        print_summary(job_packages, args.mode)
        return

    # ── 4. Check Playwright ───────────────────────────────────────────────────
    sep("STEP 4 / 5  BROWSER AUTOMATION CHECK")
    try:
        from playwright.async_api import async_playwright
        async with async_playwright() as p:
            b = await p.chromium.launch(headless=True)
            await b.close()
        ok("Playwright: ready")
    except Exception as e:
        err(f"Playwright not ready: {e}")
        warn("Run: playwright install chromium")
        warn("Switching to draft_only mode.")
        print_summary(job_packages, "draft_only")
        return

    # ── 5. Applications ───────────────────────────────────────────────────────
    sep("STEP 5 / 5  APPLYING")
    from app.agents.application_agent import ApplicationAgent
    applicant = ApplicationAgent(mode=args.mode)

    # Update env mode for applicant
    os.environ["SUBMISSION_MODE"] = args.mode

    results = []
    for pkg in job_packages:
        job     = pkg["job"]
        company = job["company_name"]
        title   = job["title"]
        source  = job.get("source_name", "")
        info(f"Applying: {company} — {title} ({source}) | score={job.get('overall_score')}")

        try:
            if source == "Greenhouse":
                result = await applicant.apply_greenhouse(job, pkg["resume_path"], pkg["cl_path"], pkg["answers"])
            elif source == "Lever":
                result = await applicant.apply_lever(job, pkg["resume_path"], pkg["cl_path"], pkg["answers"])
            else:
                result = {"status": "skipped", "reason": f"Source {source} not automated yet"}

            status = result.get("status", "unknown")
            if "error" in status:
                err(f"  -> {status}: {result.get('error','')}")
            else:
                ok(f"  -> {status}")
            results.append({**pkg["job"], "apply_result": result})
        except Exception as e:
            err(f"  Application failed: {e}")

    # Save results
    res_path = f"generated/logs/applied_{ts}.json"
    with open(res_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, default=str)

    print_summary(job_packages, args.mode, results)


def print_summary(packages, mode, results=None):
    sep("PIPELINE COMPLETE")
    ok(f"Mode: {mode}")
    ok(f"Jobs processed: {len(packages)}")
    ok(f"Documents in: generated/resumes/ and generated/cover_letters/")
    if results:
        submitted = sum(1 for r in results if "submitted" in r.get("apply_result", {}).get("status",""))
        ok(f"Applications submitted/approved: {submitted}/{len(results)}")
    print()
    print("  Next steps:")
    print("  1. Review documents in generated/resumes/ and generated/cover_letters/")
    print("  2. View screenshots in generated/screenshots/")
    print("  3. Launch dashboard: python -m streamlit run dashboard/streamlit_app.py")
    print()


if __name__ == "__main__":
    args = parse_args()

    sep("JOB HUNTER AI PIPELINE")
    print(f"  Mode: {args.mode}")
    print(f"  Top N: {args.top}")
    print(f"  Min score: {args.min_score}")
    print(f"  Discover only: {args.discover_only}")

    asyncio.run(run_pipeline(args))
