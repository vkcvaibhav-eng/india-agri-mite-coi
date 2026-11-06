"""Parse the Tamil Nadu eriophyoid checklist of Dyamanagouda et al. (2020).

Dyamanagouda, Vishnupriya, Ramaraju & Mohankumar 2020. Journal of Entomology and
Zoology Studies 8(6): 137-146. Check: 73 genera, 281 species (Eriophyidae 252,
Phytoptidae 2, Diptilomiopidae 27). Every species is a Tamil Nadu record; the
list gives host plant and the citation but no other state.

Usage: parse_dyamanagouda2020.py <layout text> [out.csv]
"""
import csv
import re
import sys
from pathlib import Path

GENUS = re.compile(r"^\s*(\d{1,3})\)\s*Genus\s*:\s*([A-Z][a-z]+)\s*(.*)$")
FAMILY = re.compile(r"^\s*Family\s*:\s*([A-Z][a-z]+)")
SUBFAM = re.compile(r"^\s*Sub\s?[Ff]amily\s*:\s*([A-Z][a-z]+)")
ROW = re.compile(r"^\s*(\d{1,3})\.?(?:(\s+)(.*))?$")
# The source prints only "Family: Eriophyidae"; the later subfamilies belong to the
# other two families (counts match the paper: 252 / 2 / 27 species).
FAMILY_OF_SUBFAMILY = {"Phytoptinae": "Phytoptidae", "Sierraphytoptinae": "Phytoptidae",
                       "Diptilomiopinae": "Diptilomiopidae", "Rhyncaphytoptinae": "Diptilomiopidae"}
# Rows whose epithet, author or year sit on lines the column layout scatters
# around the number; values read by hand from the printed table.
UM = "Umapathy and Mohanasundaram"
OVERRIDES = {
    68: ("integrifoliavagrans", "Mohanasundaram", "1983"), 74: ("immigrans", "Kiefer", "1940"),
    119: ("allophylae", UM, "2000"), 122: ("apodytae", UM, "2000"), 123: ("ariyankavensis", UM, "2000"),
    124: ("articulate", UM, "2000"), 127: ("attakattiensis", UM, "2000"),
    140: ("cymbopogonis", "Mohanasundaram and Subramaniam", "1978"),
    154: ("guerreronis", "Keifer", "1965"), 157: ("justiciae", "Mohanasundaram", "1982"),
    169: ("marudamalaiensis", "Mohanasundaram", "1990"), 181: ("sapindi", "Channabasavanna", "1966"),
    211: ("hexandrae", UM, "1999"), 217: ("rosae", "Mohanasundaram", "1981"),
    218: ("rotundae", "Mohanasundaram", "1983"), 231: ("chebulae", "Mohanasundaram", "1980"),
    256: ("carmonae", UM, "2002"), 268: ("attakattiensis", UM, "2002"),
}
YEAR = re.compile(r"((?:1[89]|20)\d{2})\d?")


def chunks(line):
    if line.startswith("      "):
        parts = [""] + re.split(r"\s{3,}", line.strip())
    else:
        parts = re.split(r"\s{3,}", line.strip())
    return parts[0], (parts[1] if len(parts) > 1 else ""), (parts[2] if len(parts) > 2 else "")


def main(src, out):
    lines = Path(src).read_text(errors="replace").splitlines()
    start = next(i for i, l in enumerate(lines) if FAMILY.match(l))
    end = next(i for i, l in enumerate(lines) if re.match(r"^\s*References", l) and i > start)
    family = sub = genus = None
    blocks, cur, pre = [], None, []
    expect = 1
    body = [l for l in lines[start:end]
            if l.strip() and "entomoljournal" not in l and "Journal of Entomology" not in l
            and not re.match(r"^\s*~\s*\d+\s*~", l)]
    for i, l in enumerate(body):
        if re.match(r"^\s*Conclusion", l):
            break
        if m := FAMILY.match(l):
            family = m.group(1); continue
        if m := SUBFAM.match(l):
            sub = m.group(1); continue
        if m := GENUS.match(l):
            genus = m.group(2); continue
        m = ROW.match(l)
        if m and int(m.group(1)) == expect:
            cur = {"n": expect, "family": family, "subfamily": sub, "genus": genus,
                   "lines": list(pre) + ([m.group(3)] if m.group(3) else [])}
            pre = []
            blocks.append(cur)
            expect += 1
            continue
        nm = ROW.match(body[i + 1]) if i + 1 < len(body) else None
        # an epithet (or epithet + author) printed on the line above its number; only
        # when the numbered line itself does not start with an epithet, so that a
        # wrapped host name ("Justicia glabra") stays with the row above
        own = (nm.group(3) or "").strip() if nm else ""
        if nm and int(nm.group(1)) == expect and not re.match(r"^[a-z]", own) and re.match(r"^\s*[a-z]", l):
            pre.append(l.strip())
        elif cur is not None:
            cur["lines"].append(l.strip())
    rows = []
    for b in blocks:
        txt = re.sub(r"\s+", " ", " ".join(b["lines"]))
        m = re.match(r"^([A-Z]?[a-z]+)", txt)
        epithet = m.group(1).lower() if m else ""
        rest = txt[m.end():] if m else txt
        am = re.search(r"((?:[A-Z][\w.]*)(?:\s*(?:,|and|&)?\s*[A-Z][\w.]*)*)\s*,\s*((?:1[89]|20)\d{2})\d?\b", rest)
        auth, year = (am.group(1).strip(), am.group(2)) if am else ("", "")
        if b["n"] in OVERRIDES:
            epithet, auth, year = OVERRIDES[b["n"]]
        hm = re.search(r"(Unidentified[^;]*?(?=\s+[A-Z][a-z]+ (?:and|\(|[A-Z])|$)|[A-Z][a-z]+(?: [a-z.]+)*\s*\([A-Z][a-z]+\))", rest)
        rows.append({
            "number": b["n"], "family": FAMILY_OF_SUBFAMILY.get(b["subfamily"], b["family"]),
            "subfamily": b["subfamily"], "genus": b["genus"],
            "species_epithet": epithet, "species": f"{b['genus']} {epithet}" if epithet else "",
            "authority": auth, "year": year, "host_raw": hm.group(1).strip() if hm else "",
            "row_raw": txt[:250], "india_states": "Tamil Nadu",
            "needs_review": int(not (epithet and year)),
        })
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)
    fam = {}
    for r in rows:
        fam.setdefault(r["family"], set()).add(r["genus"])
    print(f"species: {len(rows)} (paper: 281); genera: {len({r['genus'] for r in rows})} (paper: 73)")
    for k, v in fam.items():
        print(" ", k, len(v), "genera,", sum(1 for r in rows if r["family"] == k), "species")
    print("flagged:", sum(r["needs_review"] for r in rows))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "data/checklist/dyamanagouda2020_eriophyoidea_tamilnadu.csv")
