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

`scripts/parse_gupta_karmakar2015.py` reads Gupta & Karmakar (2015), *Records of the Zoological Survey of India* 115(1): 51–72, into `data/checklist/gupta_karmakar2015_phytoseiidae.csv`. It recovers all 211 species the paper states. Two numbered species-group headings (*markwelli* and *oguroi* groups of *Scapulaseius*) are skipped, and entries 208–211, the four new species of Karmakar & Gupta (2014) listed after *Typhlodromus*, are placed in *Amblyseius*, *Neoseiulus* and *Euseius* as the paper's introduction and Gupta & Mondal (2023) give them. The list has citations only, so no states or hosts. Genus is taken from the heading each entry sits under, so subgenus placements are not separated.

### Further sources

- `scripts/parse_dyamanagouda2020.py` → `data/checklist/dyamanagouda2020_eriophyoidea_tamilnadu.csv`: Dyamanagouda et al. (2020), *Journal of Entomology and Zoology Studies* 8(6): 137–146. 281 Eriophyoidea species in 73 genera (Eriophyidae 252, Phytoptidae 2, Diptilomiopidae 27), matching the paper's totals. All are Tamil Nadu records. 18 rows with a scattered table layout were set by hand (`OVERRIDES`). A wrapped host name on the line above a numbered row is no longer read as that row's epithet; this had given 17 rows wrong names (for example *Aceria umapathy*, *Aceria justicia*, *Aceria sapindus*).
- `scripts/parse_tarsonemidae_wb.py` → `data/checklist/tarsonemidae_west_bengal.csv`: named species only from Mondal et al. (2023) and Karmakar (2016). The Mondal table gives the describing paper, not the authority, so authority is blank for those.
- Mesa et al. (2009), the Tenuipalpidae world catalogue, is not yet used: the file supplied holds only the front matter.

`scripts/parse_mesa2009.py` → `data/checklist/mesa2009_tenuipalpidae_india_types.csv`: the 53 Tenuipalpidae that Mesa et al. (2009), *Zootaxa* 2098, record as described from India (Appendix A country code IND; 51 matched to catalogue entries, 7 rows need review). **Limit:** the catalogue gives the country of original description only, so species described elsewhere but present in India (for example *Brevipalpus phoenicis*, *B. californicus*, *Raoiella indica*) are not in this file. `…_leads.csv` lists 60 other entries whose redescriptions cite an Indian author, as leads to check against Indian literature.

`scripts/parse_mitra2018.py` → `data/checklist/mitra2018_tenuipalpidae_west_bengal.csv`: 17 Tenuipalpidae from southern West Bengal (Mitra et al. 2018, *Acarologia* 58(4): 850–854), six of them new records for India. This note also fills part of the gap in the Mesa file: it confirms West Bengal records of *Brevipalpus californicus*, *B. obovatus*, *B. phoenicis* and *B. lewisi*. It states 102 species in 15 genera known from India per Gupta & Mandal (2015), which is the source still to find.

`scripts/parse_gupta_bose2017.py` → `data/checklist/gupta_bose2017_south_bengal.csv`: Gupta & Bose (2017), *Records of the Zoological Survey of India* 117(2): 154–181, mites on medicinal plants in South Bengal. 113 entries, 98 named; 73 named species fall in the six families (Tetranychidae 22, Tenuipalpidae 19, Tarsonemidae 2, Eriophyidae 3, Phytoseiidae 27), with districts and host plants. Two headings (*Amblyseius coffeae*, *Euseius finlandicus*) were read from the page images because the text layer drops the species name. Seven numbered entries are not parsed; none is in the six families (Stigmaeidae, Tydeidae, Ameroseiidae).

`scripts/parse_mitra2025.py` → `data/checklist/mitra2025_tenuipalpidae_india.csv`: Mitra (2025), *International Journal of Tropical Insect Science* 45: 1041–1055, the current national Tenuipalpidae checklist. 101 species in 15 genera with Indian states, other countries and host plants; all genus counts match the abstract. This supersedes the partial Tenuipalpidae sources above for the denominator.

Tarsonemidae update: `tarsonemidae_west_bengal.csv` now has 25 named species (was 22) with authority and year for 15, taken from the Plazi treatments of the describing papers (Zootaxa 5072, 4942, 5023, 5138, 5182; Journal of Natural History 2021). Authorities are still blank for *Floridotarsonemus kathali/kukri*, three *Fungitarsonemus*, three *Metatarsonemus* (connexus, diplojuga, infundibulum), *Xenotarsonemus krishnai*, *Daidalotarsonemus duolamella* and the four Karmakar 2016 species' years. The count is still below the 32 Indian species stated by Karmakar et al. (2022), whose species list is not public.

## Gupta & Mondal (2023), Plant Mites of India (national list to 2022)

`scripts/parse_gupta_mondal2023.py` -> `data/checklist/gupta_mondal2023_all.csv` (1,249 numbered accounts:
Tetranychidae 134, Tuckerellidae 4, Tenuipalpidae 103, Eriophyoidea 535, Tarsonemidae 28, other predatory
families 150, Phytoseiidae 295; 30 are unidentified `sp.` records). Source is the user's OCR transcription of the
handbook (unproofread, kept outside this repository). Only name, authority, family, Indian states, hosts and page
are kept. Covers literature up to 2022, so 2023-2026 descriptions are absent. Compared with the earlier lists
(exact, spelling-variant and genus-change matches pooled), the union is about: Tetranychidae 148, Tenuipalpidae 111,
Phytoseiidae 315, Eriophyoidea 546, Tarsonemidae 29. These first estimates are replaced by `species_list.csv` below.
The file also gives `year` (only where a citation reads *Name Author, Year*) and `citation_names` (the names that open
the book's taxonomic citations, as Name|Author|Year).

## Additions since 2022 and name corrections

`data/checklist/additions_2022_2026.csv` lists 55 names from papers read after the 2022 cut-off of Gupta & Mondal
(2023): 31 Phytoseiidae, 16 Tarsonemidae and 8 Eriophyoidea, each with its source and, where found, DOI. Some 2022
names turned out to be in the book as well; the build joins them. `name_corrections.csv` records eight spellings in
the sources that differ from the published names. `unverified_names.csv` holds names seen only in pasted answers (none at present);
`leads_to_verify.csv` lists what is still open (none at present). The four *Typhlodromus* (*Anthoseius*) of Biswas & Karmakar 2026 were read from the paper itself.

## species_list.csv (stage 1 output)

```
python scripts/build_species_list.py
```

joins all the lists above into `data/checklist/species_list.csv`, one row per species of the six groups. Names are
matched in four passes within each group: exact binomial; spelling variant; a synonym or older combination that a
source cites (Gupta & Mondal 2023 citations, Chalil et al. 2024 synonym lines, Gupta 1985 original combinations), or an
old subgenus that is now a genus; and recombination (same epithet, first author and year in another genus, with no
second candidate). No pass joins two names that one carefully compiled source lists as two species, except where a
newer source treats them as synonyms; those rows are flagged. The name shown is taken from the most recent specialist
list for the group, with the epithet spelling most sources agree on.

| status | counted | meaning |
|---|---|---|
| confirmed | 1 | in at least one list or paper published after 1985 |
| historical_only | 0 | only in Gupta (1985): a synonym, older combination or OCR-damaged name no newer source prints |
| unverified | 0 | name seen only in pasted answers |

Counted species: Tetranychidae 144, Tenuipalpidae 114, Eriophyoidea 587 (Eriophyidae 517, Diptilomiopidae 65,
Phytoptidae 2, family not given 3), Tarsonemidae 43, Tuckerellidae 4, Phytoseiidae 332; total 1,224.

Columns worth knowing: `sources` (which lists hold the species), `other_names_in_sources` (spellings and
combinations used by them), `joined_by`, and `flags`, among them `not_in_gupta_mondal_2023`,
`regional_lists_or_papers_only`, `check_vs:<id>` (a join refused because only one source keeps the two names apart:
a possible double count), `same_name_as:<id>` (homonyms kept apart), `synonymised_by_newer_source`,
`authority_differs`, `family_differs` and `spelling_varies`.

Other outputs: `species_list_names.csv` maps every name seen in the sources, and every synonym or combination they
cite, to its `species_id` (for matching COI record names in stage 3); `species_list_review.csv` lists each join that
is not an exact match and each join the rules refused; `species_list_summary.csv` gives the counts per group and
per source. Species ids are reassigned when the list is rebuilt.
