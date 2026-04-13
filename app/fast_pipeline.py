"""
Fast Apply Pipeline
Loads the already-discovered jobs, ranks them quickly using keyword matching + GPT for top candidates,
generates documents, then applies.
"""

import os
import sys
import json
import asyncio
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def sep(label=""): print(f"\n{'='*60}\n  {label}\n{'='*60}")
def ok(m):   print(f"  [OK]   {m}")
def info(m): print(f"  [-->]  {m}")
def warn(m): print(f"  [!!]   {m}")
def err(m):  print(f"  [ERR]  {m}")


# ── Quick local pre-filter (no API cost) ─────────────────────────────────────
STRONG_TITLE_WORDS = [
    "data scientist", "ai engineer", "machine learning engineer", "ml engineer",
    "analytics engineer", "data analyst", "applied scientist",
    "nlp", "python developer", "full stack", "fullstack",
    "data engineer", "business intelligence", "bi engineer",
]
BOOST_WORDS = [
    "healthcare", "health", "nlp", "python", "flask", "analytics",
    "machine learning", "deep learning", "sql", "dashboard",
]
DISCARD_WORDS = [
    "senior director", "vp ", "vice president", "principal engineer",
    "staff engineer", "distinguished", "manager, advanced analytics",
    "hardware", "embedded", "sales engineer", "account executive",
    "intern", "graduate program",
]

def prefilter_jobs(jobs: list, max_results: int = 50) -> list:
    """Fast keyword-based pre-filter to get the best candidates before GPT scoring."""
    global applied_urls
    if "applied_urls" not in globals():
        applied_urls = set()

    scored = []
    for job in jobs:
        title   = job["title"].lower()
        desc    = job.get("description_text", "").lower()

        # Hard exclude
        if any(d in title for d in DISCARD_WORDS):
            continue

        # Skip already applied
        if job.get("application_url") in applied_urls:
            continue

        # Compute quick score
        score = 0
        for w in STRONG_TITLE_WORDS:
            if w in title:
                score += 15
                break
        for w in BOOST_WORDS:
            if w in title or w in desc[:500]:
                score += 3
        
        # Location / source geo tier (PRIMARY sort key — overrides keyword scores)
        loc  = job.get("location", "").lower()
        src  = job.get("source_name", "").lower()

        if src == "topjobs":
            geo_tier = 100  # TopJobs = Sri Lanka, always first
        elif any(t in loc for t in ["sri lanka", "colombo", "kandy", "galle"]):
            geo_tier = 90
        elif any(t in loc for t in ["dubai", "uae", "abu dhabi", "sharjah"]):
            geo_tier = 80
        elif any(t in loc for t in ["singapore"]):
            geo_tier = 70
        elif any(t in loc for t in ["malaysia", "kuala lumpur", "indonesia", "thailand",
                                     "vietnam", "india", "philippines", "asia"]):
            geo_tier = 50
        elif any(t in loc for t in ["uk", "united kingdom", "london"]):
            geo_tier = 30
        elif any(t in loc for t in ["usa", "america", "canada"]):
            geo_tier = 20
        else:
            geo_tier = 10

        # Workplace type adds to keyword score (not geo_tier)
        wt = job.get("workplace_type", "").lower()
        if wt == "remote":
            score += 10
        elif wt == "hybrid":
            score += 5

        if score > 0 or geo_tier > 10:
            scored.append({**job, "pre_score": score, "geo_tier": geo_tier})

    # PRIMARY sort by geo_tier, SECONDARY by keyword score — geography always wins
    scored.sort(key=lambda x: (x["geo_tier"], x["pre_score"]), reverse=True)
    return scored[:max_results]


async def run_fast_pipeline(mode="auto_safe", top=50, min_score=60):
    global applied_urls

    # ── Already Applied Check ───────────────────────────────────────────────
    applied_urls = set()
    log_path = "generated/logs/applications.jsonl"
    if os.path.exists(log_path):
        with open(log_path, encoding="utf-8") as f:
            for line in f:
                try:
                    data = json.loads(line)
                    # Key is 'status', not 'action'
                    if "submitted" in data.get("status", "") or "filled" in data.get("status", ""):
                        applied_urls.add(data.get("url"))
                except:
                    pass

    # ── Load discovered jobs ─────────────────────────────────────────────────
    sep("STEP 1 / 4  LOADING DISCOVERED JOBS")
    import glob
    log_files = sorted(glob.glob("generated/logs/discovered_*.json"), reverse=True)
    if not log_files:
        err("No discovered jobs found. Run: python -m app.pipeline --discover-only")
        return

    with open(log_files[0], encoding="utf-8") as f:
        all_jobs = json.load(f)

    ok(f"Loaded {len(all_jobs)} jobs from {log_files[0]}")

    # ── Pre-filter ──────────────────────────────────────────────────────────
    candidates = prefilter_jobs(all_jobs, max_results=300)
    ok(f"Pre-filtered to {len(candidates)} strong candidates (no API cost)")
    for i, j in enumerate(candidates[:50], 1):
        print(f"    {i:02d}. [{j['pre_score']:2d}] {j['company_name']:20s} | {j['title'][:55]}")

    # ── GPT Ranking on pre-filtered set ────────────────────────────────────
    sep("STEP 2 / 4  AI RANKING (GPT-4o-mini)")
    from app.agents.ranking_agent import RankingAgent
    ranker  = RankingAgent()
    ranked  = ranker.rank_jobs(candidates, min_score=min_score)
    shortlist = ranked[:top]

    if not shortlist:
        warn("No jobs met the minimum score. Lowering threshold to 50...")
        shortlist = sorted(candidates, key=lambda x: x.get("pre_score", 0), reverse=True)[:top]
        # Give them a default score so they still get documents
        for j in shortlist:
            if "overall_score" not in j:
                j["overall_score"] = j.get("pre_score", 50)
                j["recommendation"] = "apply after review"
                j["fit_reasons"] = ["Keyword match"]
                j["gaps"] = []

    ok(f"Final shortlist — top {len(shortlist)} jobs:")
    print()
    for i, j in enumerate(shortlist, 1):
        rec = j.get("recommendation", "")
        wt  = j.get("workplace_type", "")
        print(f"    {i:02d}. [{j.get('overall_score',0):3d}/100] "
              f"{j['company_name']:22s} | {j['title'][:45]:45s} | {wt:8s} | {rec}")

    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    rank_path = f"generated/logs/ranked_{ts}.json"
    with open(rank_path, "w", encoding="utf-8") as f:
        json.dump(shortlist, f, indent=2, default=str)
    ok(f"Saved ranked shortlist -> {rank_path}")

    # ── Document Generation ─────────────────────────────────────────────────
    sep("STEP 3 / 4  DOCUMENT GENERATION")
    from app.agents.resume_agent import ResumeAgent
    resume_agent = ResumeAgent()

    packages = []
    for job in shortlist:
        company = job["company_name"]
        title   = job["title"]
        info(f"Generating docs for: {company} — {title}")
        try:
            rp = resume_agent.tailor_resume(job)
            ok(f"  Resume        -> {rp}")
            cp = resume_agent.write_cover_letter(job)
            ok(f"  Cover Letter  -> {cp}")
            an = resume_agent.generate_answers(job)
            ok(f"  Answers       -> {len(an)} questions")
            packages.append({"job": job, "resume_path": rp, "cl_path": cp, "answers": an})
        except Exception as e:
            err(f"  Failed for {company}: {e}")

    ok(f"Documents generated for {len(packages)} jobs")

    if mode == "draft_only":
        sep("DONE — DRAFT MODE")
        ok("All documents generated. Review them in:")
        ok("  generated/resumes/")
        ok("  generated/cover_letters/")
        ok("  generated/answers/")
        ok("Re-run with --mode assisted to open browser and fill forms.")
        return packages

    # ── Applications ─────────────────────────────────────────────────────────
    sep("STEP 4 / 4  BROWSER APPLICATION")
    from app.agents.application_agent import ApplicationAgent
    # Pass mode explicitly — do NOT rely on os.environ alone
    applicant = ApplicationAgent(mode=mode)
    os.environ["SUBMISSION_MODE"] = mode

    results = []
    for pkg in packages:
        job     = pkg["job"]
        source  = job.get("source_name", "")
        company = job["company_name"]
        title   = job["title"]
        score   = job.get("overall_score", 0)
        info(f"Applying: {company} — {title} (score={score}, source={source})")

        try:
            if source == "Greenhouse":
                result = await asyncio.wait_for(
                    applicant.apply_greenhouse(job, pkg["resume_path"], pkg["cl_path"], pkg["answers"]),
                    timeout=90
                )
            elif source == "Lever":
                result = await asyncio.wait_for(
                    applicant.apply_lever(job, pkg["resume_path"], pkg["cl_path"], pkg["answers"]),
                    timeout=90
                )
            else:
                result = {"status": "skipped", "reason": f"Source {source} not automated"}

            status = result.get("status", "?")
            ok(f"  -> {status}")
            results.append({**job, "result": result})
        except asyncio.TimeoutError:
            err(f"  Application failed: Timed out after 90 seconds. Browser is likely stuck. Skipping.")
        except Exception as e:
            err(f"  Application failed: {e}")

    # ── Summary ──────────────────────────────────────────────────────────────
    sep("PIPELINE COMPLETE")
    ok(f"Mode: {mode}")
    ok(f"Jobs discovered: {len(all_jobs)}")
    ok(f"Jobs pre-filtered: {len(candidates)}")
    ok(f"Jobs AI-ranked: {len(ranked) if 'ranked' in dir() else len(shortlist)}")
    ok(f"Documents generated: {len(packages)}")
    if results:
        submitted = sum(1 for r in results if "submitted" in r.get("result", {}).get("status", ""))
        ok(f"Applications submitted/approved: {submitted}/{len(results)}")
    ok("Screenshots: generated/screenshots/")
    ok("Application log: generated/logs/applications.jsonl")

    return packages


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode",      default="auto_safe", choices=["draft_only","assisted","auto_safe"])
    parser.add_argument("--top",       type=int, default=50)
    parser.add_argument("--min-score", type=int, default=60)
    args = parser.parse_args()

    asyncio.run(run_fast_pipeline(args.mode, args.top, args.min_score))
