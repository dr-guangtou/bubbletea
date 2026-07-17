# Logistic regularization sensitivity

**Date:** 2026-07-18  
**Benchmark:** v3 development partition only  
**Validation partition:** Sealed and uninspected

The original grid ended at `C = 3`. All 50 repeated outer fits selected that
boundary, so the nested comparison grid was expanded first through `C = 100` and
then through `C = 3000`.

With the grid ending at 100, four of five outer folds selected 100 and one selected
30. With the grid ending at 3000, four folds selected 3000 and one selected 100.
The resulting pooled logistic recall is 92.47%, and macro priority-contaminant
retention is 2.18%. Individual-fold recall remains 80.77--97.30%, so the apparent
contaminant improvement does not remove fold instability.

This experiment shows that `C = 3` imposed more regularization than the current
inner objective prefers. It does not justify selecting 3000: the preference remains
at the search boundary, and repeatedly enlarging the grid would convert small,
fold-specific retention differences into an effectively unregularized model choice.
The correct next comparison is therefore explicit weakly regularized versus
unregularized logistic regression, assessed for coefficient and prediction
convergence as well as grouped-CV behavior. No `C` or threshold is frozen.

That direct comparison uses `C = 100, 300, 1000, 3000` and an explicitly
unregularized fit. At the fixed grouped-OOF 90% recall operating point, all models
measure 90.41% UCD recall. Macro priority retention is 2.25%, 1.91%, 1.88%, 2.03%,
and 2.03%, respectively. Thus `C = 3000` and the unregularized model already make
identical aggregate selection decisions, while `C = 1000` is slightly better on
this fixed split and retains a finite regularization safeguard. Full-development
probability correlation with the unregularized model rises from 0.955 at `C = 100`
to 0.991 at 1000 and 0.997 at 3000. Raw coefficient vectors converge more slowly,
so coefficient equality is not claimed.

The measured candidate for repeated stability is `C = 1000`, compared directly
against `C = 3000` and unregularized logistic regression. This is a development-only
candidate, not a frozen hyperparameter.

Across ten fixed grouped repeats, all three configurations retain exactly 90.41%
of reliable UCDs. Median macro priority retention is 1.96% for `C = 1000`, 2.11%
for `C = 3000`, and 2.11% for the unregularized fit. `C = 1000` has the lowest
paired retention in seven repeats, versus one for 3000 and two for unregularized.
Its maximum fold coefficient-vector norm is 5.35, compared with 7.01 and 12.94.
The evidence therefore recommends `C = 1000`: it gives the best repeated retention
at identical measured recall and avoids unnecessary coefficient growth. Project-lead
approval is still required before recording it as the frozen regularization policy.

The project lead approved `C = 1000` on 2026-07-18. The frozen regularization and
subsequently approved threshold are recorded in
`data/literature/sources/point_source_logistic_policy_v1.json`.

The frozen threshold is 0.8277833629, defined as the median of ten grouped-OOF
thresholds individually calibrated to retain at least 90% of reliable UCDs. It is
not an in-sample quantile and was not selected using validation data.

Artifacts:

- `data/literature/validation/point_source_ml_comparison_v4.json` (`C <= 100`)
- `data/literature/validation/point_source_ml_comparison_v5.json` (`C <= 3000`)
- `data/literature/validation/point_source_ml_fold_metrics_v5.csv`
- `data/literature/validation/logistic_regularization_convergence_v1.json`
- `data/literature/validation/logistic_regularization_convergence_coefficients_v1.csv`
- `data/literature/validation/logistic_regularization_stability_v1.json`
- `data/literature/validation/logistic_regularization_stability_metrics_v1.csv`
- `data/literature/validation/logistic_regularization_stability_validation_v1.json`
