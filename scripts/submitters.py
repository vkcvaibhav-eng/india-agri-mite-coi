"""Submitting laboratory of each GenBank record, from the Direct Submission reference.

The journal line of that reference reads 'Submitted (DD-MMM-YYYY) Department,
Institution, City, ...'. The date is dropped and the rest, lower-cased, identifies
the submission series used to hold out a laboratory's own records when names are
compared. Writes data/processed/submitters.csv.
"""
import csv
import glob
import os
import re

from Bio import SeqIO

ROOT = os.path.join(os.path.dirname(__file__), "..")
out = {}
for path in sorted(glob.glob(os.path.join(ROOT, "data", "raw", "ncbi", "*.gb"))):
    for rec in SeqIO.parse(path, "genbank"):
        sub = ""
        for ref in rec.annotations.get("references", []) or []:
            if ref.title.strip().lower() == "direct submission" and ref.journal.startswith("Submitted"):
                sub = re.sub(r"^Submitted \([^)]*\)\s*", "", ref.journal)
        authors = ""
        refs = rec.annotations.get("references", []) or []
        if refs:
            authors = refs[-1].authors.split(",")[0].strip()
        out[rec.id] = (re.sub(r"\s+", " ", sub).strip().lower(), authors)


KEY = re.compile(r"universit|institut|college|centre|center|council|icar|museum|academy|bureau|survey|laborator|school", re.I)


def institution(line):
    """Institution of a submitter line, so that one laboratory's differently typed
    addresses fall together ('Univ. of Agril. Sciences, GKVK' = 'University of Agricultural
    Sciences, GKVK campus')."""
    t = line.lower().replace("agril.", "agricultural").replace("agri.", "agricultural").replace("univ.", "university")
    bits = [b.strip(" .") for b in t.split(",") if b.strip(" .")]
    for i, b in enumerate(bits):
        if KEY.search(b):
            generic = re.match(r"(university|institute|college|school) of ", b)
            nxt = bits[i + 1].split()[0] if generic and i + 1 < len(bits) and bits[i + 1].split() else ""
            return re.sub(r"[^a-z ]", "", b + " " + nxt).strip()
    return re.sub(r"[^a-z ]", "", bits[0]).strip() if bits else ""
with open(os.path.join(ROOT, "data", "processed", "submitters.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["accession", "submitter", "institution", "first_submitting_author"])
    for k, (s, a) in sorted(out.items()):
        w.writerow([k, s, institution(s), a])
print(len(out), "records;", len({s for s, _ in out.values()}), "distinct submitter lines;",
      len({institution(s) for s, _ in out.values()}), "institutions")
