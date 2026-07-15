# Voggel et al. (2020)

**Title:** A Gaia-based Catalog of Candidate Stripped Nuclei and Luminous
Globular Clusters in the Halo of Centaurus A

**Authors:** Voggel, K. T.; Seth, A. C.; Sand, D. J.; Hughes, A.; Strader, J.;
Crnojevic, D.; Caldwell, N.

**Journal:** The Astrophysical Journal, Volume 899, Article 140
**ADS Bibcode:** `2020ApJ...899..140V`
**DOI:** `10.3847/1538-4357/ab6f69`
**VizieR Catalog:** `J/ApJ/899/140`
**Retrieval Date:** 2026-07-14

The previous repository metadata incorrectly used bibcode suffix `W`, a different
title, DOI `10.3847/1538-4357/aba842`, and an unrelated arXiv identifier. The
bibliographic identity above was verified against NASA ADS and the original VizieR
`ReadMe` on 2026-07-14. The incorrect legacy bibcode is retained only as an alias
in the v2 reference model.

## Data Files

| File | Description |
|---|---|
| `Voggel_2020_ApJ_899_140.pdf` | Locally retained paper PDF |
| `ReadMe.txt` | Original VizieR schema and provenance |
| `table2.dat` | 632 Gaia-selected candidate luminous clusters |
| `table3.dat` | 14 MIKE spectroscopic targets |
| `table4.dat` | 57 previously confirmed objects used for completeness |
| `J_ApJ_899_140_table2.dat.fits` | FITS conversion of Table 2 |
| `J_ApJ_899_140_table3.dat.fits` | FITS conversion of Table 3 |
| `J_ApJ_899_140_table4.dat.fits` | FITS conversion of Table 4 |

Raw VizieR file URLs, byte counts, and SHA-256 hashes are recorded in
`data/literature/validation/vizier_retrieval.json`. Catalog membership and Gaia
extendedness are candidate evidence, not confirmation by themselves.

The derived FITS conversions are retained for compatibility and have the
following local-file digests:

| File | Bytes | SHA-256 |
|---|---:|---|
| `J_ApJ_899_140_table2.dat.fits` | 72000 | `a12d0e7b6ceae50eb34da37695e46891d7a65c3900670cd2aafeadadb7f933e2` |
| `J_ApJ_899_140_table3.dat.fits` | 20160 | `bb11b30b4bf4566e42a382a90cf0be1b5026fcbee8d134d4c2e63f9ed66adeb3` |
| `J_ApJ_899_140_table4.dat.fits` | 20160 | `6d57fbe7384186c05a1ae59d02347c2dbfdbb80cc56bc86915336ed3fad1c494` |

The locally retained `Voggel_2020_ApJ_899_140.pdf` is 2361813 bytes with SHA-256
`aba5a56a2ff18488a24fe0c70d24b8cefc7f3f20f533f220bf4a03260214256d`.

Table 4 is ingested as a reference/comparison sample distinct from the 632 new
Gaia-selected table 2 candidates. Row-level review approved 34 sub-arcsecond
associations to existing Fahrion or Dumont objects and retained 22 rows as new
reference objects. T17-1596 is additionally associated with Fahrion HHH86-C15 at
1.37 arcseconds through the published Taylor GC0218 and Woodley HHH86-C15 alias
chain. All reported confirmations remain pending object-level evidence review.
