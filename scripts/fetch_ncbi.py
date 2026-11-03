"""Stage 2a: download COI sequences for the six mite families from NCBI nuccore.

Two queries are run per family and logged separately:
  coi_gene    - records annotated or titled as COI / COX1
  mitogenome  - complete or partial mitochondrial genomes, from which the
                COI coding sequence is cut out

Usage:
  python scripts/fetch_ncbi.py                      # all families
  python scripts/fetch_ncbi.py --family tetranychidae phytoseiidae
  python scripts/fetch_ncbi.py --email you@host --min-length 300
"""
import argparse
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from Bio import SeqIO  # noqa: E402

import common  # noqa: E402

EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

COI_TERMS = (
    'COI[All Fields] OR COX1[All Fields] OR CO1[All Fields] OR COXI[All Fields] '
    'OR "cytochrome c oxidase subunit 1"[All Fields] '
    'OR "cytochrome c oxidase subunit I"[All Fields] '
    'OR "cytochrome oxidase subunit 1"[All Fields] '
    'OR "cytochrome oxidase subunit I"[All Fields]'
)


def build_queries(taxon):
    return {
        "coi_gene": f'"{taxon}"[Organism] AND ({COI_TERMS}) AND 100:3000[SLEN]',
        "mitogenome": f'"{taxon}"[Organism] AND mitochondrion[Filter] AND 10000:30000[SLEN]',
    }


class Entrez:
    def __init__(self, email, api_key=None, tool="india-agri-mite-coi"):
        self.email = email
        self.api_key = api_key
        self.tool = tool
        self.delay = 0.12 if api_key else 0.40

    def _params(self, extra):
        p = {"tool": self.tool, "email": self.email}
        if self.api_key:
            p["api_key"] = self.api_key
        p.update(extra)
        return p

    def _get(self, endpoint, params, attempts=4):
        url = f"{EUTILS}/{endpoint}?" + urllib.parse.urlencode(self._params(params))
        last = None
        for attempt in range(attempts):
            try:
                with urllib.request.urlopen(url, timeout=180) as resp:
                    data = resp.read().decode("utf-8", errors="replace")
                time.sleep(self.delay)
                return data
            except Exception as exc:  # noqa: BLE001 - network, retry
                last = exc
                wait = 5 * (attempt + 1)
                print(f"  ! {endpoint} failed ({exc}); retrying in {wait}s", flush=True)
                time.sleep(wait)
        raise RuntimeError(f"{endpoint} failed after {attempts} attempts: {last}")

    def search(self, term, retmax=100000):
        xml = self._get("esearch.fcgi", {
            "db": "nuccore", "term": term, "retmax": retmax,
            "usehistory": "y", "retmode": "xml",
        })
        count = _tag(xml, "Count")
        return {
            "count": int(count) if count else 0,
            "webenv": _tag(xml, "WebEnv"),
            "query_key": _tag(xml, "QueryKey"),
        }

    def fetch_gb(self, webenv, query_key, start, size):
        return self._get("efetch.fcgi", {
            "db": "nuccore", "WebEnv": webenv, "query_key": query_key,
            "retstart": start, "retmax": size,
            "rettype": "gb", "retmode": "text",
        })


def _tag(xml, name):
    try:
        return xml.split(f"<{name}>")[1].split(f"</{name}>")[0]
    except IndexError:
        return None


def _q(feature, *names):
    for name in names:
        values = feature.qualifiers.get(name)
        if values:
            return values[0].strip()
    return ""


def extract_coi(record):
    """Return (sequence, how) for the COI part of a GenBank record."""
    best = None
    for feature in record.features:
        if feature.type not in ("CDS", "gene"):
            continue
        text = " ".join(
            feature.qualifiers.get("gene", [])
            + feature.qualifiers.get("product", [])
            + feature.qualifiers.get("note", [])
        )
        if common.COI_PATTERN.search(text):
            try:
                seq = str(feature.extract(record.seq))
            except Exception:  # noqa: BLE001
                continue
            if best is None or len(seq) > len(best):
                best = seq
    if best:
        return best, "annotated_feature"
    if len(record.seq) <= 3000:
        return str(record.seq), "whole_record"
    return "", "no_coi_found"


def parse_records(gb_text, family, taxon, query_name, min_length):
    import io
    rows, seqs, dropped = [], {}, []
    for record in SeqIO.parse(io.StringIO(gb_text), "genbank"):
        seq, how = extract_coi(record)
        organism = record.annotations.get("organism", "").strip()
        parts = organism.split()
        source = next((f for f in record.features if f.type == "source"), None)
        refs = record.annotations.get("references", []) or []
        pubmeds = [r.pubmed_id for r in refs if getattr(r, "pubmed_id", "")]
        row = {
            "record_id": f"NCBI_{record.id}",
            "source": "ncbi",
            "accession": record.id,
            "marker": "COI",
            "family_as_given": family,
            "genus_as_given": parts[0] if parts else "",
            "species_as_given": " ".join(parts[:2]) if len(parts) > 1 else "",
            "organism_as_given": organism,
            "seq_length": len(seq),
            "coi_source": how,
            "pubmed_ids": ";".join(pubmeds),
            "reference_title": refs[0].title.strip() if refs and refs[0].title else "",
            "reference_journal": refs[0].journal.strip() if refs and refs[0].journal else "",
            "submission_date": record.annotations.get("date", ""),
            "sequence_md5": common.seq_md5(seq) if seq else "",
        }
        if source is not None:
            country, state, locality = _split_geo(_q(source, "geo_loc_name", "country"))
            row.update({
                "country": country,
                "state_province": state,
                "locality": locality or _q(source, "isolation_source"),
                "host": _q(source, "host", "lab_host"),
                "collection_date": _q(source, "collection_date"),
                "collected_by": _q(source, "collected_by"),
                "specimen_voucher": _q(source, "specimen_voucher", "isolate", "strain"),
                "identified_by": _q(source, "identified_by"),
            })
            latlon = _q(source, "lat_lon")
            if latlon:
                row["latitude"], row["longitude"] = _parse_latlon(latlon)
        if not seq or len(seq) < min_length:
            dropped.append((record.id, how, len(seq)))
            continue
        rows.append(row)
        seqs[row["record_id"]] = seq
    return rows, seqs, dropped


def _split_geo(text):
    """GenBank writes geography as 'India: Gujarat, Navsari'."""
    if not text:
        return "", "", ""
    country, _, rest = text.partition(":")
    bits = [b.strip() for b in rest.split(",") if b.strip()]
    state = bits[0] if bits else ""
    locality = ", ".join(bits[1:])
    return country.strip(), state, locality


def _parse_latlon(text):
    try:
        bits = text.split()
        lat = float(bits[0]) * (-1 if bits[1].upper() == "S" else 1)
        lon = float(bits[2]) * (-1 if bits[3].upper() == "W" else 1)
        return lat, lon
    except Exception:  # noqa: BLE001
        return "", ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--family", nargs="*", help="family keys from config/families.json")
    ap.add_argument("--email", default="vkcvaibhav@gmail.com",
                    help="contact address sent to NCBI, as their policy requires")
    ap.add_argument("--min-length", type=int, default=250,
                    help="drop sequences shorter than this (hard cleaning comes in stage 3)")
    ap.add_argument("--batch", type=int, default=150)
    args = ap.parse_args()

    client = Entrez(args.email, common.env_api_key())
    if client.api_key:
        print("using NCBI_API_KEY from the environment")

    all_rows, all_seqs = [], {}
    raw_dir = common.RAW / "ncbi"
    raw_dir.mkdir(parents=True, exist_ok=True)

    for fam in common.load_families(args.family):
        taxon = fam["ncbi_taxon"]
        for query_name, query in build_queries(taxon).items():
            print(f"\n[{fam['key']}] {query_name}")
            result = client.search(query)
            found = result["count"]
            print(f"  {found} records in nuccore")
            if not found:
                common.log_query("ncbi", fam["key"], query_name, query, 0, 0)
                continue
            rows, seqs, dropped = [], {}, []
            chunks = []
            for start in range(0, found, args.batch):
                print(f"  fetching {start + 1}-{min(start + args.batch, found)}", flush=True)
                text = client.fetch_gb(result["webenv"], result["query_key"], start, args.batch)
                chunks.append(text)
                r, s, d = parse_records(text, fam["ncbi_taxon"], taxon, query_name, args.min_length)
                rows.extend(r)
                seqs.update(s)
                dropped.extend(d)
            (raw_dir / f"{fam['key']}_{query_name}.gb").write_text("".join(chunks), encoding="utf-8")
            print(f"  kept {len(rows)}, dropped {len(dropped)}")
            common.log_query("ncbi", fam["key"], query_name, query, found, len(rows),
                             note=f"dropped={len(dropped)}")
            all_rows.extend(rows)
            all_seqs.update(seqs)

    # one record may answer both queries; accession wins
    unique = {}
    for row in all_rows:
        unique.setdefault(row["record_id"], row)
    rows = list(unique.values())

    common.write_metadata(common.INTERIM / "ncbi_metadata.csv", rows)
    common.write_fasta(common.INTERIM / "ncbi_coi.fasta", rows, all_seqs)
    print(f"\n{len(rows)} NCBI records written to data/interim/")


if __name__ == "__main__":
    main()
