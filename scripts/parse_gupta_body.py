"""Stage 1b: pull author, year, hosts and Indian state records for each of the 557
species out of the body of Gupta (1985), Handbook: Plant Mites of India.

Needs data/checklist/gupta1985_contents.csv from parse_gupta_contents.py.

Each species entry runs: its number alone on a line, the name and author, the
synonymy (first line carries the original description and year), then Diagnosis,
Host or Habitat, and a closing line `Distribution: INDIA: <states>; outside India: ...`.

Pages are read in layout mode: in raw reading order the label "Distribution:" is
separated from its value. Species are located by the printed page the contents give for them (PDF page =
printed page + 38). Where OCR has damaged the number, the contents name is matched
fuzzily on the same pages. Positions must come out in strictly increasing order;
the script stops if they do not.

  python scripts/parse_gupta_body.py /path/to/Gupta_1985.pdf

Writes data/checklist/gupta1985_species.csv. Text is kept as OCR read it.
"""
import csv
import difflib
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTENTS = ROOT / "data" / "checklist" / "gupta1985_contents.csv"
OUT = ROOT / "data" / "checklist" / "gupta1985_species.csv"

OFFSET = 38                       # PDF page minus printed page
FIRST_BODY, LAST_BODY = 41, 452

RUNNING = re.compile(
    r"^\s*(HANDBOOK\s*:?.*|Plant\s+mites\s+of\s+India|Zoological\s+Survey\s+[DOo]f\s+India|\d{1,3})\s*$",
    re.I)
INDIA = re.compile(r"[Il1]\s*N\s*[DdOo]\s*[Il1]\s*A\s*:", re.I)
OUTSIDE = re.compile(r"out\s*side\s+[Il1]ndia\s*:", re.I)
YEAR = re.compile(r"\b(1[789]\d\d)[a-z]?\b")
CAPTION = re.compile(
    r"^\s*\d+\s*[\.,:;]+\s*(Dorsum|Venter|Tibia|Female|Male|Fig|Leg|Palp|Gnath|Genit|Propod|Rostr|Spermat)", re.I)

# States and territories as the book names them (1985 boundaries). Each key is a
# spelling or OCR-damaged form already seen; everything else is matched fuzzily.
STATES = {
    "Andhra Pradesh": ["andhrapradesh", "ap"],
    "Arunachal Pradesh": ["arunachalpradesh", "nefa"],
    "Assam": ["assam"],
    "Bihar": ["bihar"],
    "Delhi": ["delhi", "newdelhi"],
    "Goa": ["goa"],
    "Gujarat": ["gujarat"],
    "Haryana": ["haryana"],
    "Himachal Pradesh": ["himachalpradesh", "hp"],
    "Jammu & Kashmir": ["jammukashmir", "jammu", "kashmir", "jk"],
    "Karnataka": ["karnataka", "kamataka", "mysore"],
    "Kerala": ["kerala"],
    "Madhya Pradesh": ["madhyapradesh", "mp"],
    "Maharashtra": ["maharashtra"],
    "Manipur": ["manipur"],
    "Meghalaya": ["meghalaya"],
    "Mizoram": ["mizoram"],
    "Nagaland": ["nagaland"],
    "Orissa": ["orissa", "odisha"],
    "Punjab": ["punjab"],
    "Rajasthan": ["rajasthan"],
    "Sikkim": ["sikkim"],
    "Tamil Nadu": ["tamilnadu", "madras"],
    "Tripura": ["tripura"],
    "Uttar Pradesh": ["uttarpradesh", "up"],
    "West Bengal": ["westbengal", "wbengal", "bengal"],
    "Andaman & Nicobar Islands": ["andaman", "nicobar", "carnicobar", "andamannicobar"],
    "Pondicherry": ["pondicherry", "pondichery"],
    "Chandigarh": ["chandigarh"],
    "Lakshadweep": ["lakshadweep", "laccadive"],
}
STATE_KEYS = {alias: name for name, aliases in STATES.items() for alias in aliases}
STOP = re.compile(
    r"^(Remarks|Rernarks|Nature\s+of\s+damage|Bionomics|Biology|Control|Economic|Host|Habitat|Genus|"
    r"Subgenus|Tribe|Subfam|Fam\.|Figs?\.?|Diagnosis|Key|Order|Distri\w*)\b", re.I)


def state_of(token):
    """One state name from a piece of OCR text, or '' if it does not look like one."""
    t = re.sub(r"[^a-z]", "", token.lower().replace("&", ""))
    if len(t) > 6 and t.endswith(("isis", "islands", "island", "isi", "isl", "is")) and not t.endswith(("assam",)):
        stripped = re.sub(r"(isis|islands?|isi|isl|is)$", "", t)
        t = stripped if len(stripped) >= 5 else t
    if t.startswith(("nicob", "andam", "carnic")):
        return "Andaman & Nicobar Islands"
    if t in STATE_KEYS:
        return STATE_KEYS[t]
    if len(t) < 4:
        return ""
    hit = difflib.get_close_matches(t, [k for k in STATE_KEYS if len(k) > 3], n=1, cutoff=0.74 if len(t) >= 8 else 0.82)
    return STATE_KEYS[hit[0]] if hit else ""


def read_pages(pdf):
    pages = {}
    for p in range(FIRST_BODY, LAST_BODY + 1):
        text = subprocess.run(["pdftotext", "-layout", "-f", str(p), "-l", str(p), str(pdf), "-"],
                              capture_output=True, text=True, check=True).stdout
        pages[p] = text.split("\n")
    return pages


def norm(s):
    return re.sub(r"[^a-z]", "", s.lower())


def locate(rows, pages):
    last, printed = None, {}
    for r in rows:
        n = int(r["number"])
        if r["printed_page"].isdigit():
            last = int(r["printed_page"])
        printed[n] = last
    found = {}
    for r in rows:                                   # pass 1: the bare number line
        n = int(r["number"])
        pat = re.compile(rf"^\s*{n}\s*[\.,:;]{{1,2}}\s*(\S.*)?$")
        for pg in (printed[n] + OFFSET, printed[n] + OFFSET + 1, printed[n] + OFFSET - 1, printed[n] + OFFSET + 2):
            lines = pages.get(pg, [])
            for i, line in enumerate(lines):
                if pat.match(line) and not CAPTION.match(line):
                    ahead = " ".join(x for x in lines[i:i + 6] if x.strip())
                    if re.search(r"[A-Z]\w*\s*\(?\w*\)?\s*[a-z]{4,}", ahead):
                        found[n] = (pg, i)
                        break
            if n in found:
                break
    for r in rows:                                   # pass 2: fuzzy name match
        n = int(r["number"])
        if n in found:
            continue
        target, best = norm(r["name_ocr"]), (0.0, None)
        for pg in range(printed[n] + OFFSET - 1, printed[n] + OFFSET + 4):
            for i, line in enumerate(pages.get(pg, [])):
                if len(line.strip()) < 8:
                    continue
                cand = norm(re.sub(r"^\s*\d+\s*[\.,:;]*", "", line))
                if cand:
                    ratio = difflib.SequenceMatcher(None, target, cand[:len(target) + 6]).ratio()
                    if ratio > best[0]:
                        best = (ratio, (pg, i))
        if best[0] >= 0.72:
            found[n] = best[1]
            found[f"fuzzy{n}"] = round(best[0], 2)
    return found


def entry_lines(pages, start, end):
    """Lines from one heading to the next, across pages, minus running heads."""
    out = []
    for pg in range(start[0], (end[0] if end else start[0]) + 1):
        lines = pages.get(pg, [])
        lo = start[1] if pg == start[0] else 0
        hi = end[1] if end and pg == end[0] else len(lines)
        out.extend(l for l in lines[lo:hi] if not RUNNING.match(l))
    return out


def clean_states(text):
    """Split an INDIA: list into canonical states; return (states, unmatched pieces)."""
    states, unmatched = [], []
    text = re.sub(r"\s+", " ", text).strip(" .;")
    for short, full in ((r"\bU\s*\.?\s*[Pp]\b\.?", "Uttar Pradesh"), (r"\bM\s*\.?\s*P\b\.?", "Madhya Pradesh"),
                        (r"\bH\s*\.?\s*[Pp]\b\.?", "Himachal Pradesh"), (r"\bA\s*\.?\s*P\b\.?", "Andhra Pradesh"),
                        (r"\bJ\s*\.?\s*&\.?\s*K\b\.?", "Jammu & Kashmir"), (r"\bW\s*\.\s*Bengal", "West Bengal"),
                        (r"Jammu\s*&\.?\s*Kashmir", "Jammu & Kashmir")):
        text = re.sub(short, full, text)
    for part in re.split(r"[,;]|\sand\s|\.\s", text):
        piece = part.strip(" .:()'\"?-_")
        if not piece:
            continue
        name = state_of(piece)
        if name:
            if name not in states:
                states.append(name)
        elif len(piece) > 2:
            unmatched.append(piece)
    return states, unmatched


def is_label(text, word, cutoff=0.72):
    """True if `text` (the part of a line before its colon) reads as the label `word`."""
    t = re.sub(r"[^a-z]", "", text.lower())
    return 4 <= len(t) <= len(word) + 4 and difflib.SequenceMatcher(None, t, word).ratio() >= cutoff


def collect(lines, word, plural=False):
    """Text of a labelled field: from the label to the next label or blank line.

    The label must be followed by a colon (or, for Distribution, run straight into
    'INDIA:'), so ordinary words such as 'distributed' inside a diagnosis do not count.
    """
    for i, line in enumerate(lines):
        m = re.match(r"^\s*([^:;,]{3,22}?)\s*[:;,]\s*(.*)$", line)
        first = None
        if m and is_label(m.group(1), word):
            first = m.group(2)
        elif plural and m and is_label(m.group(1), word + "s"):
            first = m.group(2)
        elif word == "distribution":
            nc = re.match(r"^\s*(Dis\w{3,9})\s+(?:\S\s+)?([Il1]N[DO0Il1]\w{0,2}\s*[:;!].*)$", line)
            if nc and is_label(nc.group(1), word):
                first = nc.group(2)
        if first is None:
            continue
        parts = [first]
        if word == "distribution":
            # OCR sometimes sets the INDIA part on the line above its own label
            before = next((l.strip() for l in reversed(lines[:i]) if l.strip()), "")
            if re.match(r"^[Il1]N[DO0Il1A]\w{0,2}\s*[:;!]", before) and not re.match(r"^[Il1]N", first.strip()):
                parts = [before, first]
        for nxt in lines[i + 1:]:
            if not nxt.strip() or STOP.match(nxt.strip()) or re.match(r"^\s*\d+\s*[\.,:;]+\s*$", nxt):
                break
            parts.append(nxt.strip())
        return re.sub(r"\s+", " ", " ".join(parts)).strip()
    return ""


INDIA_WORD = re.compile(r"^\W*([A-Za-z~|]{3,6})\W{0,6}")
OUTSIDE_AT = re.compile(r"out\s*side\W{0,3}\s*[Il1]\s*n\s*d\s*[il1~]?\s*[a~]?\W{0,4}", re.I)


def split_distribution(dist):
    """'INDIA: a, b ; outside India: c'  ->  ('a, b', 'c'), tolerant of OCR damage."""
    outside = ""
    mo = OUTSIDE_AT.search(dist)
    if mo:
        outside, dist = dist[mo.end():].strip(), dist[:mo.start()]
    head = re.match(r"^(.{0,14}?)[:;!]\s*", dist)
    if head:
        words = re.findall(r"[A-Za-z~|]{3,6}", head.group(1))
        if words and difflib.SequenceMatcher(None, words[-1].lower(), "india").ratio() >= 0.5:
            dist = dist[head.end():]
    else:
        first = INDIA_WORD.match(dist)
        if first and difflib.SequenceMatcher(None, first.group(1).lower(), "india").ratio() >= 0.55:
            dist = dist[first.end():]
    return dist.strip(" .;:"), outside.strip(" .;:")


def extract(lines):
    dist = collect(lines, "distribution")
    india, outside = split_distribution(dist)
    states, unmatched = clean_states(india)
    host = collect(lines, "host", plural=True) or collect(lines, "habitat", plural=True)

    body = [l.strip() for l in lines if l.strip()]
    heading = body[1] if body and re.match(r"^\d+\s*[\.,:;]*$", body[0]) and len(body) > 1 else (body[0] if body else "")
    year, original = "", ""
    for l in body[1:8]:
        y = YEAR.search(l)
        if y:
            year, original = y.group(1), l
            break
    return {
        "heading_ocr": heading,
        "original_combination_ocr": original,
        "year_first_listed": year,
        "india_states": ";".join(states),
        "india_unmatched": ";".join(unmatched),
        "india_states_raw": india,
        "outside_india_raw": outside,
        "host_raw": host,
        "has_distribution": "1" if dist else "",
    }


def main():
    pdf = Path(sys.argv[1])
    rows = list(csv.DictReader(CONTENTS.open(encoding="utf-8")))
    pages = read_pages(pdf)
    found = locate(rows, pages)
    fuzzy = {k: v for k, v in found.items() if isinstance(k, str)}
    pos = {k: v for k, v in found.items() if isinstance(k, int)}
    missing = [int(r["number"]) for r in rows if int(r["number"]) not in pos]
    if missing:
        sys.exit(f"could not locate species: {missing}")
    previous = (0, 0)
    for n in range(1, len(rows) + 1):
        if pos[n] <= previous:
            sys.exit(f"species {n} is out of order in the body text: {pos[n]} after {previous}")
        previous = pos[n]

    out = []
    for r in rows:
        n = int(r["number"])
        nxt = pos.get(n + 1)
        lines = entry_lines(pages, pos[n], nxt)
        rec = {k: r[k] for k in ("number", "family", "subfamily", "tribe", "genus", "subgenus",
                                 "name_ocr", "printed_page")}
        rec["located_by"] = f"name match {fuzzy[f'fuzzy{n}']}" if f"fuzzy{n}" in fuzzy else "number"
        rec.update(extract(lines))
        why = []
        if not rec["india_states"]:
            why.append("no state parsed")
        if rec["india_unmatched"]:
            why.append("unmatched text in India list")
        if not rec["year_first_listed"]:
            why.append("no year found")
        if rec["located_by"] != "number":
            why.append("heading found by name match")
        rec["needs_review"] = "; ".join(why)
        out.append(rec)

    fields = list(out[0].keys())
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(out)

    n_dist = sum(1 for o in out if o["has_distribution"])
    n_states = sum(1 for o in out if o["india_states"])
    print(f"{len(out)} species written")
    print(f"  located by name match rather than number: {len(fuzzy)}")
    print(f"  with a Distribution line: {n_dist}")
    print(f"  with at least one Indian state parsed: {n_states}")
    print(f"  with a first-listed year: {sum(1 for o in out if o['year_first_listed'])}")
    print(f"  flagged for review: {sum(1 for o in out if o['needs_review'])}")


if __name__ == "__main__":
    main()
