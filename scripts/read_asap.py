"""Stage 5c: read the ASAP and ABGD results (Spart Explorer, MNHN) and compare them with the names.

Input: data/processed/delimitation/spart_results/<run>/{asap,abgd}/... as downloaded from
https://spartexplorer.mnhn.fr (one folder per input file asap_<genus>_sites<a>-<b>.fas).
For each run it takes
  ASAP  the best-scored partition (rank 1 in the .res.cvs table)
  ABGD  the recursive partition at prior P = 0.0129 (the middle of the default range)
and for every name in the file reports how many subsets its sequences fall in and which
other names share those subsets.
Writes data/processed/name_delimitation.csv and logs/delimitation_summary.csv
"""
import csv
import glob
import os
import re
from collections import Counter, defaultdict

ROOT = os.path.join(os.path.dirname(__file__), "..")
RES = os.path.join(ROOT, "data", "processed", "delimitation", "spart_results")
ABGD_PRIOR = "0.012915"


def read_spart(path):
    """Return (list of partition labels, subset counts, {sample: [subset per partition]}, distance)."""
    txt = open(path, encoding="utf-8", errors="ignore").read()
    labels = re.search(r"N_spartitions\s*=\s*\d+\s*:\s*(.*?);", txt, re.S).group(1).split("/")
    nsub = [int(x.split(":")[0]) for x in re.search(r"N_subsets\s*=\s*(.*?);", txt, re.S).group(1).split("/")]
    dist = re.search(r"Distance\s+([^\]/]+)", txt).group(1).strip()
    block = txt.split("Individual_assignment", 1)[1]
    assign = {}
    for line in block.splitlines():
        m = re.match(r"\s*(\S+)\s*:\s*([\d\s/]+)", line)
        if m:
            assign[m.group(1)] = [int(x) for x in m.group(2).replace(";", "").split("/")]
    return [l.strip() for l in labels], nsub, assign, dist


# geography is read from coi_metadata.csv (geo_status), not from the IN/XX tag written into
# the input file names, which used the earlier substring rule
GEO = {r["record_id"].replace(".", "_"): r["geo_status"]
       for r in csv.DictReader(open(os.path.join(ROOT, "data", "processed", "coi_metadata.csv"), encoding="utf-8"))}


# ASAP partition reported per run: rank 1 unless set here (rank 3 for a file whose best-ranked
# partition splits one well-sampled species at a very low threshold)
ASAP_RANK = {}


def asap_groups(run, rank=None):
    """Number of subsets in the ASAP partition of the given rank (default ASAP_RANK or 1)."""
    rank = rank or ASAP_RANK.get(run, 1)
    res = glob.glob(os.path.join(RES, run, "asap", "*.res.cvs"))[0]
    table = [r for r in csv.reader(open(res), delimiter="\t")][1:]
    return int(table[rank - 1][1])


def name_of(sample):
    m = re.search(r"_(IN|XX)_(.*)$", sample)
    if not m:
        return sample, False
    rid = sample[:m.start()]
    return m.group(2).replace("_", " "), GEO.get(rid) == "india"


def compare(assign_one):
    """assign_one: {sample: subset}. Returns per-name rows."""
    sub_names = defaultdict(set)
    name_subs = defaultdict(Counter)
    india = Counter()
    for s, k in assign_one.items():
        n, ind = name_of(s)
        named = not re.search(r"\b(sp|cf|aff)\b", n) and len(n.split()) >= 2
        if named:
            sub_names[k].add(n)
            name_subs[n][k] += 1
            india[n] += ind
    out = []
    for n, subs in name_subs.items():
        others = sorted({o for k in subs for o in sub_names[k] if o != n})
        split = len(subs) > 1
        verdict = ("one subset, name alone" if not split and not others else
                   "one subset, shared with other names" if not split else
                   "split, no other names" if not others else "split and shared with other names")
        out.append(dict(name=n, n_seq=sum(subs.values()), n_india=india[n], n_subsets=len(subs),
                        subset_sizes=";".join(str(v) for _, v in subs.most_common()),
                        other_names_sharing=" | ".join(others), verdict=verdict))
    return out, len(set(assign_one.values()))


rows, summ = [], []
for run in sorted(glob.glob(os.path.join(RES, "*"))):
    rname = os.path.basename(run)
    a_sp = glob.glob(os.path.join(run, "asap", "*.fas.spart"))
    b_sp = glob.glob(os.path.join(run, "abgd", "*.rec.spart"))
    b_res = glob.glob(os.path.join(run, "abgd", "*.res.cvs"))
    a_res = glob.glob(os.path.join(run, "asap", "*.res.cvs"))
    if a_sp:
        labels, nsub, assign, dist = read_spart(a_sp[0])
        best = next(csv.reader(open(a_res[0]), delimiter="\t"))  # header
        rank1 = [r for r in csv.reader(open(a_res[0]), delimiter="\t")][1]
        # the spart lists partitions in ASAP's own order; pick the one with rank 1's subset count
        target = int(rank1[1])
        idx = nsub.index(target)
        per, n = compare({s: v[idx] for s, v in assign.items()})
        for p in per:
            rows.append(dict(run=rname, method="ASAP", distance=dist, partition=f"rank 1 ({target} subsets)",
                             threshold=rank1[7], **p))
        summ.append(dict(run=rname, method="ASAP", distance=dist, samples=len(assign), subsets=n,
                         threshold=rank1[7], asap_score=rank1[2], asap_pvalue=rank1[3]))
    if b_sp and b_res:
        labels, nsub, assign, dist = read_spart(b_sp[0])
        res = list(csv.reader(open(b_res[0]), delimiter="\t"))
        want = next((int(r[2]) for r in res[1:] if r[0].startswith(ABGD_PRIOR[:6])), None)
        if want and want in nsub and want > 1:
            idx = nsub.index(want)
            per, n = compare({s: v[idx] for s, v in assign.items()})
            for p in per:
                rows.append(dict(run=rname, method="ABGD", distance=dist,
                                 partition=f"recursive, P={ABGD_PRIOR} ({want} subsets)", threshold="", **p))
            summ.append(dict(run=rname, method="ABGD", distance=dist, samples=len(assign), subsets=n,
                             threshold=f"P={ABGD_PRIOR}", asap_score="", asap_pvalue=""))
        else:
            summ.append(dict(run=rname, method="ABGD", distance=dist, samples=len(assign), subsets=want or 1,
                             threshold=f"P={ABGD_PRIOR}: no usable partition", asap_score="", asap_pvalue=""))

with open(os.path.join(ROOT, "data", "processed", "name_delimitation.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)
with open(os.path.join(ROOT, "logs", "delimitation_summary.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(summ[0]))
    w.writeheader()
    w.writerows(summ)
for s in summ:
    print(s)
