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

On a runner: Actions tab, *Download COI records*, Run workflow. `source`
defaults to `ncbi`, which is the half that works there; see the BOLD note below. Add an `NCBI_API_KEY` repository
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

BOLD is read through the v5 portal API, since the v3 and v4 public endpoints were
retired in July 2026. Each family goes through the three-step token flow
(`/api/query/preprocessor`, `/api/query`, `/api/documents/<query_id>/download`)
and comes back as BCDM TSV; records whose marker is not a COI variant are dropped.
A family that fails is logged and skipped rather than ending the run.

The portal sits behind bot protection that answers requests from cloud runner
addresses with a challenge page instead of data, so the BOLD step is not run on
GitHub Actions. Run it from your own machine:

```
python scripts/fetch_bold.py
git add data logs && git commit -m "BOLD snapshot" && git push
```

Failing that, export each family from the portal in a browser into
`data/raw/bold/` and read the files with
`python scripts/fetch_bold.py --from-tsv "data/raw/bold/*.tsv"`. The portal also
caps how much one download may return; a family refused as too large can be
narrowed with `--geo India` or requested from support@boldsystems.org.

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
