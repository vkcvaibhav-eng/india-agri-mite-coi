"""Names, authorities, hosts and Indian states from the digitized Gupta & Mondal (2023)
Handbook: Plant Mites of India (up to 2022). Input: structured OCR draft JSON
(species list). Output keeps only what the checklist needs, not account text."""
import json, re, csv, sys, os, difflib
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
from names import parse, parse_cited, display, stem


def citation_texts(r):
    oc = r.get("original_citation") if isinstance(r.get("original_citation"), dict) else {}
    texts = [oc.get("citation_text_ocr") or oc.get("scientific_name_ocr") or ""]
    return texts + [c.get("citation_text_ocr") or "" for c in (r.get("citations") or [])
                    if c.get("citation_kind") == "taxonomic_citation"]


def cited_names(r):
    """Names that open the book's taxonomic citations for an entry, as
    Name|Author|Year: the original combination and later combinations or synonyms.
    Author and year are given only where the citation reads 'Name Author, Year';
    'Name, Author, Year' is a later use of the name and gets neither."""
    out = []
    for t in citation_texts(r):
        name, auth, year = parse_cited(t)
        if name:
            item = f"{display(*name)}|{auth}|{year}"
            if item not in out:
                out.append(item)
    return ";".join(out)


def year_of(r):
    """Year of the name: from the first citation that gives an authority for the
    same epithet, so that a later use of the name does not supply the year."""
    me = parse(r.get("scientific_name") or "")
    for t in citation_texts(r):
        name, auth, year = parse_cited(t)
        if name and me and year and difflib.SequenceMatcher(None, stem(name[2]), stem(me[2])).ratio() >= 0.8:
            return year
    return ""

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
        year=year_of(r), level=r["identification_level"], india_states=";".join(st), india_unmatched=";".join(un),
        distribution_raw=dist, host_raw=first(r.get("host_text_ocr")),
        flags=";".join(r.get("review_flags") or []), pages=",".join(str(p["book_page"]) for p in r["source_pages"]),
        citation_names=cited_names(r),
    ))
with open(OUT, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
print(len(rows), "rows ->", OUT)
