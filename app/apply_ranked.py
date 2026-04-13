"""
Run Auto-Apply from already ranked jobs.
Bypasses the slow discovery and ranking phase.
"""

import os
import sys
import json
import asyncio
import glob
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def sep(label=""): print(f"\n{'='*60}\n  {label}\n{'='*60}")
def ok(m):   print(f"  [OK]   {m}")
def err(m):  print(f"  [ERR]  {m}")

async def run_apply():
    # 1. Load the most recent ranked file
    ranked_files = sorted(glob.glob("generated/logs/ranked_*.json"), reverse=True)
    if not ranked_files:
        err("No ranked jobs found.")
        return

    with open(ranked_files[0], encoding="utf-8") as f:
        jobs = json.load(f)
    ok(f"Loaded {len(jobs)} ranked jobs from {ranked_files[0]}")

    # 2. Re-generate docs or locate them? Actually, they should be in the folders.
    # But just in case, we'll re-generate because it's fast (only 10 jobs) or use what's there.
    # To be perfectly safe, let's just generate docs and then apply.
    from app.agents.resume_agent import ResumeAgent
    resume_agent = ResumeAgent()

    packages = []
    for job in jobs[:10]:
        company = job["company_name"]
        title   = job["title"]
        try:
            rp = resume_agent.tailor_resume(job)
            cp = resume_agent.write_cover_letter(job)
            an = resume_agent.generate_answers(job)
            packages.append({"job": job, "resume_path": rp, "cl_path": cp, "answers": an})
        except Exception as e:
            err(f"Doc generation failed for {company}: {e}")

    # 3. Apply
    sep("STARTING APPLICATIONS (AUTO_SAFE)")
    from app.agents.application_agent import ApplicationAgent
    applicant = ApplicationAgent()
    os.environ["SUBMISSION_MODE"] = "auto_safe"

    results = []
    for pkg in packages:
        job = pkg["job"]
        print(f"\n[-->] Applying to: {job['company_name']} - {job['title']}")
        try:
            source = job.get("source_name", "")
            if source == "Greenhouse":
                res = await asyncio.wait_for(
                    applicant.apply_greenhouse(job, pkg["resume_path"], pkg["cl_path"], pkg["answers"]),
                    timeout=90
                )
            elif source == "Lever":
                res = await asyncio.wait_for(
                    applicant.apply_lever(job, pkg["resume_path"], pkg["cl_path"], pkg["answers"]),
                    timeout=90
                )
            else:
                res = {"status": "skipped", "reason": f"Unknown source {source}"}
            ok(f"Result: {res['status']}")
            results.append({**job, "result": res})
        except asyncio.TimeoutError:
            err(f"Apply failed: Timed out after 90 seconds. Browser is likely stuck. Skipping.")
        except Exception as e:
            err(f"Apply failed: {e}")

if __name__ == "__main__":
    asyncio.run(run_apply())
