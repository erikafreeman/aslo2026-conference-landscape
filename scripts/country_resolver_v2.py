"""
country_resolver_v2.py
======================
Definitive country resolution for the ASLO-SIL 2026 programme analysis.

WHY A THIRD VERSION
-------------------
v0 (`_conference_landscape.py` COUNTRY_PATS): listed "USA" first with `\\.edu`/`\\.gov`,
   so first-match-wins sent every .edu.au/.edu.cn to the United States (56 rows).
v1 (`country_detect_fixed.py`): resolved the ccTLD first. That killed the .edu bug but
   left a WORSE problem intact: institutions named in Portuguese/Spanish/French whose
   authors use gmail were invisible. Brazil resolved to 17 when the true figure is ~3x
   that. The bias ran in exactly one direction: anglophone institutions (.edu/.ca, English
   names) resolved cleanly; Global South institutions did not. That inflates the very
   under-representation the essay reports.

v2 RULE ORDER (institution truth first, mail provider last):
  1. Institution gazetteer on the affiliation string. An affiliation naming a real
     institution is the strongest evidence of where the presenting author works.
  2. Explicit country/city names in the affiliation.
  3. Email country-code TLD, but ONLY for institutional domains. Consumer mail
     (gmail/yahoo/outlook/hotmail/pm.me/gmx/...) reflects a person's mail provider,
     not their country: `yahoo.fr` on a Université du Québec affiliation is Canadian.
  4. Generic .edu/.gov => USA, LAST, so it can never outrank a named foreign institution.

v2.1 FIX (Oberlin): the Germany pattern was `berlin`, with no word boundary, so
`Oberlin College` (Ohio) matched and resolved to Germany. Its own address,
ylin@oberlin.edu, would have resolved it correctly under rule 4. The lesson is
that rule 1 (institution first), which fixed the Brazil undercount, is also what
let a substring outrank a correct email: a fix can introduce a new error. The
pattern is now `\bberlin\b`, which still matches "TU Berlin", "IGB Berlin" and
"Humboldt-Universitat zu Berlin". USA 480->481, Germany 83->82.

Note that `barcelona` is deliberately left WITHOUT a word boundary: it must keep
matching "BarcelonaTech" (Universitat Politecnica de Catalunya), which is in
Barcelona and carries no other Spanish signal.

Anything still unresolved is reported as unresolved. It is never guessed.
"""
import re

CONSUMER = re.compile(
    r"@(gmail|googlemail|yahoo|ymail|outlook|hotmail|live|msn|aol|icloud|me\.com|mac\.com|"
    r"protonmail|proton\.me|pm\.me|gmx|web\.de|mail\.ru|yandex|qq\.com|163\.com|126\.com|"
    r"foxmail|zoho|fastmail|hushmail|inbox|mailfence|tutanota|posteo)\.", re.I)

# Institution / city / country patterns, checked in this order.
# Longest-specific first within each country; countries ordered so that no pattern of one
# country can shadow a more specific pattern of another (verified by the residual audit).
GAZETTEER = [
    ("Brazil", [r"universidade", r"\bUFMG\b", r"\bUFRN\b", r"\bUFSCar\b", r"\bUFRJ\b", r"\bUSP\b",
                r"\bUNESP\b", r"\bUNICAMP\b", r"\bINPA\b", r"\bUNIVALI\b", r"\bFiocruz\b",
                r"federal (rural )?university of (minas|rio|sao|s[aã]o|santa|paran|bahia|goi[aá]s|cear[aá]|paraiba|para[ií]ba|juiz|pernambuco|espirito|esp[ií]rito)",
                r"national institute for space research", r"centre of nuclear energy in agriculture",
                r"itaipu", r"vila velha", r"col[eé]gio nossa senhora", r"\bbras[ií]l", r"\bbrazil\b"]),
    ("Mexico", [r"aut[oó]noma de m[eé]xico", r"\bUNAM\b", r"aut[oó]noma metropolitana",
                r"\bCINVESTAV\b", r"\bECOSUR\b", r"\bmexico\b", r"\bm[eé]xico\b"]),
    ("Peru", [r"san marcos", r"\bUNMSM\b", r"cayetano heredia", r"\bperu\b", r"\bper[uú]\b"]),
    ("Colombia", [r"universidad del rosario", r"javeriana", r"\bEAFIT\b", r"antioquia",
                  r"\bbogot[aá]\b", r"\bcolombia\b"]),
    ("Chile", [r"universidad de concepci[oó]n", r"universidad austral", r"o'?higgins",
               r"cat[oó]lica de la sant[ií]sima", r"b[ií]o-b[ií]o", r"\bchile\b"]),
    ("Argentina", [r"bariloche", r"comahue", r"\bCONICET\b", r"\bINALI\b", r"\bargentina\b"]),
    ("Uruguay", [r"universidad de la rep[uú]blica", r"\bUDELAR\b", r"\buruguay\b"]),
    ("Ecuador", [r"university of cuenca", r"\becuador\b"]),
    ("Canada", [r"trent university", r"mcgill", r"university of toronto", r"toronto metropolitan",
                r"memorial university", r"university of ottawa", r"western university",
                r"university of lethbridge", r"universit[eé] de montr[eé]al", r"queen'?s university",
                r"university of regina", r"concordia university", r"university of manitoba",
                r"\bUQAC\b", r"\bUQAT\b", r"\bUQAR\b", r"wilfrid laurier", r"laurentian universit",
                r"canadian rivers institute", r"university of new brunswick", r"canadian wildlife",
                r"IISD[\s\-]?experimental lakes", r"experimental lakes area", r"\bINRS\b",
                r"simon fraser", r"datastream", r"york university", r"vancouver island university",
                r"universit[eé] TELUQ", r"centre for earth observation science",
                r"university of victoria", r"university of saskatchewan", r"\bCIOOS\b", r"\bSLGO\b",
                r"ab[eé]nakis", r"dawson college", r"h2o geomatics", r"ocean diagnostics",
                r"university of calgary", r"university of guelph", r"university of waterloo",
                r"dalhousie", r"laval", r"british columbia", r"\bUBC\b",
                r"\bcanada\b", r"\bqu[eé]bec\b", r"\bontario\b"]),
    ("USA", [r"cornell", r"cary institute", r"university of texas", r"university of montana",
             r"miami university", r"bigelow laborator", r"university of georgia", r"rensselaer",
             r"michigan tech", r"science museum of minnesota", r"university of minnesota",
             r"woods hole", r"university of colorado", r"university of vermont",
             r"st\.? croix watershed", r"national ecological observatory", r"\bNEON\b",
             r"dartmouth", r"university of michigan", r"grand valley state",
             r"southern california coastal water", r"auburn university", r"university of wyoming",
             r"southern nevada water", r"rutgers", r"marine biological laboratory",
             r"columbia university", r"penn state", r"smithsonian", r"university of maine",
             r"indiana university", r"nature conservancy", r"florida fish and wildlife",
             r"city university of new york", r"\bMBARI\b", r"smith-root", r"new hampshire",
             r"springs? stewardship", r"\bNCCOS\b", r"\bSUNY\b", r"oregon state",
             r"center for limnology", r"university of alabama", r"louisiana state",
             r"university of south alabama", r"california state university", r"\bCUAHSI\b",
             r"battelle", r"tetra tech", r"oakland university", r"university of california",
             r"university of north carolina", r"swampscott", r"\bNASA\b", r"university of kansas",
             r"university of nevada", r"rochester institute", r"illinois natural history",
             r"university of illinois", r"harvard", r"international institute of tropical forestry",
             r"gloucester marine", r"chemical currencies", r"C-CoMP", r"vermont department", r"7 lakes alliance",
             r"northwest indian fisheries", r"university of wisconsin", r"university of connecticut",
             r"\bUSGS\b", r"\bNOAA\b", r"\bEPA\b", r"virginia tech", r"\bUSA\b",
             r"\bUnited States\b", r", US\b"]),
    ("Ghana", [r"university of cape coast", r"ghana ocean", r"methodist university college",
               r"\bghana\b"]),
    ("Kenya", [r"university of eldoret", r"\bkenya\b"]),
    ("Nigeria", [r"ajayi crowther", r"nigerian?\b", r"\blagos\b"]),
    ("South Africa", [r"southern ocean carbon climate observatory", r"\bSOCCO\b", r"south africa"]),
    ("Turkey", [r"middle east technical university", r"\bMETU\b", r"\bt[uü]rkiye\b", r"\bturkey\b"]),
    ("Israel", [r"weizmann", r"\bIOLR\b", r"\bisrael\b"]),
    ("Singapore", [r"national university of singapore", r"\bsingapore\b"]),
    ("Taiwan", [r"national taiwan", r"academia sinica", r"national pingtung", r"\btaiwan\b"]),
    ("Korea", [r"chungnam national", r"pukyong national", r"chonnam national", r"\bkorea\b"]),
    ("Japan", [r"kyoto university", r"toho university", r"tohoku university", r"hokkaido",
               r"nagoya", r"kyushu university", r"biwako", r"\btokyo\b", r"\bjapan\b"]),
    ("China", [r"jinan university", r"chinese academy", r"\bNIGLAS\b", r"yunnan university",
               r"nanjing", r"tsinghua", r"peking", r"wuhan", r"\bbeijing\b", r"\bchina\b"]),
    ("India", [r"university of delhi", r"indian institute", r"\bIIT\b",
               r"central marine fisheries research", r"gujarat institute", r"\bindia\b"]),
    ("Iceland", [r"holar university", r"\biceland\b"]),
    ("Ireland", [r"trinity college dublin", r"\bireland\b"]),
    ("UK", [r"university of bristol", r"nottingham", r"\bUK\b", r"united kingdom", r"england",
            r"scotland", r"wales"]),
    ("Hungary", [r"nyiregyhaz", r"ny[ií]regyh[aá]z", r"HUN-REN", r"\bhungary\b"]),
    ("Estonia", [r"estonian university", r"\bestonia\b"]),
    ("Serbia", [r"university of belgrade", r"\bserbia\b"]),
    ("Denmark", [r"aarhus", r"university of copenhagen", r"copenhagen university", r"\bdenmark\b"]),
    ("Netherlands", [r"radboud", r"b-ware", r"IHE delft", r"cytobuoy", r"wageningen",
                     r"\bNIOZ\b", r"netherlands"]),
    ("Spain", [r"university of vic", r"\bICREA\b", r"\bCREAF\b", r"IMDEA", r"\bCSIC\b",
               r"\bspain\b", r"barcelona", r"madrid"]),
    ("France", [r"savoie mont blanc", r"institute of evolutionary science of montpellier",
                r"western brittany", r"centre alpin", r"\bGEOPS\b", r"\bCNRS\b", r"\bINRAE\b",
                r"\bIRD\b", r"\bIFREMER\b", r"paris-saclay", r"agroparistech",
                r"universit[eé] de |universit[eé] savoie", r"\bfrance\b"]),
    ("Germany", [r"leibn[ia]tz", r"leibniz", r"german environment agency",
                 r"german federal institute of hydrology", r"university of cologne",
                 r"brandenburg university", r"duisburg-essen", r"university of konstanz",
                 r"\bIGB\b", r"helmholtz", r"\bUFZ\b", r"freiberg", r"university bremen",
                 r"\bgermany\b", r"\bberlin\b"]),
    ("Austria", [r"\bBOKU\b", r"university of natural resources and life sciences",
                 r"natural resources and life sciences", r"\baustria\b", r"vienna"]),
    ("Switzerland", [r"university of geneva", r"swiss federal institute", r"\bEawag\b",
                     r"\bETH\b", r"\bEPFL\b", r"switzerland"]),
    ("Australia", [r"southern cross university", r"southern queensland", r"\baustralia\b"]),
    ("Belgium", [r"\bbelgium\b", r"ghent"]),
    ("Portugal", [r"\bportugal\b", r"lisbon"]),
    ("Italy", [r"\bitaly\b", r"\bitalia\b"]),
    ("Sweden", [r"\bsweden\b", r"uppsala", r"stockholm"]),
    ("Norway", [r"\bnorway\b"]),
    ("Finland", [r"\bfinland\b", r"helsinki"]),
    ("Poland", [r"\bpoland\b"]),
    ("Czech", [r"\bczech\b"]),
    ("Russia", [r"\brussia\b", r"moscow"]),
    ("New Zealand", [r"new zealand"]),
    ("Indonesia", [r"\bindonesia\b", r"jakarta", r"bandung"]),
    ("Myanmar", [r"\bmyanmar\b", r"yangon"]),
    ("UAE", [r"abu dhabi"]),
]
GAZ = [(c, [re.compile(p, re.I) for p in pats]) for c, pats in GAZETTEER]

CCTLD = {
    "au": "Australia", "ca": "Canada", "cn": "China", "uk": "UK", "de": "Germany",
    "fr": "France", "ch": "Switzerland", "nl": "Netherlands", "es": "Spain", "it": "Italy",
    "br": "Brazil", "jp": "Japan", "se": "Sweden", "no": "Norway", "dk": "Denmark",
    "fi": "Finland", "at": "Austria", "be": "Belgium", "il": "Israel", "za": "South Africa",
    "kr": "Korea", "mx": "Mexico", "ar": "Argentina", "cl": "Chile", "pl": "Poland",
    "tr": "Turkey", "in": "India", "nz": "New Zealand", "pt": "Portugal", "ee": "Estonia",
    "cz": "Czech", "hu": "Hungary", "ru": "Russia", "rs": "Serbia", "sa": "Saudi Arabia",
    "sg": "Singapore", "hk": "Hong Kong", "ph": "Philippines", "ng": "Nigeria",
    "uy": "Uruguay", "tw": "Taiwan", "co": "Colombia", "id": "Indonesia", "pe": "Peru",
    "mm": "Myanmar", "ie": "Ireland", "gr": "Greece", "th": "Thailand", "my": "Malaysia",
    "is": "Iceland", "ke": "Kenya", "gh": "Ghana",
}


def resolve(affiliation, email):
    """Return (country, rule) or (None, 'unresolved'). Never guesses."""
    aff = (affiliation or "").strip()
    em = (email or "").strip().lower()

    # 1 + 2. Institution gazetteer / explicit country or city names.
    for country, pats in GAZ:
        if any(p.search(aff) for p in pats):
            return country, "institution"

    # 3. Email country code, institutional domains only.
    if em and not CONSUMER.search(em):
        m = re.search(r"@[\w\.\-]+\.([a-z]{2})$", em)
        if m and m.group(1) in CCTLD:
            return CCTLD[m.group(1)], "cctld"
        # 4. Generic US domains, last.
        if re.search(r"\.(edu|gov)$", em):
            return "USA", "us-generic-domain"

    return None, "unresolved"
