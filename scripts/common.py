"""Shared helpers for the COI download pipeline."""
import csv
import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "families.json"
RAW = ROOT / "data" / "raw"
INTERIM = ROOT / "data" / "interim"
PROCESSED = ROOT / "data" / "processed"
LOGS = ROOT / "logs"

COI_PATTERN = re.compile(
    r"(cytochrome\s*c?\s*oxidase\s*(subunit\s*)?(1|i)\b"
    r"|\bco[\s\-_]?1\b|\bcox[\s\-_]?1\b|\bcoi\b|\bmt[\s\-_]?co1\b)",
    re.IGNORECASE,
)

# Columns every source must produce, in this order.
METADATA_FIELDS = [
    "record_id",
    "source",
    "accession",
    "bold_processid",
    "bold_bin",
    "marker",
    "family_as_given",
    "genus_as_given",
    "species_as_given",
    "organism_as_given",
    "seq_length",
    "coi_source",
    "country",
    "state_province",
    "locality",
    "latitude",
    "longitude",
    "host",
    "collection_date",
    "collected_by",
    "specimen_voucher",
    "identified_by",
    "institution",
    "pubmed_ids",
    "reference_title",
    "reference_journal",
    "submission_date",
    "sequence_md5",
]


def load_families(keys=None):
    families = json.loads(CONFIG.read_text())["families"]
    if keys:
        wanted = {k.lower() for k in keys}
        families = [f for f in families if f["key"] in wanted]
        missing = wanted - {f["key"] for f in families}
        if missing:
            raise SystemExit(f"unknown family key(s): {', '.join(sorted(missing))}")
    return families


def utc_stamp():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def seq_md5(seq):
    return hashlib.md5(str(seq).upper().replace("-", "").encode()).hexdigest()


def write_metadata(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=METADATA_FIELDS, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in METADATA_FIELDS})


def read_metadata(path):
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def write_fasta(path, rows, seqs):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            seq = seqs.get(row["record_id"])
            if not seq:
                continue
            label = "{rid}|{src}|{acc}|{sp}".format(
                rid=row["record_id"],
                src=row["source"],
                acc=row.get("accession") or row.get("bold_processid") or "NA",
                sp=(row.get("species_as_given") or row.get("organism_as_given") or "unidentified").replace(" ", "_"),
            )
            fh.write(f">{label}\n")
            for i in range(0, len(seq), 70):
                fh.write(seq[i:i + 70] + "\n")


def log_query(source, family, query_name, query, n_found, n_kept, note=""):
    """Append one line to the provenance log. This log goes into the paper."""
    LOGS.mkdir(parents=True, exist_ok=True)
    path = LOGS / "download_log.csv"
    new = not path.exists()
    with path.open("a", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        if new:
            writer.writerow([
                "timestamp_utc", "source", "family", "query_name",
                "query", "records_found", "records_kept", "note",
            ])
        writer.writerow([utc_stamp(), source, family, query_name, query, n_found, n_kept, note])


def env_api_key():
    key = os.environ.get("NCBI_API_KEY", "").strip()
    return key or None
