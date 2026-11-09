"""List sequences whose name differs from the majority name of their ASAP group.

Uses the best-ranked ASAP partition of each run, or the rank set in ASAP_RANK (read_asap.py). Writes data/processed/suspect_names.csv.
"""
import collections
import csv
import glob
import os
import re

HERE = os.path.dirname(__file__)
exec(open(os.path.join(HERE, "read_asap.py")).read().split("rows, summ = [], []")[0])
ROOT = os.path.join(HERE, "..")
meta = {skey(r["record_id"]): r for r in csv.DictReader(open(os.path.join(ROOT, "data", "processed", "coi_metadata.csv")))}
RUNS = [(os.path.basename(p), asap_groups(os.path.basename(p)),
         f"rank {ASAP_RANK.get(os.path.basename(p), 1)} ({asap_groups(os.path.basename(p))} groups)")
        for p in sorted(glob.glob(os.path.join(RES, "*")))]
UNNAMED = re.compile(r"\b(sp|cf|aff)\b")
out = []
for run, target, label in RUNS:
    labels, nsub, assign, _ = read_spart(glob.glob(os.path.join(RES, run, "asap", "*.fas.spart"))[0])
    idx = asap_index(labels, nsub, asap_row(run))
    subs = collections.defaultdict(list)
    for s, v in assign.items():
        subs[v[idx]].append(s)
    for k, ss in subs.items():
        names = collections.Counter(name_of(s)[0] for s in ss if not UNNAMED.search(name_of(s)[0]))
        if len(names) < 2:
            continue
        top = names.most_common()
        tie = len(top) > 1 and top[0][1] == top[1][1]
        major = "tie: " + " = ".join(a for a, b in top if b == top[0][1]) if tie else top[0][0]
        for s in ss:
            n, ind = name_of(s)
            if (not tie and n == major) or UNNAMED.search(n):
                continue
            m = meta.get(re.sub(r"_(IN|XX)_.*$", "", s), {})
            out.append(dict(region=run, asap_partition=label, asap_group=k, group_majority_name=major,
                            conflict="tie" if tie else "majority disagreement",
                            group_composition="; ".join(f"{a} {b}" for a, b in names.most_common()),
                            name_on_record=n, accession=m.get("accession") or m.get("bold_processid", ""),
                            indian="yes" if ind else "no", geo_status=m.get("geo_status", ""), country=m.get("country", ""),
                            state_or_locality=(m.get("state_province", "") + " " + m.get("locality", "")).strip(),
                            host=m.get("host", ""), collection_date=m.get("collection_date", ""),
                            reference=m.get("reference_title", "") if m.get("reference_title") != "Direct Submission"
                            else m.get("reference_journal", "")))
with open(os.path.join(ROOT, "data", "processed", "suspect_names.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(out[0]))
    w.writeheader()
    w.writerows(out)
print(len(out), "sequences")
