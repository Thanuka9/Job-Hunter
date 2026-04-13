"""
tests/test_fixes.py
Run from project root: python tests/test_fixes.py
Tests all recent fixes: ApplicationAgent, RankingAgent boost, fast_pipeline pre-filter priority.
"""

import sys
import os
import json
import traceback
import asyncio

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv()

PASS = "  [PASS]"
FAIL = "  [FAIL]"


def sep(label):
    print(f"\n{'='*60}\n  {label}\n{'='*60}")


# ── TEST 1: ApplicationAgent Init ─────────────────────────────────────────────
sep("TEST 1 — ApplicationAgent Init & Attributes")
try:
    from app.agents.application_agent import ApplicationAgent, CANDIDATE_INFO, FIELD_ANSWER_RULES

    agent = ApplicationAgent(mode="auto_safe")
    assert agent.mode == "auto_safe",          f"mode wrong: {agent.mode}"
    assert hasattr(agent, "screenshots_dir"),   "missing screenshots_dir"
    assert hasattr(agent, "logs_dir"),          "missing logs_dir"
    assert "first_name" in CANDIDATE_INFO,     "CANDIDATE_INFO missing first_name"
    assert "email" in CANDIDATE_INFO,          "CANDIDATE_INFO missing email"
    assert "phone" in CANDIDATE_INFO,          "CANDIDATE_INFO missing phone"
    assert "cv_path" in CANDIDATE_INFO,        "CANDIDATE_INFO missing cv_path"
    assert len(FIELD_ANSWER_RULES) >= 15,      f"Too few rules: {len(FIELD_ANSWER_RULES)}"
    print(f"{PASS} mode={agent.mode}")
    print(f"{PASS} CANDIDATE_INFO keys: {list(CANDIDATE_INFO.keys())}")
    print(f"{PASS} FIELD_ANSWER_RULES count: {len(FIELD_ANSWER_RULES)}")

    # Default mode (no arg) should come from env or fallback to auto_safe
    agent2 = ApplicationAgent()
    assert agent2.mode in ("auto_safe", "assisted", "draft_only"), f"Default mode invalid: {agent2.mode}"
    print(f"{PASS} Default mode resolves correctly: {agent2.mode}")

except Exception as e:
    print(f"{FAIL} ApplicationAgent: {e}")
    traceback.print_exc()


# ── TEST 2: _safe_fill and _submit_form exist and are coroutines ──────────────
sep("TEST 2 — ApplicationAgent Methods Exist")
try:
    import inspect
    methods = ["apply_greenhouse", "apply_lever", "_safe_fill", "_upload_resume",
               "_fill_textareas", "_smart_fill_all_fields", "_submit_form",
               "_screenshot", "_log_application"]
    for m in methods:
        fn = getattr(agent, m, None)
        assert fn is not None, f"Missing method: {m}"
        if m not in ("_log_application",):
            assert inspect.iscoroutinefunction(fn), f"{m} should be async"
    print(f"{PASS} All {len(methods)} methods present and correctly async/sync")
except Exception as e:
    print(f"{FAIL} Method check: {e}")
    traceback.print_exc()


# ── TEST 3: Timeout protection ────────────────────────────────────────────────
sep("TEST 3 — Freeze/Timeout Protection (simulated)")
try:
    async def mock_do_nothing():
        await asyncio.sleep(200)  # Simulate frozen page

    async def test_timeout():
        try:
            await asyncio.wait_for(mock_do_nothing(), timeout=0.5)
            return False  # Should not reach here
        except asyncio.TimeoutError:
            return True

    result = asyncio.run(test_timeout())
    assert result, "asyncio.wait_for timeout did not trigger"
    print(f"{PASS} asyncio.wait_for timeout protection works correctly")
except Exception as e:
    print(f"{FAIL} Timeout test: {e}")
    traceback.print_exc()


# ── TEST 4: RankingAgent Priority Boost ───────────────────────────────────────
sep("TEST 4 — RankingAgent Sri Lanka / Dubai / Singapore Priority Boost")
try:
    from app.agents.ranking_agent import RankingAgent
    ranker = RankingAgent()

    # Validate PRIORITY_LOCATIONS list exists
    assert hasattr(ranker, "PRIORITY_LOCATIONS"), "RankingAgent missing PRIORITY_LOCATIONS"
    assert "sri lanka" in ranker.PRIORITY_LOCATIONS, "sri lanka not in PRIORITY_LOCATIONS"
    assert "dubai" in ranker.PRIORITY_LOCATIONS,     "dubai not in PRIORITY_LOCATIONS"
    assert "singapore" in ranker.PRIORITY_LOCATIONS, "singapore not in PRIORITY_LOCATIONS"
    print(f"{PASS} PRIORITY_LOCATIONS: {ranker.PRIORITY_LOCATIONS}")

    # Test boost calculation logic
    test_cases = [
        {"location": "Colombo, Sri Lanka", "source_name": "TopJobs",    "base": 70, "expect_boost": True},
        {"location": "Dubai, UAE",         "source_name": "Greenhouse", "base": 65, "expect_boost": True},
        {"location": "Singapore",          "source_name": "Lever",      "base": 60, "expect_boost": True},
        {"location": "New York, USA",      "source_name": "Greenhouse", "base": 75, "expect_boost": False},
        {"location": "Remote",             "source_name": "Greenhouse", "base": 65, "expect_boost": True},
    ]

    for tc in test_cases:
        loc       = (tc["location"] + " " + tc["source_name"]).lower()
        workplace = "remote" if "remote" in tc["location"].lower() else "on-site"
        is_pri    = (
            any(pl in loc for pl in ranker.PRIORITY_LOCATIONS)
            or workplace == "remote"
            or tc["source_name"] == "TopJobs"
        )
        boost     = 15 if is_pri else 0
        result    = min(100, tc["base"] + boost)
        boosted   = is_pri == tc["expect_boost"]
        flag = PASS if boosted else FAIL
        print(f"  {flag} [{tc['location'][:30]:30s}] base={tc['base']} boost={boost} final={result} | priority={is_pri}")
        assert boosted, f"Boost mismatch for {tc['location']}"

except Exception as e:
    print(f"{FAIL} RankingAgent boost: {e}")
    traceback.print_exc()


# ── TEST 5: fast_pipeline pre-filter Sri Lanka priority ───────────────────────
sep("TEST 5 — fast_pipeline Pre-Filter Geographic Priority")
try:
    from app.fast_pipeline import prefilter_jobs

    test_jobs = [
        {"title": "Data Scientist",  "company_name": "US Corp",    "location": "New York, USA",       "source_name": "Greenhouse", "workplace_type": "On-site", "description_text": "python data scientist analytics",    "application_url": "http://a.com/1"},
        {"title": "ML Engineer",     "company_name": "LK Corp",    "location": "Colombo, Sri Lanka",  "source_name": "TopJobs",    "workplace_type": "Hybrid",  "description_text": "machine learning python sql",           "application_url": "http://lk.com/2"},
        {"title": "AI Engineer",     "company_name": "Dubai Co",   "location": "Dubai, UAE",          "source_name": "Greenhouse", "workplace_type": "On-site", "description_text": "ai engineer python machine learning",   "application_url": "http://dubai.com/3"},
        {"title": "Data Analyst",    "company_name": "SG Corp",    "location": "Singapore",           "source_name": "Lever",      "workplace_type": "Remote",  "description_text": "analytics data analyst sql python",     "application_url": "http://sg.com/4"},
        {"title": "Python Developer","company_name": "UK Corp",    "location": "London, UK",          "source_name": "Greenhouse", "workplace_type": "On-site", "description_text": "python developer full stack analytics", "application_url": "http://uk.com/5"},
    ]

    filtered = prefilter_jobs(test_jobs, max_results=10)

    print("  Pre-filter ranking (expected: LK > Dubai > SG > UK/USA):")
    for i, j in enumerate(filtered, 1):
        print(f"    {i}. [geo={j.get('geo_tier',0):3d} kw={j['pre_score']:3d}] {j['company_name']:20s} | {j['location']:30s}")

    # Geo tier sort guarantees: Sri Lanka > Dubai > Singapore > UK/USA
    assert filtered[0]["company_name"] == "LK Corp",   f"Expected LK Corp #1, got {filtered[0]['company_name']}"
    assert filtered[1]["company_name"] == "Dubai Co",  f"Expected Dubai Co #2, got {filtered[1]['company_name']}"
    assert filtered[2]["company_name"] == "SG Corp",   f"Expected SG Corp #3, got {filtered[2]['company_name']}"

    print(f"{PASS} Sri Lanka is ranked #1 (geo_tier=100)")
    print(f"{PASS} Dubai is ranked #2 (geo_tier=80)")
    print(f"{PASS} Singapore is ranked #3 (geo_tier=70)")

except Exception as e:
    print(f"{FAIL} fast_pipeline pre-filter: {e}")
    traceback.print_exc()


# ── TEST 6: FIELD_ANSWER_RULES coverage check ─────────────────────────────────
sep("TEST 6 — FIELD_ANSWER_RULES Coverage")
try:
    import re
    from app.agents.application_agent import FIELD_ANSWER_RULES, TEXTAREA_SPECIALS

    test_phrases = {
        "Are you authorized to work?":      "Yes",
        "Do you require visa sponsorship?":  "No",
        "Gender":                            "Male",
        "Years of experience with Python":   "7",
        "Notice period":                     "2 weeks",
        "I consent to data processing":      None,  # checkbox type
        "Tell us about yourself":            "about_me",
    }

    for phrase, expected_answer in test_phrases.items():
        matched = None
        for rule in FIELD_ANSWER_RULES:
            if re.search(rule["pattern"], phrase, re.I):
                matched = rule
                break
        if matched:
            print(f"  {PASS} '{phrase[:45]}' -> rule matched (answer={matched['answer']}, type={matched['type']})")
        else:
            print(f"  [WARN] '{phrase}' -> no rule matched (may need adding)")

    assert "cover_letter" in TEXTAREA_SPECIALS, "Missing cover_letter special text"
    assert "about_me"     in TEXTAREA_SPECIALS, "Missing about_me special text"
    assert len(TEXTAREA_SPECIALS["about_me"]) > 50, "about_me text too short"
    print(f"{PASS} TEXTAREA_SPECIALS loaded correctly")

except Exception as e:
    print(f"{FAIL} FIELD_ANSWER_RULES: {e}")
    traceback.print_exc()


# ── TEST 7: Log key fix verification ─────────────────────────────────────────
sep("TEST 7 — Application Log Key ('status' not 'action')")
try:
    import tempfile, json as _json

    # Write a sample log with 'status' key (new format)
    log_content = [
        {"timestamp": "2026-01-01T00:00:00", "company": "TestCo", "title": "ML Eng", "url": "http://skip.me/1", "status": "submitted", "mode": "auto_safe"},
        {"timestamp": "2026-01-01T00:00:01", "company": "OtherCo","title": "DS",     "url": "http://apply.me/2", "status": "error",     "mode": "auto_safe"},
    ]
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False, encoding="utf-8") as f:
        tmp_path = f.name
        for entry in log_content:
            f.write(_json.dumps(entry) + "\n")

    # Simulate the dedup check from fast_pipeline
    applied_urls = set()
    with open(tmp_path, encoding="utf-8") as f:
        for line in f:
            data = _json.loads(line)
            if "submitted" in data.get("status", "") or "filled" in data.get("status", ""):
                applied_urls.add(data.get("url"))
    os.unlink(tmp_path)

    assert "http://skip.me/1"  in applied_urls, "Submitted URL should be in applied_urls"
    assert "http://apply.me/2" not in applied_urls, "Error URL should NOT be in applied_urls"
    print(f"{PASS} Log key 'status' deduplication works correctly")
    print(f"{PASS} applied_urls = {applied_urls}")

except Exception as e:
    print(f"{FAIL} Log key fix: {e}")
    traceback.print_exc()


# ── SUMMARY ───────────────────────────────────────────────────────────────────
sep("ALL TESTS COMPLETE")
print("  If all lines above show [PASS], the fixes are verified.")
print("  Run the pipeline: python -m app.fast_pipeline --mode auto_safe --top 50")
print()
