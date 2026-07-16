"""
country_detect_fixed.py
=======================
Corrected country detection for the ASLO-SIL 2026 programme analysis.

WHY THIS EXISTS
---------------
The original `COUNTRY_PATS` in `_conference_landscape.py` is a dict checked in key
order, and its FIRST key is "USA" with the patterns `\\.edu\\b` and `\\.gov\\b`.
First-match-wins therefore assigned every country-code address under .edu/.gov to
the United States: `.edu.au`, `.edu.cn`, `.edu.br`, `.gov.ar` and so on.
56 presentations were misassigned: an institutional address at `gdou.edu.cn`
("Guangdong Ocean University, China"), for example, was counted as USA.

Two further defects:
  * Colombia, Indonesia, Peru and Myanmar had NO pattern at all, so their count of
    zero meant "undetectable", not "absent". Writing that up as "did not appear in
    the inventory" turned detector silence into evidence of absence.
  * India had only `\\bIndia\\b` / `\\.in\\b`, so "Hindu college, University of Delhi"
    (yahoo.com address) was missed, and India was reported as absent when it is present.

THE FIX
-------
1. Resolve the email's country-code top-level domain FIRST. A 2-letter final label
   is decisive and cannot be shadowed by a generic pattern.
2. Only then fall back to affiliation/name patterns.
3. Add patterns for the previously unrepresented countries.

Import `detect()` from here rather than reimplementing, so the manuscript, the
figures and the verification script all share ONE corrected rule.
"""
import re

# Country-code TLDs observed in the programme's email addresses.
CCTLD = {
    "au": "Australia", "ca": "Canada", "cn": "China", "uk": "UK", "de": "Germany",
    "fr": "France", "ch": "Switzerland", "nl": "Netherlands", "es": "Spain",
    "it": "Italy", "br": "Brazil", "jp": "Japan", "se": "Sweden", "no": "Norway",
    "dk": "Denmark", "fi": "Finland", "at": "Austria", "be": "Belgium", "il": "Israel",
    "za": "South Africa", "kr": "Korea", "mx": "Mexico", "ar": "Argentina",
    "cl": "Chile", "pl": "Poland", "tr": "Turkey", "in": "India", "nz": "New Zealand",
    "pt": "Portugal", "ee": "Estonia", "cz": "Czech", "hu": "Hungary", "ru": "Russia",
    "rs": "Serbia", "sa": "Saudi Arabia", "sg": "Singapore", "hk": "Hong Kong",
    "ph": "Philippines", "ng": "Nigeria", "uy": "Uruguay", "tw": "Taiwan",
    "co": "Colombia", "id": "Indonesia", "pe": "Peru", "mm": "Myanmar",
    "ie": "Ireland", "gr": "Greece", "th": "Thailand", "my": "Malaysia", "is": "Iceland",
}

# Countries absent from the original dict, plus institution names that do not
# contain their country's name. Added so that a zero is interpretable.
EXTRA_PATS = {
    "Colombia":  [r"\bColombia\b", r"\bBogot[aá]\b", r"\bMedell[ií]n\b"],
    "Indonesia": [r"\bIndonesia\b", r"\bJakarta\b", r"\bBandung\b"],
    "Peru":      [r"\bPeru\b", r"\bLima,\s*Peru\b"],
    "Myanmar":   [r"\bMyanmar\b", r"\bYangon\b"],
    "India":     [r"\bIndia\b", r"University of Delhi", r"\bIIT\b", r"\bBangalore\b",
                  r"\bMumbai\b", r"\bChennai\b", r"\bKolkata\b"],
}


def build(base_pats):
    """Merge the pipeline's patterns with EXTRA_PATS and compile."""
    merged = {k: list(v) for k, v in base_pats.items()}
    for k, v in EXTRA_PATS.items():
        merged[k] = sorted(set(merged.get(k, []) + v))
    return {k: [re.compile(p, re.I) for p in v] for k, v in merged.items()}


def detect(affiliation, email, compiled):
    """Return a country or None. ccTLD is decisive and is checked first."""
    e = (email or "").strip().lower()
    m = re.search(r"@[\w\.\-]+\.([a-z]{2})$", e)
    if m and m.group(1) in CCTLD:
        return CCTLD[m.group(1)]
    text = (affiliation or "") + " " + e
    for country, pats in compiled.items():
        if any(p.search(text) for p in pats):
            return country
    return None


def load_base_pats(landscape_py_text):
    """Pull COUNTRY_PATS out of _conference_landscape.py textually."""
    m = re.search(r"COUNTRY_PATS = \{\n(.*?)\n\}\nCOUNTRY_PATS = \{k",
                  landscape_py_text, re.S)
    return eval("{" + m.group(1) + "\n}")
