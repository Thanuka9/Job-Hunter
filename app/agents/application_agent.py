"""
Application Agent v3
Uses Playwright to fill and submit Greenhouse and Lever applications.
Mode: auto_safe (Full Auto) by default  |  assisted for human review
Key fixes:
  - Per-page hard timeout (120s) prevents infinite freezes
  - Robust field-filling with fallback strategies
  - Comprehensive question answering (dropdowns, radios, comboboxes, textareas)
  - Multi-strategy submit detection with force-click fallback
  - Proper networkidle wait before form scanning
"""

import logging
import os
import json
import asyncio
import traceback
from datetime import datetime
from typing import Dict, Optional

logger = logging.getLogger("ApplicationAgent")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

CANDIDATE_INFO = {
    "first_name":  os.getenv("CANDIDATE_FIRST_NAME", "Thanuka"),
    "last_name":   os.getenv("CANDIDATE_LAST_NAME",  "Ellepola"),
    "email":       os.getenv("CANDIDATE_EMAIL",       "Thanuka.ellepola@gmail.com"),
    "phone":       os.getenv("CANDIDATE_PHONE",       "+94 77 670 5832"),
    "linkedin":    os.getenv("LINKEDIN_URL",          "https://www.linkedin.com/in/thanuka-ellepola-a559b01aa/"),
    "github":      os.getenv("GITHUB_URL",            "https://github.com/Thanuka9"),
    "portfolio":   os.getenv("PORTFOLIO_URL",         "https://thanukaellepola.careers/"),
    "location":    "Sri Lanka",
    "cv_path":     os.path.abspath("Thanuka Ellepola CV.pdf"),
    "salary":      os.getenv("EXPECTED_SALARY", "Open to discussion"),
    "notice":      os.getenv("NOTICE_PERIOD",   "2 weeks"),
}

# ── Comprehensive answer rules ─────────────────────────────────────────────────
FIELD_ANSWER_RULES = [
    # Authorization & visa
    {"pattern": r"authorized|authorised|legally eligible|right to work|work.*authoriz|eligible to work", "answer": "Yes", "type": "select_radio"},
    {"pattern": r"require.*sponsor|need.*sponsor|visa.*sponsor|sponsorship", "answer": "No",  "type": "select_radio"},
    # Gender
    {"pattern": r"\bgender\b", "answer": "Male", "type": "select_radio"},
    # Race / ethnicity
    {"pattern": r"race|ethnicity|ethnic", "answer": "Asian", "type": "select_radio"},
    # Veteran
    {"pattern": r"veteran|military service|armed forces", "answer": "No", "type": "select_radio"},
    # Disability
    {"pattern": r"disability|disabled|disabilit", "answer": "No", "type": "select_radio"},
    # Relocation
    {"pattern": r"willing.*relocat|open.*relocat|relocat.*willing", "answer": "Yes", "type": "select_radio"},
    # Remote ok
    {"pattern": r"remote.*work|work.*remote|work.*from.*home", "answer": "Yes", "type": "select_radio"},
    # Residency
    {"pattern": r"citizen.*singapore|singapore.*citizen|singapore.*pr|permanent resident.*singapore", "answer": "No", "type": "select_radio"},
    {"pattern": r"citizen.*uae|uae.*citizen|citizen.*dubai", "answer": "No", "type": "select_radio"},
    # Experience years
    {"pattern": r"years.*experience.*python|python.*years|hands.on.*python", "answer": "7", "type": "input_number"},
    {"pattern": r"years.*experience.*react|react.*years", "answer": "5", "type": "input_number"},
    {"pattern": r"years.*experience.*sql|sql.*years", "answer": "7", "type": "input_number"},
    {"pattern": r"years.*experience.*machine learning|ml.*years|years.*ml", "answer": "5", "type": "input_number"},
    {"pattern": r"years.*experience|how many years|total experience", "answer": "7", "type": "input_number"},
    # Salary
    {"pattern": r"salary.*expect|expect.*salary|desired.*salary|compensation", "answer": "Open to discussion", "type": "input_text"},
    # Notice
    {"pattern": r"notice period|start date|available.*start|when.*available", "answer": "2 weeks", "type": "input_text"},
    # Consent / GDPR
    {"pattern": r"consent|gdpr|privacy|data.*process|i agree|i understand|terms", "answer": "Yes", "type": "checkbox"},
    # Cover letter / motivation
    {"pattern": r"cover letter|motivation|why.*apply|why.*interested|tell us why", "answer": "cover_letter", "type": "textarea_special"},
    # About yourself
    {"pattern": r"about yourself|introduce yourself|tell us about", "answer": "about_me", "type": "textarea_special"},
    # Country
    {"pattern": r"country.*residence|where.*live|current.*country", "answer": "Sri Lanka", "type": "select_radio"},
    # Heard about
    {"pattern": r"how.*hear|where.*hear|referr", "answer": "LinkedIn", "type": "select_radio"},
]

TEXTAREA_SPECIALS = {
    "cover_letter": (
        "I am excited to apply for this role. With 7+ years of experience in AI engineering, "
        "data science, and full-stack development, I have built NLP pipelines processing 7M+ records, "
        "deployed ML models for healthcare payment prediction, and developed production Flask/Python systems. "
        "I am highly motivated and confident in bringing measurable impact to your team."
    ),
    "about_me": (
        "I am Thanuka Ellepola, an AI Engineer and Data Scientist with 7+ years of experience in "
        "healthcare analytics and full-stack development. I specialize in Python, machine learning, "
        "NLP, and scalable web applications. I have built real-world AI systems processing millions "
        "of records and am passionate about data-driven problem solving."
    ),
}


class ApplicationAgent:

    def __init__(self, mode: Optional[str] = None):
        self.mode = mode or os.getenv("SUBMISSION_MODE", "auto_safe")
        self.screenshots_dir = "generated/screenshots"
        self.logs_dir        = "generated/logs"
        os.makedirs(self.screenshots_dir, exist_ok=True)
        os.makedirs(self.logs_dir, exist_ok=True)
        logger.info(f"ApplicationAgent initialized — mode={self.mode}")

    # ─────────────────────────────────────────────────────────── Greenhouse ──

    async def apply_greenhouse(self, job: dict, resume_path: str,
                                cover_letter_path: str, answers: dict) -> dict:
        """Fill and submit a Greenhouse application form with full freeze protection."""
        from playwright.async_api import async_playwright

        url     = job.get("application_url", "")
        company = job.get("company_name", "Unknown")
        title   = job.get("title", "Unknown")
        result  = {"status": "pending", "mode": self.mode, "url": url}

        if not url:
            result.update({"status": "error", "error": "No application URL"})
            return result

        try:
            # Hard 120-second wall-clock timeout for the whole application
            result = await asyncio.wait_for(
                self._do_greenhouse(job, resume_path, answers, result),
                timeout=120,
            )
        except asyncio.TimeoutError:
            result.update({"status": "error", "error": "Timed out (120s) — page likely frozen"})
            logger.error(f"  [TIMEOUT] {company} — {title}")
        except Exception as e:
            result.update({"status": "error", "error": str(e)})
            logger.error(f"  [ERR] {company}: {e}")
        return result

    async def _do_greenhouse(self, job, resume_path, answers, result):
        from playwright.async_api import async_playwright

        url     = job["application_url"]
        company = job.get("company_name", "Unknown")
        title   = job.get("title", "Unknown")

        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=(self.mode != "assisted"),
                slow_mo=100,
                args=["--no-sandbox", "--disable-dev-shm-usage"],
            )
            ctx = await browser.new_context(
                viewport={"width": 1280, "height": 900},
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
                ),
            )
            page = await ctx.new_page()
            # Per-navigation timeout
            page.set_default_navigation_timeout(45000)
            page.set_default_timeout(15000)

            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=45000)
                # Extra wait for React hydration
                try:
                    await page.wait_for_load_state("networkidle", timeout=10000)
                except Exception:
                    pass
                await asyncio.sleep(1)
                await self._screenshot(page, company, title, "01_opened")

                # ── Basic personal fields ──────────────────────────────────
                await self._safe_fill(page, [
                    'input[name="first_name"]', '#first_name',
                    'input[autocomplete="given-name"]',
                ], CANDIDATE_INFO["first_name"])

                await self._safe_fill(page, [
                    'input[name="last_name"]', '#last_name',
                    'input[autocomplete="family-name"]',
                ], CANDIDATE_INFO["last_name"])

                await self._safe_fill(page, [
                    'input[name="email"]', '#email', 'input[type="email"]',
                    'input[autocomplete="email"]',
                ], CANDIDATE_INFO["email"])

                await self._safe_fill(page, [
                    'input[name="phone"]', '#phone', 'input[type="tel"]',
                    'input[autocomplete="tel"]', 'input[name="phone_number"]',
                ], CANDIDATE_INFO["phone"])

                # LinkedIn / portfolio / website
                await self._safe_fill(page, [
                    'input[name*="linkedin"]', 'input[id*="linkedin"]',
                    'input[placeholder*="LinkedIn"]', 'input[id*="34532171002"]',
                ], CANDIDATE_INFO["linkedin"])

                await self._safe_fill(page, [
                    'input[name*="website"]', 'input[placeholder*="Portfolio"]',
                    'input[placeholder*="website"]', 'input[name*="portfolio"]',
                ], CANDIDATE_INFO["portfolio"])

                await self._safe_fill(page, [
                    'input[name*="github"]', 'input[placeholder*="GitHub"]',
                    'input[id*="github"]',
                ], CANDIDATE_INFO["github"])

                # ── CV Upload ──────────────────────────────────────────────
                await self._upload_resume(page, resume_path)

                # ── Textarea Q&A (free text questions) ────────────────────
                await self._fill_textareas(page, answers, job)

                # ── Comprehensive form question answering ──────────────────
                await self._smart_fill_all_fields(page, job)

                await asyncio.sleep(1)
                await self._screenshot(page, company, title, "02_filled")

                # ── Submit ─────────────────────────────────────────────────
                if self.mode == "auto_safe":
                    submitted = await self._submit_form(page)
                    if submitted:
                        success = False
                        try:
                            url_before = page.url
                            await asyncio.sleep(4)
                            if page.url != url_before or "confirm" in page.url.lower() or "thanks" in page.url.lower():
                                success = True
                            else:
                                try:
                                    success_el = page.locator("text=/application submitted|thank you for applying|received your application/i").first
                                    if await success_el.count() > 0:
                                        success = True
                                except Exception:
                                    pass
                        except Exception:
                            pass
                            
                        if success:
                            await self._screenshot(page, company, title, "03_submitted")
                            result["status"] = "submitted"
                            logger.info(f"  [SUCCESS] Submitted: {company} — {title}")
                        else:
                            await self._screenshot(page, company, title, "03_validation_error")
                            result["status"] = "validation_error"
                            logger.warning(f"  [!!] Validation Error (missing fields): {company} — {title}")
                    else:
                        result["status"] = "submit_button_not_found"
                        await self._screenshot(page, company, title, "03_no_submit")
                        logger.warning(f"  [!!] Submit button not found: {company}")
                else:
                    print(f"\n  [APPROVAL REQUIRED] {company} — {title}")
                    print(f"  URL: {url}")
                    input("  Review the form, then press ENTER when done...")
                    result["status"] = "submitted_manually"

                self._log_application(job, result["status"], self.mode)

            except Exception as e:
                result.update({"status": "error", "error": str(e)})
                traceback.print_exc()
                try:
                    await self._screenshot(page, company, title, "ERROR")
                except Exception:
                    pass
            finally:
                await browser.close()

        return result

    # ──────────────────────────────────────────────────────────────── Lever ──

    async def apply_lever(self, job: dict, resume_path: str,
                           cover_letter_path: str, answers: dict) -> dict:
        """Fill and submit a Lever application form with full freeze protection."""
        url     = job.get("application_url", "")
        company = job.get("company_name", "Unknown")
        title   = job.get("title", "Unknown")
        result  = {"status": "pending", "mode": self.mode, "url": url}

        if not url:
            result.update({"status": "error", "error": "No application URL"})
            return result

        try:
            result = await asyncio.wait_for(
                self._do_lever(job, resume_path, answers, result),
                timeout=120,
            )
        except asyncio.TimeoutError:
            result.update({"status": "error", "error": "Timed out (120s)"})
            logger.error(f"  [TIMEOUT] {company} — {title}")
        except Exception as e:
            result.update({"status": "error", "error": str(e)})
        return result

    async def _do_lever(self, job, resume_path, answers, result):
        from playwright.async_api import async_playwright

        url     = job["application_url"]
        company = job.get("company_name", "Unknown")
        title   = job.get("title", "Unknown")

        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=(self.mode != "assisted"),
                slow_mo=100,
                args=["--no-sandbox", "--disable-dev-shm-usage"],
            )
            ctx = await browser.new_context(
                viewport={"width": 1280, "height": 900},
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
                ),
            )
            page = await ctx.new_page()
            page.set_default_navigation_timeout(45000)
            page.set_default_timeout(15000)

            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=45000)
                try:
                    await page.wait_for_load_state("networkidle", timeout=10000)
                except Exception:
                    pass
                await asyncio.sleep(1)
                await self._screenshot(page, company, title, "01_opened")

                full_name = f"{CANDIDATE_INFO['first_name']} {CANDIDATE_INFO['last_name']}"

                await self._safe_fill(page, [
                    'input[name="name"]', 'input[placeholder*="Full name"]',
                    'input[placeholder*="Name"]',
                ], full_name)

                await self._safe_fill(page, [
                    'input[name="email"]', 'input[type="email"]',
                ], CANDIDATE_INFO["email"])

                await self._safe_fill(page, [
                    'input[name="phone"]', 'input[type="tel"]',
                ], CANDIDATE_INFO["phone"])

                await self._safe_fill(page, [
                    'input[name="urls[LinkedIn]"]', 'input[name*="linkedin"]',
                    'input[placeholder*="LinkedIn"]',
                ], CANDIDATE_INFO["linkedin"])

                await self._safe_fill(page, [
                    'input[name*="website"]', 'input[name*="portfolio"]',
                    'input[placeholder*="Portfolio"]',
                ], CANDIDATE_INFO["portfolio"])

                # Resume upload
                await self._upload_resume(page, resume_path)

                # Free text questions
                await self._fill_textareas(page, answers, job)

                # Smart field answering
                await self._smart_fill_all_fields(page, job)

                await asyncio.sleep(1)
                await self._screenshot(page, company, title, "02_filled")

                if self.mode == "auto_safe":
                    submitted = await self._submit_form(page)
                    if submitted:
                        success = False
                        try:
                            url_before = page.url
                            await asyncio.sleep(4)
                            if page.url != url_before or "confirm" in page.url.lower() or "thanks" in page.url.lower():
                                success = True
                            else:
                                try:
                                    success_el = page.locator("text=/application submitted|thank you for applying|received your application/i").first
                                    if await success_el.count() > 0:
                                        success = True
                                except Exception:
                                    pass
                        except Exception:
                            pass

                        if success:
                            await self._screenshot(page, company, title, "03_submitted")
                            result["status"] = "submitted"
                            logger.info(f"  [SUCCESS] Submitted: {company} — {title}")
                        else:
                            await self._screenshot(page, company, title, "03_validation_error")
                            result["status"] = "validation_error"
                            logger.warning(f"  [!!] Validation Error (missing fields): {company} — {title}")
                    else:
                        result["status"] = "submit_button_not_found"
                        await self._screenshot(page, company, title, "03_no_submit")
                else:
                    print(f"\n  [APPROVAL REQUIRED] {company} — {title}")
                    input("  Review and press ENTER when done...")
                    result["status"] = "submitted_manually"

                self._log_application(job, result["status"], self.mode)

            except Exception as e:
                result.update({"status": "error", "error": str(e)})
                traceback.print_exc()
                try:
                    await self._screenshot(page, company, title, "ERROR")
                except Exception:
                    pass
            finally:
                await browser.close()

        return result

    # ─────────────────────────────────────────────────────────── Helpers ──────

    async def _safe_fill(self, page, selectors: list, value: str):
        """Try each selector until one works. No crash on miss."""
        for sel in selectors:
            try:
                locator = page.locator(sel).first
                if await locator.count() > 0:
                    try:
                        await locator.scroll_into_view_if_needed(timeout=3000)
                    except Exception:
                        pass
                    # Clear then fill
                    await locator.fill("", timeout=5000)
                    await locator.fill(value, timeout=5000)
                    return True
            except Exception:
                continue
        return False

    async def _upload_resume(self, page, resume_path: str):
        """Upload CV/resume file if a file input is present."""
        if not resume_path or not os.path.exists(resume_path):
            logger.warning(f"  Resume path not found: {resume_path}")
            return
        try:
            file_inputs = [
                'input[type="file"][name*="resume"]',
                'input[type="file"][name*="cv"]',
                'input[type="file"][accept*="pdf"]',
                'input[type="file"]',
            ]
            for sel in file_inputs:
                loc = page.locator(sel).first
                if await loc.count() > 0:
                    await loc.set_input_files(resume_path)
                    await asyncio.sleep(2)  # Wait for upload to process
                    logger.info(f"  Resume uploaded: {resume_path}")
                    return
        except Exception as e:
            logger.warning(f"  Resume upload failed: {e}")

    async def _fill_textareas(self, page, answers: dict, job: dict):
        """Fill visible empty textareas with AI-generated answers."""
        try:
            qa_values = [v for v in answers.values() if isinstance(v, str) and v.strip()]
            textareas = await page.locator("textarea:visible").all()
            idx = 0
            for ta in textareas:
                try:
                    current = await ta.input_value()
                    if current.strip():
                        continue  # Already filled
                    # Get label/question context
                    label_text = ""
                    try:
                        label_text = await ta.evaluate(
                            """el => {
                                let c = el.closest('.field') || el.closest('.form-group') || el.parentElement;
                                return c ? c.innerText : '';
                            }"""
                        )
                    except Exception:
                        pass
                    label_lower = label_text.lower()

                    # Check if it's a special field
                    filled = False
                    for rule in FIELD_ANSWER_RULES:
                        import re
                        if rule["type"] == "textarea_special" and re.search(rule["pattern"], label_lower, re.I):
                            special_text = TEXTAREA_SPECIALS.get(rule["answer"], rule["answer"])
                            await ta.fill(special_text)
                            filled = True
                            break
                    if not filled and idx < len(qa_values):
                        await ta.fill(qa_values[idx])
                        idx += 1
                except Exception:
                    continue
        except Exception as e:
            logger.warning(f"  Textarea fill warning: {e}")

    async def _smart_fill_all_fields(self, page, job: dict):
        """
        Uses LLMService to dynamically read all unfilled fields and decide how to fill them.
        This handles native dropdowns, custom select elements, checkboxes, and radios robustly.
        """
        from app.services.llm_service import LLMService
        llm = LLMService()

        # Inject JS to assign tracking IDs and extract form context
        js_extractor = """
        () => {
            let fields = [];
            // Target inputs, selects, textareas
            let els = document.querySelectorAll('input:not([type="hidden"]):not([type="file"]):not([type="submit"]), select, textarea');
            
            let groups = {}; // to group radios and checkboxes
            
            els.forEach((el, idx) => {
                let isFilled = false;
                if (el.tagName === 'INPUT' && ['text','email','tel','number'].includes(el.type)) {
                    if (el.value.trim().length > 0) isFilled = true;
                } else if (el.tagName === 'TEXTAREA') {
                    if (el.value.trim().length > 0) isFilled = true;
                } else if (el.tagName === 'SELECT') {
                    if (el.selectedIndex > 0 && el.options[el.selectedIndex].value !== '') isFilled = true;
                } else if (el.type === 'radio' || el.type === 'checkbox') {
                    if (el.checked) isFilled = true;
                }
                
                if (isFilled) return;
                
                // assign a tracking ID to the element on the actual page
                let aiId = 'ai_elem_' + idx;
                el.setAttribute('data-ai-id', aiId);
                
                let labelText = '';
                if (el.labels && el.labels.length > 0) {
                    labelText = el.labels[0].innerText;
                } else {
                    let container = el.closest('.field') || el.closest('.form-group') || el.parentElement;
                    if (container) labelText = container.innerText;
                }
                labelText = labelText.replace(/\\n/g, ' ').trim();
                
                if (el.type === 'radio' || el.type === 'checkbox') {
                    let gname = el.name || labelText;
                    if (!groups[gname]) groups[gname] = { type: el.type, label: labelText, options: [] };
                    
                    let specLabel = labelText;
                    let explicitLabel = el.closest('label');
                    if (explicitLabel) specLabel = explicitLabel.innerText.replace(/\\n/g, ' ').trim();
                    groups[gname].options.push({ id: aiId, text: specLabel });
                } else {
                    let opts = [];
                    if (el.tagName === 'SELECT') {
                        opts = Array.from(el.options).filter(o => o.value).map(o => o.text.replace(/\\n/g, ' ').trim());
                    }
                    fields.push({
                        id: aiId,
                        type: el.tagName.toLowerCase() + (el.type ? ' ' + el.type : ''),
                        label: labelText,
                        options: opts
                    });
                }
            });
            
            for (let k in groups) {
                fields.push({
                    id: 'group',
                    type: groups[k].type + ' group',
                    label: groups[k].label,
                    radio_options: groups[k].options
                });
            }
            return fields;
        }
        """
        
        try:
            form_data = await page.evaluate(js_extractor)
            if not form_data:
                return

            # Integrate LangChain + RAG Service
            from app.services.rag_service import RAGService
            rag = RAGService()
            
            # Use LangChain to solve the JSON mapping
            actions = rag.extract_and_solve_form(form_data, CANDIDATE_INFO)
            
            # Execute Actions in Playwright
            for ai_id, action_val in actions.items():
                try:
                    locator = page.locator(f"[data-ai-id='{ai_id}']").first
                    if await locator.count() == 0:
                        continue
                        
                    el_type = await locator.evaluate("el => el.type || el.tagName.toLowerCase()")
                    await locator.scroll_into_view_if_needed(timeout=1000)
                    
                    if isinstance(action_val, bool) and action_val == True:
                        if not await locator.is_checked():
                            # Radios/Checkboxes via force click because labels often cover them
                            await locator.click(force=True, timeout=2000)
                            await asyncio.sleep(0.2)
                    elif el_type == "select-one":
                        # Try selecting by label text
                        try:
                            await locator.select_option(label=str(action_val), timeout=2000)
                        except Exception:
                            # Fallback to index 1
                            await locator.select_option(index=1, timeout=1000)
                        await asyncio.sleep(0.2)
                    else:
                        await locator.fill(str(action_val), timeout=2000)
                        await asyncio.sleep(0.2)
                except Exception as eval_e:
                    logger.debug(f"Action failed for {ai_id}: {eval_e}")
                    
        except Exception as e:
            logger.error(f"  [!!] LLM Smart Fill failed: {e}")

    async def _submit_form(self, page) -> bool:
        """
        Multi-strategy submit: tries buttons by text, id, type, then force-clicks.
        Returns True if a submit was triggered.
        """
        submit_strategies = [
            # Text-based
            'button:has-text("Submit Application")',
            'button:has-text("Submit")',
            'button:has-text("Apply Now")',
            'button:has-text("Apply")',
            'button:has-text("Send Application")',
            'button:has-text("Complete Application")',
            # Attribute-based
            'button[id="submit_app"]',
            'input[id="submit_app"]',
            'button[type="submit"]',
            'input[type="submit"]',
            '#submit_button',
            '#submit-application',
            '.submit-button',
            '[data-qa="btn-submit"]',
            '[data-testid*="submit"]',
        ]
        for sel in submit_strategies:
            try:
                btn = page.locator(sel).first
                if await btn.count() > 0:
                    visible = await btn.is_visible()
                    if visible:
                        await btn.scroll_into_view_if_needed()
                        await asyncio.sleep(0.5)
                        try:
                            await btn.click(timeout=8000)
                        except Exception:
                            # Force click as fallback
                            await btn.click(force=True, timeout=8000)
                        logger.info(f"  Submit clicked via: {sel}")
                        return True
            except Exception:
                continue
        return False

    async def _screenshot(self, page, company: str, title: str, step: str):
        safe_co = "".join(c if c.isalnum() else "_" for c in company)[:20]
        safe_ti = "".join(c if c.isalnum() else "_" for c in title)[:30]
        ts      = datetime.utcnow().strftime("%H%M%S")
        path    = os.path.join(self.screenshots_dir, f"{safe_co}_{safe_ti}_{step}_{ts}.png")
        try:
            await page.screenshot(path=path, full_page=True)
        except Exception:
            pass

    def _log_application(self, job: dict, action: str, mode: str):
        log_path = f"{self.logs_dir}/applications.jsonl"
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "company":   job.get("company_name"),
            "title":     job.get("title"),
            "url":       job.get("application_url"),
            "status":    action,
            "mode":      mode,
        }
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
