# T-00 — 10 RISKS AND DECISIONS

## Risk register and mitigations

- **Instructor approval — high:** project approval is unconfirmed; obtain it before committing to production scope. No academic deadline was invented.
- **Incomplete capture/censoring — high:** historical marketplace extract, sparse final months, unknown extraction time. Declare observation limits and fixed follow-up; keep unknown outcomes unlabeled.
- **Selection bias — high:** delivered/reviewed/text-present cohorts differ from all purchasers. Report cohort denominators and status/text-response distributions.
- **Temporal leakage — high:** static revised fields and full-history aggregates. Instrument event-time contracts; test as-of features and embargo label boundaries.
- **Class imbalance/drift — high:** low late prevalence and month variation. Use AP, monthly cohorts, calibration and capacity-based top-K evaluation.
- **Review ambiguity — medium:** score conflicts and survey-generation timestamps. Use unanimous labels, sensitivity definitions and answer-time maturity.
- **Join inflation — high:** several one-to-many children and duplicated geolocation. Validate keys, aggregate each child separately and reconcile money in cents.
- **Catalog/geography errors — medium:** missing attributes, zero dimensions, unmatched ZIP/categories. Missing flags, screened coordinates, no fabricated values.
- **Privacy/license — high:** free text may contain identifiers; no raw exports, mask demo snippets and verify publisher license before redistribution/commercialization.
- **DL compute — medium:** no measured GPU budget. Begin classical baseline, one small CNN fallback, approve transformer resources separately.
- **Integration/deployment — medium:** versioned feature schema, unknown cold-start and latency. Validate feature contracts and package/version compatibility before serving.
- **Scope/team workload — high:** four students and broad technology list. Prioritize three coherent modules; no task assignment made in audit.

## SQL Business Analytics

**GO; MVP.** Nine relational tables support observed sales, freight, payments, delivery and reviews; preserve grain and distinguish recorded payments from net revenue. Scientific/engineering condition: validate population and evaluation gates before claiming usefulness; difficulty medium.

## Customer Segmentation

**CONDITIONAL GO; MVP descriptive; Advanced clustering.** 96,096 customers; only 3.12% repeat. Use descriptive recency/monetary and cohort profiles; benchmark clustering stability against seller/order/category alternatives. Scientific/engineering condition: validate population and evaluation gates before claiming usefulness; difficulty medium.

## Future Customer Value Prediction

**NO-GO; Deferred.** 90-day windows have only 210, 233 and 299 repeat buyers. Zero-heavy observed marketplace payments are not lifetime value or profit. Scientific/engineering condition: validate population and evaluation gates before claiming usefulness; difficulty high.

## Delivery Delay Prediction

**CONDITIONAL GO; MVP.** 96,470 calendar-label examples, 6,534 late. Lightweight out-of-time lift exists; delivered-only selection and availability assumptions limit deployment claims. Scientific/engineering condition: validate population and evaluation gates before claiming usefulness; difficulty medium.

## Review Risk Prediction

**CONDITIONAL GO; Advanced.** 98,400 purchase-stage labels; weak out-of-time purchase baseline. Prefer post-delivery intervention only for reviews not yet created. Scientific/engineering condition: validate population and evaluation gates before claiming usefulness; difficulty high.

## Portuguese Review NLP

**GO; MVP primary DL track.** 40,950 nonempty messages; strong classical baseline. Ratings are weak sentiment labels, and actual language proportions need manual validation. Scientific/engineering condition: validate population and evaluation gates before claiming usefulness; difficulty medium.

## Tabular Deep Learning

**CONDITIONAL GO; Optional.** Enough rows for an MLP comparison; no evidence it beats trees, little justification for a complex tabular network. Scientific/engineering condition: validate population and evaluation gates before claiming usefulness; difficulty high.

## FastAPI Model Serving

**GO; MVP future architecture.** Serve versioned feature contracts and probabilities; no backend implemented in T-00. Scientific/engineering condition: validate population and evaluation gates before claiming usefulness; difficulty medium.

## Explainable AI

**GO; MVP.** Explain fitted predictions, not causality. Verify SHAP compatibility later; logistic coefficients provide a baseline. Scientific/engineering condition: validate population and evaluation gates before claiming usefulness; difficulty medium.

## MLflow / MLOps

**GO; Advanced lightweight tracking.** Record hashes, splits, parameters and metrics; avoid an elaborate platform for four students. Scientific/engineering condition: validate population and evaluation gates before claiming usefulness; difficulty medium.
## Provenance and license

Source: [Olist Kaggle dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce), checked 2026-10-10. Local file SHA-256 hashes identify this audit snapshot; they do not prove it is an unmodified publisher release, and download/version metadata was not supplied. Publisher page was accessible but its dynamic license field did not render in the browsing tool. CC BY-NC-SA 4.0 is the reported dataset license in available search metadata/independent references, but primary publisher metadata confirmation remains an explicit release gate. Do not treat this audit as a definitive licensing determination.

If confirmed, [Creative Commons BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/) requires credit, license link, indication of changes, noncommercial use and compatible sharing of adaptations. Public access does not mean unrestricted redistribution. Keep raw data and generated derivatives out of Git, link the publisher, and verify terms before publishing data, review examples or commercial services. Model-card licensing does not override dataset obligations.

## Reproduction and validation

From `/Users/wageehgadd/Desktop/olist-intelligence`:

```sh
.venv/bin/python -B scripts/audit/run.py
.venv/bin/python -B scripts/audit/supplement.py
.venv/bin/python -B scripts/audit/baselines.py
.venv/bin/python -B scripts/audit/report.py
.venv/bin/python -B -m pytest tests/audit -q
```

Audit configuration: scripts/audit/config.json. Dependency specification: scripts/audit/requirements.txt. Aggregate JSON/CSV outputs: data/processed/t00/ (ignored). Markdown reports are reviewable repository changes; nothing was committed or pushed. No raw records, review texts, IDs or coordinates are exported in reports. Raw-file hashes are checked during run and by tests. Baseline models are not saved. Numerical summaries are deterministic for the fixed snapshot; library/platform changes may affect floating-point results. Environment versions are recorded in statistics.json.

Known limits: no causal analysis, exhaustive language/PII annotation, clustered confidence intervals, calibrated or tuned final models, historical version reconstruction, net-profit data, external customer history or neural training. Geographical box filtering is approximate. Outlier flags do not justify deleting source rows. Automated tests protect important contracts but are not a complete proof of scientific validity.
