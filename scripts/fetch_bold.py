"""Stage 2b: download COI records for the six mite families from BOLD v5.

The v3 and v4 public APIs were retired in July 2026. The v5 portal uses a
three-step token flow:

  1. /api/query/preprocessor  turns a loose search string into scope:field:value
     triplets
  2. /api/query               turns the triplets into a query_id
  3. /api/documents/<id>/download  returns the records as BCDM TSV

Usage:
  python scripts/fetch_bold.py
  python scripts/fetch_bold.py --family phytoseiidae --geo India
  python scripts/fetch_bold.py --from-tsv "data/raw/bold/*.tsv"
"""
import argparse
import csv
import glob
import io
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import common  # noqa: E402

PORTAL = "https://portal.boldsystems.org/api"
TRIPLET = re.compile(r"^[a-z_]+:[a-z_/]+:.+$")
USER_AGENT = "india-agri-mite-coi/1.0 (research pipeline)"

# BCDM column names, with the older v4 spellings kept as fallbacks.
COLUMN_ALIASES = {
    "processid": ["processid", "process_id"],
    "bin": ["bin_uri", "bin"],
    "family": ["family", "family_name"],
    "genus": ["genus", "genus_name"],
    "species": ["species", "species_name"],
    "marker": ["marker_code", "markercode", "marker"],
    "nucleotides": ["nuc", "nucleotides", "sequence"],
    "accession": ["insdc_acs", "genbank_accession", "accession"],
    "country": ["country/ocean", "country_ocean", "country"],
    "state": ["province/state", "province_state", "province", "region"],
    "locality": ["site", "sector", "exactsite", "locality"],
    "lat": ["lat", "latitude", "coord_lat"],
    "lon": ["lon", "longitude", "coord_lon"],
    "host": ["associated_taxa", "host", "extrainfo", "notes"],
    "collection_date": ["collection_date_start", "collectiondate_start", "collection_date"],
    "collectors": ["collectors", "collected_by"],
    "voucher": ["museumid", "catalognum", "fieldid", "sampleid"],
    "identified_by": ["identified_by", "identification_provided_by"],
    "institution": ["inst", "institution_storing", "institution"],
}


def get(url, attempts=4, as_json=True):
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    last = None
    for attempt in range(attempts):
        try:
            with urllib.request.urlopen(request, timeout=900) as resp:
                raw = resp.read().decode("utf-8", errors="replace")
            return json.loads(raw) if as_json else raw
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            if "Just a moment" in body or "challenge" in body.lower():
                raise RuntimeError(
                    f"HTTP {exc.code}: the portal returned a bot-protection challenge page "
                    "instead of data, so this address cannot reach the API. Run the script "
                    "from your own machine, or export the family TSVs from the portal by hand "
                    "and read them with --from-tsv.") from exc
            raise RuntimeError(f"HTTP {exc.code} from {url}\n{body[:400]}") from exc
        except Exception as exc:  # noqa: BLE001 - network or parse, retry
            last = exc
            wait = 10 * (attempt + 1)
            print(f"  ! request failed ({exc}); retrying in {wait}s", flush=True)
            time.sleep(wait)
    raise RuntimeError(f"request failed after {attempts} attempts: {url}: {last}")


def harvest_triplets(obj, found):
    """The preprocessor response shape is not documented; pull out any triplet."""
    if isinstance(obj, str):
        if TRIPLET.match(obj.strip()):
            found.append(obj.strip())
    elif isinstance(obj, dict):
        for value in obj.values():
            harvest_triplets(value, found)
    elif isinstance(obj, list):
        for value in obj:
            harvest_triplets(value, found)
    return found


def find_value(obj, names):
    if isinstance(obj, dict):
        for name in names:
            if name in obj and isinstance(obj[name], (str, int)):
                return str(obj[name])
        for value in obj.values():
            hit = find_value(value, names)
            if hit:
                return hit
    elif isinstance(obj, list):
        for value in obj:
            hit = find_value(value, names)
            if hit:
                return hit
    return None


def resolve_query(taxon, geo=None):
    """Ask the preprocessor for triplets; fall back to an explicit one."""
    terms = f"tax:{taxon}" + (f";geo:{geo}" if geo else "")
    url = f"{PORTAL}/query/preprocessor?" + urllib.parse.urlencode({"query": terms})
    try:
        triplets = harvest_triplets(get(url), [])
    except Exception as exc:  # noqa: BLE001
        print(f"  ! preprocessor unavailable ({exc}); using an explicit triplet")
        triplets = []
    # the preprocessor falls back to ID matching on strings it cannot place
    triplets = [t for t in triplets if not t.startswith("ids:")]
    if not triplets:
        triplets = [f"tax:family:{taxon}"]
        if geo:
            triplets.append(f"geo:country/ocean:{geo}")
    return ";".join(dict.fromkeys(triplets))


def get_query_id(query, extent="full"):
    url = f"{PORTAL}/query?" + urllib.parse.urlencode({"query": query, "extent": extent})
    payload = get(url)
    query_id = find_value(payload, ["query_id", "queryId", "id"])
    total = find_value(payload, ["recordsTotal", "records_total", "total"])
    if not query_id:
        raise RuntimeError(f"no query_id in the response for {query}: {str(payload)[:300]}")
    return query_id, total


def download_tsv(query_id):
    url = f"{PORTAL}/documents/{urllib.parse.quote(query_id, safe='')}/download?format=tsv"
    return get(url, as_json=False), url


def pick(row, key):
    for name in COLUMN_ALIASES[key]:
        value = row.get(name)
        if value and str(value).strip() and str(value).strip().lower() not in ("none", "null", "na"):
            return str(value).strip()
    return ""


def parse_tsv(text, family_key, min_length):
    rows, seqs, n_total, skipped_marker = [], {}, 0, 0
    reader = csv.DictReader(io.StringIO(text), delimiter="\t")
    for record in reader:
        n_total += 1
        marker = pick(record, "marker")
        if marker and not common.COI_PATTERN.search(marker):
            skipped_marker += 1
            continue
        seq = re.sub(r"[^A-Za-z]", "", pick(record, "nucleotides")).upper()
        processid = pick(record, "processid")
        if not processid or len(seq) < min_length:
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
    ap.add_argument("--geo", help="restrict to one country, e.g. India")
    ap.add_argument("--extent", default="full", choices=["full", "limited"])
    ap.add_argument("--from-tsv", nargs="*", help="parse already downloaded BCDM TSV files")
    ap.add_argument("--min-length", type=int, default=250)
    args = ap.parse_args()

    raw_dir = common.RAW / "bold"
    raw_dir.mkdir(parents=True, exist_ok=True)
    all_rows, all_seqs, failures = [], {}, []

    if args.from_tsv:
        paths = []
        for pattern in args.from_tsv:
            paths.extend(sorted(glob.glob(pattern)))
        if not paths:
            raise SystemExit("--from-tsv matched no files")
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
            print(f"\n[{fam['key']}] BOLD v5, taxon={taxon}"
                  + (f", geo={args.geo}" if args.geo else ""))
            try:
                query = resolve_query(taxon, args.geo)
                print(f"  query: {query}")
                query_id, total = get_query_id(query, args.extent)
                print(f"  query_id obtained, recordsTotal={total}")
                text, url = download_tsv(query_id)
            except Exception as exc:  # noqa: BLE001 - one family must not sink the rest
                print(f"  ! {fam['key']} failed: {exc}")
                failures.append(fam["key"])
                common.log_query("bold", fam["key"], "v5_portal", str(exc), 0, 0, note="failed")
                continue
            (raw_dir / f"{fam['key']}.tsv").write_text(text, encoding="utf-8")
            rows, seqs, n_total, skipped = parse_tsv(text, fam["bold_taxon"], args.min_length)
            print(f"  {n_total} records, kept {len(rows)} (non-COI markers: {skipped})")
            common.log_query("bold", fam["key"], "v5_portal", f"{query} -> {url}",
                             n_total, len(rows), note=f"non_coi_markers={skipped}")
            all_rows.extend(rows)
            all_seqs.update(seqs)

    unique = {}
    for row in all_rows:
        unique.setdefault(row["record_id"], row)
    rows = list(unique.values())

    common.write_metadata(common.INTERIM / "bold_metadata.csv", rows)
    common.write_fasta(common.INTERIM / "bold_coi.fasta", rows, all_seqs)
    print(f"\n{len(rows)} BOLD records written to data/interim/")
    if failures:
        print("families that failed: " + ", ".join(failures))
        print("if the download was refused as too large, retry that family with --geo India,")
        print("or request the full set from support@boldsystems.org and use --from-tsv")


if __name__ == "__main__":
    main()
