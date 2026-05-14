"""
Pull environmental non-target screening (NTS) / suspect screening community
matches from OpenAlex. Uses the same UHR-MS instrument variants as v2 so the
counts are comparable to the seven other communities.
"""
import requests, time, json, csv
from pathlib import Path
from collections import Counter

BASE = "https://api.openalex.org/works"
MAIL = "erika.freeman@igb-berlin.de"

OUT_LISTS = Path(r"G:\My Drive\3-WorkAndPurpose\0-ABC_Lab\06-Teaching_Outreach\1-ConferenceTalks\ASLO2026\_BibliometricAnalysis\paper_lists")
OUT_RAW = Path(r"G:\My Drive\3-WorkAndPurpose\0-ABC_Lab\06-Teaching_Outreach\1-ConferenceTalks\ASLO2026\_BibliometricAnalysis\raw_data")

INSTRUMENT_VARIANTS = [
    '"FT-ICR"',
    '"FTICR"',
    '"FT ICR"',
    '"Fourier transform ion cyclotron"',
    '"Orbitrap"',
    '"ultrahigh resolution mass"',
    '"ultra-high resolution mass"',
    '"high resolution mass spectrometry"',  # NTS papers often phrase it this way
    '"high-resolution mass spectrometry"',
]

# Topic phrases the NTS / suspect-screening community uses
NTS_TOPICS = [
    "non-target screening",
    "non-target analysis",
    "nontarget screening",
    "nontarget analysis",
    "suspect screening",
    "wide-scope screening",
    "contaminants of emerging concern",
    "transformation products",
    "non-targeted screening",
]


def fetch(filter_str, max_calls=100):
    works = {}
    cursor = "*"
    n_calls = 0
    while cursor and n_calls < max_calls:
        params = {
            "filter": filter_str + ",publication_year:2000-2025",
            "per-page": 200,
            "select": "id,doi,title,publication_year,authorships,primary_location",
            "cursor": cursor,
            "mailto": MAIL,
        }
        try:
            r = requests.get(BASE, params=params, timeout=60)
        except requests.RequestException as e:
            print(f"    [net err] {e}")
            break
        n_calls += 1
        if not r.ok:
            print(f"    [{r.status_code}] {r.text[:120]}")
            break
        data = r.json()
        for w in data.get("results", []):
            works[w["id"]] = w
        cursor = data.get("meta", {}).get("next_cursor")
        if not cursor or not data.get("results"):
            break
        time.sleep(0.12)
    return works


print("=== Environmental non-target screening (NTS) ===")
queries = [
    f'title_and_abstract.search:{instr} AND "{topic}"'
    for instr in INSTRUMENT_VARIANTS
    for topic in NTS_TOPICS
]

all_works = {}
for q in queries:
    w = fetch(q)
    new = len(set(w.keys()) - set(all_works.keys()))
    all_works.update(w)
    topic = q.split('AND "')[-1].rstrip('"')
    instr = q.split('search:')[1].split(' AND')[0].strip('"')
    print(f"  {instr:<38s} x {topic:<35s} +{new:5d} (total {len(all_works)})")

rows = []
year_counter = Counter()
journal_counter = Counter()
for wid, w in all_works.items():
    title = (w.get("title") or "").strip()
    year = w.get("publication_year")
    journal = ((w.get("primary_location") or {}).get("source") or {}).get("display_name", "") or ""
    authors = [a.get("author", {}).get("display_name") for a in w.get("authorships", []) if a.get("author")]
    authors = [n for n in authors if n]
    auth_short = ", ".join(authors[:3]) + (f" et al. (n={len(authors)})" if len(authors) > 3 else "")
    rows.append({
        "year": year, "title": title, "authors_short": auth_short,
        "all_authors": "; ".join(authors), "journal": journal,
        "doi": w.get("doi", "") or "", "openalex_id": wid,
    })
    if year:
        year_counter[year] += 1
    if journal:
        journal_counter[journal] += 1

OUT_LISTS.mkdir(parents=True, exist_ok=True)
OUT_RAW.mkdir(parents=True, exist_ok=True)

csv_path = OUT_LISTS / "fticr_environmental_nts_v1.csv"
with open(csv_path, "w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["year", "title", "authors_short", "all_authors", "journal", "doi", "openalex_id"])
    w.writeheader()
    for r in sorted(rows, key=lambda x: (x["year"] or 0, x["journal"].lower())):
        w.writerow(r)

out = {
    "queried": "2026-05-14",
    "label": "Environmental non-target screening / suspect screening",
    "method": "OpenAlex strict title_and_abstract.search. UHR-MS instruments AND NTS topic phrases. Deduplicated by OpenAlex work-id.",
    "instrument_variants": INSTRUMENT_VARIANTS,
    "topics": NTS_TOPICS,
    "total_unique_works": len(rows),
    "year_2025": year_counter.get(2025, 0),
    "year_totals": {str(y): year_counter[y] for y in sorted(year_counter)},
    "top_10_journals": dict(journal_counter.most_common(10)),
}
json_path = OUT_RAW / "fticr_environmental_nts_v1.json"
with open(json_path, "w", encoding="utf-8") as f:
    json.dump(out, f, indent=2)

print(f"\n-> {len(rows)} unique works saved to {csv_path.name}")
print(f"-> 2025: {year_counter.get(2025, 0)} papers")
print(f"-> Summary JSON: {json_path.name}")
print(f"\nTop 5 journals:")
for j, n in journal_counter.most_common(5):
    print(f"  {n:4d}  {j}")
