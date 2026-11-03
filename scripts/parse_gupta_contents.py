"""Stage 1a: read the numbered species list out of Gupta (1985), Handbook: Plant
Mites of India, from its Systematic Contents pages.

The PDF has an OCR text layer. `pdftotext -layout` keeps each species on its own
line with its number and printed page, and keeps the Order / Family / Subfamily /
Tribe / Genus / Subgenus headings in order, so each species can be given its
taxonomic placement as it is read.

The book numbers its species 1..557 strictly in order, so the number assigned
here comes from the sequence. The number OCR actually read is kept beside it
(`number_ocr`) so that damaged ones can be checked rather than trusted.

  python scripts/parse_gupta_contents.py /path/to/Gupta_1985.pdf

Writes data/checklist/gupta1985_contents.csv. Names are exactly as OCR read them;
repair happens in a later step, never here.
"""
import csv
import difflib
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "checklist" / "gupta1985_contents.csv"

FIRST_PAGE, LAST_PAGE = 15, 40
RANKS = ["order", "family", "subfamily", "tribe", "genus", "subgenus"]
EXPECTED = 557

FAMILIES = ["Tetranychidae", "Tuckerellidae", "Tenuipalpidae", "Nalepellidae", "Eriophyidae",
            "Rhyncaphytoptidae", "Tarsonemidae", "Cheyletidae", "Stigmaeidae", "Tydeidae",
            "Bdellidae", "Cunaxidae", "Erythraeidae", "Ameroseiidae", "Ascidae",
            "Phytoseiidae", "Acaridae", "Oribatulidae"]

HEAD = re.compile(
    r"^\s*(Order|Fam\.?|Subfam\.?|Tribe|Genus|Subgenus|\(\)enus)\s+(.+?)\s*(?:\.{2,})?\s*(?:[SIl]?\d{1,3})?\s*$")
# a species line starts with its number; OCR damages it as '3~0', '41 (' or '302..'
START = re.compile(r"^\s*(\d[\d~]{0,3}|\d{1,3}\s\()\s*[\.:,~;]{1,2}\s*(\S.*?)\s*$")
TAIL_PAGE = re.compile(r"^(.*\S)\s+([SIl]?\d{2,3})$")


def page_text(pdf, page):
    return subprocess.run(
        ["pdftotext", "-layout", "-f", str(page), "-l", str(page), str(pdf), "-"],
        capture_output=True, text=True, check=True).stdout


def fix_page(token):
    return token.replace("S", "5").replace("I", "1").replace("l", "1") if token else ""


def rank_of(word):
    return {"order": "order", "fam": "family", "subfam": "subfamily", "tribe": "tribe",
            "genus": "genus", "()enus": "genus", "subgenus": "subgenus"}[word.lower().rstrip(".")]


OCR_FAMILY = {"tuckbrbllidae": "Tuckerellidae", "tuckerellidae": "Tuckerellidae"}


def canonical_family(raw):
    plain = re.sub(r"[^A-Za-z]", "", raw).lower()
    if plain in OCR_FAMILY:
        return OCR_FAMILY[plain]
    key = plain.replace("ll", "ii").replace("ai", "ae")
    hit = difflib.get_close_matches(key, [f.lower() for f in FAMILIES], n=1, cutoff=0.7)
    return hit[0].capitalize() if hit else raw


def contents_lines(pdf):
    text = "\n".join(page_text(pdf, p) for p in range(FIRST_PAGE, LAST_PAGE + 1))
    lines = text.splitlines()
    begin = [i for i, l in enumerate(lines) if "SYSTEMATIC CONTENTS" in l][-1]
    end = next(i for i in range(begin, len(lines)) if lines[i].strip() == "INTRODUCTION")
    return lines[begin + 1:end]


def main():
    pdf = Path(sys.argv[1])
    context = {r: "" for r in RANKS}
    rows, pending = [], None

    def close():
        nonlocal pending
        if pending:
            pending["name_ocr"] = re.sub(r"\s+", " ", pending["name_ocr"]).strip()
            rows.append(pending)
            pending = None

    for raw in contents_lines(pdf):
        line = raw.rstrip()
        if not line.strip():
            continue
        start = START.match(line)
        if start:
            close()
            name, page = start.group(2), ""
            tail = TAIL_PAGE.match(name)
            if tail:
                name, page = tail.group(1), fix_page(tail.group(2))
            pending = {"number_ocr": start.group(1), "name_ocr": name,
                       "printed_page": page, **context}
            continue
        head = HEAD.match(line)
        if head:
            close()
            rank = rank_of(head.group(1))
            context[rank] = re.sub(r"\s+", " ", head.group(2)).strip()
            for lower in RANKS[RANKS.index(rank) + 1:]:
                context[lower] = ""
            continue
        if pending and not pending["printed_page"]:      # a name wrapped onto this line
            tail = TAIL_PAGE.match(line.strip())
            if tail:
                pending["name_ocr"] += " " + tail.group(1)
                pending["printed_page"] = fix_page(tail.group(2))
            else:
                pending["name_ocr"] += " " + line.strip()
    close()

    for i, r in enumerate(rows, start=1):
        r["number"] = i
        r["number_matches_ocr"] = "1" if r["number_ocr"] == str(i) else ""
        r["family"] = canonical_family(r["family"])

    OUT.parent.mkdir(parents=True, exist_ok=True)
    fields = ["number", "number_ocr", "number_matches_ocr", "name_ocr", "printed_page"] + RANKS
    with OUT.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

    odd = [(r["number"], r["number_ocr"], r["name_ocr"]) for r in rows if not r["number_matches_ocr"]]
    print(f"{len(rows)} species read; the book states {EXPECTED}")
    print(f"{len(odd)} where the OCR number differs from the sequence:")
    for o in odd:
        print("  ", o)


if __name__ == "__main__":
    main()
