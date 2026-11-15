# T-00 audit reproduction

## Reproduction and validation

From `/Users/wageehgadd/Desktop/olist-intelligence`:

```sh
.venv/bin/python -B scripts/audit/run.py
.venv/bin/python -B scripts/audit/supplement.py
.venv/bin/python -B scripts/audit/baselines.py
.venv/bin/python -B scripts/audit/report.py
.venv/bin/python -B -m pytest tests/audit -q
```

Audit configuration: scripts/audit/config.json. Dependency specification: scripts/audit/requirements.txt. Aggregate JSON/CSV outputs: data/processed/t00/ (ignored). At the time this T-00 audit reproduction guide was first written, the Markdown reports were reviewable working-tree changes and no audit commit or push had occurred. The reports and scripts were later published in the initial team-sharing commit; this sentence records the original as-run context, not the current repository state. No raw records, review texts, IDs or coordinates are exported in reports. Raw-file hashes are checked during run and by tests. Baseline models are not saved. Numerical summaries are deterministic for the fixed snapshot; library/platform changes may affect floating-point results. Environment versions are recorded in statistics.json.

Known limits: no causal analysis, exhaustive language/PII annotation, clustered confidence intervals, calibrated or tuned final models, historical version reconstruction, net-profit data, external customer history or neural training. Geographical box filtering is approximate. Outlier flags do not justify deleting source rows. Automated tests protect important contracts but are not a complete proof of scientific validity.
