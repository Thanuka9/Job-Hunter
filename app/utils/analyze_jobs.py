import json
from collections import Counter

jobs = json.load(open("generated/logs/discovered_20260411_072253.json"))
print(f"Total jobs discovered: {len(jobs)}")
src = Counter(j["source_name"] for j in jobs)
print("By source:", dict(src))
companies = Counter(j["company_name"] for j in jobs).most_common(10)
print("Top companies:")
for co, n in companies:
    print(f"  {co}: {n}")
print("\nSample jobs:")
for j in jobs[:15]:
    print(f"  [{j['source_name']:12s}] {j['company_name']:25s} | {j['title'][:55]}")
