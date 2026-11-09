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


# the parent body is preferred over its departments and centres: a university first, then an
# institute, bureau, directorate or other centre, then a laboratory, and the ICAR council last
# (it is the parent of many separate institutes)
TIERS = [re.compile(p, re.I) for p in (
    r"universi",                       # also catches the typo 'universiy'
    r"institut|bureau|directorate|research cent|college|museum|academy|survey|school",
    r"centre|center|laborator",
    r"council|icar",
)]
CITY = {"gkvk": "bengaluru", "bangalore": "bengaluru", "bengaluru": "bengaluru", "hebbal": "bengaluru"}


def institution(line):
    """Parent institution of a submitter line, so that one body's differently typed
    addresses fall together: 'Univ. of Agril. Sciences, GKVK' = 'University of Agricultural
    Sciences, GKVK campus', and 'CPBMB, Kerala Agricultural Universiy' = 'Agricultural
    Entomology, Kerala Agricultural University'."""
    t = line.lower().replace("agril.", "agricultural").replace("agri.", "agricultural").replace("univ.", "university")
    t = t.replace("universiy", "university").replace("&", "and")
    t = re.sub(r"\([^)]*\)", "", t)                 # '(icar-nbair)'
    t = re.sub(r"\bicar\s*-\s*|\bicar\s+(?=[a-z])", "", t)   # 'ICAR-National Bureau ...' = 'National Bureau ...' 
    bits = [b.strip(" .") for b in t.split(",") if b.strip(" .")]
    for tier in TIERS:
        for i, b in enumerate(bits):
            if tier.search(b):
                # several universities of agricultural sciences: keep the campus
                generic = re.fullmatch(r"university of agricultural sciences", b)
                nxt = bits[i + 1].split()[0] if generic and i + 1 < len(bits) and bits[i + 1].split() else ""
                nxt = CITY.get(re.sub(r"[^a-z]", "", nxt), nxt)
                return re.sub(r"[^a-z]", "", b + nxt)
    return re.sub(r"[^a-z]", "", bits[0]) if bits else ""


with open(os.path.join(ROOT, "data", "processed", "submitters.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["accession", "submitter", "institution", "first_submitting_author"])
    for k, (s, a) in sorted(out.items()):
        w.writerow([k, s, institution(s), a])
print(len(out), "records;", len({s for s, _ in out.values()}), "distinct submitter lines;",
      len({institution(s) for s, _ in out.values()}), "institutions")
