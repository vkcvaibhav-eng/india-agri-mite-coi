"""List sequences whose name differs from the majority name of their ASAP group.

Uses the ASAP partitions chosen in the paper: Tetranychus sites 271-670 rank 3 (24 groups, 3.9%),
the best-ranked partition for the other runs. Writes data/processed/suspect_names.csv.
"""
import collections
import csv
import glob
import os
import re

HERE = os.path.dirname(__file__)
exec(open(os.path.join(HERE, "read_asap.py")).read().split("rows, summ = [], []")[0])
ROOT = os.path.join(HERE, "..")
meta = {r["record_id"].replace(".", "_"): r for r in csv.DictReader(open(os.path.join(ROOT, "data", "processed", "coi_metadata.csv")))}
RUNS = [("Tetranychus_sites271-670", 24, "rank 3 (24 groups, 3.9%)"),
        ("Tetranychus_sites741-1140", 25, "rank 1 (25 groups, 3.0%)"),
        ("Oligonychus_sites261-660", 8, "rank 1 (8 groups, 9.3%)"),
        ("Oligonychus_sites761-1160", 11, "rank 1 (11 groups, 3.1%)"),
        ("Phytoseiidae_sites321-720", 11, "rank 1 (11 groups, 11.4%)")]
UNNAMED = re.compile(r"\b(sp|cf|aff)\b")
out = []
for run, target, label in RUNS:
    _, nsub, assign, _ = read_spart(glob.glob(os.path.join(RES, run, "asap", "*.fas.spart"))[0])
    idx = nsub.index(target)
    subs = collections.defaultdict(list)
    for s, v in assign.items():
        subs[v[idx]].append(s)
    for k, ss in subs.items():
        names = collections.Counter(name_of(s)[0] for s in ss if not UNNAMED.search(name_of(s)[0]))
        if len(names) < 2:
            continue
        major = names.most_common(1)[0][0]
        for s in ss:
            n, ind = name_of(s)
            if n == major or UNNAMED.search(n):
                continue
            m = meta.get(re.sub(r"_(IN|XX)_.*$", "", s), {})
            out.append(dict(region=run, asap_partition=label, asap_group=k, group_majority_name=major,
                            group_composition="; ".join(f"{a} {b}" for a, b in names.most_common()),
                            name_on_record=n, accession=m.get("accession") or m.get("bold_processid", ""),
                            indian="yes" if ind else "no", country=m.get("country", ""),
                            state_or_locality=(m.get("state_province", "") + " " + m.get("locality", "")).strip(),
                            host=m.get("host", ""), collection_date=m.get("collection_date", ""),
                            reference=m.get("reference_title", "") if m.get("reference_title") != "Direct Submission"
                            else m.get("reference_journal", "")))
with open(os.path.join(ROOT, "data", "processed", "suspect_names.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(out[0]))
    w.writeheader()
    w.writerows(out)
print(len(out), "sequences")
