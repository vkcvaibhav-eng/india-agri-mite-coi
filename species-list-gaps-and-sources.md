# Species-list gaps and sources

Updated: 10 November 2026 (Asia/Kolkata).

## Current checklist

The current [species list](data/checklist/species_list.csv) contains **1,221 counted species**, 5 historical-only rows excluded from the count, and no unverified rows. These are reproducible counts of the current file, not a claim that every taxonomic identity has been settled.

| Group | Counted species | Missing authority | Missing year |
| --- | --- | --- | --- |
| Tetranychidae | 148 | 0 | 0 |
| Tenuipalpidae | 114 | 0 | 3 |
| Eriophyoidea | 580 | 8 | 30 |
| Tarsonemidae | 43 | 3 | 5 |
| Tuckerellidae | 4 | 0 | 0 |
| Phytoseiidae | 332 | 6 | 12 |
| Total | 1,221 | 17 | 50 |

Eriophyoidea comprise Eriophyidae 513, Diptilomiopidae 65 and Phytoptidae 2.

Identity decisions in force ([authority corrections](data/checklist/authority_corrections.csv), [duplicate review](data/checklist/duplicate_review.csv)):

- *Amblyseiulella nicobarensis* (Gupta) is counted as *Paraphytoseius cracentis* (Corpuz & Rimando, 1966): Prasad & Karmakar (2015), Persian Journal of Acarology 4(2): 143–162, types examined.
- *Amblyseiulella multidentatus* (Swirski & Shechter, 1961) is joined to *Paraphytoseius orientalis* (Narayanan, Kaur & Ghai, 1960): Chant & McMurtry (2003), International Journal of Acarology 29(3): 179–224, p. 220; followed by Moraes et al. (2004) and Lofego et al. (2024). Matthysse & Denmark (1981) had used *P. multidentatus* as the senior name for this group.
- *Eriophyes euphorbiae* Mohanasundaram, 1983 (Tamil Nadu list) is joined to its replacement name *Eriophyes antiquorum* Amrine & Stasny, 1994, under which Gupta & Mondal (2023) list the same mite on *Euphorbia antiquorum*.
- *Euseius mangiferae* Chatterjee & Gupta, 2003 is shown as *Euseius indica* (replacement name; Gupta & Karmakar 2015, entry 116); *Tegolophus gmelinae* is joined to *T. mohanasundarami* Amrine & Stasny, 1994; *Eriophyes alangii* is Nalepa, 1914; the subgenus of *Mixonychus jayaraji* is spelt *Tylonychus*.

Filling an author or year alone does not change the species count. Confirming additional distinct Indian taxa, synonymy, replacement names or duplicate identities can change it.

## 5 Gupta (1985)-only rows

All are `historical_only`, `counted=0`.

| Species ID | Name | Authority | Year |
| --- | --- | --- | --- |
| TET0126 | Tetranychus cinnabarinus | (Boisd.) | 1867 |
| ERI0384 | Eriophyes ladakhensis | Rishi & Rather | 1982 |
| PHY0011 | Amblyseius (Typhlodromalus) havu | Pritchard &. Baker | 1962 |
| PHY0127 | Garhwalicus himalayensis | Gupta & Ray | 1981 |
| PHY0174 | Paraamblyseius formosanus | (Ehara) | 1970 |

- *Tetranychus cinnabarinus* is kept as a COI-search alias of *T. urticae* (Auger et al. 2013) and not counted.
- *Eriophyes ladakhensis* Rishi & Rather, 1982 (Indian Journal of Acarology 6: 14–16; Gupta 1985, entry 229) is not in Gupta & Mondal (2023) or the later lists; it stays uncounted until the original paper or a catalogue confirms it is valid and not a synonym.
- *Amblyseius* (*Typhlodromalus*) *havu* Pritchard & Baker, 1962 (entry 476), *Paraamblyseius formosanus* (Ehara, 1970) (entry 500) and *Garhwalicus himalayensis* Gupta & Ray, 1981 (entry 554) have Indian records in Gupta (1985) but are absent from Gupta & Karmakar (2015). They stay uncounted until the Phytoseiidae Database or a revision shows why they were left out.
- *Calacarus saliyarensis* was a parse error for *Procalacarus aliyarensis* Mohanasundaram, 1983 (entry 271) and is joined to that counted row.

## 17 counted species missing an authority

Blank metadata stays blank until a source supports a value.

| Species ID | Name | Group | Sources |
| --- | --- | --- | --- |
| ERI0026 | Diptilomiopus ficus | Eriophyoidea | som2025 |
| ERI0085 | Acalitus odoratus | Eriophyoidea | karn2025 |
| ERI0125 | Aceria boisi | Eriophyoidea | karn2025 |
| ERI0134 | Aceria clerodendrum | Eriophyoidea | som2025 |
| ERI0155 | Aceria ficarius | Eriophyoidea | karn2025 |
| ERI0156 | Aceria ficivagrans | Eriophyoidea | som2025 |
| ERI0223 | Aceria zeala | Eriophyoidea | karn2025 |
| ERI0232 | Aculops lycopersici | Eriophyoidea | karn2025 |
| TAR0011 | Fungitarsonemus baganbilasae | Tarsonemidae | tarswb2023 |
| TAR0012 | Fungitarsonemus icchepaharicus | Tarsonemidae | tarswb2023 |
| TAR0014 | Fungitarsonemus rishyapensis | Tarsonemidae | tarswb2023 |
| PHY0079 | Euseius asperivorous | Phytoseiidae | gm2023 |
| PHY0187 | Phytoscutus keralaensis | Phytoseiidae | gm2023 |
| PHY0188 | Phytoscutus keralicus | Phytoseiidae | gm2023 |
| PHY0189 | Phytoscutus punicae | Phytoseiidae | gm2023 |
| PHY0206 | Phytoseius imbricus | Phytoseiidae | gm2023 |
| PHY0313 | Typhlodromus (Anthoseius) parandae | Phytoseiidae | gm2023 |

## 50 counted species missing a year

The missing-authority rows are included here, so the two queues must not be added together.

| Species ID | Name | Authority | Sources |
| --- | --- | --- | --- |
| TEN0007 | Brevipalpus araucanus | Smith-Meyer | gb2017 |
| TEN0011 | Brevipalpus creber | Chaudhri | gb2017 |
| TEN0015 | Brevipalpus edwinae | Baker | gb2017 |
| ERI0026 | Diptilomiopus ficus | Missing | som2025 |
| ERI0035 | Diptilomiopus lagerstroemae | Chakrabarti, Pandit & Mondal | gm2023 |
| ERI0080 | Acalitus delhiensis | Menon, Joshi & Ramamurthy | gm2023 |
| ERI0085 | Acalitus odoratus | Missing | karn2025 |
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
| ERI0305 | Calacarus vasicae | Chakrabarti, Sarkar & Pandit | gm2023 |
| ERI0320 | Caliphytoptus ulmifoliae | Umapathy & Mohanasundaram | gm2023 |
| ERI0327 | Colomerus vitis | (Pgst.) | gm2023;g1985 |
| ERI0341 | Cosella meghalayensis | Chakrabarti, Das & Pandit | gm2023 |
| ERI0345 | Cosetacus sharadi | Menon, Joshi & Ramamurthy | gm2023 |
| ERI0363 | Epitrimerus buchneriae | Mohanasundaram & Venkatesh | gm2023 |
| ERI0379 | Eriophyes erineus | (Nalepa) | gm2023 |
| ERI0441 | Neodicrothrix piperae | Mohanasundaram | gm2023;tn2020 |
| ERI0459 | Oxycenus diospyrosis | Ghosh, Mondal & Chakrabarti | gm2023 |
| ERI0490 | Phyllocoptruta daturae | Mohanasundaram & Ranganath | gm2023 |
| ERI0542 | Tegonotus ferrugeniae | Mohanasundaram | gm2023 |
| ERI0556 | Tetra buteae | Umapathy | gm2023 |
| ERI0573 | Tumescoptes trachycarpi | Keifer | gm2023 |
| TAR0011 | Fungitarsonemus baganbilasae | Missing | tarswb2023 |
| TAR0012 | Fungitarsonemus icchepaharicus | Missing | tarswb2023 |
| TAR0014 | Fungitarsonemus rishyapensis | Missing | tarswb2023 |
| TAR0024 | Steneotarsonemus furcatus | De Leon | gm2023;tarswb2023 |
| TAR0026 | Steneotarsonemus konoi | Smiley & Emmanouel | gm2023;tarswb2023 |
| PHY0049 | Amblyseius maai | Tseng | gm2023 |
| PHY0061 | Amblyseius parbatabasii | Karmakar et al. | gm2023 |
| PHY0074 | Asperoseius latericulus | Karmakar & Bhowmik | gm2023 |
| PHY0079 | Euseius asperivorous | Missing | gm2023 |
| PHY0097 | Euseius hima | (Pritchard & Baker) | gm2023 |
| PHY0187 | Phytoscutus keralaensis | Missing | gm2023 |
| PHY0188 | Phytoscutus keralicus | Missing | gm2023 |
| PHY0189 | Phytoscutus punicae | Missing | gm2023 |
| PHY0206 | Phytoseius imbricus | Missing | gm2023 |
| PHY0217 | Phytoseius mauritiana | Bhowmik & Karmakar | gm2023 |
| PHY0266 | Typhlodromips cinchonai | Molla & Karmakar | gm2023 |
| PHY0313 | Typhlodromus (Anthoseius) parandae | Missing | gm2023 |

## Tuckerellidae

Comparison with the user's *Tuckerella* review paper remains pending. Neither GenBank nor BOLD held a Tuckerellidae record in November 2026.

| Species ID | Name | Authority | Year |
| --- | --- | --- | --- |
| TUC0001 | Tuckerella channabasavannai | Mallik & Kumar | 1992 |
| TUC0002 | Tuckerella delhiensis | Ghai & Maninder | 1976 |
| TUC0003 | Tuckerella indica | Prasad | 1973 |
| TUC0004 | Tuckerella kumaonensis | Gupta | 1979 |

## Conflict flags

13 counted rows carry `authority_differs`, `year_differs_between_sources` or `family_differs`.

| Species ID | Name | Authority | Year | Flags |
| --- | --- | --- | --- | --- |
| TET0009 | Bryobia praetiosa | Koch | 1836 | authority_differs:koch/pritchard |
| TET0028 | Eotetranychus neoperplexus | Estebanes & Baker | 1950 | authority_differs:estebanes/mcgregor |
| TEN0044 | Larvacarus transitans | (Ewing) | 1922 | spelling_varies;year_differs_between_sources (set to 1922 in `authority_corrections.csv`, November 2026) |
| ERI0138 | Aceria cordiae | Channabasavanna | 1966 | authority_differs:channabasavanna/nalepa |
| ERI0212 | Aceria trichocnemum | (Nalepa) | 1929 | spelling_varies;year_differs_between_sources |
| ERI0234 | Aculops pretoriensis | Smith Meyer & Ueckermann | 1990 | authority_differs:meyersmith/smithmeyer |
| ERI0353 | Disella oblongifoliae | Ghosh, Mondal & Chakrabarti | 1986 | authority_differs:ghosh/ghosmondal |
| ERI0409 | Hemiscolocenus rares | Mohanasundaram | 1986 | family_differs:Diptilomiopidae(tn2020)/Eriophyidae(gm2023) |
| ERI0567 | Tetra tyrohylae | Smith Meyer | 1992 | authority_differs:meyersmith/smithmeyer |
| ERI0568 | Tetra visci | Smith Meyer | 1992 | authority_differs:meyersmith/smithmeyer |
| PHY0182 | Paraphytoseius cracentis | (Corpuz & Rimando) | 1966 | authority_differs:ai/gupta |
| PHY0216 | Phytoseius maldahaensis | Gupta | 1992 | spelling_varies;year_differs_between_sources |
| PHY0328 | Typhlodromus (Anthoseius) torbatejamae | Denmark and Danesshvar | 1982 | spelling_varies;year_differs_between_sources |

Absence from another checklist alone is not evidence of absence from India, nor proof that the other list under-reports it. For species found in a single regional list, verify the record and check broader sources and synonyms.

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

The original PDFs and the user's Tuckerella review are not embedded in this checklist repository. Page verification of the rows listed above remains open.

Correction inputs:

- [name_corrections.csv](data/checklist/name_corrections.csv): supported spelling/name changes.
- [authority_corrections.csv](data/checklist/authority_corrections.csv): supported author/year overrides with their basis.
- [duplicate_review.csv](data/checklist/duplicate_review.csv): reviewed same/different decisions and notes.
- [species_list_names.csv](data/checklist/species_list_names.csv): source-name mapping for later sequence matching.
- [species_list_review.csv](data/checklist/species_list_review.csv): non-exact joins and rejected joins.
- [species_list_summary.csv](data/checklist/species_list_summary.csv): current group/source counts.

After supported corrections, rebuild with `python scripts/build_species_list.py` and review all changed output rows. Species IDs can be reassigned on rebuild; locate a taxon using its name, authority and source as well as the snapshot ID. Update the README and this note when counts change.
