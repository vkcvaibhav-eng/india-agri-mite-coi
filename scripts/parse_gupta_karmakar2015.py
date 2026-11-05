"""Parse the Phytoseiidae checklist of Gupta & Karmakar (2015).

Gupta, S.K. & Karmakar, K. 2015. An updated checklist of Indian phytoseiid
mites (Acari: Mesostigmata). Records of the Zoological Survey of India 115(1):
51-72. States the total as 211 species in 21 genera.

The list gives only citations (no states, hosts or localities). Species are
numbered entries "N. epithet (Author), year: page; ..." under genus headings.
Entries starting with a capital letter (genus and subgenus notes) are skipped.

Usage: parse_gupta_karmakar2015.py <pdftotext raw text> [out.csv]
"""
import csv
import re
import sys
from pathlib import Path

GENUS = re.compile(r"^Genus\s+([A-Z][a-z]+)\b")
SUBFAM = re.compile(r"^Subfamily\s+([A-Z]+)")
ENTRY = re.compile(r"^(\d{1,3})\.\s+([a-z][a-z-]+),?(?:\s+(.*))?$")
YEAR = re.compile(r"^(?P<auth>.*?)[,\s]+\(?(?P<year>1[89]\d{2}|20[01]\d)[a-z]?\b")


def main(src, out):
    lines = [l.strip() for l in Path(src).read_text(errors="replace").splitlines()]
    genus = subfam = None
    entries = []
    for i, l in enumerate(lines):
        m = SUBFAM.match(l)
        if m:
            subfam = m.group(1).capitalize()
        m = GENUS.match(l)
        if m:
            genus = m.group(1)
            continue
        m = ENTRY.match(l)
        if m and genus:
            n, epithet, rest = int(m.group(1)), m.group(2), m.group(3) or ""
            text = rest
            for nxt in lines[i + 1:i + 6]:
                if re.search(r"\d{4}", text):
                    break
                text = (text + " " + nxt).strip()
            ym = YEAR.match(text)
            auth = ym.group("auth").strip(" ,()") if ym else ""
            year = ym.group("year") if ym else ""
            entries.append({
                "number": n, "subfamily": subfam, "genus": genus, "species_epithet": epithet,
                "species": f"{genus} {epithet}", "authority": auth, "year": year,
                "citation_raw": text[:200],
                "needs_review": int(not year),
            })
    seen, rows = set(), []
    for e in entries:
        k = e["species"]
        if k in seen:
            continue
        seen.add(k)
        rows.append(e)
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    nums = sorted(e["number"] for e in entries)
    print(f"entries: {len(entries)}; unique species: {len(rows)} (paper states 211)")
    print(f"genera: {len({r['genus'] for r in rows})} (paper states 21); no year: {sum(r['needs_review'] for r in rows)}")
    print("max number:", nums[-1])


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "data/checklist/gupta_karmakar2015_phytoseiidae.csv")
