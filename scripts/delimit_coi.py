"""Stage 5a: do the names on Indian COI records hold up?

Sequences are placed on one full-length COI reference per group (pairwise local
alignment, both strands); those that do not map are listed in not_mapped.csv.

For each group, takes every Indian COI record (representatives only) and, for every
species with Indian records, up to MAX_FOREIGN records of the same species from
other countries. Aligns them with MAFFT, computes uncorrected p-distances over the
sites two sequences share (at least MIN_OVERLAP), and joins sequences into clusters
by single linkage at a threshold (3% and 2%), in the way BOLD BINs and simple
barcode-gap analyses do.

Writes data/processed/delimitation/<group>.fasta and _aligned.fasta,
       data/processed/delimitation/clusters.csv      one row per sequence
       data/processed/name_reliability.csv           one row per Indian name
       logs/name_reliability_summary.csv
"""
import csv
import os
import subprocess
from collections import Counter, defaultdict

import numpy as np
from Bio import Align
from Bio.Seq import Seq

ROOT = os.path.join(os.path.dirname(__file__), "..")
PR = os.path.join(ROOT, "data", "processed")
OUT = os.path.join(PR, "delimitation")
os.makedirs(OUT, exist_ok=True)
MAX_FOREIGN = 40
MIN_OVERLAP = 300
THRESHOLDS = (0.03, 0.02)
# one full-length COI per group; every sequence is placed on its coordinates (as BOLD does)
REFERENCE = {"Tetranychidae": "NC_024679.1", "Phytoseiidae": "NC_069213.1", "Tarsonemidae": "KX790788.1",
             "Eriophyoidea": "NC_029209.1", "Tenuipalpidae": "XM_074747291.1"}
MIN_MAPPED = 200      # sites placed on the reference
MIN_IDENTITY = 0.60   # identity to the reference over the mapped sites
ALIGNER = Align.PairwiseAligner(mode="local", match_score=2, mismatch_score=-1,
                                open_gap_score=-4, extend_gap_score=-1)


def place(seq, ref):
    """Return the sequence on reference coordinates ('-' where not covered), sites mapped, identity."""
    best = None
    for s in (seq, str(Seq(seq).reverse_complement())):
        a = ALIGNER.align(ref, s)[0]
        if best is None or a.score > best[0].score:
            best = (a, s)
    a, s = best
    out = ["-"] * len(ref)
    same = n = 0
    for (r0, r1), (q0, q1) in zip(*a.aligned):
        for i in range(r1 - r0):
            out[r0 + i] = s[q0 + i]
            n += 1
            same += s[q0 + i] == ref[r0 + i]
    return "".join(out), n, (same / n if n else 0)


def rows(p):
    with open(p, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def read_fasta(p):
    seqs, name = {}, None
    for line in open(p):
        line = line.strip()
        if line.startswith(">"):
            name = line[1:].split("|")[0]
            seqs[name] = []
        elif name:
            seqs[name].append(line)
    return {k: "".join(v).upper() for k, v in seqs.items()}


meta = {r["record_id"]: r for r in rows(os.path.join(PR, "coi_metadata.csv"))}
match = [r for r in rows(os.path.join(PR, "coi_matched.csv")) if r["is_representative"] == "1"]
seqs = read_fasta(os.path.join(PR, "coi_raw.fasta"))


def label(r):
    return r["valid_name"] or r["species_as_given"]


# open names (sequence-only Indian names) are compared with their foreign records too
india = [r for r in match if r["india_record"] == "1"]
names_in_india = {label(r) for r in india if r["match_basis"] not in ("no_species_name", "cf_or_aff")}
chosen = defaultdict(list)
for r in india:
    chosen[r["group"]].append(r)
foreign = defaultdict(list)
for r in match:
    if r["india_record"] != "1" and label(r) in names_in_india and r["match_basis"] != "no_species_name":
        foreign[(r["group"], label(r))].append(r)
for (g, n), rs in foreign.items():
    # spread the sample over BINs and countries first, then by length
    rs.sort(key=lambda r: (r["bold_bin"] == "", -int(r["seq_length"] or 0)))
    seen, pick = set(), []
    for r in rs:
        k = (r["bold_bin"], r["country"])
        if k not in seen:
            pick.append(r)
            seen.add(k)
    for r in rs:
        if len(pick) >= MAX_FOREIGN:
            break
        if r not in pick:
            pick.append(r)
    chosen[g].extend(pick[:MAX_FOREIGN])


def pdist(aln):
    ids = list(aln)
    a = np.array([list(aln[i]) for i in ids])
    valid = np.isin(a, list("ACGT"))
    n = len(ids)
    d = np.full((n, n), np.nan)
    for i in range(n):
        both = valid[i] & valid
        ov = both.sum(1)
        diff = ((a[i] != a) & both).sum(1)
        with np.errstate(invalid="ignore", divide="ignore"):
            row = diff / ov
        row[ov < MIN_OVERLAP] = np.nan
        d[i] = row
    np.fill_diagonal(d, 0)
    return ids, d


def clusters(ids, d, t):
    parent = list(range(len(ids)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    ii, jj = np.where(np.nan_to_num(d, nan=1) <= t)
    for i, j in zip(ii, jj):
        if i < j:
            parent[find(i)] = find(j)
    roots = {}
    return [roots.setdefault(find(i), len(roots) + 1) for i in range(len(ids))]


clrows = []
DROPPED = []
# sequences flagged by screen_coi.py (stop codons in all frames, or far from everything) are left out
SCREEN = os.path.join(OUT, "screen.csv")
FLAGGED = {r["record_id"] for r in rows(SCREEN) if r["flags"]} if os.path.exists(SCREEN) else set()
for g, rs in chosen.items():
    rs = [r for r in rs if r["record_id"] in seqs and 200 <= len(seqs[r["record_id"]]) <= 2000
]
    if len(rs) < 2:
        continue
    by = {r["record_id"]: r for r in rs}
    raw = os.path.join(OUT, f"{g}.fasta")
    with open(raw, "w") as f:
        for r in rs:
            f.write(f">{r['record_id']}\n{seqs[r['record_id']]}\n")
    ref_id = next(k for k, v in meta.items() if v["accession"] == REFERENCE[g])
    ref = seqs[ref_id]
    aln, dropped = {}, []
    for r in rs:
        placed, n, ident = place(seqs[r["record_id"]], ref)
        if n >= MIN_MAPPED and ident >= MIN_IDENTITY:
            aln[r["record_id"]] = placed
        else:
            dropped.append(dict(record_id=r["record_id"], accession=r["accession"] or r["bold_processid"], group=g,
                                name=label(r), india_record=r["india_record"], sites_mapped=n,
                                identity_to_reference=f"{ident:.3f}"))
    DROPPED.extend(dropped)
    with open(os.path.join(OUT, f"{g}_on_reference.fasta"), "w") as f:
        for k, v in aln.items():
            f.write(f">{k}|{label(by[k]).replace(' ', '_')}\n{v}\n")
    aln = {k: v for k, v in aln.items() if k not in FLAGGED}
    ids, d = pdist(aln)
    cl = {t: clusters(ids, d, t) for t in THRESHOLDS}
    for k, rid in enumerate(ids):
        r = by[rid]
        same = [j for j in range(len(ids)) if label(by[ids[j]]) == label(r) and j != k and not np.isnan(d[k, j])]
        other = [j for j in range(len(ids)) if label(by[ids[j]]) != label(r) and not np.isnan(d[k, j])
                 and by[ids[j]]["match_basis"] not in ("no_species_name", "cf_or_aff")]
        nn = min(other, key=lambda j: d[k, j]) if other else None
        # best close match (Meier et al. 2006): the nearest named sequence(s) within 3%
        named = [j for j in range(len(ids)) if j != k and not np.isnan(d[k, j])
                 and by[ids[j]]["match_basis"] not in ("no_species_name", "cf_or_aff")]
        if not named:
            bcm = "no overlapping sequence"
        else:
            dmin = min(d[k, j] for j in named)
            best = {label(by[ids[j]]) for j in named if d[k, j] <= dmin + 1e-9}
            if dmin > 0.03:
                bcm = "no match within 3%"
            elif best == {label(r)}:
                bcm = "correct"
            elif label(r) in best:
                bcm = "ambiguous"
            else:
                bcm = "incorrect"
        fo_same = [j for j in same if by[ids[j]]["india_record"] != "1"]
        clrows.append(dict(record_id=rid, accession=r["accession"] or r["bold_processid"], group=g, name=label(r),
                           match_basis=r["match_basis"], india_record=r["india_record"], country=r["country"],
                           bold_bin=r["bold_bin"], length=len(seqs[rid]),
                           cluster_3pct=f"{g[:3]}{cl[0.03][k]}", cluster_2pct=f"{g[:3]}{cl[0.02][k]}",
                           best_close_match=bcm,
                           n_foreign_same_name_overlapping=len(fo_same),
                           min_dist_foreign_same_name=f"{min(d[k, j] for j in fo_same):.4f}" if fo_same else "",
                           max_dist_same_name=f"{max(d[k, j] for j in same):.4f}" if same else "",
                           nearest_other_name=label(by[ids[nn]]) if nn is not None else "",
                           dist_nearest_other_name=f"{d[k, nn]:.4f}" if nn is not None else ""))

with open(os.path.join(OUT, "not_mapped.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(DROPPED[0]))
    w.writeheader()
    w.writerows(DROPPED)
print("not mapped:", len(DROPPED), "of which Indian:", sum(x["india_record"] == "1" for x in DROPPED))
with open(os.path.join(OUT, "clusters.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(clrows[0]))
    w.writeheader()
    w.writerows(clrows)

# one row per Indian name
by_cl = defaultdict(list)
for c in clrows:
    by_cl[c["cluster_3pct"]].append(c)
rel = []
for (g, n) in sorted({(c["group"], c["name"]) for c in clrows if c["india_record"] == "1"}):
    ind = [c for c in clrows if c["name"] == n and c["group"] == g and c["india_record"] == "1"]
    fo = [c for c in clrows if c["name"] == n and c["group"] == g and c["india_record"] != "1"]
    unnamed = any(c["match_basis"] in ("no_species_name", "cf_or_aff") for c in ind)
    icl = Counter(c["cluster_3pct"] for c in ind)
    bc = Counter(c["best_close_match"] for c in ind)
    ov = [c for c in ind if c["n_foreign_same_name_overlapping"]]
    near_abroad = [c for c in ov if float(c["min_dist_foreign_same_name"]) <= 0.03]
    if unnamed:
        verdict = "no species name"
    elif bc["incorrect"]:
        verdict = "some Indian sequences closest to another name"
    elif not fo:
        verdict = "no foreign sequences of this name"
    elif not ov:
        verdict = "foreign sequences do not overlap (other COI region)"
    elif len(near_abroad) == len(ov):
        verdict = "matches the same name abroad (within 3%)"
    elif near_abroad:
        verdict = "only some Indian sequences match abroad"
    else:
        verdict = "more than 3% from the same name abroad"
    rel.append(dict(group=g, name=n, n_india=len(ind), n_foreign_compared=len(fo),
                    india_seqs_overlapping_foreign=len(ov),
                    min_dist_india_to_foreign=min((c["min_dist_foreign_same_name"] for c in ov), default=""),
                    max_dist_within_name=max((c["max_dist_same_name"] for c in ind if c["max_dist_same_name"]), default=""),
                    bcm_correct=bc["correct"], bcm_ambiguous=bc["ambiguous"], bcm_incorrect=bc["incorrect"],
                    bcm_no_match=bc["no match within 3%"] + bc["no overlapping sequence"],
                    closest_other_names="; ".join(sorted({c["nearest_other_name"] for c in ind
                                                          if c["best_close_match"] in ("incorrect", "ambiguous")})),
                    nearest_other_name=min(ind, key=lambda c: float(c["dist_nearest_other_name"] or 9))["nearest_other_name"],
                    min_dist_to_other_name=min((c["dist_nearest_other_name"] for c in ind if c["dist_nearest_other_name"]), default=""),
                    india_clusters_3pct=len(icl), verdict=verdict))
with open(os.path.join(PR, "name_reliability.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rel[0]))
    w.writeheader()
    w.writerows(rel)
summ = Counter((r["group"], r["verdict"]) for r in rel)
with open(os.path.join(ROOT, "logs", "name_reliability_summary.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["group", "verdict", "indian_names"])
    for (g, v), n in sorted(summ.items()):
        w.writerow([g, v, n])
for (g, v), n in sorted(summ.items()):
    print(g, v, n)
