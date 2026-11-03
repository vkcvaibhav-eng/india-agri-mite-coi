"""Stage 2b: download COI records for the six mite families from BOLD.

Default route is the public v4 combined endpoint, which returns specimen data
and sequences in one TSV. If that endpoint is retired, export the family TSVs
by hand from the BOLD data portal and parse them with:

    python scripts/fetch_bold.py --from-tsv data/raw/bold/*.tsv

Usage:
  python scripts/fetch_bold.py
  python scripts/fetch_bold.py --family phytoseiidae
"""
import argparse
import csv
import glob
import io
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import common  # noqa: E402

DEFAULT_BASE = "https://v4.boldsystems.org/index.php/API_Public/combined"

# BOLD has renamed columns between interface versions; accept either spelling.
COLUMN_ALIASES = {
    "processid": ["processid", "process_id"],
    "bin": ["bin_uri", "bin"],
    "family": ["family_name", "family"],
    "genus": ["genus_name", "genus"],
    "species": ["species_name", "species"],
    "marker": ["markercode", "marker_code", "marker"],
    "nucleotides": ["nucleotides", "nuc", "sequence"],
    "accession": ["genbank_accession", "insdc_acs", "accession"],
    "country": ["country", "country/ocean", "country_ocean"],
    "state": ["province_state", "province/state", "province", "region"],
    "locality": ["exactsite", "exact_site", "sector", "locality"],
    "lat": ["lat", "latitude", "decimal_latitude"],
    "lon": ["lon", "longitude", "decimal_longitude"],
    "host": ["associated_taxa", "host", "extrainfo", "notes"],
    "collection_date": ["collectiondate_start", "collection_date", "collection_date_start"],
    "collectors": ["collectors", "collected_by"],
    "voucher": ["catalognum", "catalog_num", "sampleid", "museumid"],
    "identified_by": ["identification_provided_by", "identified_by"],
    "institution": ["institution_storing", "inst", "institution"],
}


def pick(row, key):
    for name in COLUMN_ALIASES[key]:
        value = row.get(name)
        if value and value.strip() and value.strip().lower() not in ("none", "null", "na"):
            return value.strip()
    return ""


def fetch_taxon(taxon, base, attempts=4):
    url = f"{base}?" + urllib.parse.urlencode({"taxon": taxon, "format": "tsv"})
    last = None
    for attempt in range(attempts):
        try:
            with urllib.request.urlopen(url, timeout=600) as resp:
                return resp.read().decode("utf-8", errors="replace"), url
        except Exception as exc:  # noqa: BLE001 - network, retry
            last = exc
            wait = 10 * (attempt + 1)
            print(f"  ! BOLD request failed ({exc}); retrying in {wait}s", flush=True)
            time.sleep(wait)
    raise RuntimeError(f"BOLD request failed after {attempts} attempts: {last}")


def parse_tsv(text, family_key, min_length):
    rows, seqs, n_total, skipped_marker = [], {}, 0, 0
    reader = csv.DictReader(io.StringIO(text), delimiter="\t")
    for record in reader:
        n_total += 1
        marker = pick(record, "marker")
        if marker and not common.COI_PATTERN.search(marker):
            skipped_marker += 1
            continue
        seq = pick(record, "nucleotides").replace("-", "").replace("\n", "").upper()
        if len(seq) < min_length:
            continue
        processid = pick(record, "processid")
        if not processid:
            continue
        species = pick(record, "species")
        genus = pick(record, "genus")
        row = {
            "record_id": f"BOLD_{processid}",
            "source": "bold",
            "accession": pick(record, "accession"),
            "bold_processid": processid,
            "bold_bin": pick(record, "bin"),
            "marker": marker or "COI",
            "family_as_given": pick(record, "family") or family_key,
            "genus_as_given": genus or (species.split()[0] if species else ""),
            "species_as_given": species,
            "organism_as_given": species or genus,
            "seq_length": len(seq),
            "coi_source": "bold_record",
            "country": pick(record, "country"),
            "state_province": pick(record, "state"),
            "locality": pick(record, "locality"),
            "latitude": pick(record, "lat"),
            "longitude": pick(record, "lon"),
            "host": pick(record, "host"),
            "collection_date": pick(record, "collection_date"),
            "collected_by": pick(record, "collectors"),
            "specimen_voucher": pick(record, "voucher"),
            "identified_by": pick(record, "identified_by"),
            "institution": pick(record, "institution"),
            "sequence_md5": common.seq_md5(seq),
        }
        rows.append(row)
        seqs[row["record_id"]] = seq
    return rows, seqs, n_total, skipped_marker


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--family", nargs="*")
    ap.add_argument("--base", default=DEFAULT_BASE)
    ap.add_argument("--from-tsv", nargs="*", help="parse already downloaded TSV files instead")
    ap.add_argument("--min-length", type=int, default=250)
    args = ap.parse_args()

    raw_dir = common.RAW / "bold"
    raw_dir.mkdir(parents=True, exist_ok=True)
    all_rows, all_seqs = [], {}

    if args.from_tsv:
        paths = []
        for pattern in args.from_tsv:
            paths.extend(sorted(glob.glob(pattern)))
        for path in paths:
            key = Path(path).stem
            print(f"\n[{key}] reading {path}")
            rows, seqs, n_total, skipped = parse_tsv(
                Path(path).read_text(encoding="utf-8", errors="replace"), key, args.min_length)
            print(f"  {n_total} records, kept {len(rows)}")
            common.log_query("bold", key, "local_tsv", path, n_total, len(rows),
                             note=f"non_coi_markers={skipped}")
            all_rows.extend(rows)
            all_seqs.update(seqs)
    else:
        for fam in common.load_families(args.family):
            taxon = fam["bold_taxon"]
            print(f"\n[{fam['key']}] BOLD taxon={taxon}")
            text, url = fetch_taxon(taxon, args.base)
            (raw_dir / f"{fam['key']}.tsv").write_text(text, encoding="utf-8")
            rows, seqs, n_total, skipped = parse_tsv(text, fam["bold_taxon"], args.min_length)
            print(f"  {n_total} records, kept {len(rows)} (non-COI markers: {skipped})")
            common.log_query("bold", fam["key"], "combined", url, n_total, len(rows),
                             note=f"non_coi_markers={skipped}")
            all_rows.extend(rows)
            all_seqs.update(seqs)

    unique = {}
    for row in all_rows:
        unique.setdefault(row["record_id"], row)
    rows = list(unique.values())

    common.write_metadata(common.INTERIM / "bold_metadata.csv", rows)
    common.write_fasta(common.INTERIM / "bold_coi.fasta", rows, all_seqs)
    print(f"\n{len(rows)} BOLD records written to data/interim/")


if __name__ == "__main__":
    main()
