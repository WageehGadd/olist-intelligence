# T-00 validation record

Executed on 2026-10-10 in the existing project Python 3.10.20 environment.

- `scripts/audit/run.py`: completed; all nine datasets loaded, profiling/relations/temporal/targets/customer/text aggregates written. Raw hashes identical before and after.
- `scripts/audit/supplement.py`: completed; validated item-grain joins, geography distance/coverage, catalog and payment screening.
- `scripts/audit/baselines.py`: completed; three dummy-versus-classical chronological experiments; no model files saved.
- `scripts/audit/report.py`: completed; all 12 required Markdown reports, reproduction README and machine-readable feature matrix generated.
- `.venv/bin/python -B -m pytest tests/audit -q`: **9 passed in 2.25s**. Tests cover calendar boundaries, conflicting labels, chronology, missing inputs, raw hashes, label totals, maturity purging, financial join grain and report sections/no raw identifiers.
- Independent standard-library `csv.reader` pass: all nine source row counts and column counts matched profiling outputs; every row had the expected column width.
- `git diff --check`: passed. New files are untracked, so this check alone does not cover all new file whitespace.
- `git check-ignore`: raw data, processed outputs and virtual environment remain excluded.
- Report scan: no 32-character hexadecimal raw identifiers. Code intentionally never exports review texts, customer IDs or coordinate records. No exhaustive PII detector or legal review was performed.

Corrections during execution: explicitly parsed `order_approved_at`; standardized mixed-format synthetic timestamp fixture. Failed runs were repaired and successful executions followed. No warning was suppressed, no dependencies installed, no raw files modified, and no commit/push occurred.

Workstreams A–H and J delivered with limitations documented; I lightweight baselines executed. Partial checks: primary publisher license metadata confirmation, validated language proportions/human sentiment annotations, historical feature availability, rolling/grouped sensitivity, calibration and uncertainty, neural experiments and actual deployment resources. None blocks a bounded planning handoff; all constrain later claims and public release.
