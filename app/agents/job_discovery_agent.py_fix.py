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
