"""Stage 5b: screen the reference-placed COI sequences and export clean files for ASAP.

Reads data/processed/delimitation/<group>_on_reference.fasta (written by delimit_coi.py)
and clusters.csv. A sequence is flagged when
  stop_codon     every one of the six reading frames of the original sequence has a stop codon
                 under the invertebrate mitochondrial code (NCBI table 5): a numt, a frame error or not COI
  far_from_all   no other sequence in the group is within 20% (not the same gene region,
                 contamination or a mislabelled marker)
Writes data/processed/delimitation/screen.csv
       data/processed/delimitation/asap_<genus>.fasta  for genera with Indian sequences
       (clean sequences only, trimmed to the reference window most Indian sequences share)
"""
import csv
import os
from collections import Counter, defaultdict

import numpy as np

ROOT = os.path.join(os.path.dirname(__file__), "..")
D = os.path.join(ROOT, "data", "processed", "delimitation")
STOPS = {"TAA", "TAG"}          # table 5: TGA is Trp, AGA/AGG are Ser
GROUPS = ["Tetranychidae", "Tenuipalpidae", "Eriophyoidea", "Tarsonemidae", "Phytoseiidae"]
MIN_SITES = 300


def read(p):
    out, k = {}, None
    for line in open(p):
        line = line.strip()
        if line.startswith(">"):
            k = line[1:]
            out[k] = []
        else:
            out[k].append(line)
    return {k: "".join(v) for k, v in out.items()}


from Bio.Seq import Seq


def raw_fasta(p):
    out, k = {}, None
    for line in open(p):
        line = line.strip()
        if line.startswith(">"):
            k = line[1:].split("|")[0]
            out[k] = []
        elif k:
            out[k].append(line)
    return {k: "".join(v).upper() for k, v in out.items()}


RAW = raw_fasta(os.path.join(ROOT, "data", "processed", "coi_raw.fasta"))


def min_stops(seq):
    """Fewest internal stop codons over the six reading frames (table 5)."""
    best = None
    for s in (seq, str(Seq(seq).reverse_complement())):
        for f in range(3):
            t = s[f:]
            t = t[:len(t) // 3 * 3]
            codons = [t[i:i + 3] for i in range(0, len(t) - 3, 3)]   # last codon may be a terminal stop
            n = sum(c in STOPS for c in codons)
            best = n if best is None else min(best, n)
    return best


clusters = {r["record_id"]: r for r in csv.DictReader(open(os.path.join(D, "clusters.csv")))}
rows, keep = [], defaultdict(dict)
for g in GROUPS:
    p = os.path.join(D, f"{g}_on_reference.fasta")
    if not os.path.exists(p):
        continue
    seqs = read(p)
    ids = list(seqs)
    a = np.array([list(seqs[i]) for i in ids])
    valid = np.isin(a, list("ACGT"))
    for k, sid in enumerate(ids):
        rid, name = sid.split("|", 1)
        s = seqs[sid]
        stops = min_stops(RAW[rid].replace("-", "")) if rid in RAW else 0
        both = valid[k] & valid
        ov = both.sum(1)
        diff = ((a[k] != a) & both).sum(1)
        with np.errstate(invalid="ignore", divide="ignore"):
            dist = np.where(ov >= MIN_SITES, diff / ov, np.nan)
        dist[k] = np.nan
        nearest = np.nanmin(dist) if np.isfinite(dist).any() else np.nan
        flags = []
        if stops:
            flags.append("stop_codon")
        if not np.isfinite(nearest) or nearest > 0.20:
            flags.append("far_from_all")
        c = clusters.get(rid, {})
        rows.append(dict(record_id=rid, accession=c.get("accession", ""), group=g, name=name.replace("_", " "),
                         india_record=c.get("india_record", ""), sites=int(valid[k].sum()), stop_codons=stops,
                         nearest_any=f"{nearest:.4f}" if np.isfinite(nearest) else "", flags=";".join(flags)))
        if not flags:
            keep[g][sid] = s

with open(os.path.join(D, "screen.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)

# ASAP input per genus: clean sequences, trimmed to the window covered by most Indian sequences
summary = []
for g, seqs in keep.items():
    by_genus = defaultdict(dict)
    for sid, s in seqs.items():
        by_genus[sid.split("|", 1)[1].split("_")[0]][sid] = s
    for genus, ss in by_genus.items():
        ind = [sid for sid in ss if clusters.get(sid.split("|")[0], {}).get("india_record") == "1"]
        if len(ind) < 3 or len(ss) < 8:
            continue
        cov = np.zeros(len(next(iter(ss.values()))))
        for sid in ind:
            cov += np.array([ch != "-" for ch in ss[sid]])
        win = np.where(cov >= 0.5 * len(ind))[0]
        lo, hi = win.min(), win.max() + 1
        out = {}
        for sid, s in ss.items():
            t = s[lo:hi]
            if sum(ch != "-" for ch in t) >= MIN_SITES:
                rid = sid.split("|")[0]
                tag = "IN" if clusters.get(rid, {}).get("india_record") == "1" else "XX"
                out[f"{rid}_{tag}_{sid.split('|')[1]}"] = t.replace("-", "N") if False else t
        with open(os.path.join(D, f"asap_{genus}.fasta"), "w") as f:
            for k, v in out.items():
                f.write(f">{k}\n{v}\n")
        summary.append((g, genus, len(out), sum("_IN_" in k for k in out), lo + 1, hi))

flagged = [r for r in rows if r["flags"]]
print("sequences screened:", len(rows), "flagged:", len(flagged),
      "Indian flagged:", sum(r["india_record"] == "1" for r in flagged))
print(Counter(f for r in flagged for f in r["flags"].split(";")))
for s in summary:
    print("ASAP file", s)
