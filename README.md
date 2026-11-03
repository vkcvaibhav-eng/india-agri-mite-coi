# india-agri-mite-coi

Download and provenance code for Paper 1 of the project *Integrating DNA barcodes
and published records to assess the state of knowledge of agricultural mites in
India*.

Six families are covered: Tetranychidae, Tenuipalpidae, Eriophyoidea,
Tarsonemidae, Tuckerellidae and Phytoseiidae. Ticks, dust mites and veterinary
mites are outside the scope.

## What is here

| path | purpose |
|---|---|
| `config/families.json` | the six families and their taxon names at each archive |
| `scripts/fetch_ncbi.py` | stage 2a, NCBI nuccore download |
| `scripts/fetch_bold.py` | stage 2b, BOLD download |
| `scripts/combine.py` | stage 2c, merge and remove duplicates |
| `scripts/common.py` | shared columns, helpers, provenance log |
| `.github/workflows/download.yml` | runs the three scripts on a GitHub runner |
| `data/raw/` | the untouched GenBank and TSV responses |
| `data/interim/` | one metadata table and FASTA per archive |
| `data/processed/` | `coi_raw.fasta`, `coi_metadata.csv` |
| `logs/` | `download_log.csv`, `combine_summary.csv` |

## Running it

On a runner: Actions tab, *Download COI records*, Run workflow. Leave the
inputs as `all` and `both` for a full snapshot. Add an `NCBI_API_KEY` repository
secret first; without it the download is limited to three requests a second.

Locally:

```
pip install -r requirements.txt
python scripts/fetch_ncbi.py
python scripts/fetch_bold.py
python scripts/combine.py
```

One family at a time: `--family tetranychidae phytoseiidae`.

## Queries

Two NCBI queries are run per family and logged separately:

- `coi_gene` — organism, any of the COI/COX1 name variants, 100–3000 bp
- `mitogenome` — organism, mitochondrion filter, 10000–30000 bp; the COI coding
  sequence is cut out of these from the annotation

For BOLD the whole family is pulled from the public combined endpoint and records
whose marker is not a COI variant are dropped. If that endpoint has been retired,
export each family from the BOLD data portal into `data/raw/bold/` and run
`python scripts/fetch_bold.py --from-tsv "data/raw/bold/*.tsv"`.

`logs/download_log.csv` records the date, exact query string, records found and
records kept for every query. That file is the provenance trail for the methods
section, so it is committed with the data.

## Duplicates

A BOLD record carrying a GenBank accession that is already in the NCBI set is
folded into that record; its geography and voucher fields fill any gaps, and
`also_in` is set to `bold`. Records that are not identical but share a sequence
and a species name are kept and marked with a `dup_group` so the coverage counts
in stage 4 and the trees in stage 5 can treat them as one without losing the
record count.

## What this code does not do

No cleaning beyond a minimum length of 250 bp: stop-codon checks, contaminant
removal and the synonym update against the Indian checklist all belong to stage 3
and are not in this repository yet.
