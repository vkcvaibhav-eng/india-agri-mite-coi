"""Parse the Indian Tenuipalpidae checklist of Mitra (2025).

Mitra, S. 2025. Checklist of flat mites (Acari: Tenuipalpidae) and new host plant
records from India. International Journal of Tropical Insect Science 45:
1041-1055. https://doi.org/10.1007/s42690-025-01491-x
Check: 101 species in 15 genera (Tenuipalpus 47, Brevipalpus 19, ...).

Each numbered entry: name and authority, citations, "Host plants:",
"Distribution: India (states), other countries".

Usage: parse_mitra2025.py <pdftotext raw text> [out.csv]
"""
import csv
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from states import clean_states  # noqa: E402

# genus may be glued to the epithet in the text layer ("Brevipalpusnangalensis")
GENERA = ["Aegyptobia", "Brevipalpus", "Cenopalpus", "Dolichotetranychus", "Dolichoetranychus", "Krugeria",
          "Larvacarus", "Obuloides", "Pentamerismus", "Phytoptipalpus", "Priscapalpus", "Raoiella",
          "Tenuilichus", "Tenuipalpus", "Terminalichus", "Ultratenuipalpus"]
FIX_GENUS = {"Dolichoetranychus": "Dolichotetranychus"}
HEAD = re.compile(r"^(\d{1,3})\.\s*(" + "|".join(GENERA) + r")\s*(\(?[A-Z][a-z]+\)?\s+)?([a-z][a-z-]+)\s*(.*)$")
NOISE = re.compile(r"International Journal of Tropical Insect Science|^\d{4}$|^\s*$")
EXPECT = {"Tenuipalpus": 47, "Brevipalpus": 19, "Dolichotetranychus": 7, "Terminalichus": 6, "Aegyptobia": 4,
          "Raoiella": 4, "Ultratenuipalpus": 3, "Cenopalpus": 2, "Priscapalpus": 2, "Tenuilichus": 2,
          "Krugeria": 1, "Larvacarus": 1, "Obuloides": 1, "Pentamerismus": 1, "Phytoptipalpus": 1}


def main(src, out):
    lines = [l.strip() for l in Path(src).read_text(errors="replace").splitlines()]
    end = next(i for i, l in enumerate(lines) if re.match(r"^(Discussion|Conclusion|Acknowledg)", l) and i > 100)
    entries, cur = [], None
    for l in lines[:end]:
        m = HEAD.match(l)
        # the two-column text flow interleaves some entries (83, 90, 84, 91 ...), so accept any unseen number
        if m and 1 <= int(m.group(1)) <= 101:
            if int(m.group(1)) not in {e["n"] for e in entries}:
                cur = {"n": int(m.group(1)), "genus": FIX_GENUS.get(m.group(2), m.group(2)),
                       "subgenus": (m.group(3) or "").strip(" ()"), "epithet": m.group(4), "auth": m.group(5), "body": []}
                entries.append(cur)
                continue
        if cur is not None and not NOISE.search(l) and not l.startswith("Genus"):
            cur["body"].append(l)
    rows = []
    for e in entries:
        t = re.sub(r"\s+", " ", " ".join(e["body"]))
        auth = e["auth"]
        if not re.search(r"\d{4}", auth) and e["body"]:          # authority wrapped onto the next line
            auth = (auth + " " + e["body"][0]).strip()
        ym = re.search(r"(1[789]\d{2}|20[0-2]\d)", auth)
        hosts = re.search(r"Host plants?:\s*(.*?)(?:Distribution:|$)", t)
        dist = re.search(r"Distribution:\s*(.*?)(?:Remarks?:|$)", t)
        dist = dist.group(1).strip(" .") if dist else ""
        ind = re.search(r"India\s*\(([^)]*)\)", dist)
        states, unmatched = clean_states(ind.group(1)) if ind else ([], [])
        outside = re.sub(r"India\s*\([^)]*\)\s*(,|and)?", "", dist).strip(" ,.")
        rows.append({
            "number": e["n"], "genus": e["genus"], "species": f"{e['genus']} {e['epithet']}",
            "authority": re.sub(r"[\s,]*(1[789]\d{2}|20[0-2]\d)[a-z]?.*$", "", auth).strip(" ,()"),
            "year": ym.group(1) if ym else "",
            "india_states": "; ".join(states), "india_unmatched": "; ".join(unmatched),
            "outside_india_raw": outside, "host_raw": hosts.group(1).strip(" .") if hosts else "",
            "needs_review": int(not (ym and states) or bool(unmatched)),
        })
    rows.sort(key=lambda r: r["number"])
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    c = Counter(r["genus"] for r in rows)
    print(f"species: {len(rows)} (paper: 101); genera: {len(c)} (paper: 15); flagged: {sum(r['needs_review'] for r in rows)}")
    print("genus counts differing from abstract:", {g: (c.get(g, 0), n) for g, n in EXPECT.items() if c.get(g, 0) != n})


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "data/checklist/mitra2025_tenuipalpidae_india.csv")
