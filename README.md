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

## Species checklist (stage 1)

`data/checklist/` holds the denominator for the coverage analysis, built from
S. K. Gupta (1985), *Handbook: Plant Mites of India* (Zoological Survey of India,
Calcutta): 557 species, 131 genera, 18 families. The book's PDF is not in this
repository; only the extracted names, states and hosts are.

| file | content |
|---|---|
| `gupta1985_contents.csv` | the numbered species list from the Systematic Contents, with family, subfamily, tribe, genus and subgenus |
| `gupta1985_species.csv` | the same 557 species with the first-listed year, Indian states, hosts and outside-India distribution taken from each entry |

```
python scripts/parse_gupta_contents.py Gupta_1985.pdf
python scripts/parse_gupta_body.py     Gupta_1985.pdf
```

The PDF is a scan with an OCR layer, and the OCR is not clean. What is checked
and what is not:

- The species count matches the book's own total (557), numbering agrees with the
  book's sequence for 555 of 557, and entries are located in strictly increasing
  order in the body text.
- Indian states are matched against a fixed list of states and territories; text
  that does not match is kept in `india_unmatched` rather than guessed at.
  States are as the book prints them, which means 1985 boundaries (no Jharkhand,
  Chhattisgarh, Uttarakhand, Telangana) and the spellings Orissa and Pondicherry.
- `needs_review` marks 28 rows that a person should read against the page:
  no state parsed, unmatched text, no year found, or a heading found by name.
- **Species names are still as OCR read them** (`name_ocr`). They contain
  damage such as `terpoglwssiani` and `Amh/yseius`. They must be corrected against
  the world catalogues before they are matched to sequence labels.

The book is from 1985. It fixes the Indian baseline at that date and does not
include the species recorded or described since, nor the genus changes since,
especially in Phytoseiidae and Eriophyoidea. A name-for-name match of this list
against the sequence set is therefore a floor on coverage, not a measurement of it.

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

### Updated sources (stage 1b)

`scripts/parse_chalil2024.py` reads Chalil et al. (2024), *Persian Journal of Acarology* 13(1): 29–75, into `data/checklist/chalil2024_tetranychidae.csv` (135 Tetranychidae species with synonyms, type data, Indian states, outside-India distribution, hosts). 4 rows are flagged where the source names a region rather than a state. `scripts/states.py` holds the state matching shared by the checklist parsers. `synonyms_raw` can still carry stray citation fragments and needs cleaning before name matching.
