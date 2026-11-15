# V3-08 — Classical Delivery-Delay Baselines

## Scope and evaluation boundary

This report compares a prior DummyClassifier, LogisticRegression, and RandomForestClassifier for the V3-06 delivered-order calendar-delay label. It is a provisional classical comparison, not the final deployed-model decision. V3-09 must compare the small MLP on the same frozen splits before model selection.

All candidates use exactly the eight V3-07 predictors in frozen order: purchase_hour, purchase_weekday, purchase_month, promised_lead_days, customer_state, item_price_total, freight_total, item_count. Order ID, purchase timestamp, target, delivery outcomes, and other metadata are not predictors. Each candidate has its own preprocessing-plus-estimator Pipeline built with the shared V3-07 make_preprocessor. Imputers, scaler, and one-hot categories fit separately on training rows only. Validation is transform-only. No class weighting is used; candidates share the same training objective, while imbalance is described and thresholds are chosen on validation.

**The final test labels were not read by the V3-08 training/evaluation path. No test metrics were calculated.** The loader checks test row count, order ID uniqueness, purchase-date membership, and split assignment only. It does not index test target or feature columns. Test performance remains reserved until the V3-09 comparison and final selection protocol are complete.

## Frozen data and split verification

The local run used the V3-07 generated artifacts after validating the feature CSV SHA-256 against both its feature audit and split manifest, checking the exact schema and feature order, reconciling train/validation labels and partition row counts to the manifest, and checking the fixed boundaries.

| Partition | Purchase-date window | Rows | Late |
|---|---|---:|---:|
| Train | 2017-01-01 through 2017-12-31 | 43,426 | 2,453 |
| Validation | 2018-01-01 through 2018-03-31 | 20,627 | 2,657 |
| Test, reserved | 2018-04-01 through 2018-08-31 | 32,150 | Not evaluated |
| Excluded pre-window | Before 2017-01-01 | 267 | Not evaluated |
| Excluded post-window | From 2018-09-01 | 0 | Not evaluated |

Train prevalence is **5.64869%** (2,453/43,426). Validation prevalence is **12.88118%** (2,657/20,627), a substantial shift. The train and validation order IDs are disjoint. The feature schema, eligibility population, and V3-07 calendar boundaries were not changed.

## Candidate configurations

- **DummyClassifier:** prior strategy; emits the training class prior as the positive probability.
- **LogisticRegression:** C=1.0, lbfgs solver, max_iter=2000, random_state=42, no class weighting.
- **RandomForestClassifier:** 200 trees, max_depth=12, min_samples_leaf=5, max_features=sqrt, random_state=42, n_jobs=-1, no class weighting.

The fixed seed applies to LR and RF. The modest RF configuration is a single candidate, not a search. Fit warnings were captured per estimator; none were emitted in this run.

## Threshold policy and metrics

Positive class is late=1. Average Precision is sklearn average_precision_score and is reported as a stepwise ranking summary; it is not trapezoidal PR-AUC. ROC-AUC is threshold-free. For each candidate, the selected decision threshold maximizes validation F1 over the distinct observed validation probabilities plus 0, 0.5, and 1; ties choose the highest threshold. This policy is applied independently per candidate and is not retuned using test outcomes. F1 balances precision and recall through their harmonic mean; no operational cost ratio for false alerts versus missed delays was supplied, so this is a transparent comparison policy rather than a business-optimal decision rule. Conventional 0.5 metrics are also shown for context.

Confusion matrices are shown as rows actual class 0/1 and columns predicted class 0/1, i.e. [[TN, FP], [FN, TP]].

### Validation results at the validation-selected threshold

| Candidate | AP | ROC-AUC | Threshold | Precision | Recall | F1 | Predicted-positive rate | Actual prevalence | Confusion matrix |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| Dummy prior | 0.128812 | 0.500000 | 0.056487 | 0.128812 | 1.000000 | 0.228225 | 1.000000 | 0.128812 | [[0, 17,970], [0, 2,657]] |
| Logistic Regression | 0.270696 | 0.705939 | 0.036043 | 0.301967 | 0.427550 | 0.353949 | 0.182382 | 0.128812 | [[15,344, 2,626], [1,521, 1,136]] |
| Random Forest | 0.199838 | 0.624731 | 0.045893 | 0.202855 | 0.459917 | 0.281534 | 0.292044 | 0.128812 | [[13,168, 4,802], [1,435, 1,222]] |

### Validation results at threshold 0.5

| Candidate | Precision | Recall | F1 | Predicted-positive rate | Confusion matrix |
|---|---:|---:|---:|---:|---|
| Dummy prior | 0.000000 | 0.000000 | 0.000000 | 0.000000 | [[17,970, 0], [2,657, 0]] |
| Logistic Regression | 1.000000 | 0.000376 | 0.000752 | 0.000048 | [[17,970, 0], [2,656, 1]] |
| Random Forest | 0.000000 | 0.000000 | 0.000000 | 0.000000 | [[17,970, 0], [2,657, 0]] |

The prior Dummy's selected threshold predicts every validation row late; it is context, not a useful operational policy. The LR and RF 0.5 results show that their output probabilities are mostly below 0.5 under this fit and cohort. A validation-optimized threshold improves validation F1 but is also cohort-specific.

### Training ranking diagnostics

| Candidate | Training AP | Training ROC-AUC |
|---|---:|---:|
| Dummy prior | 0.056487 | 0.500000 |
| Logistic Regression | 0.135308 | 0.694215 |
| Random Forest | 0.363177 | 0.871120 |

LR is the provisional classical candidate by the declared validation Average Precision criterion (0.270696, highest among these three). This is not final model selection: RF's training/validation gap and temporal prevalence shift deserve scrutiny, and V3-09 still has to run the MLP comparison.

## Reproducibility, artifacts, and runtime

Reproduce the local comparison from the repository root with:

    .venv/bin/python -m src.ml.train_classical

The run used Python 3.10.20, scikit-learn 1.7.2, pandas 2.3.3, NumPy 2.2.6, and joblib 1.6.0. Per-model fit times were Dummy 0.024 s, LR 0.047 s, and RF 0.596 s; total experiment time including predictions, persistence, and reload verification was 52.658 s. These are local wall-clock observations, not performance guarantees.

Pipelines include their own fitted preprocessing and are saved only under ignored models/local/v3_08_classical/. Reloaded probabilities matched pre-save validation probabilities for all three candidates.

| Local artifact | SHA-256 | Size |
|---|---|---:|
| models/local/v3_08_classical/dummyclassifier.joblib | 09b163fb926f79dc421462b9a63d34c23745d20934ce1de81c0c1c6a5ceefb5f | 4,338 bytes |
| models/local/v3_08_classical/logisticregression.joblib | 4532b8de92bd50f7bb2130595907ed4f45409e24d097ae788d120ae75a1f20d4 | 4,890 bytes |
| models/local/v3_08_classical/randomforestclassifier.joblib | 218c4e3f387c2acfd0996fe328df7d9aadee93053cea2834c1d763a9688e8167 | 11,749,019 bytes |

The ignored local metrics JSON is data/processed/v3_08_classical_metrics.json. It records candidate configs, train/validation metrics, threshold rules, package versions, row counts, warnings, runtime, and artifact metadata. It explicitly records that test metrics were not generated.

Input provenance:

- V3-07 feature CSV SHA-256: 93c358f9f5ed781613aa6645fd5cdaa570453304d0fe5d758324a78ee4d78548
- V3-07 split CSV SHA-256 for this run: 8c4178a81971a65e8a3d1e8af10bf5bae05fb4cc2465878eb53c4f8ee4558722
- Split manifest version: v1

The raw dataset files, processed datasets, fitted pipelines, and metrics JSON remain ignored and untracked. No model binary or data artifact is part of this documentation.

## Limitations and V3-09 handoff

Validation prevalence (12.88%) is more than twice training prevalence (5.65%). Precision depends on prevalence, and the validation-selected thresholds may not transfer to another period or deployment population. No probability calibration was performed, so scores should not be interpreted as calibrated individual risk. The F1 threshold policy encodes a particular precision/recall tradeoff; it is not a cost-based operational threshold.

The label is retrospective and conditional on eventual delivery. No extraction timestamp proves complete follow-up; unresolved/non-delivered orders are not negative examples. The historical extract does not prove that final promise dates, cart/item amounts, or customer state were available in the same form at order creation. These limitations constrain claims about live deployment.

V3-09 should use the same feature rows, chronological partitions, and validation-only threshold/evaluation protocol for its small MLP comparison. Keep the final test untouched until classical and MLP candidates, features, and threshold policy are frozen. Logistic Regression is only the provisional classical AP leader; no final deployed model is selected here.
