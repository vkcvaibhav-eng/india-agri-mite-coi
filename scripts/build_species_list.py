#!/usr/bin/env python3
"""Stage 1 output: the species of the six groups of Paper 1 recorded from India.

Reads the checklists in data/checklist/ and writes there:
  species_list.csv          one row per species
  species_list_names.csv    every name that points to a row (spellings and
                            combinations used by the sources, synonyms and older
                            combinations they cite), for Stage 3 name matching
  species_list_review.csv   every join that is not an exact name match, and every
                            join the rules refused
  species_list_summary.csv  counts per group and per source

Names are joined within each group in four passes:
  1 exact binomial (subgenus dropped, name_corrections.csv applied first); two
    records with the same binomial but clearly different authors and years are
    kept apart as homonyms
  2 spelling: same genus and near-identical epithet, or same epithet and
    near-identical genus
  3 a synonym or older combination cited by a source (the taxonomic citations of
    Gupta & Mondal 2023, the synonym lines of Chalil et al. 2024, the original
    combination printed in Gupta 1985), or an old subgenus that is now a genus
    (Amblyseius (Euseius) ovalis = Euseius ovalis)
  4 recombination: same epithet stem, same first author and same year, other genus,
    and no third candidate
Passes 2-4 never join two names that one carefully compiled source lists as two
species. The one exception is a synonym cited by a source newer than the one that
lists both (pass 3); such rows carry the flag synonymised_by_newer_source.

Status: confirmed (in at least one list or paper published after 1985),
historical_only (only in Gupta 1985), unverified (name seen only in pasted
answers). Only confirmed rows have counted = 1.
"""
import csv
import difflib
import os
import re
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from names import display, first_author, key, parse, parse_cited, stem
from states import clean_states

D = "data/checklist/"
GROUPS = ["Tetranychidae", "Tenuipalpidae", "Eriophyoidea", "Tarsonemidae", "Tuckerellidae", "Phytoseiidae"]
PREFIX = {"Tetranychidae": "TET", "Tenuipalpidae": "TEN", "Eriophyoidea": "ERI",
          "Tarsonemidae": "TAR", "Tuckerellidae": "TUC", "Phytoseiidae": "PHY"}
ERIO_FAMILIES = ["Eriophyidae", "Diptilomiopidae", "Phytoptidae"]
OLD_ERIO = {"Rhyncaphytoptidae": "Diptilomiopidae", "Nalepellidae": "Phytoptidae"}
SECTION = {"tetranychidae": "Tetranychidae", "tenuipalpidae": "Tenuipalpidae", "eriophyoidea": "Eriophyoidea",
           "tarsonemidae": "Tarsonemidae", "tuckerellidae": "Tuckerellidae", "phytoseiidae": "Phytoseiidae"}

# key: (year of the source, file, refuses joins of two names it lists separately)
# Som 2025, Karnataka 2025 and the small regional notes print some names twice
# with typos, so they do not refuse joins.
SOURCES = {
    "add2026":    (2026, "additions_2022_2026.csv", False),
    "mandal2026": (2026, "mandal2026_eriophyoidea_west_bengal.csv", True),
    "som2025":    (2025, "som2025_eriophyoidea_south_bengal.csv", False),
    "karn2025":   (2025, "dyamanagouda2025_eriophyoidea_karnataka.csv", False),
    "mitra2025":  (2025, "mitra2025_tenuipalpidae_india.csv", True),
    "chalil2024": (2024, "chalil2024_tetranychidae.csv", True),
    "gm2023":     (2023, "gupta_mondal2023_all.csv", True),
    "tarswb2023": (2023, "tarsonemidae_west_bengal.csv", True),
    "tn2020":     (2020, "dyamanagouda2020_eriophyoidea_tamilnadu.csv", True),
    "mitra2018":  (2018, "mitra2018_tenuipalpidae_west_bengal.csv", False),
    "gb2017":     (2017, "gupta_bose2017_south_bengal.csv", False),
    "gk2015":     (2015, "gupta_karmakar2015_phytoseiidae.csv", True),
    "mesa2009":   (2009, "mesa2009_tenuipalpidae_india_types.csv", True),
    "g1985":      (1985, "gupta1985_species.csv", True),
    "unverified": (2026, "unverified_names.csv", False),
}
NATIONAL = {"gm2023", "chalil2024", "mitra2025", "gk2015", "mesa2009", "g1985"}
OCR = {"gm2023", "g1985"}        # names read by OCR; the rest are typed text
# Dyamanagouda et al. 2020 sometimes print the Tamil Nadu recorder (Mohanasundaram,
# Umapathy) in place of the authority; Som et al. 2025 print stray authorities.
WEAK_AUTHOR = {"som2025"}
WEAK_RECORDER = {"tn2020": ("mohanasundaram", "umapathy")}
NAME_RANK = {
    "Tetranychidae": ["add2026", "chalil2024", "gm2023", "gb2017", "g1985", "unverified"],
    "Tenuipalpidae": ["add2026", "mitra2025", "gm2023", "mesa2009", "mitra2018", "gb2017", "g1985", "unverified"],
    "Eriophyoidea": ["add2026", "mandal2026", "gm2023", "tn2020", "som2025", "karn2025", "gb2017", "g1985", "unverified"],
    "Tarsonemidae": ["add2026", "tarswb2023", "gm2023", "gb2017", "g1985", "unverified"],
    "Tuckerellidae": ["gm2023", "g1985", "unverified"],
    "Phytoseiidae": ["add2026", "gm2023", "gk2015", "gb2017", "g1985", "unverified"],
}
AUTH_RANK = ["add2026", "chalil2024", "mitra2025", "gm2023", "gk2015", "tn2020", "tarswb2023", "mesa2009",
             "mitra2018", "mandal2026", "gb2017", "som2025", "karn2025", "g1985", "unverified"]
FAMILY_RANK = ["add2026", "mandal2026", "gm2023", "tn2020", "g1985"]
PARTICLES = {"de", "van", "von", "der", "la", "le", "du", "da", "del"}


def ratio(a, b):
    return difflib.SequenceMatcher(None, a, b).ratio()


def same_author(x, y, cut):
    if min(len(x), len(y)) == 1:        # an initial, as in "(C. & F.)"
        return x[0] == y[0]
    return ratio(x, y) >= cut or (min(len(x), len(y)) >= 4 and (x in y or y in x))


def skel(s):
    """OCR-tolerant form of a name: letters the 1985 scan confuses are merged."""
    return s.lower().replace("rn", "m").translate(str.maketrans("bcolj1", "heuiii"))


def rows(f):
    with open(D + f, newline="") as fh:
        return list(csv.DictReader(fh))


def group_of(fam):
    fam = (fam or "").strip()
    if fam in ERIO_FAMILIES or fam in OLD_ERIO or fam == "Eriophyoidea":
        return "Eriophyoidea"
    return fam if fam in GROUPS else None


CORR = {}
for r in rows("name_corrections.csv"):
    p = parse(r["name_in_older_list"])
    if p and parse(r["corrected_name"]):
        CORR[key(p[0], p[2])] = r["corrected_name"]

RECS = []


def add(src, group, name, family="", auth="", year="", states="", cited=(), alt=(), ref="", note="", agree=False):
    """One source row. cited: (name, author, year) the source gives as synonyms or
    older combinations of this species."""
    if group not in GROUPS:
        return
    p = parse(name)
    if not p:
        return
    printed = display(*p)
    if key(p[0], p[2]) in CORR:
        p = parse(CORR[key(p[0], p[2])])
    g, sg, e = p
    st, _ = clean_states(states or "")
    # page furniture that the table parsers left in some authorities
    auth = re.split(r"\s*\(?(?:Co)?n?tinued\)|\s+MANDAL ET AL", auth or "")[0]
    if src == "mandal2026":
        auth = re.split(r"\s+(?:1[789]|20)\d\d", auth)[0]
    weak = src in WEAK_AUTHOR or first_author(auth).startswith(WEAK_RECORDER.get(src, ("\0",)))
    rec = dict(id=len(RECS), src=src, group=group, family=OLD_ERIO.get(family.strip(), family.strip()),
               g=g, sg=sg, e=e, name=display(g, sg, e), printed={printed, display(g, sg, e)}, keys={key(g, e)},
               aliases=[], auth=(auth or "").strip(), a1="" if weak else first_author(auth),
               year="" if weak else (year or ""), states=st, ref=ref, note=note, agree=agree)
    for n in alt:
        q = parse(n)
        if q:
            rec["keys"].add(key(q[0], q[2]))
            rec["printed"].add(display(*q))
    for n, a, y in cited:
        q = parse(n) if isinstance(n, str) else n
        if q and key(q[0], q[2]) not in rec["keys"]:
            rec["aliases"].append((key(q[0], q[2]), display(*q), first_author(a), y or "", "cited"))
    if sg and sg != g:
        rec["aliases"].append((key(sg, e), display(sg, "", e), rec["a1"], rec["year"], "subgenus"))
    RECS.append(rec)


def citations_from(text, sep):
    out = []
    for part in (text or "").split(sep):
        name, a, y = parse_cited(part)
        if name:
            out.append((name, a, y))
    return out


def clean_g85_genus(g, known):
    g = re.sub(r"\s+", "", g or "").replace("/", "l").replace(";", "i").replace(".", "")
    if g[:1] == "l":
        g = "I" + g[1:]
    g = g[:1].upper() + g[1:].lower()
    if g in known or not g:
        return g
    hit = [k for k in difflib.get_close_matches(g, known, n=3, cutoff=0.8) if abs(len(k) - len(g)) <= 2]
    return hit[0] if hit else g


def clean_letters(t):
    return re.sub(r"[^A-Za-z-]", "", t.replace(";", "i").replace("/", "l").replace("~", "s"))


def epithet_after_genus(letters, genus):
    """The letters after the genus in a run of OCR letters; the genus may have
    gained or lost up to two letters."""
    n = len(genus)
    cuts = range(max(1, n - 2), min(len(letters), n + 2) + 1)
    if not cuts:
        return ""
    cut = max(cuts, key=lambda c: (ratio(letters[:c].lower(), genus.lower()), -abs(c - n)))
    ep = letters[cut:]
    if ep[:1] == "I":          # OCR prints a capital I for l
        ep = "l" + ep[1:]
    return ep.lower().replace("-", "")


def g85_heading(heading, genus):
    """(epithet, authority) from a Gupta 1985 heading such as
    '9.  Petrobia (Tetraoychioa) harti (Ewing)'. The letters of the genus are
    skipped, so a genus or epithet broken by OCR ('M onoceronychus',
    'cheri ani') is read whole. The token after the genus always belongs to the
    name, even when OCR capitalised it ('Aceria Iitchii (Keifer)')."""
    h = re.sub(r"['’‘`´,]", " ", re.sub(r"^\s*\d+\s*[^A-Za-z(]*", "", heading or ""))
    toks = h.split()
    if len(toks) > 1 and toks[1].startswith("("):
        j = 1
        while j < len(toks) and ")" not in toks[j]:
            j += 1
        toks = toks[:1] + toks[j + 1:]
    k = 2
    while k < len(toks):
        t, c = toks[k], clean_letters(toks[k]).lower()
        if not c or t[:1].isupper() or t.startswith("(") or c in PARTICLES or c in AUTHORS:
            break
        k += 1
    raw = "".join(toks[1:k])
    ep = epithet_after_genus(clean_letters("".join(toks[:k])), genus)
    ok = re.fullmatch(r"[a-z]{3,}", ep)
    return (ep if ok else ""), " ".join(toks[k:]), bool(ok) and not re.search(r"[^a-z]", raw[1:])


def g85_contents_epithet(name_ocr, genus):
    s = re.sub(r"\([^)]*\)?", " ", name_ocr or "")
    s = re.split(r"[^A-Za-z\s()/;~.\-]", s)[0]
    ep = epithet_after_genus(clean_letters(s), genus)
    tail = s.split(None, 1)[1] if len(s.split(None, 1)) > 1 else ""
    ok = re.fullmatch(r"[a-z]{3,}", ep)
    return (ep if ok else ""), bool(ok) and not re.search(r"[^a-z\s]", tail[1:])


AUTHORS = set()


def load():
    for r in rows(SOURCES["add2026"][1]):
        note = "first record for India" if "first record from india" in r["notes"].lower() else ""
        add("add2026", group_of(r["family"]), r["species"], family=r["family"], auth=r["authority"],
            year=r["year"], states=r["india_states"], ref=r["source"], note=note)
    for r in rows(SOURCES["unverified"][1]):
        add("unverified", group_of(r["family"]), r["species"], family=r["family"], auth=r["authority"],
            year=r["year"], states=r["india_states"], ref=r["claimed_source"])
    for r in rows(SOURCES["mandal2026"][1]):
        add("mandal2026", "Eriophyoidea", r["species"], family=r["family"], auth=r["authority"],
            year=r["year"], states="West Bengal")
    for r in rows(SOURCES["som2025"][1]):
        add("som2025", "Eriophyoidea", r["species"], auth=r["authority_fragment"], states=r["india_states"],
            ref="row " + r["number"])
    for r in rows(SOURCES["karn2025"][1]):
        add("karn2025", "Eriophyoidea", r["species"], states=r["india_states"],
            note="new record for India" if r["new_record_india"] == "1" else "")
    for r in rows(SOURCES["mitra2025"][1]):
        add("mitra2025", "Tenuipalpidae", r["species"], auth=r["authority"], year=r["year"],
            states=r["india_states"])
    for r in rows(SOURCES["chalil2024"][1]):
        add("chalil2024", "Tetranychidae", r["species"], auth=r["authority"], year=r["year"],
            states=r["india_states"], cited=citations_from(r["synonyms_raw"].replace(";", "|"), "|"))
    for r in rows(SOURCES["gm2023"][1]):
        grp = SECTION.get(r["section"])
        if grp and r["level"] == "named_species_account":
            cited = []
            for item in r["citation_names"].split(";"):
                n, _, rest = item.partition("|")
                a, _, y = rest.partition("|")
                if n:
                    cited.append((n, a, y))
            add("gm2023", grp, r["species"], family=r["family"], auth=r["authority"], year=r["year"],
                states=r["india_states"], cited=cited, ref="book no. " + r["number"])
    for r in rows(SOURCES["tarswb2023"][1]):
        add("tarswb2023", "Tarsonemidae", r["species"], auth=r["authority"], year=r["year"],
            states=r["india_states"])
    for r in rows(SOURCES["tn2020"][1]):
        add("tn2020", "Eriophyoidea", r["species"], family=r["family"], auth=r["authority"], year=r["year"],
            states=r["india_states"])
    for r in rows(SOURCES["mitra2018"][1]):
        add("mitra2018", "Tenuipalpidae", r["species"], auth=r["authority"], year=r["year"],
            states=r["india_states"], note="new record for India" if r["new_record_india"] == "1" else "")
    for r in rows(SOURCES["gb2017"][1]):
        if r["in_scope_family"] == "1" and r["unnamed_sp"] != "1":
            add("gb2017", group_of(r["family"]), r["species"], family=r["family"], auth=r["authority"],
                states=r["india_states"])
    for r in rows(SOURCES["gk2015"][1]):
        add("gk2015", "Phytoseiidae", r["species"], auth=r["authority"], year=r["year"])
    for r in rows(SOURCES["mesa2009"][1]):
        add("mesa2009", "Tenuipalpidae", r["species"], auth=r["authority"], year=r["year"],
            states=r["india_states"])
    known = sorted({r["g"] for r in RECS} | {"Phytoptus"})
    AUTHORS.update(r["a1"] for r in RECS if len(r["a1"]) >= 5)
    for r in rows(SOURCES["g1985"][1]):
        grp = group_of(r["family"])
        if not grp:
            continue
        genus = clean_g85_genus(r["genus"], known)
        sg = re.sub(r"\s+", "", r["subgenus"] or "").replace("/", "l").replace(";", "i").replace("~", "s")
        sg = sg[:1].upper() + sg[1:].lower() if re.fullmatch(r"[A-Za-z]{4,}", sg) else ""
        e_head, auth, head_clean = g85_heading(r["heading_ocr"], genus)
        e_cont, cont_clean = g85_contents_epithet(r["name_ocr"], genus)
        # the reading without stray capitals or symbols is preferred
        ep = e_cont if (e_cont and cont_clean and not head_clean) else (e_head or e_cont)
        if not ep:
            continue
        other = e_head if ep == e_cont else e_cont
        alt = [f"{genus} {other}"] if other and other != ep and ratio(other, ep) >= 0.7 else []
        orig = parse_cited(r["original_combination_ocr"])
        year = orig[2] if orig[0] and orig[2] and ratio(stem(orig[0][2]), stem(ep)) >= 0.75 else ""
        add("g1985", grp, display(genus, sg, ep), family=r["family"], auth=auth, year=year,
            states=r["india_states"], alt=alt, cited=[orig] if orig[0] else [], ref="no. " + r["number"],
            agree=bool(e_head and e_head == e_cont))


load()

# ---- joining -------------------------------------------------------------------------------
parent = list(range(len(RECS)))
CL = {i: ({RECS[i]["src"]} if SOURCES[RECS[i]["src"]][2] else set()) for i in range(len(RECS))}
CFLAGS = defaultdict(set)
BASIS = defaultdict(set)
WAIVED = defaultdict(set)   # sources whose separate listing a newer synonymy has overruled
REVIEW = []


def find(i):
    while parent[i] != i:
        parent[i] = parent[parent[i]]
        i = parent[i]
    return i


def union(a, b, basis=None):
    a, b = find(a), find(b)
    if a == b:
        return a
    parent[b] = a
    CL[a] |= CL.pop(b)
    CFLAGS[a] |= CFLAGS.pop(b, set())
    BASIS[a] |= BASIS.pop(b, set())
    WAIVED[a] |= WAIVED.pop(b, set())
    if basis:
        BASIS[a].add(basis)
    return a


def members():
    out = defaultdict(list)
    for i in range(len(RECS)):
        out[find(i)].append(i)
    return out


def ids_of(root):
    return [i for i in range(len(RECS)) if find(i) == root]


def label(root):
    ids = ids_of(root)
    return " / ".join(sorted({RECS[i]["name"] for i in ids})), ";".join(sorted({RECS[i]["src"] for i in ids}))


def log(action, basis, score, a, b, evidence, blockers=(), ka="", kb=""):
    na, sa = label(find(a))
    nb, sb = label(find(b))
    REVIEW.append(dict(action=action, basis=basis, score=f"{score:.2f}" if score else "", group=RECS[a]["group"],
                       name_a=na, sources_a=sa, name_b=nb, sources_b=sb, evidence=evidence,
                       _a=a, _b=b, _blockers=tuple(blockers), _ka=ka, _kb=kb))


def authors(ids):
    return {RECS[i]["a1"] for i in ids if len(RECS[i]["a1"]) >= 3}


def years(ids):
    return {int(RECS[i]["year"]) for i in ids if RECS[i]["year"]}


# pass 1: exact, homonyms kept apart
by_key = defaultdict(list)
for r in RECS:
    for k in r["keys"]:
        by_key[(r["group"], k)].append(r["id"])


CITED_AUTH = defaultdict(list)     # (group, key) -> first authors a source cites for that name
for r in RECS:
    for a, shown, a1, yr, kind in r["aliases"]:
        if kind == "cited" and len(a1) >= 3:
            CITED_AUTH[(r["group"], a)].append(a1)


def clash(r1, r2):
    """Two records with the same binomial that are different species: a 1985 name
    and a much later name by other authors, or a name that a source cites, with
    its author, under another species (Amblyseius meghalayensis Gupta 1978, now
    Scapulaseius, and Amblyseius meghalayensis Kar & Karmakar 2021). Otherwise the
    same binomial in two lists is taken as one species."""
    a, b = r1["a1"], r2["a1"]
    if len(a) >= 3 and len(b) >= 3 and not same_author(a, b, 0.6):
        for k in r1["keys"] & r2["keys"]:
            for c in CITED_AUTH.get((r1["group"], k), ()):
                if same_author(c, a, 0.7) != same_author(c, b, 0.7):
                    return True
    if "g1985" not in (r1["src"], r2["src"]):
        return False
    a, b, y1, y2 = r1["a1"], r2["a1"], r1["year"], r2["year"]
    return (len(a) >= 3 and len(b) >= 3 and not same_author(a, b, 0.6)
            and y1 and y2 and abs(int(y1) - int(y2)) > 20)


for (grp, k), kids in by_key.items():
    subs = []
    for i in kids:
        for s in subs:
            if not any(clash(RECS[i], RECS[j]) for j in s):
                s.append(i)
                break
        else:
            subs.append([i])
    for s in subs:
        for j in s[1:]:
            union(s[0], j)
    for s in subs[1:]:
        a, b = RECS[subs[0][0]], RECS[s[0]]
        log("kept apart", "homonym", 0, a["id"], b["id"],
            f"{a['name']} {a['auth']} {a['year']} ({a['src']}) vs {b['name']} {b['auth']} {b['year']} ({b['src']})")
KEYIDX = defaultdict(set)
for r in RECS:
    for k in r["keys"]:
        KEYIDX[(r["group"], k)].add(r["id"])
        if r["src"] == "g1985":
            KEYIDX[(r["group"], "~" + skel(k))].add(r["id"])


# pass 2: spelling
def spelling(k1, k2):
    """Similarity of two binomials as spellings of one name; below 0.85 (same genus,
    epithets at least 0.8 alike) the join needs the same author and the same year."""
    g1, e1 = k1.split(" ", 1)
    g2, e2 = k2.split(" ", 1)
    if min(len(e1), len(e2)) < 4:
        return 0
    if g1 == g2:
        if stem(e1) == stem(e2):
            return 0.99
        if difflib.SequenceMatcher(None, e1, e2).quick_ratio() < 0.8:
            return 0
        r = ratio(e1, e2)
        return r if r >= 0.8 else 0
    if e1 == e2 or stem(e1) == stem(e2):
        r = ratio(g1, g2)
        return 0.9 + r / 20 if r >= 0.8 else 0
    if difflib.SequenceMatcher(None, k1, k2).quick_ratio() < 0.92:
        return 0
    r = ratio(k1, k2)
    return r if r >= 0.92 else 0


G85KEYS = {k for r in RECS if r["src"] == "g1985" for k in r["keys"]}


def spelling_pass(waivers):
  mem = members()
  for grp in GROUPS:
      roots = sorted(r for r, m in mem.items() if RECS[m[0]]["group"] == grp)
      keys = {r: sorted({k for i in mem[r] for k in RECS[i]["keys"]}) for r in roots}
      cands = []
      for x in range(len(roots)):
          for y in range(x + 1, len(roots)):
              best, pair = 0, None
              for ka in keys[roots[x]]:
                  for kb in keys[roots[y]]:
                      s = spelling(ka, kb)
                      if (ka in G85KEYS or kb in G85KEYS) and skel(ka.split()[0]) == skel(kb.split()[0]):
                          s = max(s, spelling(ka.split()[0] + " " + skel(ka.split()[1]),
                                              ka.split()[0] + " " + skel(kb.split()[1])))
                      if s > best:
                          best, pair = s, (ka, kb)
              if best:
                  cands.append((best, roots[x], roots[y], pair))
      cands.sort(key=lambda c: -c[0])
      for s, x, y, pair in cands:
          A, B = find(x), find(y)
          if A == B:
              continue
          ia, ib = ids_of(A), ids_of(B)
          ev = f"{pair[0]} ~ {pair[1]}"
          shared = CL[A] & CL[B]
          waived = shared and waivers and shared <= (WAIVED[A] | WAIVED[B])
          if shared and not waived:
              if not waivers:
                  log("refused", "spelling", s, A, B, ev + f"; {', '.join(sorted(shared))} list both",
                      shared, *pair)
              continue
          aa, ab = authors(ia), authors(ib)
          auth_same = bool(aa and ab) and any(same_author(p, q, 0.75) for p in aa for q in ab)
          if aa and ab and not auth_same:
              log("refused", "spelling", s, A, B,
                  ev + f"; authors differ ({'/'.join(sorted(aa))} vs {'/'.join(sorted(ab))})", ("authors",), *pair)
              continue
          ya, yb = years(ia), years(ib)
          if s < 0.85 and not (auth_same and ya & yb):
              continue
          year_clash = bool(ya and yb) and not any(abs(p - q) <= 2 for p in ya for q in yb)
          if year_clash and not auth_same:
              log("refused", "spelling", s, A, B,
                  ev + f"; years differ ({'/'.join(map(str, sorted(ya)))} vs {'/'.join(map(str, sorted(yb)))})",
                  ("years",), *pair)
              continue
          log("joined", "spelling", s, A, B, ev + ("; same author, years differ" if year_clash else "")
              + (f"; {', '.join(sorted(shared))} list both, overruled by a newer synonymy" if waived else ""))
          root = union(A, B, "spelling")
          if year_clash:
              CFLAGS[root].add("year_differs_between_sources")
          if waived:
              CFLAGS[root].add("synonymised_by_newer_source")


spelling_pass(False)


# pass 3: synonyms and older combinations cited by a source; old subgenus = genus
for r in sorted(RECS, key=lambda r: (-SOURCES[r["src"]][0], r["id"])):
    for a, shown, a1, yr, kind in r["aliases"]:
        A = find(r["id"])
        cand = []
        for t in sorted(KEYIDX.get((r["group"], a), set()) | KEYIDX.get((r["group"], "~" + skel(a)), set())):
            if find(t) == A:
                continue
            T = RECS[t]
            if a1 and T["a1"] and not same_author(a1, T["a1"], 0.7):
                continue
            if yr and T["year"] and abs(int(yr) - int(T["year"])) > 2:
                continue
            cand.append(t)
        targets = {find(t) for t in cand}
        if not targets:
            continue
        if kind == "cited":
            what, basis = f"{r['src']} cites {shown} under {r['name']}", f"cited name ({r['src']})"
        else:
            what, basis = f"{r['name']} ({r['src']}): subgenus {shown.split()[0]} is now a genus", "old subgenus"
        if len(targets) > 1:
            log("refused", basis, 0, r["id"], cand[0], what + "; matches more than one row")
            continue
        B = targets.pop()
        tyears = years(ids_of(B))
        if kind == "cited" and tyears and min(tyears) >= SOURCES[r["src"]][0]:
            log("refused", basis, 0, r["id"], B, what + f"; {shown} dates from {min(tyears)}, not before this source")
            continue
        shared = CL[A] & CL[B]
        older = {x for x in CL[A] | CL[B] if SOURCES[x][0] < SOURCES[r["src"]][0]} if kind == "cited" and r["src"] != "g1985" else set()
        if not shared or shared <= (WAIVED[A] | WAIVED[B]):
            log("joined", basis, 0, r["id"], B, what + (f"; {', '.join(sorted(shared))} list both, overruled by a newer synonymy" if shared else ""))
            root = union(A, B, "cited name" if kind == "cited" else "old subgenus")
            WAIVED[root] |= older
            if shared:
                CFLAGS[root].add("synonymised_by_newer_source")
        elif kind == "cited" and r["src"] != "g1985" and all(SOURCES[r["src"]][0] > SOURCES[s][0] for s in shared):
            log("joined", f"synonym in newer source ({r['src']})", 0, r["id"], B,
                what + f"; {', '.join(sorted(shared))} list both")
            root = union(A, B, "cited name")
            CFLAGS[root].add(f"synonymised_by_newer_source:{r['src']}")
            WAIVED[root] |= older
        else:
            log("refused", basis, 0, r["id"], B, what + f"; {', '.join(sorted(shared))} list both as species",
                shared, a, a)

# pass 3b: spelling again, now that newer synonymies may overrule an older double listing
spelling_pass(True)

# pass 4: recombination (other genus, same epithet stem, same first author and year)
mem = members()
for grp in GROUPS:
    bucket = defaultdict(set)
    for root, m in mem.items():
        if RECS[m[0]]["group"] == grp:
            for i in m:
                for k in RECS[i]["keys"]:
                    bucket[stem(k.split()[1])].add(root)
                    if RECS[i]["src"] == "g1985":
                        bucket[stem(skel(k.split()[1]))].add(root)
    # near-identical epithets (a typo in one list) also make a candidate pair
    eps = defaultdict(set)
    for root, m in mem.items():
        if RECS[m[0]]["group"] == grp:
            for i in m:
                for k in RECS[i]["keys"]:
                    eps[k.split()[1]].add(root)
    elist = sorted(eps)
    for x in range(len(elist)):
        for y in range(x + 1, len(elist)):
            e1, e2 = elist[x], elist[y]
            if min(len(e1), len(e2)) >= 6 and difflib.SequenceMatcher(None, e1, e2).quick_ratio() >= 0.9 \
                    and ratio(e1, e2) >= 0.9 and stem(e1) != stem(e2):
                bucket[("~", e1, e2)] |= eps[e1] | eps[e2]
    pairs, seen_pairs = [], set()
    for st, roots in bucket.items():
        roots = sorted(roots)
        for x in range(len(roots)):
            for y in range(x + 1, len(roots)):
                if (roots[x], roots[y]) in seen_pairs:
                    continue
                seen_pairs.add((roots[x], roots[y]))
                ia, ib = mem[roots[x]], mem[roots[y]]
                ga = {k.split()[0] for i in ia for k in RECS[i]["keys"]}
                gb = {k.split()[0] for i in ib for k in RECS[i]["keys"]}
                if any(ratio(p, q) >= 0.8 for p in ga for q in gb):
                    continue
                need_year = bool(years(ia) and years(ib))
                hit = [(RECS[i], RECS[j]) for i in ia for j in ib
                       if RECS[i]["a1"] and RECS[j]["a1"] and same_author(RECS[i]["a1"], RECS[j]["a1"], 0.8)
                       and (not need_year or (RECS[i]["year"] and RECS[i]["year"] == RECS[j]["year"]))]
                if hit:
                    pairs.append((roots[x], roots[y], hit[0]))
    viable = []
    for x, y, (p, q) in pairs:
        ev = f"{p['name']} {p['auth']} {p['year']} = {q['name']} {q['auth']} {q['year']}"
        if CL[x] & CL[y]:
            log("refused", "recombination", 0, x, y, ev + f"; {', '.join(sorted(CL[x] & CL[y]))} list both",
                CL[x] & CL[y], key(p["g"], p["e"]), key(q["g"], q["e"]))
        else:
            viable.append((x, y, ev))
    partners = Counter()
    for x, y, _ in viable:
        partners[x] += 1
        partners[y] += 1
    for x, y, ev in viable:
        A, B = find(x), find(y)
        if A == B:
            continue
        if partners[x] > 1 or partners[y] > 1:
            log("refused", "recombination", 0, A, B, ev + "; more than one candidate")
            continue
        if CL[A] & CL[B]:
            log("refused", "recombination", 0, A, B, ev + f"; {', '.join(sorted(CL[A] & CL[B]))} list both", CL[A] & CL[B])
            continue
        log("joined", "recombination", 0, A, B, ev)
        union(A, B, "recombination")

# ---- one row per species -------------------------------------------------------------------
mem = members()
genus_family = defaultdict(Counter)
for r in RECS:
    if r["group"] == "Eriophyoidea" and r["family"] in ERIO_FAMILIES and r["src"] in ("mandal2026", "gm2023", "tn2020", "add2026"):
        genus_family[r["g"]][r["family"]] += 1


def weight(r):
    """Vote of one source for the spelling of the epithet."""
    if r["src"] == "unverified":
        return 0.1
    if r["src"] in OCR:
        return 1.5 if r["agree"] else 1.0
    return 1.2


out, names_out = [], []
taken = {(RECS[m[0]]["group"], k) for m in mem.values() for i in m for k in RECS[i]["keys"]}
for root, m in mem.items():
    recs = [RECS[i] for i in m]
    grp = recs[0]["group"]
    rank = NAME_RANK[grp]
    recs.sort(key=lambda r: (rank.index(r["src"]) if r["src"] in rank else 99, r["id"]))
    best = recs[0]
    votes = defaultdict(float)
    for r in recs:
        if r["g"].lower() == best["g"].lower():
            votes[r["e"]] += weight(r)
    ep = max(votes, key=lambda e: (votes[e], e == best["e"]))
    flags = set(CFLAGS.get(root, set()))
    if len(votes) > 1:
        flags.add("spelling_varies")
    valid = display(best["g"], best["sg"], ep)
    vkey = key(best["g"], ep)
    same = [r for r in recs if vkey in r["keys"]]
    by_auth = sorted(same, key=lambda r: AUTH_RANK.index(r["src"])) + sorted(recs, key=lambda r: AUTH_RANK.index(r["src"]))
    auth = next((r["auth"] for r in by_auth if r["auth"] and r["src"] not in WEAK_AUTHOR | set(WEAK_RECORDER)), "") or \
        next((r["auth"] for r in by_auth if r["auth"]), "")
    yvotes = Counter(r["year"] for r in recs if r["year"])
    year = max(yvotes, key=lambda y: (yvotes[y], -next(i for i, r in enumerate(by_auth) if r["year"] == y))) if yvotes else ""
    srcs = [s for s in SOURCES if any(r["src"] == s for r in recs)]
    family = grp
    if grp == "Eriophyoidea":
        fams = {(r["family"], r["src"]) for r in recs if r["family"] in ERIO_FAMILIES and r["src"] in FAMILY_RANK[:-1]}
        if len({f for f, _ in fams}) > 1:
            flags.add("family_differs:" + "/".join(sorted(f"{f}({s})" for f, s in fams)))
        fr = sorted((r for r in recs if r["family"] in ERIO_FAMILIES and r["src"] in FAMILY_RANK),
                    key=lambda r: FAMILY_RANK.index(r["src"]))
        if fr:
            family = fr[0]["family"]
        elif genus_family.get(best["g"]):
            family = genus_family[best["g"]].most_common(1)[0][0]
        else:
            family = ""
            flags.add("family_not_assigned")
    if set(srcs) == {"unverified"}:
        status = "unverified"
    elif set(srcs) <= {"g1985", "unverified"}:
        status = "historical_only"
    else:
        status = "confirmed"
    if status == "confirmed":
        if "gm2023" not in srcs:
            flags.add("not_in_gupta_mondal_2023")
        if not (set(srcs) & NATIONAL):
            flags.add("regional_lists_or_papers_only")
    a1s = {r["a1"] for r in same if r["a1"] and r["src"] in ("chalil2024", "mitra2025", "gm2023", "gk2015", "mesa2009", "add2026", "mandal2026")}
    if len(a1s) > 1 and not all(same_author(p, q, 0.7) for p in a1s for q in a1s):
        flags.add("authority_differs:" + "/".join(sorted(a1s)))
    states = sorted({s for r in recs for s in r["states"]})
    variants = defaultdict(set)
    for r in recs:
        for n in r["printed"]:
            if n != valid:
                variants[n].add(r["src"])
    notes = sorted({r["note"] for r in recs if r["note"]})
    auth = auth.strip(" |;,")
    out.append(dict(group=grp, family=family, genus=best["g"], species=valid, authority=auth, year=year,
                    status=status, counted=1 if status == "confirmed" else 0, n_sources=len(srcs),
                    sources=";".join(srcs), india_states=";".join(states), n_states=len(states),
                    other_names_in_sources="; ".join(f"{n} [{','.join(sorted(s))}]" for n, s in sorted(variants.items())),
                    joined_by=";".join(sorted(BASIS.get(root, set()))) or "exact", flags=flags,
                    notes="; ".join(notes), _root=root))
    names_out.append((root, valid, "valid", ";".join(srcs)))
    for n, s in sorted(variants.items()):
        names_out.append((root, n, "listed_as", ";".join(sorted(s))))
    cited = defaultdict(set)
    for r in recs:
        for a, shown, a1, yr, kind in r["aliases"]:
            if kind == "cited" and (grp, a) not in taken and shown != valid and shown not in variants:
                cited[shown].add(r["src"])
    for n, s in sorted(cited.items()):
        names_out.append((root, n, "cited_synonym_or_combination", ";".join(sorted(s))))

order = {g: i for i, g in enumerate(GROUPS)}
out.sort(key=lambda r: (order[r["group"]], r["family"], r["species"].lower()))
ids = {}
count = Counter()
for r in out:
    count[r["group"]] += 1
    r["species_id"] = f"{PREFIX[r['group']]}{count[r['group']]:04d}"
    ids[r["_root"]] = (r["species_id"], r["species"])
row_of = {r["_root"]: r for r in out}

# Two rows left apart by a refused join are flagged for a look when a single source
# kept them apart and the epithets agree (a possible double count), or when they
# are homonyms.
for rv in REVIEW:
    if rv["action"] == "joined":
        continue
    A, B = find(rv["_a"]), find(rv["_b"])
    if A == B:
        continue
    if rv["basis"] == "homonym":
        row_of[A]["flags"].add(f"same_name_as:{ids[B][0]}")
        row_of[B]["flags"].add(f"same_name_as:{ids[A][0]}")
        continue
    bl = rv["_blockers"]
    if len(bl) != 1 or bl[0] == "authors":
        continue
    ka, kb = rv["_ka"], rv["_kb"]
    if ka and kb and stem(ka.split()[1]) != stem(kb.split()[1]):
        continue
    row_of[A]["flags"].add(f"check_vs:{ids[B][0]}")
    row_of[B]["flags"].add(f"check_vs:{ids[A][0]}")

for r in out:
    r["flags"] = ";".join(sorted(r["flags"]))
cols = ["species_id", "group", "family", "genus", "species", "authority", "year", "status", "counted", "n_sources",
        "sources", "india_states", "n_states", "other_names_in_sources", "joined_by", "flags", "notes"]
with open(D + "species_list.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
    w.writeheader()
    w.writerows(out)
with open(D + "species_list_names.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["species_id", "valid_name", "name", "kind", "sources"])
    for root, n, kind, s in sorted(names_out, key=lambda x: (ids[x[0]][0], x[2] != "valid", x[1])):
        w.writerow([ids[root][0], ids[root][1], n, kind, s])
for rv in REVIEW:
    rv["species_id_a"], rv["species_id_b"] = ids[find(rv["_a"])][0], ids[find(rv["_b"])][0]
with open(D + "species_list_review.csv", "w", newline="") as f:
    cols_r = ["action", "basis", "score", "group", "species_id_a", "name_a", "sources_a",
              "species_id_b", "name_b", "sources_b", "evidence"]
    w = csv.DictWriter(f, fieldnames=cols_r, extrasaction="ignore")
    w.writeheader()
    w.writerows(sorted(REVIEW, key=lambda r: (order[r["group"]], r["action"], r["basis"], r["name_a"])))

summ = []
for grp in GROUPS + ["All"]:
    g_rows = [r for r in out if grp in ("All", r["group"])]
    row = dict(group=grp, counted=sum(r["counted"] for r in g_rows),
               historical_only=sum(r["status"] == "historical_only" for r in g_rows),
               unverified=sum(r["status"] == "unverified" for r in g_rows), rows=len(g_rows),
               not_in_gupta_mondal_2023=sum("not_in_gupta_mondal_2023" in r["flags"] for r in g_rows),
               flagged_check_vs=sum("check_vs:" in r["flags"] for r in g_rows))
    for s in SOURCES:
        row[f"in_{s}"] = sum(s in r["sources"].split(";") for r in g_rows)
        row[f"only_{s}"] = sum(r["sources"] == s for r in g_rows)
    summ.append(row)
with open(D + "species_list_summary.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(summ[0]))
    w.writeheader()
    w.writerows(summ)
for r in summ:
    print(f"{r['group']:14} counted {r['counted']:4}  historical_only {r['historical_only']:3}  unverified {r['unverified']}"
          f"  rows {r['rows']}  check_vs {r['flagged_check_vs']}")
print("review:", sorted(Counter((r["action"], r["basis"].split(" (")[0]) for r in REVIEW).items()))
