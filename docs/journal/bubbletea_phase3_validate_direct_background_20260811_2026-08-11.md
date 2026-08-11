---
date: 2026-08-11
repo: bubbletea
branch: phase3_validate_direct_background_20260811
tags:
  - journal
  - phase3
  - background
  - validation
---

## Progress

- Froze contract `validation_run_contract_d75e3ddea7013547c088` before opening any
  of the 102 reserved large-sky fields; all 11 contract safeguards passed.
- Retrieved all 102 fields in bounded, resumable batches without a failed attempt:
  1,534,299 Gaia sources, 86,189 passing sources, and 459 verified strips over
  205.079837 square degrees.
- Verified every external field receipt, source checkpoint hash, metadata hash, and
  the cumulative source count; all 17 retrieval safeguards passed.
- Applied the unchanged direct latitude-band procedure once. Its validation typical
  density difference is a factor of 1.197, with 63/102 fields inside the 68% range
  and 94/102 inside the 95% range.
- Applied the unchanged fitted diagnostic without refitting. Its validation typical
  difference is a factor of 1.128, with 66/102 fields inside the 68% range and
  100/102 inside the 95% range; it remains secondary.
- Preserved every validation comparison pool, measured range, fitted value, and
  residual; all 20 evaluation safeguards passed.

## Lessons Learned

- The direct procedure transferred consistently: its validation typical difference
  is close to development, and its 95% coverage increased from 90.95% to 92.16%.
- A numerically tighter fitted diagnostic does not override its predeclared
  secondary role after validation results are opened.
- Historical metric columns require an explicit name mapping before development and
  validation differences are calculated.

## Key Issues

- The direct 95% ranges still cover 92.16%, not 95%, of reserved fields; keep this
  measured limitation visible rather than widening the ranges after validation.
- Eight direct results and two fitted-diagnostic results lie outside their frozen
  95% ranges and remain preserved field-level outcomes.
- The next scientific task is calibrating the central galaxy exclusion and
  concentric outer annuli before a small official real-host run.
- Repository-wide pre-commit remains blocked by 13 pre-existing Ruff errors in
  archived notebooks and older scripts; all task-specific hooks pass.
