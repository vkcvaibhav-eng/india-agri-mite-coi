"""Named Tarsonemidae from two West Bengal papers.

Mondal et al. 2023, J. Insect Biodiversity and Systematics 9(2): 265-282: table of
38 morphospecies; the named ones carry the paper describing them.
Karmakar 2016, J. Acarological Society of Japan 25(S1): 77-81: 11 species, four of
them named (Table 1).
Species left as "sp." are not written out, since they have no valid name.
Authority and year of the Mondal species are those of the cited description, not
printed in the table, so they are not filled here.

Usage: parse_tarsonemidae_wb.py <mondal layout text> [out.csv]
"""
import csv
import re
import sys
from pathlib import Path

ROWRE = re.compile(r"^((?:[A-Z][a-z]+t|T)arsonemus)\s+([a-z]+)\s+((?:\d+\s+){6})\s*(.+?)\s*$")
KARMAKAR = [  # Karmakar 2016, Table 1, named species only
    ("Polyphagotarsonemus", "latus", "Banks", "Throughout West Bengal"),
    ("Steneotarsonemus", "spinki", "Smiley", "Throughout West Bengal"),
    ("Steneotarsonemus", "furcatus", "De Leon", "Sub-Himalayan and coastal zones"),
    ("Steneotarsonemus", "konoi", "Smiley & Emmanouel", "Throughout West Bengal"),
]
# Authority and year confirmed from Plazi treatments (tb.plazi.org) of the describing papers.
# Plazi prints Metatarsonemus sirishi both as "shirishi" (heading) and "sirishi" (text); Mondal 2023 uses "sirishi".
PLAZI = {
    "Bongotarsonemus bicornus": ("Mondal & Karmakar", "2021"), "Bongotarsonemus unicornus": ("Mondal & Karmakar", "2021"),
    "Ceratotarsonemus bengalicus": ("Karmakar & Kayal", "2022"), "Daidalotarsonemus tambulae": ("Karmakar & Mondal", "2023"),
    "Metatarsonemus badurkani": ("Karmakar & Mondal", "2021"), "Metatarsonemus sirishi": ("Karmakar & Mondal", "2021"),
    "Tarsonemus narkelae": ("Karmakar & Mondal", "2021"), "Tarsonemus mondouriensis": ("Karmakar & Ganguly", "2021"),
    "Steneotarsonemus amlisoae": ("Karmakar, Ganguly & Mondal", "2021"), "Steneotarsonemus indianensis": ("Karmakar & Mondal", "2021"),
    "Steneotarsonemus subfurcatus": ("Lin & Zhang", "1990"),
}
# Indian species found in the Plazi treatments that Mondal et al. 2023 does not list (not West Bengal-only claims).
EXTRA = [("Steneotarsonemus", "amlisoae", "Ganguly et al. 2021, Zootaxa 5023(3)"),
         ("Steneotarsonemus", "indianensis", "Mondal et al. 2021, Int. J. Acarol."),
         ("Steneotarsonemus", "subfurcatus", "Ganguly et al. 2022, Zootaxa 5138(5)")]
ZONES = ["Northern Hilly", "Teesta-Terai", "New Alluvial", "Old Alluvial", "Red & Laterite", "Coastal Saline"]


def main(src, out):
    rows = []
    for l in Path(src).read_text(errors="replace").splitlines():
        m = ROWRE.match(l.strip())
        if not m or m.group(2) == "sp":
            continue
        counts = [int(x) for x in m.group(3).split()]
        rows.append({
            "species": f"{m.group(1)} {m.group(2)}", "authority": "", "source": "Mondal et al. 2023",
            "described_in": m.group(4), "india_states": "West Bengal",
            "zones": "; ".join(z for z, c in zip(ZONES, counts) if c), "year": "",
        })
    for g, e, d in EXTRA:
        rows.append({"species": f"{g} {e}", "authority": "", "year": "", "source": "Plazi treatment", "described_in": d,
                     "india_states": "West Bengal", "zones": ""})
    for r in rows:
        if r["species"] in PLAZI:
            r["authority"], r["year"] = PLAZI[r["species"]]
        else:
            r.setdefault("year", "")
    for g, e, a, d in KARMAKAR:
        rows.append({"species": f"{g} {e}", "authority": a, "source": "Karmakar 2016", "described_in": "",
                     "india_states": "West Bengal", "zones": d, "year": ""})
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    print(f"named species: {len(rows)}; with authority: {sum(1 for r in rows if r['authority'])}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "data/checklist/tarsonemidae_west_bengal.csv")
