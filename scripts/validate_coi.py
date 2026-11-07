"""Stage 3b: check that every representative record really is COI.

Each representative sequence is placed on a complete mitochondrial COI of its
group (local pairwise alignment, both strands). A record counts as COI when at
least MIN_MAPPED sites are placed at MIN_IDENTITY or more identity to the
reference and at least one of its six reading frames is free of internal stop
codons under the invertebrate mitochondrial code (NCBI table 5). Placement alone
is not enough: 18S and 28S rRNA sequences reach 57-59% identity to a COI
reference, against 61% for the least similar COI record. Tenuipalpidae have no complete mitochondrial COI in GenBank, so they
are placed on the Tetranychidae reference (same superfamily, Tetranychoidea).

Writes data/processed/coi_validation.csv and logs/validation_summary.csv.
"""
import csv
import os
from collections import Counter
from multiprocessing import Pool

from Bio import Align
from Bio.Seq import Seq

ROOT = os.path.join(os.path.dirname(__file__), "..")
PR = os.path.join(ROOT, "data", "processed")
REFERENCE = {"Tetranychidae": "NC_024679.1", "Tenuipalpidae": "NC_024679.1", "Phytoseiidae": "NC_069213.1",
             "Tarsonemidae": "KX790788.1", "Eriophyoidea": "NC_029209.1"}
GROUP = {"Eriophyidae": "Eriophyoidea", "Diptilomiopidae": "Eriophyoidea", "Phytoptidae": "Eriophyoidea"}
MIN_MAPPED = 200
MIN_IDENTITY = 0.60
ALIGNER = Align.PairwiseAligner(mode="local", match_score=2, mismatch_score=-1,
                                open_gap_score=-4, extend_gap_score=-1)


def group_of(family):
    return GROUP.get(family, family)


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


def place(seq, ref):
    best = None
    for s in (seq, str(Seq(seq).reverse_complement())):
        a = ALIGNER.align(ref, s)[0]
        if best is None or a.score > best[0].score:
            best = (a, s)
    a, s = best
    same = n = 0
    start = None
    for (r0, r1), (q0, q1) in zip(*a.aligned):
        start = r0 if start is None else start
        for i in range(r1 - r0):
            n += 1
            same += s[q0 + i] == ref[r0 + i]
        end = r1
    return n, (same / n if n else 0.0), (start or 0) + 1, (end if n else 0)


STOPS = {"TAA", "TAG"}   # table 5: TGA is Trp, AGA/AGG are Ser


def min_stops(seq):
    best = None
    for s in (seq, str(Seq(seq).reverse_complement())):
        for f in range(3):
            t = s[f:]
            t = t[:len(t) // 3 * 3]
            n = sum(t[i:i + 3] in STOPS for i in range(0, len(t) - 3, 3))
            best = n if best is None else min(best, n)
    return best


def work(args):
    rid, seq, ref = args
    return (rid,) + place(seq, ref)


if __name__ == "__main__":
    meta = list(csv.DictReader(open(os.path.join(PR, "coi_metadata.csv"), encoding="utf-8")))
    seqs = read_fasta(os.path.join(PR, "coi_raw.fasta"))
    by_acc = {r["accession"]: r["record_id"] for r in meta if r["accession"]}
    refs = {g: seqs[by_acc[a]] for g, a in REFERENCE.items()}
    reps = [r for r in meta if r["is_representative"] == "1"]
    jobs = [(r["record_id"], seqs[r["record_id"]], refs[group_of(r["family_as_given"])])
            for r in reps if r["record_id"] in seqs and group_of(r["family_as_given"]) in refs]
    import sys
    old = os.path.join(PR, "coi_validation.csv")
    if "--reuse-placement" in sys.argv and os.path.exists(old):
        res = {r["record_id"]: (int(r["sites_placed"]), float(r["identity_to_reference"]),
                                int(r["ref_start"]), int(r["ref_end"])) for r in csv.DictReader(open(old))}
        todo = [j for j in jobs if j[0] not in res]
        with Pool(os.cpu_count()) as pool:
            res.update({x[0]: x[1:] for x in pool.map(work, todo, chunksize=20)})
        print(len(todo), "records placed anew")
    else:
        with Pool(os.cpu_count()) as pool:
            res = {x[0]: x[1:] for x in pool.map(work, jobs, chunksize=50)}
    out = []
    for r in reps:
        g = group_of(r["family_as_given"])
        n, ident, a, b = res.get(r["record_id"], (0, 0.0, 0, 0))
        stops = min_stops(seqs[r["record_id"]]) if r["record_id"] in seqs else -1
        ok = n >= MIN_MAPPED and ident >= MIN_IDENTITY and stops == 0
        out.append(dict(record_id=r["record_id"], accession=r["accession"] or r["bold_processid"], group=g,
                        species_as_given=r["species_as_given"], geo_status=r["geo_status"],
                        sites_placed=n, identity_to_reference=f"{ident:.3f}", ref_start=a, ref_end=b, min_stop_codons=stops,
                        coi_validated="1" if ok else "0"))
    with open(os.path.join(PR, "coi_validation.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0]))
        w.writeheader()
        w.writerows(out)
    c = Counter((o["group"], o["coi_validated"]) for o in out)
    ci = Counter((o["group"], o["coi_validated"]) for o in out if o["geo_status"] == "india")
    with open(os.path.join(ROOT, "logs", "validation_summary.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["group", "representatives", "validated", "failed", "indian_validated", "indian_failed"])
        for g in sorted({o["group"] for o in out}):
            w.writerow([g, c[(g, "1")] + c[(g, "0")], c[(g, "1")], c[(g, "0")], ci[(g, "1")], ci[(g, "0")]])
            print(g, c[(g, "1")], "validated,", c[(g, "0")], "failed; Indian", ci[(g, "1")], ci[(g, "0")])
