"""Mites recorded on medicinal plants in South Bengal, Gupta & Bose (2017).

Records of the Zoological Survey of India 117(2): 154-181. 120 species in 44
genera and 15 families; includes the nine Tenuipalpidae new to India. Numbered
species entries under "Family" and "Genus" headings, each with a collection-data
paragraph (district, host, date).

Entries named "sp." or "spp." are kept with a flag, not as valid names.

Usage: parse_gupta_bose2017.py <pdftotext raw text> [out.csv]
"""
import csv
import re
import sys
from pathlib import Path

FAMILY = re.compile(r"^Family\s+[IVX]+\.?\s+([A-Z]+)\b")
GENUS = re.compile(r"^Genus\s+([A-Z][a-z]+)")
ENTRY = re.compile(r"^(\d{1,3})\.\s+([A-Z][a-z]+)\s+((?:sp\.?|spp\.?|spn\.?)(?:\s+nr\.\s+[a-z]+)?|[a-z]{3,})\s*(.*)$")
# Two headings lose their italic species name in the text layer; read from the page images.
HAND = {93: ("Amblyseius", "coffeae", "De Leon"), 100: ("Euseius", "finlandicus", "(Oudemans)")}
# Genus headings missing from the printed text (spelled in the species line only).
EXTRA_GENERA = {"Gynaesius", "Typhlodromips"}
KEEP = {"TETRANYCHIDAE", "TENUIPALPIDAE", "TARSONEMIDAE", "ERIOPHYIDAE", "PHYTOSEIIDAE"}


def main(src, out):
    lines = [l.strip() for l in Path(src).read_text(errors="replace").splitlines()]
    family = None
    # genus names printed as headings anywhere; couplets of the keys start with other words
    genera = {m.group(1) for l in lines if (m := GENUS.match(l))} | EXTRA_GENERA
    entries = []
    for i, l in enumerate(lines):
        if m := FAMILY.match(l):
            family = m.group(1)
            continue
        hm = re.match(r"^(\d{1,3})\.$", l)
        if hm and int(hm.group(1)) in HAND and family:
            g, ep, au = HAND[int(hm.group(1))]
            entries.append({"i": i, "n": int(hm.group(1)), "family": family, "genus": g, "epithet": ep, "rest": au})
            continue
        m = ENTRY.match(l)
        if m and family and m.group(2) in genera and any("Collection data" in x for x in lines[i + 1:i + 45]):
            entries.append({"i": i, "n": int(m.group(1)), "family": family, "genus": m.group(2),
                            "epithet": m.group(3), "rest": m.group(4)})
    rows = []
    for k, e in enumerate(entries):
        end = entries[k + 1]["i"] if k + 1 < len(entries) else len(lines)
        block = " ".join(lines[e["i"]:end])
        cd = re.search(r"Collection data:(.*?)(?:Remarks|Genus |Family |$)", block)
        cd = re.sub(r"\s+", " ", cd.group(1)).strip() if cd else ""
        hosts = sorted(set(h.strip(" ,.") for h in re.findall(r"ex\.\s+([A-Z][a-z]+(?: [a-z]+)?)", cd)))
        districts = sorted(set(re.findall(r"(South 24 Parganas|North 24 Parganas|Howrah|Hooghly|Nadia|Bardhaman|"
                                           r"East Medinipur|West Medinipur|Birbhum|Bankura|Purulia)", cd)))
        sp = e["epithet"].startswith(("sp", "spp", "spn"))
        rows.append({
            "number": e["n"], "family": e["family"].capitalize(), "genus": e["genus"],
            "species": "" if sp else f"{e['genus']} {e['epithet']}",
            "authority": "" if sp else re.sub(r"\s+", " ", e["rest"]).strip(" ,"),
            "unnamed_sp": int(sp), "india_states": "West Bengal", "districts": "; ".join(districts),
            "hosts_raw": "; ".join(hosts),
            "in_scope_family": int(e["family"] in KEEP),
        })
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    named = [r for r in rows if not r["unnamed_sp"]]
    print(f"entries: {len(rows)}; named species: {len(named)}; in the six-family scope: {sum(r['in_scope_family'] for r in named)}")
    import collections
    print(dict(collections.Counter(r["family"] for r in named if r["in_scope_family"])))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "data/checklist/gupta_bose2017_south_bengal.csv")
