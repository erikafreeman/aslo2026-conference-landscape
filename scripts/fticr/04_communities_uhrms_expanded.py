"""
v2: Fair UHR-MS comparison. Adds Orbitrap and "ultrahigh resolution mass" variants
to each community query so counts are apples-to-apples with the DOM comprehensive
pull (1,746 papers).
"""
import requests, time, json, csv
from pathlib import Path
from collections import Counter

BASE = "https://api.openalex.org/works"
MAIL = "erika.freeman@igb-berlin.de"

OUT_LISTS = Path(r"G:\My Drive\3-WorkAndPurpose\0-ABC_Lab\06-Teaching_Outreach\1-ConferenceTalks\ASLO2026\_BibliometricAnalysis\paper_lists")
OUT_RAW = Path(r"G:\My Drive\3-WorkAndPurpose\0-ABC_Lab\06-Teaching_Outreach\1-ConferenceTalks\ASLO2026\_BibliometricAnalysis\raw_data")

# UHR-MS instrument variants, matching the DOM comprehensive pull
INSTRUMENT_VARIANTS = [
    '"FT-ICR"',
    '"FTICR"',
    '"FT ICR"',
    '"Fourier transform ion cyclotron"',
    '"Orbitrap"',
    '"ultrahigh resolution mass"',
    '"ultra-high resolution mass"',
]

COMMUNITIES = {
    "clinical_metabolomics": {
        "label": "Clinical metabolomics",
        "topics": [
            "clinical metabolomics",
            "cancer biomarker",
            "inborn errors of metabolism",
            "exhaled breath",
            "patient plasma",
            "serum metabolome",
        ],
    },
    "proteomics": {
        "label": "Proteomics",
        "topics": [
            "top-down proteomics",
            "top-down mass spectrometry",
            "intact protein",
            "post-translational modification",
            "proteoform",
        ],
    },
    "pharma": {
        "label": "Pharma (drug metabolism, ADME, impurity profiling)",
        "topics": [
            "drug metabolism",
            "drug metabolite",
            "ADME",
            "impurity profiling",
            "pharmaceutical impurity",
            "metabolite identification",
        ],
    },
    "lipidomics": {
        "label": "Lipidomics",
        "topics": [
            "lipidomics",
            "lipidome",
            "atherosclerosis lipid",
            "neurodegeneration lipid",
        ],
    },
    "maldi_imaging": {
        "label": "MALDI imaging of tissue",
        "topics": [
            "MALDI imaging",
            "mass spectrometry imaging",
            "tissue imaging",
            "imaging mass spectrometry",
        ],
    },
    "microbiome_exposome": {
        "label": "Microbiome / exposome",
        "topics": [
            "microbiome",
            "gut microbiota",
            "exposome",
            "human microbiome",
        ],
    },
    "petroleomics": {
        "label": "Petroleomics (NHMFL / Marshall lineage)",
        "topics": [
            "petroleomics",
            "crude oil",
            "petroleum analysis",
            "asphaltene",
            "heavy oil",
        ],
    },
}


def build_queries(comm_def):
    return [
        f'title_and_abstract.search:{instr} AND "{topic}"'
        for instr in INSTRUMENT_VARIANTS
        for topic in comm_def["topics"]
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


summary = {
    "queried": "2026-05-14",
    "method": ("OpenAlex strict title_and_abstract.search, 7 UHR-MS instrument variants "
               "(FT-ICR, FTICR, FT ICR, Fourier transform ion cyclotron, Orbitrap, "
               "ultrahigh resolution mass, ultra-high resolution mass) AND topic phrase. "
               "Deduplicated by OpenAlex work-id."),
    "year_range": "2000-2025",
    "instrument_variants": INSTRUMENT_VARIANTS,
    "communities": {},
}

for slug, comm in COMMUNITIES.items():
    print(f"\n=== {comm['label']} ===")
    queries = build_queries(comm)
    all_works = {}
    for q in queries:
        w = fetch(q)
        new = len(set(w.keys()) - set(all_works.keys()))
        all_works.update(w)
        topic = q.split('AND "')[-1].rstrip('"')
        instr = q.split('search:')[1].split(' AND')[0].strip('"')
        print(f"  {instr:<35s} x {topic:<35s} +{new:5d} (total {len(all_works)})")

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

    csv_path = OUT_LISTS / f"fticr_{slug}_v2.csv"
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["year", "title", "authors_short", "all_authors", "journal", "doi", "openalex_id"])
        w.writeheader()
        for r in sorted(rows, key=lambda x: (x["year"] or 0, x["journal"].lower())):
            w.writerow(r)
    print(f"  -> {len(rows)} unique works saved to {csv_path.name}")

    summary["communities"][slug] = {
        "label": comm["label"],
        "total_unique_works": len(rows),
        "year_2025": year_counter.get(2025, 0),
        "year_totals": {str(y): year_counter[y] for y in sorted(year_counter)},
        "top_10_journals": dict(journal_counter.most_common(10)),
    }

out_json = OUT_RAW / "fticr_communities_summary_v2.json"
with open(out_json, "w", encoding="utf-8") as f:
    json.dump(summary, f, indent=2)

out_csv = OUT_RAW.parent / "fticr_communities_summary_v2.csv"
with open(out_csv, "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f)
    w.writerow(["community", "label", "total_papers", "papers_2025",
                "top_journal_1", "top_journal_2", "top_journal_3"])
    for slug, d in summary["communities"].items():
        tj = list(d["top_10_journals"].keys())
        w.writerow([slug, d["label"], d["total_unique_works"], d["year_2025"],
                    tj[0] if len(tj) > 0 else "",
                    tj[1] if len(tj) > 1 else "",
                    tj[2] if len(tj) > 2 else ""])

print("\n=== UHR-MS COMMUNITY COUNTS (FT-ICR + Orbitrap + ultrahigh-res variants, 2000-2025) ===")
print(f"{'Community':<50s} {'Total':>8s} {'2025':>6s}")
for slug, d in summary["communities"].items():
    print(f"{d['label']:<50s} {d['total_unique_works']:>8d} {d['year_2025']:>6d}")
print(f"\nSummary JSON: {out_json}")
print(f"Summary CSV:  {out_csv}")
