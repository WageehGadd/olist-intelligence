# T-01 — Olist Intelligence concept brief

Prepared: October 27, 2026. Task owner: **Wageeh Hussain Wageeh (Team Leader)**, identified as **Wageeh** in the unchanged canonical ledger. Collaborators: Hamza, Hasnaa and Rana. Academic reviewer: Instructor; identity not supplied.

**Status:** prepared for team-lead review following user-reported instructor approval dated October 26, 2026. The user reports that Olist Intelligence was accepted as an extended version of **DEPI Project #7**. This newly prepared brief is not represented as the document previously submitted or approved. Its submission has not been independently verified.

## Purpose and academic context

Olist Intelligence — Explainable E-Commerce Analytics & Predictive Intelligence Platform — is the team's DEPI Round 5 Data Scientist graduation project. It combines relational business analysis with scientifically evaluated predictive models and an explainable academic demonstration application. The aim is to help users explore historical e-commerce activity, delivery risks and submitted customer feedback.

The Project #7 relationship is user-reported. No official booklet text, base-project title, instructor identity, written response or evidence URL was supplied; this brief does not invent those details or claim a verified requirement-by-requirement mapping.

## Dataset and feasibility foundation

The nine Brazilian E-Commerce Public Dataset by Olist tables cover orders, customers, products, sellers, order items, payments, reviews, geolocation and category translation. The committed [T-00 audit](audits/FINAL_DATASET_AUDIT_REPORT.md) and [validation record](audits/VALIDATION.md) document completed local analysis, reproduced aggregates and tests. No raw-data download or rerun is required for this governance task.

T-00 measured 99,441 orders and 96,096 distinct customer identities, with only about 3.12% observed repeat purchasers. Calendar-day delivery labeling yields 96,470 eligible orders and 6,534 late deliveries. There are 40,950 nonempty review messages. These are historical audit findings, not live-market measurements or new T-01 experiments. Missingness, conflicting reviews, ZIP duplication, join amplification and incomplete temporal coverage constrain interpretation.

## Proposed modules and unchanged scope

The [Master Plan V2.2](planning/OLIST_INTELLIGENCE_MASTER_EXECUTION_PLAN_V2_2.md) and [canonical ledger](planning/OLIST_INTELLIGENCE_TASK_LEDGER_V2_2.csv) remain authoritative. This brief introduces no new task, ownership, dependency or architecture change.

- **Data foundation:** typed ingestion into PostgreSQL, with SQLite fallback; explicit table grain, validated keys, quality checks and separately aggregated child tables.
- **SQL analytics and customer intelligence:** historical order, category, seller and geography views; descriptive RFM and cohorts. Delivered-only RFM is a population choice; Recency uses purchase timestamps. Monetary KPIs describe gross item value plus charged freight or recorded payments, not company profit/revenue.
- **Delivery ML:** purchase-snapshot calendar-day lateness classification; dummy/logistic and tree baselines, careful feature availability, calibration, threshold selection and explainability. Final cart/original-promise availability is an assumption of the retrospective simulator.
- **Submitted-review NLP and DL comparison:** Portuguese rating-proxy classification, 1–2 versus 3–5 stars, using a TF-IDF/logistic baseline and a small CNN comparison. This analyzes a review after submission; it is neither verified sentiment annotation nor purchase-time review-risk prediction. A neural improvement is not promised.
- **Integration and academic delivery:** FastAPI backend, React frontend, model packaging, global explanations, tests, reproducible demonstration, model cards and team presentation. These remain future tasks.

Advanced scope remains T-16 boosted-tree comparison, T-24 purchase-time review risk and T-25 lightweight experiment tracking. Optional scope remains T-12 clustering and T-23 BERTimbau, subject to the existing data/resource gates. No future CLV, real-time streaming, production-readiness or unrelated module is added.

## ML methodology and evaluation

Respect transaction grain and aggregate items/payments/reviews separately before order joins. Exclude future outcomes and final statuses from purchase predictors; fit preprocessing only on training data and use point-in-time histories when implemented. Preserve the purchase-v1 raw schema and shared offline/inference transformations.

Procedure A reproduces already examined T-00 historical baselines using their exact eligibility, feature, duplicate and maturity rules. Procedure B uses chronological model-selection, calibration-fit and threshold-assessment partitions or nested time-aware out-of-fold predictions, with decisions frozen before final test evaluation. T-00's prior exposure to the historical test interval is disclosed. NLP Procedure A excludes all multi-review orders and globally repeated normalized messages and splits by answer time; changed policies are revised experiments, not reproduction.

Report average precision, precision/recall/F1, ROC-AUC, calibration/Brier score, monthly behavior and top-K capture where appropriate. Compare the CNN fairly against the classical baseline on matching populations and splits. Explanations are associations, not causal evidence. No model was trained for T-01.

## Team structure and deliverables

The four-person team remains Wageeh, Hamza, Hasnaa and Rana. V2.2 assigns Wageeh architecture/delivery ML; Hamza SQL, analytics, CNN, API core and integration; Hasnaa ETL, customer intelligence, NLP and prediction integration; Rana quality, geographic analysis, splits, labels, tests and presentation. The ledger is the exact ownership/reviewer/dependency reference; this overview does not reassign tasks.

Expected eventual deliverables are the validated data/SQL layer, evaluated delivery and review-text models, a documented classical/DL comparison, explainable FastAPI/React demonstration, reproducible tests and setup, model cards and a presentation showing each member's actual contribution. Instructor approval is recorded separately from future technical completion. No academic deadline is invented.

## Feasibility decisions, limits and outstanding decisions

SQL analytics and post-review NLP are supported by T-00. Delivery risk remains conditional on eligibility, selection bias and retrospective availability assumptions. Descriptive customer intelligence is useful; strong loyalty segmentation and future CLV claims are unsupported by sparse repeat activity. Optional clustering and transformer work remain conditional, not promised mandatory expansion.

Keep authentic datasets, generated data, model binaries and secrets outside Git. Publisher license confirmation, privacy review before displaying free text, threshold costs, three-star sensitivity, GPU access and actual team calendar/capacity remain open. T-00 raw-data tests cannot be rerun in this source-only clone; historical completion is supported by its committed evidence. T-02 owns later CI/full-data test isolation.

## Approval and next gate

See the [user-reported approval record](approval/T-01_instructor_approval.md#user-reported-instructor-approval) and [existing-schema state](planning/approval_state_v2_2.json). No additional conditions have been reported; this does not prove none were given. The state-machine gate passes on the explicitly attributed evidence reference under the existing validator, with independent authentication still outstanding.

The concept brief is prepared, but submission of this particular document to the instructor remains unverified and needs the owner's confirmation. T-03 still requires T-02 completion as well as approval; no T-02/T-03 or other implementation is authorized or started by this brief. The Master Plan/ledger remain unchanged snapshots, including their historical pending-status language.
