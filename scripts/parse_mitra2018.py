"""Tenuipalpidae recorded from southern West Bengal, Mitra, Acharya & Ghosh (2018).

Acarologia 58(4): 850-854. Short note: 17 species, six of them new records for
India (Brevipalpus melichrus, B. mitrofanovi, B. turrialbensis, Cenopalpus
picitilis, Tenuipalpus crassulus, T. leipoldti). The introduction states that 102
species in 15 genera were then known from India (Gupta & Mandal 2015), the source
to look for next.

Usage: parse_mitra2018.py <pdftotext -layout text> [out.csv]
"""
import csv
import re
import sys
from pathlib import Path

HEAD = re.compile(r"^\s+([A-Z][a-z]+) ([a-z][a-z-]+) \(?([A-Z][\w &.,-]+?),? (\d{4})\)?\s*$")


def main(src, out):
    lines = Path(src).read_text(errors="replace").splitlines()
    rows, cur = [], None
    for i, l in enumerate(lines):
        m = HEAD.match(l)
        nxt = " ".join(x.strip() for x in lines[i + 1:i + 3])
        if m and nxt.startswith("Material examined"):
            cur = {"species": f"{m.group(1)} {m.group(2)}", "authority": m.group(3).strip(" ,("), "year": m.group(4),
                   "text": ""}
            rows.append(cur)
        elif cur is not None:
            cur["text"] += " " + l.strip()
    result = []
    for r in rows:
        t = re.sub(r"\s+", " ", r["text"])
        hosts = sorted(set(re.findall(r"on ([A-Z][a-z]+(?: [a-z.-]+)+?)(?: L\.| Jacq\.| Willd\.| Retz\.| Lam\.|,| \d| \(|;|\.|$)", t)))
        dist = re.search(r"Distribution — (.*?)(?:Remarks|Acknowledgements|Brevipalpus|Cenopalpus|Tenuipalpus|Mitra S\.|$)", t)
        localities = re.findall(r"\d+♀(?: and \d+♂)?,? ([A-Z][\w ]+?) \[", t)
        result.append({
            "species": r["species"], "authority": r["authority"], "year": r["year"],
            "india_states": "West Bengal", "localities": "; ".join(dict.fromkeys(localities)),
            "hosts_raw": "; ".join(hosts),
            "distribution_raw": dist.group(1).strip(" .") if dist else "",
            "new_record_india": int("New record from India" in t),
        })
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(result[0])); w.writeheader(); w.writerows(result)
    print(f"species: {len(result)} (paper: 17); new records for India: {sum(r['new_record_india'] for r in result)} (paper: 6)")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "data/checklist/mitra2018_tenuipalpidae_west_bengal.csv")
