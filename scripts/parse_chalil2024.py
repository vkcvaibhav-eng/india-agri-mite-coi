"""Parse the Tetranychidae checklist of Chalil et al. (2024).

Poolayulla Chalil, Suada, Sangeetha et al. 2024, Persian Journal of Acarology
13(1): 29-75, "Spider mites of India": 135 species with synonyms, type host,
type locality, Indian distribution by state, outside-India distribution, hosts.

Usage: parse_chalil2024.py <layout.txt from pdftotext -layout> [out.csv]
Check: the species count must equal the 135 stated in the abstract.
"""
import csv
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from states import clean_states  # noqa: E402

HEAD = re.compile(r"^\s*(\d{1,3})\.\s+([A-Z][a-z]+(?: \([A-Z][a-z]+\))? [a-z][\w-]*.*?)\s*$")
RUNNING = re.compile(r"SPIDER MITES OF INDIA|PERSIAN JOURNAL OF ACAROLOGY|POOLAYULLA CHALIL|^\s*(\d{4}\s+)?\d{2}\s*$")
LABEL = re.compile(r"^(Type hosts?|Type locality|Distribution|Outside India|Hosts?|Synonyms?)\s*[–-]?\s*:?\s*(.*)$")
NAME = re.compile(r"^(?P<name>[A-Z][a-z]+(?: \([A-Z][a-z]+\))? [a-z][\w-]*)\s+(?P<auth>.*?)(?:,\s*(?P<year>\d{4})[a-z]?)?\)?\s*$")


def main(src, out):
    lines = Path(src).read_text(errors="replace").splitlines()
    start = next(i for i, l in enumerate(lines) if HEAD.match(l) and "Bryobia eharai" in l)
    entries, cur, expect = [], None, 1
    for l in lines[start:]:
        if RUNNING.search(l) and not HEAD.match(l):
            continue
        m = HEAD.match(l)
        if m and int(m.group(1)) == expect:
            cur = {"n": expect, "head": m.group(2), "body": []}
            entries.append(cur)
            expect += 1
        elif cur is not None and re.match(r"^\s*DISCUSSION\b", l):
            cur = None
        elif cur is not None and l.strip():
            if re.match(r"^\s*(Tribe|Genus|Subfamily|References|Acknowledg)", l) and cur["body"] and LABEL.match(cur["body"][-1]) is None and False:
                pass
            cur["body"].append(l.strip())
    rows = []
    for e in entries:
        fields = {"syn": [], "Type host": "", "Type locality": "", "Distribution": "", "Outside India": "", "Host": ""}
        key = "syn"
        for l in e["body"]:
            if re.match(r"^(Tribe|Genus|Subfamily)\s", l) and key != "syn":
                break
            m = LABEL.match(l)
            if m:
                lab = m.group(1)
                key = {"Type hosts": "Type host", "Hosts": "Host", "Synonym": "syn", "Synonyms": "syn"}.get(lab, lab)
                txt = m.group(2)
                if key == "syn":
                    continue
                fields[key] = (fields[key] + " " + txt).strip()
                # "Outside India" often follows Distribution on the same line
            elif key == "syn":
                fields["syn"].append(l)
            else:
                fields[key] = (fields[key] + " " + l).strip()
        nm = NAME.match(e["head"])
        name = nm.group("name") if nm else e["head"]
        auth = nm.group("auth").strip(" ,(") if nm else ""
        year = nm.group("year") or "" if nm else ""
        parts = re.split(r"\s*Outside\s+India\s*[–-]?\s*", fields["Distribution"], maxsplit=1, flags=re.I)
        if len(parts) == 2:
            fields["Distribution"] = parts[0]
            fields["Outside India"] = (parts[1] + " " + fields["Outside India"]).strip()
        dist = fields["Distribution"].rstrip(". ")
        states, unmatched = clean_states(dist)
        syns = [s for s in fields["syn"] if " in: " not in s and not re.search(r"\sin:\s", s)]
        rows.append({
            "number": e["n"], "species": name, "authority": auth, "year": year,
            "heading_raw": e["head"], "synonyms_raw": " | ".join(syns),
            "type_host": fields["Type host"].rstrip("."), "type_locality": fields["Type locality"].rstrip("."),
            "india_states": "; ".join(states), "india_unmatched": "; ".join(unmatched),
            "india_distribution_raw": dist, "outside_india_raw": fields["Outside India"].rstrip("."),
            "host_raw": fields["Host"].rstrip("."),
            "needs_review": int(not states or bool(unmatched)),
        })
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"species parsed: {len(rows)} (abstract states 135)")
    print(f"with states: {sum(1 for r in rows if r['india_states'])}; flagged: {sum(r['needs_review'] for r in rows)}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "data/checklist/chalil2024_tetranychidae.csv")
