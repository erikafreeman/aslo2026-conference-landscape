"""
_data_access.py
===============
One place that knows where the schedule lives and how to read a presenter's
email, so every script here runs identically against either copy of the data.

WHY THIS EXISTS
---------------
The published inventory (data/sessions_all_public.json) carries `email_domain`
("bu.edu", "uleth.ca"): full addresses are scrubbed, because a presenter's
address is personal data and nothing in the analysis needs it. The working copy
carries the full `email` field.

Country resolution only ever looks at the DOMAIN of an address: its country
code, whether it is a generic .edu/.gov, and whether the provider is consumer
mail. So both copies resolve identically, and the published data reproduces
every country number in the paper: 1,444 of 1,458 (99%), USA 480, Canada 428,
Brazil 52.

Reading p.get("email") directly would silently return None on the public copy,
dropping resolution to 73% (USA 336, Canada 367, Brazil 47) and breaking every
country claim WITHOUT raising anything. Silent wrong numbers are this project's
established failure mode, so the accessor below is the only supported way to
read an address.
"""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parent.parent

_CANDIDATES = [
    ROOT / "data" / "sessions_all_public.json",              # published: email_domain only
    ROOT / "sessions_all.json",                              # working copy: full email
    Path(__file__).resolve().parent / "sessions_all.json",
]


def data_path():
    """Return the schedule file, preferring the published inventory."""
    for p in _CANDIDATES:
        if p.exists():
            return p
    raise FileNotFoundError(
        "No schedule found. Expected data/sessions_all_public.json at the repo root; "
        "looked in: " + ", ".join(str(p) for p in _CANDIDATES)
    )


def load_sessions(path=None):
    """The inventory is JSONL: one session object per line."""
    out = []
    with open(path or data_path(), encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    out.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return out


def email_of(p):
    """An address the country resolver can read, from either schema.

    The public copy stores only the domain, so synthesise a syntactically valid
    address around it. The resolver reads nothing but the domain, so this is
    lossless for every rule it applies.
    """
    e = p.get("email")
    if e:
        return e
    d = p.get("email_domain")
    return "x@" + d.lstrip("@") if d else None
