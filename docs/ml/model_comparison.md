# V3-08 — Classical Delivery-Delay Baselines

## Scope and evaluation boundary

This report compares a prior DummyClassifier, LogisticRegression, and RandomForestClassifier for the V3-06 delivered-order calendar-delay label. It is a provisional classical comparison, not the final deployed-model decision. V3-09 must compare the small MLP on the same frozen splits before model selection.

All candidates use exactly the eight V3-07 predictors in frozen order: purchase_hour, purchase_weekday, purchase_month, promised_lead_days, customer_state, item_price_total, freight_total, item_count. Order ID, purchase timestamp, target, delivery outcomes, and other metadata are not predictors. Each candidate has its own preprocessing-plus-estimator Pipeline built with the shared V3-07 make_preprocessor. Imputers, scaler, and one-hot categories fit separately on training rows only. Validation is transform-only. No class weighting is used; candidates share the same training objective, while imbalance is described and thresholds are chosen on validation.

**Held-out rows are parsed only to verify the split artifact's integrity; they are not used for model fitting, validation metrics, threshold optimization, candidate selection, or test performance evaluation. No test metrics were generated.** Before fitting, the loader hashes the canonical V3-07 feature CSV against the audit and manifest, reconstructs the complete deterministic split from that verified feature artifact, and requires exact byte-for-byte equality with the split CSV. This integrity check necessarily reads held-out feature and target values from the canonical feature artifact, but those values do not enter training or evaluation. Test performance remains reserved until the V3-09 comparison and final selection protocol are complete.

## Frozen data and split verification

The local run used the V3-07 generated artifacts after validating the feature CSV SHA-256 against both its feature audit and split manifest, checking the exact schema and feature order, reconstructing the full split from the verified feature CSV and matching the split artifact byte-for-byte, reconciling train/validation labels and partition row counts to the manifest, and checking the fixed boundaries. The held-out labels and predictors were parsed only as part of that exact artifact-integrity check; test outcomes did not affect any fitted model, validation metric, threshold, candidate choice, or reported performance result.

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

The run used Python 3.10.20, scikit-learn 1.7.2, pandas 2.3.3, NumPy 2.2.6, and joblib 1.6.0. Per-model fit times were Dummy 0.026 s, LR 0.053 s, and RF 0.608 s; total experiment time including predictions, persistence, and reload verification was 54.438 s. These are local wall-clock observations, not performance guarantees.

Pipelines include their own fitted preprocessing and are saved only under ignored models/local/v3_08_classical/. Reloaded probabilities matched pre-save validation probabilities for all three candidates.

| Local artifact | SHA-256 | Size |
|---|---|---:|
| models/local/v3_08_classical/dummyclassifier.joblib | 09b163fb926f79dc421462b9a63d34c23745d20934ce1de81c0c1c6a5ceefb5f | 4,338 bytes |
| models/local/v3_08_classical/logisticregression.joblib | 4532b8de92bd50f7bb2130595907ed4f45409e24d097ae788d120ae75a1f20d4 | 4,890 bytes |
| models/local/v3_08_classical/randomforestclassifier.joblib | 218c4e3f387c2acfd0996fe328df7d9aadee93053cea2834c1d763a9688e8167 | 11,749,019 bytes |

The ignored local metrics JSON is data/processed/v3_08_classical_metrics.json. It records candidate configs, train/validation metrics, threshold rules, package versions, row counts, warnings, runtime, and artifact metadata. It states that held-out rows were read only to verify split-artifact integrity and records that no test metrics were generated; it does not claim held-out labels or predictors were never accessed.

Input provenance:

- V3-07 feature CSV SHA-256: 93c358f9f5ed781613aa6645fd5cdaa570453304d0fe5d758324a78ee4d78548
- V3-07 split CSV SHA-256 for this run: 8c4178a81971a65e8a3d1e8af10bf5bae05fb4cc2465878eb53c4f8ee4558722
- Split manifest version: v1

The raw dataset files, processed datasets, fitted pipelines, and metrics JSON remain ignored and untracked. No model binary or data artifact is part of this documentation.

## Limitations and V3-09 handoff

Validation prevalence (12.88%) is more than twice training prevalence (5.65%). Precision depends on prevalence, and the validation-selected thresholds may not transfer to another period or deployment population. No probability calibration was performed, so scores should not be interpreted as calibrated individual risk. The F1 threshold policy encodes a particular precision/recall tradeoff; it is not a cost-based operational threshold.

The label is retrospective and conditional on eventual delivery. No extraction timestamp proves complete follow-up; unresolved/non-delivered orders are not negative examples. The historical extract does not prove that final promise dates, cart/item amounts, or customer state were available in the same form at order creation. These limitations constrain claims about live deployment.

V3-09 should use the same feature rows, chronological partitions, and validation-only threshold/evaluation protocol for its small MLP comparison. Keep final test outcomes out of model selection and performance evaluation until classical and MLP candidates, features, and threshold policy are frozen. Held-out rows may be read solely for split-artifact integrity verification. Logistic Regression is only the provisional classical AP leader; no final deployed model is selected here.


# V3-09 — Small MLP comparison and final model selection

## Environment and method

The existing project environment uses Python 3.10.20, scikit-learn 1.7.2, NumPy 2.2.6, pandas 2.3.3, and joblib 1.6.0. TensorFlow/Keras and PyTorch were not available, so V3-09 used the already installed scikit-learn `MLPClassifier`; no dependency was installed or changed. Its `partial_fit` API permits one bounded training epoch at a time. This was suitable for the requested small feed-forward experiment on the existing laptop environment.

Reproduce the validation run once in a fresh local artifact state with `.venv/bin/python -m src.ml.train_mlp`; the command refuses to overwrite existing V3-09 outputs. After reviewing the frozen selection manifest, the separate `.venv/bin/python -m src.ml.train_mlp --evaluate-test-once` command performs only the one-time final evaluation and refuses a second claim. The sole architecture was a 32-unit then 16-unit ReLU hidden network with binary logistic output, Adam, learning rate 0.001, alpha 0.0001, batch size 256, and random seed 42. Training was capped at 120 epochs. The numeric scaler/imputers and categorical imputer/one-hot encoder were fitted on the 43,426 training rows only. Early stopping was implemented externally against binary cross-entropy on the fixed chronological validation partition, with patience 12 and minimum improvement 1e-5; the weights at the best validation-loss epoch were restored (best epoch 23; patience stopped the run at epoch 35; fit time 1.052 seconds). No fit warnings were recorded. No random internal early-stopping holdout, architecture search, class weighting, or test-driven tuning was used. A seed fixes the intended random stream, but bit-for-bit equivalence across platforms/library builds is not claimed.

The same V3-07 feature artifact, eight predictors in frozen order, target, and chronological partitions were validated using the V3-08 integrity loader. Reference counts were train 43,426 (2,453 late), validation 20,627 (2,657 late), and reserved test 32,150. All V3-08 fitted candidate checksums were verified against the existing local metrics record before comparison.

## Validation comparison and final selection

Primary ranking was declared before the test was accessed: highest validation Average Precision (`sklearn.average_precision_score`). Exact ties prefer Logistic Regression, then Random Forest, then Small MLP, then Dummy. Each candidate retains the shared V3-08 validation-F1 threshold policy (maximize F1 over observed validation probabilities plus 0, 0.5, and 1; ties choose the higher threshold); thresholds do not affect AP ranking. The MLP threshold is selected on validation only.

| Candidate | Validation AP | ROC-AUC | F1 threshold | Precision | Recall | F1 | Prevalence | Predicted-positive rate | Confusion matrix [[TN, FP], [FN, TP]] |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| Dummy prior | 0.128812 | 0.500000 | 0.056487 | 0.128812 | 1.000000 | 0.228225 | 0.128812 | 1.000000 | [[0, 17,970], [0, 2,657]] |
| Logistic Regression | 0.270696 | 0.705939 | 0.036043 | 0.301967 | 0.427550 | 0.353949 | 0.128812 | 0.182382 | [[15,344, 2,626], [1,521, 1,136]] |
| Random Forest | 0.199838 | 0.624731 | 0.045893 | 0.202855 | 0.459917 | 0.281534 | 0.128812 | 0.292044 | [[13,168, 4,802], [1,435, 1,222]] |
| Small MLP | 0.161813 | 0.545081 | 0.016790 | 0.134275 | 0.941287 | 0.235023 | 0.128812 | 0.902991 | [[1,845, 16,125], [156, 2,501]] |

Threshold-0.5 validation context (the same shared metrics; it does not alter ranking or the selected validation threshold):

| Candidate | Precision | Recall | F1 | Predicted-positive rate | Confusion matrix [[TN, FP], [FN, TP]] |
|---|---:|---:|---:|---:|---|
| Dummy prior | 0.000000 | 0.000000 | 0.000000 | 0.000000 | [[17,970, 0], [2,657, 0]] |
| Logistic Regression | 1.000000 | 0.000376 | 0.000752 | 0.000048 | [[17,970, 0], [2,656, 1]] |
| Random Forest | 0.000000 | 0.000000 | 0.000000 | 0.000000 | [[17,970, 0], [2,657, 0]] |
| Small MLP | 0.000000 | 0.000000 | 0.000000 | 0.000000 | [[17,970, 0], [2,657, 0]] |

The MLP validation values above are from the verified local run and are recorded in ignored `data/processed/v3_09_mlp_metrics.json`. Logistic Regression remains the final candidate by the declared validation AP criterion (0.270696); the MLP AP was 0.161813. Final selection is frozen with the unchanged candidate threshold in `data/processed/v3_09_model_selection.json`. The manifest records the chosen candidate, rationale, selected artifact SHA-256, feature/split hashes, split boundaries, validation comparison hash, and UTC freeze time. The manifest is created exclusively and the run refuses to overwrite prior V3-09 outputs.

The selected-model-only final test evaluation was executed exactly once on 2026-11-16 UTC, after the validation comparison and selection manifest were frozen and reverified. Before test target/predictor fields were extracted, the gate verified selection and artifact provenance, then exclusively created `data/processed/v3_09_final_test_claimed.json`. This durable claim is never removed or reset; an existing claim or result causes refusal. Results were written once to `data/processed/v3_09_final_test_metrics.json`. On 32,150 reserved test orders, 1,421 were late (4.41991% prevalence). With the frozen Logistic Regression and unchanged validation threshold 0.0360428262, test AP was 0.078627, ROC-AUC 0.671692, precision 0.065669, recall 0.710063, F1 0.120219, predicted-positive rate 0.477916, and confusion matrix [[16,373, 14,356], [412, 1,009]]. No sensitivity analysis was performed. The lower test prevalence and ranking score show material temporal generalization degradation; these results are reported without changing model selection.

## One-time final-test gate remediation

Independent review found that the original `evaluate_final_test_once` exposed caller-controlled claim and metrics paths. A caller could supply fresh destinations and bypass the existing marker; that implementation did not fully enforce a one-time evaluation.

The real-data evaluation and its claim/metrics were recorded before this remediation. The corrected public function accepts no path overrides and uses only the fixed project files under `data/processed/`. It resolves and checks canonical paths, rejects symlink aliases and output/input collisions before writing, checks the claim and result state on every attempt, and fails closed if either record is missing, malformed, or incomplete. The first permitted evaluation acquires the claim with exclusive file creation before the loader or held-out feature/label extraction; the claim is never replaced. Synthetic gate tests use a separately marked temporary fixture, require all paths to remain within that isolated root, and cannot configure alternate project paths.

The existing local selection, claim, test metrics, and selected pipeline were hashed before and after this code-only gate correction and remained byte-identical. The actual final test was **not rerun**. This fix improves future enforcement; it does not retroactively prove that the historical evaluation was performed only once. The unchanged test result is the prior recorded result described above. Synthetic regression tests cover first use, repeats, caller override rejection, path aliases/collisions, incomplete and malformed state, and concurrent claim acquisition.

The team lead explicitly approved scikit-learn `MLPClassifier` as the lightweight feed-forward implementation for this scoped V3-09 experiment, with the externally monitored chronological validation stopping protocol documented above. TensorFlow/Keras and PyTorch were not used.

## Inference handoff and limitations

`src/ml/inference.py` provides `load_selected_model`, `predict_one`, and deterministic-order `predict_batch` for V3-13; it creates no API route. The input is exactly the eight frozen features in Shared Contracts order, rejects missing/reordered/extra keys, missing or nonfinite numeric values, and non-Brazilian-UF states. It loads only the artifact named by the checksum-verified local selection manifest, reuses its fitted preprocessing, applies the frozen validation threshold, and returns `prediction`, `probability_late`, `threshold`, and SHA-256-based `model_version`. Missing or incompatible artifacts raise `InferenceArtifactError`; API-level error mapping remains V3-13. Local files are under ignored `models/local/v3_09_mlp/` and `data/processed/`; no binary or generated data belongs in Git.

The temporal train/validation prevalence shift (5.65% to 12.88%) remains material. MLP early stopping reuses validation loss and may overfit that stopping criterion; the validation metrics are therefore comparative, not an unbiased second holdout. No calibration was performed. The target remains retrospective and conditioned on eventual delivery; historical availability of promise-date, item amounts, and customer state at prediction time is unproven. The small network and single configuration do not establish neural-network superiority.
