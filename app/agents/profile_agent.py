import os
from sqlalchemy.orm import Session
from app.models.candidate_profile import CandidateProfile, CandidateSkill
from app.models.document_asset import DocumentAsset
from app.agents.document_agent import DocumentAgent
from app.services.parser_service import ParserService
import hashlib

class ProfileAgent:
    def __init__(self, db: Session):
        self.db = db
        self.doc_agent = DocumentAgent()
        self.parser = ParserService()

    def ingest_cv(self, file_path: str) -> CandidateProfile:
        """
        Ingest a CV PDF, extract structured profile data via GPT-4o,
        and persist everything into the database. Safe to re-run (idempotent).
        Returns the CandidateProfile.
        """
        file_name = os.path.basename(file_path)

        # ── dedup check ──────────────────────────────────────────
        with open(file_path, "rb") as f:
            raw = f.read()
        sha256 = hashlib.sha256(raw).hexdigest()

        existing_asset = self.db.query(DocumentAsset).filter(DocumentAsset.sha256 == sha256).first()

        if existing_asset:
            # If a complete profile already exists, return it directly
            existing_profile = self.db.query(CandidateProfile).first()
            if existing_profile and existing_profile.full_name:
                return existing_profile
            # Profile record is missing/incomplete — re-extract using stored text
            asset = existing_asset
            text  = existing_asset.extracted_text or self.parser.parse_pdf(file_path)
        else:
            # ── new asset ────────────────────────────────────────
            text  = self.parser.parse_pdf(file_path)
            asset = DocumentAsset(
                file_name  = file_name,
                file_path  = file_path,
                file_type  = "pdf",
                sha256     = sha256,
                source_type= "cv",
                extracted_text = text,
            )
            self.db.add(asset)
            self.db.commit()
            self.db.refresh(asset)

        # ── AI extraction ────────────────────────────────────────
        profile_data = self.doc_agent.extract_profile_data(text)
        asset.parsed_json = str(profile_data)
        self.db.commit()

        # ── upsert CandidateProfile ──────────────────────────────
        profile = self.db.query(CandidateProfile).first()
        if not profile:
            profile = CandidateProfile(
                full_name               = profile_data.get("full_name"),
                email                   = profile_data.get("email"),
                phone                   = profile_data.get("phone"),
                location                = profile_data.get("location"),
                linkedin_url            = profile_data.get("linkedin_url"),
                github_url              = profile_data.get("github_url"),
                portfolio_url           = profile_data.get("portfolio_url"),
                summary                 = profile_data.get("summary"),
                years_experience        = profile_data.get("years_experience"),
                target_roles            = ", ".join(profile_data.get("target_roles", [])) if isinstance(profile_data.get("target_roles"), list) else profile_data.get("target_roles"),
            )
            self.db.add(profile)
        else:
            profile.full_name           = profile_data.get("full_name")    or profile.full_name
            profile.email               = profile_data.get("email")        or profile.email
            profile.phone               = profile_data.get("phone")        or profile.phone
            profile.location            = profile_data.get("location")     or profile.location
            profile.linkedin_url        = profile_data.get("linkedin_url") or profile.linkedin_url
            profile.github_url          = profile_data.get("github_url")   or profile.github_url
            profile.portfolio_url       = profile_data.get("portfolio_url")or profile.portfolio_url
            profile.summary             = profile_data.get("summary")      or profile.summary
            profile.years_experience    = profile_data.get("years_experience") or profile.years_experience

        self.db.commit()
        self.db.refresh(profile)

        # ── skills ───────────────────────────────────────────────
        skills_data = profile_data.get("skills", {})
        if isinstance(skills_data, dict):
            for category, skill_list in skills_data.items():
                if isinstance(skill_list, list):
                    for skill_name in skill_list:
                        exists = self.db.query(CandidateSkill).filter(
                            CandidateSkill.candidate_id == profile.id,
                            CandidateSkill.skill_name   == skill_name
                        ).first()
                        if not exists:
                            self.db.add(CandidateSkill(
                                candidate_id        = profile.id,
                                skill_name          = skill_name,
                                category            = category,
                                source_document_id  = asset.id,
                            ))
        elif isinstance(skills_data, list):
            # Handle flat list format
            for skill_name in skills_data:
                exists = self.db.query(CandidateSkill).filter(
                    CandidateSkill.candidate_id == profile.id,
                    CandidateSkill.skill_name   == skill_name
                ).first()
                if not exists:
                    self.db.add(CandidateSkill(
                        candidate_id        = profile.id,
                        skill_name          = skill_name,
                        category            = "General",
                        source_document_id  = asset.id,
                    ))

        self.db.commit()
        return profile
