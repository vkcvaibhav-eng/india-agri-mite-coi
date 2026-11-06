# Species-list gaps and sources

Updated: 6 November 2026 (Asia/Kolkata). Checklist snapshot: [a8a0c5e](https://github.com/vkcvaibhav-eng/india-agri-mite-coi/commit/a8a0c5e03bb1a2091c72cb451e358bf16b4e7806).

## Current checklist

The current [species list](data/checklist/species_list.csv) contains **1,217 counted species**, five historical-only rows excluded from the count, and no unverified rows. These are reproducible counts of the current file, not a claim that every taxonomic identity has been settled.

| Group | Counted species | Missing authority | Missing year |
| --- | --- | --- | --- |
| Tetranychidae | 142 | 0 | 0 |
| Tenuipalpidae | 114 | 0 | 4 |
| Eriophyoidea | 580 | 10 | 33 |
| Tarsonemidae | 43 | 3 | 6 |
| Tuckerellidae | 4 | 0 | 1 |
| Phytoseiidae | 334 | 6 | 17 |
| Total | 1217 | 19 | 61 |

Eriophyoidea currently comprises Eriophyidae 513, Diptilomiopidae 65 and Phytoptidae 2. Stage 3 must check family assignments against the selected classification.

Missing years are now **61**. *Euseius mangiferae* Chatterjee & Gupta, 2003 is now shown as *Euseius indica* (replacement name for that junior homonym, Gupta & Karmakar 2015, entry 116) and joined to the existing *E. indica* row; *Tegolophus gmelinae* is joined to *T. mohanasundarami* Amrine & Stasny, 1994; *Eriophyes alangii* is Nalepa, 1914; and the subgenus is spelt *Tylonychus*. These are in [authority corrections](data/checklist/authority_corrections.csv) and [duplicate review](data/checklist/duplicate_review.csv). Three of the four Tuckerellidae already have years; only *T. channabasavannai* remains blank.

Filling an author or year alone does not change the species count. Confirming additional distinct Indian taxa, synonymy, replacement names, or duplicate identities can change it.

## Verification order

1. Resolve the six historical-only names below, starting with *Tetranychus cinnabarinus* for the COI name mapping.
2. Verify the 19 missing authorities against the describing papers. Check doubtful spellings before filling them.
3. Check who is credited with the replacement name *Euseius indica* (the 2015 checklist prints the original authors and year).
4. Fill the remaining years, compare the four Tuckerellidae with the user's review paper, and clear the conflict flags.

Use the original description or revision to settle nomenclature. A regional checklist can support an Indian occurrence but does not by itself establish an original authorship, year, synonymy or current combination. Retain conflicting source usages and a citation for every accepted correction. Do not treat the six historical-only rows as six automatic additions.

## Six Gupta (1985)-only rows

All six are currently `historical_only`, `counted=0`. Names and authorities below reproduce the current extracted checklist and may contain OCR errors.

| Snapshot ID | Extracted name | Extracted authority | Extracted year | Check needed |
| --- | --- | --- | --- | --- |
| TET0123 | Tetranychus cinnabarinus | (Boisd.) | 1867 | Check its accepted relationship to T. urticae and the original author/year. Preserve a supported historical name as a COI-search alias without counting the same species twice. |
| ERI0304 | Calacarus saliyarensis | Mohansundaram | 1983 | Read the original name on the page; verify spelling, authority/year and whether a counted row already represents the same taxon. |
| ERI0386 | Eriophyes ladakbensis | Rishi &. Rather | 1982 | Check the OCR spelling against the printed account and original description, including the description year. |
| PHY0013 | Amblyseius (Typhlodromalus) havu | Pritchard &. Baker | 1962 | Verify the printed epithet, current generic combination and Indian occurrence. |
| PHY0130 | Garhwalicus himalayensis | Gupta & Ray | 1981 | Verify the Gupta & Ray identity and Indian record separately from Typhlodromus (Anthoseius) himalayensis Gupta. |
| PHY0178 | Paraamblyseius formosanus | (Ehara) | 1970 | Verify the Indian identification and any later reidentification; do not infer an Indian record from occurrence elsewhere. |

The existing [duplicate review](data/checklist/duplicate_review.csv) keeps *Garhwalicus himalayensis* Gupta & Ray and *Typhlodromus* (*Anthoseius*) *himalayensis* Gupta distinct. That identity decision must not be confused with confirming which evidence qualifies a historical-only record for inclusion.

## Four review corrections: current status

| Item | Current file | Required follow-up |
| --- | --- | --- |
| Tegolophus gmelinae / T. mohanasundarami | ERI0527 T. gmelinae and ERI0532 T. mohanasundarami are both counted; both lack a year. | Verify the reported Amrine & Stasny (1994) replacement name. If these are the same identity, merge with preserved source names and recalculate the denominator. Keep T. gmelinus distinct. |
| Euseius mangiferae | PHY0110: Chatterjee & Gupta, 2003. Year correction already applied. | Check the accepted combination / replacement-name issue mentioned in duplicate_review.csv separately; do not list 2003 as an unapplied correction. |
| Eriophyes alangii | ERI0369: Nalepa, 1929; Phytoptus alangii is retained in source-name history. | Verify the proposed original year 1914 in Nalepa's publication. Keep the Nalepa identity separate from the Mohanasundaram-attributed name. |
| Mixonychus (Tylonicus) jayaraji | TET0059 still displays Tylonicus. | Verify the proposed Tylonychus spelling and combination against the relevant original/revisional source, then record the correction. |

## Nineteen counted species missing an authority

These are 10 eriophyoids, three tarsonemids and six phytoseiids. Every one also lacks a year. Blank metadata must remain blank until a source supports a value.

| Snapshot ID | Name | Group | Source keys |
| --- | --- | --- | --- |
| ERI0026 | Diptilomiopus ficus | Eriophyoidea | som2025 |
| ERI0072 | Abacarus fuzhoubambusae | Eriophyoidea | karn2025 |
| ERI0075 | Abacarus horseshoex | Eriophyoidea | karn2025 |
| ERI0086 | Acalitus odoratus | Eriophyoidea | karn2025 |
| ERI0125 | Aceria boisi | Eriophyoidea | karn2025 |
| ERI0134 | Aceria clerodendrum | Eriophyoidea | som2025 |
| ERI0155 | Aceria ficarius | Eriophyoidea | karn2025 |
| ERI0156 | Aceria ficivagrans | Eriophyoidea | som2025 |
| ERI0223 | Aceria zeala | Eriophyoidea | karn2025 |
| ERI0232 | Aculops lycopersici | Eriophyoidea | karn2025 |
| TAR0011 | Fungitarsonemus baganbilasae | Tarsonemidae | tarswb2023 |
| TAR0012 | Fungitarsonemus icchepaharicus | Tarsonemidae | tarswb2023 |
| TAR0014 | Fungitarsonemus rishyapensis | Tarsonemidae | tarswb2023 |
| PHY0081 | Euseius asperivorous | Phytoseiidae | gm2023 |
| PHY0190 | Phytoscutus keralaensis | Phytoseiidae | gm2023 |
| PHY0191 | Phytoscutus keralicus | Phytoseiidae | gm2023 |
| PHY0192 | Phytoscutus punicae | Phytoseiidae | gm2023 |
| PHY0209 | Phytoseius imbricus | Phytoseiidae | gm2023 |
| PHY0316 | Typhlodromus (Anthoseius) parandae | Phytoseiidae | gm2023 |

## Tuckerellidae comparison

Comparison with the user's Tuckerella review paper remains pending. The current fields are:

| Snapshot ID | Name | Authority | Year |
| --- | --- | --- | --- |
| TUC0001 | Tuckerella channabasavannai | Mallik & Kumar | Missing |
| TUC0002 | Tuckerella delhiensis | Ghai & Maninder | 1976 |
| TUC0003 | Tuckerella indica | Prasad | 1973 |
| TUC0004 | Tuckerella kumaonensis | Gupta | 1979 |

Verify *T. kumaonensis* and any alternative spelling using the original description and the review's evidence. Preserve each source's spelling rather than silently overwriting its transcription.

## Remaining conflict flags

Four counted rows carry `year_differs_between_sources`; seven carry `authority_differs`.

| Snapshot ID | Name | Current authority | Current year | Flags |
| --- | --- | --- | --- | --- |
| TET0009 | Bryobia praetiosa | Koch | 1836 | authority_differs:koch/pritchard |
| TET0028 | Eotetranychus neoperplexus | Estebanes & Baker | 1950 | authority_differs:estebanes/mcgregor |
| TEN0044 | Larvacarus transitans | Ewing | 1992 | spelling_varies;year_differs_between_sources |
| ERI0138 | Aceria cordiae | Channabasavanna | 1966 | authority_differs:channabasavanna/nalepa |
| ERI0212 | Aceria trichocnemum | (Nalepa) | 1929 | spelling_varies;year_differs_between_sources |
| ERI0234 | Aculops pretoriensis | Smith Meyer & Uckermann | 1990 | authority_differs:meyersmith/smithmeyer |
| ERI0354 | Disella oblongifoliae | Ghosh, Mondal & Chakrabarti | 1986 | authority_differs:ghosh/ghosmondal |
| ERI0569 | Tetra tyrohylae | Smith Meyer | 1992 | authority_differs:meyersmith/smithmeyer |
| ERI0570 | Tetra visci | Smith Meyer | 1992 | authority_differs:meyersmith/smithmeyer |
| PHY0219 | Phytoseius maldahaensis | Gupta | 1992 | spelling_varies;year_differs_between_sources |
| PHY0331 | Typhlodromus (Anthoseius) torbatejamae | Denmark and Danesshvar | 1982 | spelling_varies;year_differs_between_sources |

The single Tamil Nadu-only counted row is **ERI0381, Eriophyes euphorbiae Mohanasundaram**, with no year, from `tn2020`. Check its relationship to *Eriophyes antiquorum* and the replacement-name correction already recorded in `authority_corrections.csv` before treating it as an additional species.

For species found in a single regional list, including *Aculops lycopersici*, verify the record and inspect broader sources and synonyms. Absence from another checklist alone is not evidence of absence from India or proof that the other list under-reports it.

## Sixty-three counted species missing a year

The 19 missing-authority rows are included here, so these queues must not be added together.

| Snapshot ID | Name | Current authority | Source keys |
| --- | --- | --- | --- |
| TEN0005 | Brevipalpus absens | De leon | gb2017 |
| TEN0007 | Brevipalpus araucanus | Smith-Meyer | gb2017 |
| TEN0011 | Brevipalpus creber | Chaudhri | gb2017 |
| TEN0015 | Brevipalpus edwinae | Baker | gb2017 |
| ERI0026 | Diptilomiopus ficus | Missing | som2025 |
| ERI0035 | Diptilomiopus lagerstroemae | Chakrabarti, Pandit & Mondal | gm2023 |
| ERI0072 | Abacarus fuzhoubambusae | Missing | karn2025 |
| ERI0075 | Abacarus horseshoex | Missing | karn2025 |
| ERI0081 | Acalitus delhiensis | Menon, Joshi & Ramamurthy | gm2023 |
| ERI0086 | Acalitus odoratus | Missing | karn2025 |
| ERI0100 | Aceria acaicae | (Mohanasundaram) | gm2023;tn2020 |
| ERI0109 | Aceria amrini | Joshi, Menon & Ramamurthy | gm2023 |
| ERI0125 | Aceria boisi | Missing | karn2025 |
| ERI0134 | Aceria clerodendrum | Missing | som2025 |
| ERI0155 | Aceria ficarius | Missing | karn2025 |
| ERI0156 | Aceria ficivagrans | Missing | som2025 |
| ERI0179 | Aceria madhucae | Joshi, Menon & Ramamurthy | gm2023 |
| ERI0184 | Aceria mauritianae | (Mohanasundaram) | karn2025;gm2023;tn2020 |
| ERI0213 | Aceria tripuraensis | Menon, Joshi & Ramamurthy | gm2023 |
| ERI0223 | Aceria zeala | Missing | karn2025 |
| ERI0232 | Aculops lycopersici | Missing | karn2025 |
| ERI0255 | Aculus mackenziei | (Keifer) | gm2023;g1985 |
| ERI0279 | Anthopoda micheliae | Chakrabarti, Das & Pandit | gm2023 |
| ERI0306 | Calacarus vasicae | Chakrabarti, Sarkar & Pandit | gm2023 |
| ERI0321 | Caliphytoptus ulmifoliae | Umapathy & Mohanasundaram | gm2023 |
| ERI0328 | Colomerus vitis | (Pgst.) | gm2023;g1985 |
| ERI0342 | Cosella meghalayensis | Chakrabarti, Das & Pandit | gm2023 |
| ERI0346 | Cosetacus sharadi | Menon, Joshi & Ramamurthy | gm2023 |
| ERI0364 | Epitrimerus buchneriae | Mohanasundaram & Venkatesh | gm2023 |
| ERI0380 | Eriophyes erineus | (Nalepa) | gm2023 |
| ERI0381 | Eriophyes euphorbiae | Mohanasundaram | tn2020 |
| ERI0442 | Neodicrothrix piperae | Mohanasundaram | gm2023;tn2020 |
| ERI0460 | Oxycenus diospyrosis | Ghosh, Mondal & Chakrabarti | gm2023 |
| ERI0491 | Phyllocoptruta daturae | Mohanasundaram & Ranganath | gm2023 |
| ERI0527 | Tegolophus gmelinae | Mohansundaram | tn2020;g1985 |
| ERI0532 | Tegolophus mohanasundarami | Amrine & Stasny | gm2023 |
| ERI0544 | Tegonotus ferrugeniae | Mohanasundaram | gm2023 |
| ERI0558 | Tetra buteae | Umapathy | gm2023 |
| ERI0575 | Tumescoptes trachycarpi | Keifer | gm2023 |
| TAR0011 | Fungitarsonemus baganbilasae | Missing | tarswb2023 |
| TAR0012 | Fungitarsonemus icchepaharicus | Missing | tarswb2023 |
| TAR0014 | Fungitarsonemus rishyapensis | Missing | tarswb2023 |
| TAR0024 | Steneotarsonemus furcatus | De Leon | gm2023;tarswb2023 |
| TAR0026 | Steneotarsonemus konoi | Smiley & Emmanouel | gm2023;tarswb2023 |
| TAR0027 | Steneotarsonemus spinki | Smiley | gm2023;tarswb2023 |
| TUC0001 | Tuckerella channabasavannai | Mallik & Kumar | gm2023 |
| PHY0049 | Amblyseius lanceae | Kar & Karmakar | gm2023 |
| PHY0051 | Amblyseius maai | Tseng | gm2023 |
| PHY0063 | Amblyseius parbatabasii | Karmakar et al. | gm2023 |
| PHY0074 | Amblyseius sundi | Pritchard & Baker | gb2017 |
| PHY0076 | Asperoseius latericulus | Karmakar & Bhowmik | gm2023 |
| PHY0081 | Euseius asperivorous | Missing | gm2023 |
| PHY0092 | Euseius curcasae | Santosh, Sadanandan & Rahul | gm2023 |
| PHY0099 | Euseius hima | (Pritchard & Baker) | gm2023 |
| PHY0115 | Euseius pariyarensis | Santosh, Sadanandan & Rahul | gm2023 |
| PHY0177 | Para hivtaceiuc | ai . . | gm2023 |
| PHY0190 | Phytoscutus keralaensis | Missing | gm2023 |
| PHY0191 | Phytoscutus keralicus | Missing | gm2023 |
| PHY0192 | Phytoscutus punicae | Missing | gm2023 |
| PHY0209 | Phytoseius imbricus | Missing | gm2023 |
| PHY0220 | Phytoseius mauritiana | Bhowmik & Karmakar | gm2023 |
| PHY0269 | Typhlodromips cinchonai | Molla & Karmakar | gm2023 |
| PHY0316 | Typhlodromus (Anthoseius) parandae | Missing | gm2023 |

## Source files and evidence trail

These links identify the extracted source rows used by the build. They are not substitutes for consulting the publication when a name or year is in dispute. Full source citations and parser notes are in [README.md](README.md).

| Key | Source | Extracted rows |
| --- | --- | --- |
| g1985 | Gupta (1985), Handbook: Plant Mites of India | [gupta1985_species.csv](data/checklist/gupta1985_species.csv) |
| gm2023 | Gupta & Mondal (2023), Plant Mites of India, literature through 2022 | [gupta_mondal2023_all.csv](data/checklist/gupta_mondal2023_all.csv) |
| chalil2024 | Chalil et al. (2024), Tetranychidae | [chalil2024_tetranychidae.csv](data/checklist/chalil2024_tetranychidae.csv) |
| gk2015 | Gupta & Karmakar (2015), Phytoseiidae | [gupta_karmakar2015_phytoseiidae.csv](data/checklist/gupta_karmakar2015_phytoseiidae.csv) |
| tn2020 | Dyamanagouda et al. (2020), Tamil Nadu Eriophyoidea | [dyamanagouda2020_eriophyoidea_tamilnadu.csv](data/checklist/dyamanagouda2020_eriophyoidea_tamilnadu.csv) |
| karn2025 | Dyamanagouda et al. (2025), Karnataka Eriophyoidea | [dyamanagouda2025_eriophyoidea_karnataka.csv](data/checklist/dyamanagouda2025_eriophyoidea_karnataka.csv) |
| som2025 | Som et al. (2025), South Bengal Eriophyoidea | [som2025_eriophyoidea_south_bengal.csv](data/checklist/som2025_eriophyoidea_south_bengal.csv) |
| mandal2026 | Mandal et al. (2026), West Bengal Eriophyoidea | [mandal2026_eriophyoidea_west_bengal.csv](data/checklist/mandal2026_eriophyoidea_west_bengal.csv) |
| tarswb2023 | West Bengal Tarsonemidae compilation; consult the describing papers identified in the rows | [tarsonemidae_west_bengal.csv](data/checklist/tarsonemidae_west_bengal.csv) |
| mitra2025 | Mitra (2025), national Tenuipalpidae | [mitra2025_tenuipalpidae_india.csv](data/checklist/mitra2025_tenuipalpidae_india.csv) |
| mesa2009 | Mesa et al. (2009), Tenuipalpidae: Indian type-locality records | [mesa2009_tenuipalpidae_india_types.csv](data/checklist/mesa2009_tenuipalpidae_india_types.csv) |
| mitra2018 | Mitra et al. (2018), southern West Bengal Tenuipalpidae | [mitra2018_tenuipalpidae_west_bengal.csv](data/checklist/mitra2018_tenuipalpidae_west_bengal.csv) |
| gb2017 | Gupta & Bose (2017), mites on medicinal plants in South Bengal | [gupta_bose2017_south_bengal.csv](data/checklist/gupta_bose2017_south_bengal.csv) |
| add2026 | Additions from describing/record papers dated 2022–2026 | [additions_2022_2026.csv](data/checklist/additions_2022_2026.csv) |

The original PDFs and the user's Tuckerella review are not embedded in this checklist repository. The original-paper retrieval and page verification remain open where listed above. No new taxonomic correction is asserted by this documentation update.

Correction inputs:

- [name_corrections.csv](data/checklist/name_corrections.csv): supported spelling/name changes.
- [authority_corrections.csv](data/checklist/authority_corrections.csv): supported author/year overrides with their basis.
- [duplicate_review.csv](data/checklist/duplicate_review.csv): reviewed same/different decisions and notes.
- [species_list_names.csv](data/checklist/species_list_names.csv): source-name mapping for later sequence matching.
- [species_list_review.csv](data/checklist/species_list_review.csv): non-exact joins and rejected joins.
- [species_list_summary.csv](data/checklist/species_list_summary.csv): current group/source counts.

After supported corrections, rebuild with `python scripts/build_species_list.py` and review all changed output rows. Species IDs can be reassigned on rebuild; locate a taxon using its name, authority and source as well as the snapshot ID. Update the README and this note when counts change.

## Later stages

- **Stage 3 — cleaning:** not started in this update. Complete the checklist review first, then clean and quality-check COI records, map synonyms, and verify/relabel eriophyoid families. Preserve raw archive labels.
- **Stage 4:** detailed scope remains to be defined. The README anticipates coverage counts here; agree the denominator, record/specimen treatment and reporting units before implementing them.
- **Stage 5 — alignment and species delimitation:** not started in this update. MAFFT, IQ-TREE, ASAP and bPTP are the planned tools; analysis design and suitable data subsets remain to be specified.

## Update: two Gupta (1985)-only rows resolved from Gupta (1985) itself

- *Calacarus saliyarensis* was a parse and OCR error. Entry 271 reads *Procalacarus aliyarensis* Mohanasundaram, 1983 (Acarologia 24(1):14); it is now joined to the counted row of that name. Historical-only rows are now five.
- *Eriophyes ladakbensis* is *Eriophyes ladakhensis* Rishi & Rather, 1982 (Indian Journal of Acarology 6:14-16), as the citation line of entry 229 gives it. It is not in Gupta & Mondal (2023) or the later lists, so it stays uncounted until the original paper or a catalogue confirms it is still valid and not a synonym.
