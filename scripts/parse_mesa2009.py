"""Tenuipalpidae with an Indian type locality, from Mesa et al. (2009).

Mesa, Ochoa, Welbourn, Evans & De Moraes 2009. A catalog of the Tenuipalpidae
(Acari) of the world with a key to genera. Zootaxa 2098: 1-185.

Appendix A lists each species with the country of its original description, so
the species it codes IND are those *described from India*. It does not list every
Indian record: a species described elsewhere (Brevipalpus phoenicis,
B. californicus, Raoiella indica ...) appears only if India was its type country.
`cited_by_indian_author` flags catalogue entries whose redescriptions cite an
Indian acarologist; it marks a lead to check, not a confirmed Indian record.

Usage: parse_mesa2009.py <pdftotext -layout text> [out.csv]
"""
import csv
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from states import clean_states  # noqa: E402

ENTRY = re.compile(r"^(\d{1,4})([a-z]?)\.\s+([A-Z][a-z]+)\s+([a-z][a-z-]+)\s+(.*)$")
IND_AUTHORS = ["Gupta", "Sadana", "Channabasavanna", "Ghai", "Mohanasundaram", "Chatterjee", "Prasad",
               "Bindra", "Mondal", "Chakrabarti", "Nassar", "Narayanan", "Rahman", "Sapra", "Anwarullah"]


def main(src, out):
    lines = Path(src).read_text(errors="replace").splitlines()
    app = [i for i, l in enumerate(lines) if l.startswith("APPENDIX A")][-1]  # first hit is the contents page
    # Appendix A: genus heading, then species lines carrying a country code per region column
    genus, ind = None, {}
    for l in lines[app:]:
        if re.match(r"^\s*APPENDIX B", l):
            break
        if re.match(r"^\s{20,}[A-Z][a-z]+\s*$", l):
            genus = l.strip(); continue
        m = re.match(r"^\s+([a-z][\w-]+)\s{2,}.*?\bIND\b\s+(.+?)\s*$", l)
        if m and genus:
            ind[(genus, m.group(1))] = m.group(2)
    # main catalogue entries
    entries, cur = {}, None
    for l in lines[:app]:
        m = ENTRY.match(l.strip())
        if m:
            cur = {"n": m.group(1) + m.group(2), "text": m.group(5), "synonym": bool(m.group(2))}
            entries[(m.group(3), m.group(4))] = cur
        elif cur is not None and l.strip() and not l.startswith("Type Depository"):
            cur["text"] += " " + l.strip()
    rows = []
    for (g, e), fam in sorted(ind.items()):
        ent = entries.get((g, e))
        t = re.sub(r"\s+", " ", ent["text"]) if ent else ""
        am = re.match(r"^(.*?),\s*(\d{4})[a-z]?(?::\s*[\d\w-]+)?;\s*(.*?)(?:,\s*ex\s+(.*?))?(?:\.|—|$)", t)
        rows.append({
            "species": f"{g} {e}", "authority": am.group(1) if am else "", "year": am.group(2) if am else "",
            "type_locality": am.group(3).strip() if am else "", "type_host": (am.group(4) or "").strip() if am else "",
            "host_family_appendix": fam, "catalogue_no": ent["n"] if ent else "",
            "status": "synonym" if ent and ent["synonym"] else "valid",
            "india_states": "; ".join(clean_states(am.group(3))[0]) if am else "", "needs_review": int(not (ent and am)),
        })
    cited = set()
    for (g, e), ent in entries.items():
        if (g, e) not in ind and any(re.search(rf"\b{a}\b", ent["text"]) for a in IND_AUTHORS):
            cited.add((g, e))
    leads = out.replace(".csv", "_leads.csv")
    with open(leads, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["species", "catalogue_no", "entry_start"])
        for g, e in sorted(cited):
            w.writerow([f"{g} {e}", entries[(g, e)]["n"], re.sub(r"\s+", " ", entries[(g, e)]["text"])[:160]])
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    print(f"species described from India (IND in Appendix A): {len(ind)}; matched to catalogue entries: {sum(1 for r in rows if r['catalogue_no'])}")
    print(f"other entries citing an Indian author (leads, not in output): {len(cited)}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "data/checklist/mesa2009_tenuipalpidae_india_types.csv")
