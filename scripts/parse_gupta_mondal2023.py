"""Names, authorities, hosts and Indian states from the digitized Gupta & Mondal (2023)
Handbook: Plant Mites of India (up to 2022). Input: structured OCR draft JSON
(species list). Output keeps only what the checklist needs, not account text."""
import json, re, csv, sys, os
sys.path.insert(0, os.path.dirname(__file__))
from states import clean_states

SRC = sys.argv[1] if len(sys.argv) > 1 else "/home/claude/src/gm2023/book.json"
OUT = "data/checklist/gupta_mondal2023_all.csv"

def first(v):
    if isinstance(v, list):
        return " ".join(str(x) for x in v)
    return v or ""

def india_part(text):
    m = re.search(r"India\s*\((.*?)\)", text, re.S)
    if m:
        return m.group(1)
    return text if re.match(r"\s*(India|Andhra|Assam|Bihar|Delhi|Gujarat|Karnataka|Kerala|Tamil|West Bengal|Maharashtra)", text) else ""

FAM = {"Eriophyidae": "Eriophyidae", "Diptilomiopidae": "Diptilomiopidae", "Phytoptidae": "Phytoptidae"}

d = json.load(open(SRC))
rows = []
for r in d["species"]:
    fam = ((r.get("taxonomy_from_book_headings") or {}).get("family") or {}).get("text_ocr") or r["family_as_printed"] or ""
    fam = re.sub(r"[, ]*\d{4}$", "", fam.split()[0]).capitalize() if fam else ""
    dist = first(r.get("distribution_text_ocr"))
    st, un = clean_states(india_part(dist))
    rows.append(dict(
        number=r["book_species_number"], section=r["section_id"], family=fam,
        genus=(r.get("genus_heading_ocr") or "").split()[0] if r.get("genus_heading_ocr") else "",
        species=(r.get("scientific_name") or "").strip(), authority=(r.get("authorship") or "").strip(),
        level=r["identification_level"], india_states=";".join(st), india_unmatched=";".join(un),
        distribution_raw=dist, host_raw=first(r.get("host_text_ocr")),
        flags=";".join(r.get("review_flags") or []), pages=",".join(str(p["book_page"]) for p in r["source_pages"]),
    ))
with open(OUT, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
print(len(rows), "rows ->", OUT)
