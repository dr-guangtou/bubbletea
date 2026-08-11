# Large-sky development retrieval benchmark and pilot

**Status:** Single-field benchmark and 12-field development pilot complete
**Date:** 2026-07-19
**Issues:** BT-009, BT-022

## What was measured

All fields use the frozen 0.8-degree circles, exact spherical areas, 19 raw Gaia
columns, G-magnitude range, 5,000-row strip limit, selector version, and probability
threshold. Gaia was queried only for the 12 frozen development fields. None of the
102 held-back validation fields was queried or scored.

Raw Gaia rows are stored as verified strip checkpoints outside the repository at
`~/Dropbox/work/data/bubbletea/gaia_large_sky_v1`. The repository retains measured
strip plans, compact field summaries, and provenance manifests.

A passing source is a search candidate selected by
`point_source_logistic_model_v1`; it is not a confirmed UCD.

## Single-field performance benchmark

`sky_field_0000` is the development field closest to the declared
`|b| = 20` degree boundary. It was chosen from position alone before its Gaia count
was known.

| Measurement | Result |
|---|---:|
| Gaia sources in the frozen magnitude range | 84,025 |
| Sources passing the frozen selector | 1,393 |
| Passing-source density per square degree | 692.832618 |
| Final retrieval strips | 26 |
| Largest strip | 4,982 rows |
| External checkpoint CSV bytes | 17,369,345 |
| Measured planning time | 87.086338 seconds |
| Measured retrieval time | 43.725160 seconds |
| Local selector time | 2.161201 seconds |
| Total measured time | 133.357677 seconds |

The run deliberately stopped after retrieving one strip. On resume, that strip was
verified and skipped, and the remaining 25 were downloaded. All 18 benchmark
safeguards pass. This confirms that the 5,000-row limit and persistent restart
mechanism work for a substantially denser 0.8-degree field.

## Twelve-field pilot result

| Field | Galactic latitude | Ecliptic latitude | Gaia sources | Passing candidates | Passing density per square degree |
|---|---:|---:|---:|---:|---:|
| `sky_field_0000` | 20.080258 | 4.592953 | 84,025 | 1,393 | 692.832618 |
| `sky_field_0067` | 31.310434 | -4.243134 | 11,911 | 960 | 477.472586 |
| `sky_field_0126` | 42.450885 | 48.038246 | 14,969 | 852 | 423.756920 |
| `sky_field_0151` | 47.795850 | -7.017217 | 7,002 | 481 | 239.233660 |
| `sky_field_0220` | 67.273333 | 29.317707 | 7,708 | 754 | 375.014927 |
| `sky_field_0275` | -24.150451 | -79.497819 | 24,779 | 812 | 403.862229 |
| `sky_field_0299` | -28.183708 | -46.372292 | 41,893 | 1,425 | 708.748370 |
| `sky_field_0302` | -28.698198 | -4.040004 | 40,952 | 1,081 | 537.654027 |
| `sky_field_0357` | -38.678626 | -7.318965 | 22,443 | 1,374 | 683.382639 |
| `sky_field_0429` | -54.532984 | -33.083639 | 5,779 | 696 | 346.167625 |
| `sky_field_0432` | -55.320275 | -60.348961 | 7,745 | 1,251 | 622.206464 |
| `sky_field_0483` | -73.052711 | -14.650003 | 6,198 | 504 | 250.673108 |

Together, the fields contain 275,404 Gaia sources and 11,583 passing candidates
over 24.127040 square degrees. The combined density is 480.083765 per square
degree, retained for count and area auditing only. Individual densities span
239.233660–708.748370, with a median of 450.614753.

The pilot used 83 final strips. Planning took 182.383724 seconds in total,
retrieval took 109.159825 seconds, and local scoring took 0.256445 seconds during
the batch run. The benchmark plan and all 26 benchmark checkpoints were reused
without another download. All nine aggregate safeguards pass.

## Interpretation and limits

The measured spread confirms that one latitude-only density value will not be
adequate. It does not yet show which combination of Galactic latitude, ecliptic
latitude, Gaia depth, observation counts, or environment flags best predicts the
passing-source density. The pilot was chosen for positional coverage rather than
statistical representativeness and is too small for the final model.

The four environment-flagged pilot fields are retained. Their combined result must
not be interpreted as an environment effect because the fields were not matched in
latitude or Gaia conditions. The full development analysis must measure those
conditions and use a declared comparison before deciding whether an environment
flag changes the model or sensitivity analysis.

## Artifacts and reproduction

- `data/results/background/large_sky_development_benchmark_plan_v1.csv`
- `data/results/background/large_sky_development_benchmark_summary_v1.csv`
- `data/results/background/large_sky_development_benchmark_v1.json`
- `data/results/background/large_sky_development_retrieval_plan_v1.csv`
- `data/results/background/large_sky_development_retrieval_summary_v1.csv`
- `data/results/background/large_sky_development_retrieval_v1.json`

```bash
BUBBLETEA_EXTERNAL_DATA="$HOME/Dropbox/work/data" \
  uv run python scripts/phase3_background/benchmark_large_sky_development_retrieval.py

BUBBLETEA_EXTERNAL_DATA="$HOME/Dropbox/work/data" \
  uv run python scripts/phase3_background/run_large_sky_development_retrieval.py
```
