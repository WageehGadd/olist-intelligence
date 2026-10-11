# T-00 — 00 EXECUTIVE SUMMARY

Olist Intelligence remains a realistic four-student DEPI project, subject to instructor approval. Prioritize relational analytics, delivery risk and post-review NLP; make customer intelligence descriptive and defer future CLV. FastAPI and a dedicated frontend remain the intended integration route. No production application, model artifacts, final team allocation or Master Execution Plan was built.

Measured facts are derived from the nine local CSVs using Python 3.10.20. Recommendations and prediction-time assumptions are explicitly distinguished below. Dataset coverage is historical, not evidence of current Brazilian commerce.

- **SQL Business Analytics: GO — MVP.** Nine relational tables support observed sales, freight, payments, delivery and reviews; preserve grain and distinguish recorded payments from net revenue.
- **Customer Segmentation: CONDITIONAL GO — MVP descriptive; Advanced clustering.** 96,096 customers; only 3.12% repeat. Use descriptive recency/monetary and cohort profiles; benchmark clustering stability against seller/order/category alternatives.
- **Future Customer Value Prediction: NO-GO — Deferred.** 90-day windows have only 210, 233 and 299 repeat buyers. Zero-heavy observed marketplace payments are not lifetime value or profit.
- **Delivery Delay Prediction: CONDITIONAL GO — MVP.** 96,470 calendar-label examples, 6,534 late. Lightweight out-of-time lift exists; delivered-only selection and availability assumptions limit deployment claims.
- **Review Risk Prediction: CONDITIONAL GO — Advanced.** 98,400 purchase-stage labels; weak out-of-time purchase baseline. Prefer post-delivery intervention only for reviews not yet created.
- **Portuguese Review NLP: GO — MVP primary DL track.** 40,950 nonempty messages; strong classical baseline. Ratings are weak sentiment labels, and actual language proportions need manual validation.
- **Tabular Deep Learning: CONDITIONAL GO — Optional.** Enough rows for an MLP comparison; no evidence it beats trees, little justification for a complex tabular network.
- **FastAPI Model Serving: GO — MVP future architecture.** Serve versioned feature contracts and probabilities; no backend implemented in T-00.
- **Explainable AI: GO — MVP.** Explain fitted predictions, not causality. Verify SHAP compatibility later; logistic coefficients provide a baseline.
- **MLflow / MLOps: GO — Advanced lightweight tracking.** Record hashes, splits, parameters and metrics; avoid an elaborate platform for four students.
