"""Table 1 of Mandal, Layek, Ghosh, Bala & Debnath (2026), Systematic and Applied Acarology 31(3):
eriophyoid mites of West Bengal (232 listed). Layout table: columns found per page from the header line."""
import re, csv, sys, os
sys.path.insert(0, os.path.dirname(__file__))
SRC = sys.argv[1] if len(sys.argv) > 1 else "/home/claude/src/erio/mandal2026.txt"
OUT = "data/checklist/mandal2026_eriophyoidea_west_bengal.csv"
START = re.compile(r"^([A-Z][a-z]+)(?: \([A-Z][a-z]+\))? ([a-z][a-z-]+)\b")
lines = open(SRC, errors="replace").read().split("\n")
t0 = next(i for i, l in enumerate(lines) if "TABLE 1. Checklist" in l)
t1 = next(i for i, l in enumerate(lines) if i > t0 + 100 and re.search(r"^\s*(Family: |Description|TAXONOMY|Materials)", l) is None and "Family:" not in l and "TABLE 1" not in l and re.search(r"(?i)^\s*(Material and methods|Materials and methods|Methods)", l)) if False else len(lines)
cols = None; fam = ""; recs = []; cur = None
def flush():
    global cur
    if cur: recs.append(cur); cur = None
for i in range(t0, len(lines)):
    l = lines[i]
    if re.search(r"Materials and [Mm]ethods|^\s*Taxonomy\s*$|^\s*Family Eriophyidae Nalepa", l) and i > t0 + 200:
        break
    m = re.search(r"Family: (\w+)", l)
    if m: fam = m.group(1); continue
    if "Species" in l and "Host plant" in l:
        cols = (l.index("Species"), l.index("Host plant"), l.index("Previous/new"), l.index("References"))
        continue
    if cols is None or not l.strip(): continue
    if "Downloaded From" in l or "Terms of Use" in l or "SYSTEMATIC & APPLIED" in l or "continued on the next" in l: continue
    s0, h0, p0, r0 = cols
    sp, ho, pl, rf = l[s0 - 1:h0 - 3].strip(), l[h0 - 3:p0 - 3].strip(), l[p0 - 3:r0 - 3].strip(), l[r0 - 3:].strip()
    m = START.match(sp)
    if not m and re.fullmatch(r"[A-Z][a-z]{4,}", sp) and i + 1 < len(lines):
        nxt = lines[i + 1][s0 - 1:h0 - 3].strip()
        m2 = re.match(r"([a-z][a-z-]+)\b(.*)", nxt)
        if m2 and m2.group(1) not in ("et", "and", "al", "in", "sp"):
            flush(); cur = dict(family=fam, genus=sp, epithet=m2.group(1), auth=m2.group(2).strip(), host=ho, place=pl, ref=rf, skip=i + 1)
            continue
    if cur is not None and cur.get("skip") == i:
        cur["skip"] = None
        cur["host"] = (cur["host"] + " " + ho).strip(); cur["place"] = (cur["place"] + " " + pl).strip(); cur["ref"] = (cur["ref"] + " " + rf).strip()
        continue
    if m:
        flush(); cur = dict(family=fam, genus=m.group(1), epithet=m.group(2), auth=sp[m.end():].strip(), host=ho, place=pl, ref=rf)
    elif cur is not None and (sp or ho or pl or rf):
        cur["auth"] = (cur["auth"] + " " + sp).strip(); cur["host"] = (cur["host"] + " " + ho).strip()
        cur["place"] = (cur["place"] + " " + pl).strip(); cur["ref"] = (cur["ref"] + " " + rf).strip()
flush()
# the genus and epithet of this row sit two lines apart, so it was fused with the previous row; set by hand
for r in recs:
    if r["genus"] == "Colopodacus" and r["epithet"] == "roseusa":
        r["auth"] = "Mandal, Ghosh, Pramanik, Bala & Debnath 2025b"
        recs.insert(recs.index(r) + 1, dict(family=r["family"], genus="Brevishieldophyes", epithet="glochidionae",
            auth="Chakrabarti & Pandit 2009", host="Glochidion multiloculare (Phyllanthaceae)", place="Lataguri Forest (Jalpaiguri)", ref="Chakrabarti & Pandit 2009"))
        break
rows = []
for r in recs:
    y = re.findall(r"\b(1[89]\d\d|20[0-2]\d)[a-z]?\b", r["auth"])
    rows.append(dict(family=r["family"], species=f"{r['genus']} {r['epithet']}", authority=re.sub(r"[,\s]*\d{4}[a-z]?\*?$", "", r["auth"]).strip(),
                     year=y[-1] if y else "", host_raw=r["host"], wb_places=r["place"], reference=r["ref"],
                     new_wb_record=int("New record" in r["ref"] or r["auth"].rstrip().endswith("*") or "new" in r["ref"].lower())))
with open(OUT, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
import collections
print(len(rows), collections.Counter(r["family"] for r in rows), "-> ", OUT)
print("distinct names", len({r['species'] for r in rows}))
