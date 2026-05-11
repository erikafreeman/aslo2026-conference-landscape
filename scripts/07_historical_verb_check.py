"""
Verify (or refute) the claim that older ASLO meetings used more 'descriptive' verbs
(measure / describe / characterise) than the 2026 program does.

Approach:
  1. Download three historical ASLO program books (2003, 2007, 2010).
  2. Extract text. Find session-name lines (heuristic: lines that look like session titles).
  3. Run the same bigram analysis used on the 2026 program.
  4. Report top bigrams + the prevalence of the three target verbs.

This is approximate — PDF text extraction is imperfect, and "session names"
in old programs may include presentation titles or descriptive runs. The
purpose is sanity-checking the historical claim, not perfect bibliometrics.
"""
import json, re, requests
from pathlib import Path
from collections import Counter
from pypdf import PdfReader

OUT_DIR = Path(__file__).resolve().parent.parent / "output" / "reports"
OUT_DIR.mkdir(parents=True, exist_ok=True)
CACHE = Path(__file__).resolve().parent.parent / "data" / "historical_pdfs"
CACHE.mkdir(parents=True, exist_ok=True)

# Three historical ASLO Aquatic Sciences Meeting program books
TARGETS = [
    ("ASLO 2003 ASM (Salt Lake City)", "https://www.aslo.org/wp-content/uploads/ASLO-2003-ASM-Program-Book.pdf"),
    ("ASLO 2007 ASM (Santa Fe)", "https://www.aslo.org/wp-content/uploads/ASLO-2007-ASM-Program-Book.pdf"),
    ("ASLO 2010 Summer (Santa Fe)", "https://www.aslo.org/wp-content/uploads/ASLO-2010-Summer-Program-Book.pdf"),
]

STOPWORDS = set("""a an and or but the of in on at for to from with by as is are was were be been being
have has had do does did this that these those it its their there here we you they our your his her them him
he she which what who whom where when why how all also any not no nor through across between during among
into onto under over within without around about than then so such some other many much more most less few
both either neither each every same different new old can may might shall should will would could ought
ASLO SIL session sessions symposium oral poster talk meeting conference workshop sciences science aquatic""".split())

def tokenize(text):
    if not text:
        return []
    text = re.sub(r"[–—]", " ", text)  # en/em-dash to space
    text = re.sub(r"[^a-zA-Z\-]+", " ", text)
    return [w.lower() for w in text.split() if len(w) > 2 and w.lower() not in STOPWORDS]

def fetch_pdf(label, url):
    fname = CACHE / (label.replace(" ", "_").replace("(", "").replace(")", "") + ".pdf")
    if fname.exists():
        print("  cached: {}".format(fname.name))
        return fname
    print("  fetching {} ...".format(url))
    r = requests.get(url, timeout=60)
    if r.status_code != 200:
        print("  [err {}] could not fetch".format(r.status_code))
        return None
    fname.write_bytes(r.content)
    print("  saved {} ({} KB)".format(fname.name, len(r.content) // 1024))
    return fname

def extract_session_titles(pdf_path):
    """Best-effort extraction of session titles from an ASLO program book PDF.

    ASLO program books typically organize content by session, with session
    titles in larger font / leading lines. Without font metadata, we use
    heuristics: a candidate session-title line is short-ish (3-15 words),
    starts with a capital, doesn't end in a period (titles usually don't),
    and contains content words.
    """
    reader = PdfReader(str(pdf_path))
    title_candidates = []
    for page in reader.pages:
        try:
            text = page.extract_text() or ""
        except Exception:
            continue
        for line in text.split("\n"):
            s = line.strip()
            if not s or len(s) < 12 or len(s) > 200:
                continue
            words = s.split()
            n_words = len(words)
            if not (3 <= n_words <= 18):
                continue
            # Heuristics for "looks like a session/topic title":
            #   - First char is uppercase letter
            #   - Doesn't end in a period or comma (titles usually don't)
            #   - Doesn't contain typical body-text markers
            #   - Not mostly digits
            if not s[0].isalpha() or not s[0].isupper():
                continue
            if s.endswith(".") or s.endswith(","):
                continue
            if re.search(r"\b(pp\.|fig\.|p\.\s*\d+|table\s+\d+|page\s+\d+)\b", s, re.I):
                continue
            if sum(c.isdigit() for c in s) > n_words:
                continue
            # Title-like: at least half the words capitalised OR contains common title words
            cap_ratio = sum(1 for w in words if w[:1].isupper()) / max(n_words, 1)
            if cap_ratio < 0.4:
                continue
            title_candidates.append(s)
    # Deduplicate while preserving order
    seen = set()
    out = []
    for t in title_candidates:
        key = t.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(t)
    return out

def analyse(titles):
    word_freq = Counter()
    bigram_freq = Counter()
    for t in titles:
        toks = tokenize(t)
        for w in toks:
            word_freq[w] += 1
        for i in range(len(toks) - 1):
            bigram_freq[" ".join(toks[i:i+2])] += 1
    return word_freq, bigram_freq

# Target verbs the historical claim asserts
HIST_VERBS = ["measure", "measuring", "measurement", "measurements",
              "describe", "description", "descriptive", "describing",
              "characterise", "characterize", "characterisation", "characterization", "characterising", "characterizing"]
SYNTHESIS_VERBS = ["bridge", "bridging", "integrate", "integration", "integrating",
                   "converge", "convergence", "synthesis", "synthesize", "synthesise",
                   "scale", "scaling", "couple", "coupling", "link", "linking"]

results = {}
for label, url in TARGETS:
    print("\n=== {} ===".format(label))
    pdf = fetch_pdf(label, url)
    if pdf is None:
        continue
    titles = extract_session_titles(pdf)
    print("  Candidate titles found: {}".format(len(titles)))
    if not titles:
        continue
    print("  Sample (first 10):")
    for t in titles[:10]:
        print("    - " + t[:90])
    wf, bf = analyse(titles)
    descriptive_count = sum(wf.get(v, 0) for v in HIST_VERBS)
    synthesis_count = sum(wf.get(v, 0) for v in SYNTHESIS_VERBS)
    print("\n  Top 20 single words (after stopwords):")
    for w, n in wf.most_common(20):
        print("    {:<22s} {:>3d}".format(w, n))
    print("\n  Top 15 bigrams:")
    for bg, n in bf.most_common(15):
        print("    {:<35s} {:>3d}".format(bg, n))
    print("\n  HISTORICAL-VERB FAMILY count: {} (measure/describe/characterise variants)".format(descriptive_count))
    print("  SYNTHESIS-VERB FAMILY count:  {} (bridge/integrate/converge/scale variants)".format(synthesis_count))
    results[label] = {
        "n_titles": len(titles),
        "sample_titles": titles[:20],
        "top_20_words": dict(wf.most_common(20)),
        "top_15_bigrams": dict(bf.most_common(15)),
        "descriptive_verbs_count": descriptive_count,
        "synthesis_verbs_count": synthesis_count,
        "descriptive_verbs_seen": {v: wf.get(v, 0) for v in HIST_VERBS if wf.get(v, 0) > 0},
        "synthesis_verbs_seen": {v: wf.get(v, 0) for v in SYNTHESIS_VERBS if wf.get(v, 0) > 0},
    }

with open(OUT_DIR / "historical_verb_check.json", "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)
print("\n\nSaved: {}".format(OUT_DIR / "historical_verb_check.json"))
