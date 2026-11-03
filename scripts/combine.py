"""Stage 2c: merge the NCBI and BOLD sets, remove duplicates, write the stage 2 output.

Reads  data/interim/{ncbi,bold}_metadata.csv and the matching FASTA files.
Writes data/processed/coi_raw.fasta, data/processed/coi_metadata.csv
       logs/combine_summary.csv
"""
import argparse
import csv
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import common  # noqa: E402

EXTRA_FIELDS = ["also_in", "india_record", "dup_group", "is_representative"]


def read_fasta(path):
    seqs, label, chunks = {}, None, []
    if not path.exists():
        return seqs
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith(">"):
            if label:
                seqs[label] = "".join(chunks)
            label = line[1:].split("|")[0]
            chunks = []
        elif line.strip():
            chunks.append(line.strip())
    if label:
        seqs[label] = "".join(chunks)
    return seqs


def bare(accession):
    return re.sub(r"\.\d+$", "", (accession or "").strip()).upper()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prefer", choices=["ncbi", "bold"], default="ncbi",
                    help="which copy to keep when the same specimen sits in both archives")
    args = ap.parse_args()

    ncbi_rows = common.read_metadata(common.INTERIM / "ncbi_metadata.csv") \
        if (common.INTERIM / "ncbi_metadata.csv").exists() else []
    bold_rows = common.read_metadata(common.INTERIM / "bold_metadata.csv") \
        if (common.INTERIM / "bold_metadata.csv").exists() else []
    seqs = read_fasta(common.INTERIM / "ncbi_coi.fasta")
    seqs.update(read_fasta(common.INTERIM / "bold_coi.fasta"))
    print(f"read {len(ncbi_rows)} NCBI and {len(bold_rows)} BOLD records")

    ncbi_by_acc = {bare(r["accession"]): r for r in ncbi_rows if r.get("accession")}
    kept, folded = [], 0

    for row in ncbi_rows:
        row["also_in"] = ""
        kept.append(row)

    for row in bold_rows:
        acc = bare(row.get("accession"))
        twin = ncbi_by_acc.get(acc) if acc else None
        if twin is not None:
            # same specimen in both archives: fill the gaps in the kept copy
            twin["also_in"] = "bold"
            twin["bold_processid"] = twin.get("bold_processid") or row.get("bold_processid", "")
            twin["bold_bin"] = twin.get("bold_bin") or row.get("bold_bin", "")
            for field in ("country", "state_province", "locality", "latitude", "longitude",
                          "host", "collection_date", "collected_by", "specimen_voucher",
                          "identified_by", "institution"):
                if not twin.get(field) and row.get(field):
                    twin[field] = row[field]
            if args.prefer == "bold" and seqs.get(row["record_id"]):
                seqs[twin["record_id"]] = seqs[row["record_id"]]
            folded += 1
            continue
        row["also_in"] = ""
        kept.append(row)

    print(f"{folded} BOLD records folded into their GenBank twin")

    # flag identical sequences so stage 5 can collapse them without losing the count
    groups = {}
    for row in kept:
        key = (row.get("sequence_md5") or "", (row.get("species_as_given") or "").lower())
        groups.setdefault(key, []).append(row)
    for n, (key, members) in enumerate(groups.items(), start=1):
        for i, row in enumerate(members):
            row["dup_group"] = f"G{n:06d}" if len(members) > 1 else ""
            row["is_representative"] = "1" if i == 0 else "0"

    for row in kept:
        text = " ".join([row.get("country", ""), row.get("state_province", ""),
                         row.get("locality", "")]).lower()
        row["india_record"] = "1" if "india" in text else "0"

    fields = common.METADATA_FIELDS + EXTRA_FIELDS
    out_csv = common.PROCESSED / "coi_metadata.csv"
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in kept:
            writer.writerow({k: row.get(k, "") for k in fields})
    common.write_fasta(common.PROCESSED / "coi_raw.fasta", kept, seqs)

    summary = {}
    for row in kept:
        fam = row.get("family_as_given") or "unassigned"
        s = summary.setdefault(fam, {"total": 0, "ncbi": 0, "bold": 0, "both": 0,
                                     "india": 0, "species": set(), "india_species": set()})
        s["total"] += 1
        s[row["source"]] += 1
        if row["also_in"]:
            s["both"] += 1
        species = (row.get("species_as_given") or "").strip()
        if species and len(species.split()) > 1 and not re.search(r"\bsp{1,2}\.?$|\bcf\.|\baff\.", species):
            s["species"].add(species.lower())
            if row["india_record"] == "1":
                s["india_species"].add(species.lower())
        if row["india_record"] == "1":
            s["india"] += 1

    with (common.LOGS / "combine_summary.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["family", "records_total", "from_ncbi", "from_bold",
                         "in_both_archives", "records_from_india",
                         "named_species", "named_species_from_india"])
        for fam in sorted(summary):
            s = summary[fam]
            writer.writerow([fam, s["total"], s["ncbi"], s["bold"], s["both"],
                             s["india"], len(s["species"]), len(s["india_species"])])

    print(f"\n{len(kept)} records written to data/processed/")
    print(f"{sum(1 for r in kept if r['india_record'] == '1')} of them from India")
    for fam in sorted(summary):
        s = summary[fam]
        print(f"  {fam:<16} {s['total']:>6} records  {s['india']:>5} Indian  "
              f"{len(s['species']):>4} species  {len(s['india_species']):>4} Indian species")


if __name__ == "__main__":
    main()
