"""Stage 3: match COI records to the Indian species list.

Reads  data/processed/coi_metadata.csv          (stage 2 output)
       data/checklist/species_list.csv          (stage 1 output)
       data/checklist/species_list_names.csv    (every spelling, old combination and synonym per species)
       data/checklist/coi_name_map.csv          (archive names that map to another species)
Writes data/processed/coi_matched.csv           one row per COI record, with species_id where matched
       data/processed/coverage_by_species.csv   one row per species in the list
       data/processed/coi_names_not_in_list.csv archive names with no match, with India counts
       logs/coverage_summary.csv

Only records flagged is_representative=1 are counted, so a sequence held in both
GenBank and BOLD counts once. Matching is by genus and epithet (subgenus ignored):
  exact        the name, or a listed spelling, old combination or cited synonym
  ending       same genus, epithet differs only in a Latin ending (longispinosus/-a)
  name_map     coi_name_map.csv (for example T. cinnabarinus to T. urticae)
Names with cf., aff., nr., sp. or a code are not matched; cf./aff. names keep the
species they point at in `points_to` so a less strict count is possible.
"""
import csv
import os
import re
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(__file__))
from names import key, parse, stem  # noqa: E402

ROOT = os.path.join(os.path.dirname(__file__), "..")
CK = os.path.join(ROOT, "data", "checklist")
PR = os.path.join(ROOT, "data", "processed")
GROUP_OF_FAMILY = {"Eriophyidae": "Eriophyoidea", "Diptilomiopidae": "Eriophyoidea", "Phytoptidae": "Eriophyoidea"}
PREFIX = {"TET": "Tetranychidae", "TEN": "Tenuipalpidae", "ERI": "Eriophyoidea", "TAR": "Tarsonemidae",
          "TUC": "Tuckerellidae", "PHY": "Phytoseiidae"}
GROUPS = list(PREFIX.values())


def rows(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


species = {r["species_id"]: r for r in rows(os.path.join(CK, "species_list.csv"))}
exact = defaultdict(set)    # (group, "genus epithet") -> species ids
ending = defaultdict(set)   # (group, "genus stem") -> species ids
for r in rows(os.path.join(CK, "species_list_names.csv")):
    p = parse(r["name"])
    if not p:
        continue
    if species[r["species_id"]]["counted"] != "1":
        continue   # historical-only names are handled through coi_name_map.csv
    grp = PREFIX[r["species_id"][:3]]
    exact[(grp, key(p[0], p[2]))].add(r["species_id"])
    ending[(grp, f"{p[0].lower()} {stem(p[2].lower())}")].add(r["species_id"])
name_map = {}
for r in rows(os.path.join(CK, "coi_name_map.csv")):
    p, q = parse(r["name_in_archive"]), parse(r["maps_to"])
    name_map[key(p[0], p[2])] = key(q[0], q[2])

QUALIFIER = re.compile(r"\b(cf|aff|nr|near)\.?\s+([a-z\-]+)", re.I)


def match(grp, name):
    """Return (species_id or '', basis, points_to)."""
    name = (name or "").strip()
    q = QUALIFIER.search(name)
    if q:
        g = name.split()[0]
        ids = exact.get((grp, key(g, q.group(2))), set())
        return "", "cf_or_aff", ";".join(sorted(ids))
    p = parse(name)
    if not p or not re.fullmatch(r"[a-z\-]+", p[2]) or len(p[2]) < 3:
        return "", "no_species_name", ""
    k = key(p[0], p[2])
    for basis, kk in (("name_map", name_map.get(k)), ("exact", k)):
        if kk:
            ids = exact.get((grp, kk), set())
            if len(ids) == 1:
                return next(iter(ids)), basis, ""
            if len(ids) > 1:
                return "", "ambiguous", ";".join(sorted(ids))
    ids = ending.get((grp, f"{p[0].lower()} {stem(p[2].lower())}"), set())
    if len(ids) == 1:
        return next(iter(ids)), "ending", ""
    return "", "not_in_list", ""


recs = rows(os.path.join(PR, "coi_metadata.csv"))
INDIA = {r["accession"] for r in rows(os.path.join(CK, "india_record_overrides.csv"))}
for r in recs:
    if r["accession"].split(".")[0] in INDIA:
        r["india_record"] = "1"
out = []
for r in recs:
    grp = GROUP_OF_FAMILY.get(r["family_as_given"], r["family_as_given"])
    name = r["species_as_given"] or r["organism_as_given"]
    sid, basis, points = match(grp, name)
    out.append(dict(record_id=r["record_id"], source=r["source"], accession=r["accession"],
                    bold_processid=r["bold_processid"], bold_bin=r["bold_bin"], group=grp,
                    family_as_given=r["family_as_given"], species_as_given=name,
                    species_id=sid, valid_name=species[sid]["species"] if sid else "",
                    match_basis=basis, points_to=points, country=r["country"],
                    india_record=r["india_record"], is_representative=r["is_representative"],
                    seq_length=r["seq_length"]))

with open(os.path.join(PR, "coi_matched.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(out[0]))
    w.writeheader()
    w.writerows(out)

rep = [o for o in out if o["is_representative"] == "1"]
by_sp = defaultdict(list)
for o in rep:
    if o["species_id"]:
        by_sp[o["species_id"]].append(o)
cov = []
for sid, s in species.items():
    if s["counted"] != "1":
        continue
    m = by_sp.get(sid, [])
    india = [o for o in m if o["india_record"] == "1"]
    cov.append(dict(species_id=sid, group=s["group"], family=s["family"], species=s["species"],
                    authority=s["authority"], year=s["year"], n_coi=len(m), n_coi_india=len(india),
                    n_bins=len({o["bold_bin"] for o in m if o["bold_bin"]}),
                    n_countries=len({o["country"] for o in m if o["country"]}),
                    countries=";".join(sorted({o["country"] for o in m if o["country"]})),
                    matched_via=";".join(sorted({o["match_basis"] for o in m})),
                    names_in_archive=";".join(sorted({o["species_as_given"] for o in m}))))
with open(os.path.join(PR, "coverage_by_species.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(cov[0]))
    w.writeheader()
    w.writerows(cov)

unl = defaultdict(lambda: Counter())
for o in rep:
    if o["match_basis"] in ("not_in_list", "ambiguous", "cf_or_aff"):
        c = unl[(o["group"], o["species_as_given"], o["match_basis"], o["points_to"])]
        c["n"] += 1
        c["india"] += o["india_record"] == "1"
with open(os.path.join(PR, "coi_names_not_in_list.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["group", "species_as_given", "reason", "points_to", "n_coi", "n_coi_india"])
    for (g, n, b, p), c in sorted(unl.items(), key=lambda x: (-x[1]["india"], -x[1]["n"])):
        w.writerow([g, n, b, p, c["n"], c["india"]])

summ = []
for g in GROUPS + ["All"]:
    cs = [c for c in cov if g == "All" or c["group"] == g]
    rs = [o for o in rep if g == "All" or o["group"] == g]
    ri = [o for o in rs if o["india_record"] == "1"]
    summ.append(dict(group=g, species_in_list=len(cs),
                     with_any_coi=sum(c["n_coi"] > 0 for c in cs),
                     with_indian_coi=sum(c["n_coi_india"] > 0 for c in cs),
                     coi_records=len(rs), records_matched=sum(bool(o["species_id"]) for o in rs),
                     india_records=len(ri), india_records_matched=sum(bool(o["species_id"]) for o in ri),
                     india_records_no_species_name=sum(o["match_basis"] == "no_species_name" for o in ri),
                     india_records_name_not_in_list=sum(o["match_basis"] == "not_in_list" for o in ri)))
for s in summ:
    n = s["species_in_list"] or 1
    s["pct_with_any_coi"] = f"{100 * s['with_any_coi'] / n:.1f}"
    s["pct_with_indian_coi"] = f"{100 * s['with_indian_coi'] / n:.1f}"
with open(os.path.join(ROOT, "logs", "coverage_summary.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(summ[0]))
    w.writeheader()
    w.writerows(summ)
for s in summ:
    print(s)
print(Counter(o["match_basis"] for o in rep))
