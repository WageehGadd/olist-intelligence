"""Render self-contained evidence reports from computed aggregate artifacts."""
from pathlib import Path
import json,csv
ROOT=Path(__file__).resolve().parents[2]; OUT=ROOT/'data/processed/t00'; DOC=ROOT/'docs/audits'
def pretty(obj): return '```json\n'+json.dumps(obj,indent=2,ensure_ascii=False)+'\n```\n'
def run():
 p=json.loads((OUT/'profiles.json').read_text());s=json.loads((OUT/'statistics.json').read_text());b=json.loads((OUT/'baselines.json').read_text());x=json.loads((OUT/'supplement.json').read_text())
 verdicts=[('SQL Business Analytics','GO','MVP','Nine relational tables support observed sales, freight, payments, delivery and reviews; preserve grain and distinguish recorded payments from net revenue.'),('Customer Segmentation','CONDITIONAL GO','MVP descriptive; Advanced clustering','96,096 customers; only 3.12% repeat. Use descriptive recency/monetary and cohort profiles; benchmark clustering stability against seller/order/category alternatives.'),('Future Customer Value Prediction','NO-GO','Deferred','90-day windows have only 210, 233 and 299 repeat buyers. Zero-heavy observed marketplace payments are not lifetime value or profit.'),('Delivery Delay Prediction','CONDITIONAL GO','MVP','96,470 calendar-label examples, 6,534 late. Lightweight out-of-time lift exists; delivered-only selection and availability assumptions limit deployment claims.'),('Review Risk Prediction','CONDITIONAL GO','Advanced','98,400 purchase-stage labels; weak out-of-time purchase baseline. Prefer post-delivery intervention only for reviews not yet created.'),('Portuguese Review NLP','GO','MVP primary DL track','40,950 nonempty messages; strong classical baseline. Ratings are weak sentiment labels, and actual language proportions need manual validation.'),('Tabular Deep Learning','CONDITIONAL GO','Optional','Enough rows for an MLP comparison; no evidence it beats trees, little justification for a complex tabular network.'),('FastAPI Model Serving','GO','MVP future architecture','Serve versioned feature contracts and probabilities; no backend implemented in T-00.'),('Explainable AI','GO','MVP','Explain fitted predictions, not causality. Verify SHAP compatibility later; logistic coefficients provide a baseline.'),('MLflow / MLOps','GO','Advanced lightweight tracking','Record hashes, splits, parameters and metrics; avoid an elaborate platform for four students.')]
 exec_text='''Olist Intelligence remains a realistic four-student DEPI project, subject to instructor approval. Prioritize relational analytics, delivery risk and post-review NLP; make customer intelligence descriptive and defer future CLV. FastAPI and a dedicated frontend remain the intended integration route. No production application, model artifacts, final team allocation or Master Execution Plan was built.

Measured facts are derived from the nine local CSVs using Python 3.10.20. Recommendations and prediction-time assumptions are explicitly distinguished below. Dataset coverage is historical, not evidence of current Brazilian commerce.

'''+ '\n'.join(f'- **{n}: {v} — {tier}.** {reason}' for n,v,tier,reason in verdicts)+'\n'
 profile_text='''All files were fully loaded and profiled. Numeric summaries use pandas sample standard deviation and 1.5×IQR flags. Flags are screening indicators, not proof of errors; monetary floating-point residuals near zero must use cent tolerances. Identifier/ZIP numerical distributions have no business interpretation. Category summaries are limited to 15 values; review text and raw IDs are never exported. CSV blank fields are parsed as missing by pandas; whitespace-only nonnull values are separately counted. Candidate keys are hypotheses tested below, not declared constraints.

'''
 for n,a in p.items():
  profile_text+=f"## {n}\n\nFile `{a['rows']:,}` rows × `{a['columns']}` columns; {a['bytes']:,} bytes. Full duplicate excess: {a['full_duplicates']:,}. Candidate key {a['candidate_key']}; duplicate key excess {a['duplicate_key_excess']:,}; null key rows {a['key_null_rows']}.\n\n"
  for col,c in a['column_profile'].items():
   profile_text+=f"- `{col}`: {c['dtype']}; missing {c['missing']:,} ({c['missing_pct']:.4f}%); whitespace {c['whitespace_only']}; unique {c['unique']:,}."
   if 'min' in c:profile_text+=f" Range {c['min']} → {c['max']}."
   if 'numeric' in c:profile_text+=f" Numeric summary: {json.dumps(c['numeric'],ensure_ascii=False)}."
   if 'top_categories' in c:profile_text+=f" Top categories: {json.dumps(c['top_categories'],ensure_ascii=False)}."
   profile_text+='\n'
  profile_text+='\n'
 profile_text+='## Catalog and financial screening\n\n'+pretty({k:x[k] for k in ['product_nonpositive','payment_installments','payment_types','item_feature_missingness','distance_km']})
 relational='''Customers are order-address identities (`customer_id`), while `customer_unique_id` links observed people across orders. Orders and customers are one-to-one in this extract; customer_unique_id is not a customer-table primary key. Items use (order_id, order_item_id), payments use (order_id, payment_sequential). Product and seller IDs and translated Portuguese category names are unique candidate keys. Review ID alone is not safe: preserve source-row provenance in a review table and explicitly manage order-level label aggregation. Geolocation has no unique ZIP key.

```mermaid
erDiagram
    CUSTOMERS ||--|| ORDERS : customer_id
    ORDERS ||--o{ ITEMS : order_id
    ORDERS ||--o{ PAYMENTS : order_id
    ORDERS ||--o{ REVIEWS : order_id
    PRODUCTS ||--o{ ITEMS : product_id
    SELLERS ||--o{ ITEMS : seller_id
    TRANSLATION o|--o{ PRODUCTS : category_name
    GEO_ZIP_AGG o|--o{ CUSTOMERS : zip_prefix
    GEO_ZIP_AGG o|--o{ SELLERS : zip_prefix
```

The diagram shows logical optional children and a derived ZIP lookup, not the raw geolocation table. Aggregate child tables separately to order grain, then validate one-to-one merges. Never sum payments after joining item rows. Repeated products within an order represent units; do not deduplicate them. Multiple sellers need explicit item-level distances aggregated with price weighting or min/max, not an arbitrary first seller.

Geolocation: drop exact duplicate coordinate rows, screen the approximate Brazil box (a heuristic, not a political boundary), then median coordinates by ZIP prefix. Preserve missing ZIP lookups. Distance is Haversine straight-line km, not road distance or delivery routing. Median coordinates are static extract proxies with no historical version evidence.

Review labeling: exclude all orders with more than one distinct score (202), even if some have consistent binary labels. Retain unanimous scores, use earliest creation to enforce pre-review eligibility, and latest answer for conservative label maturity. Latest-answer label selection is only a sensitivity option, not ground truth. Review creation is survey-generation time; score/text exist at answer, so creation eligibility is conservative.

'''+pretty(s['relational'])+'Latest-answer sensitivity counts (low-score binary):\n\n'+pretty(x['review_latest_answer_sensitivity'])
 temporal='''Durations below are days, computed only when both timestamps exist. Negative durations are reported, not silently clipped. There are 1,359 carrier handoffs before approval and 23 deliveries before carrier handoff. Purchase-to-review creation is negative for 74 orders. Same-day midnight review creation can precede actual delivery hours; compare both calendar and exact times. Creation is not answer time.

Sparse early and final months are unsuitable standalone holdouts. September 2018 has 16 orders and October has 4, none delivered. Use January 2017–August 2018 for primary chronological evaluation, with sensitivity around August maturity. Missing outcomes are unknown, not on-time or good-rating labels. Canceled/unavailable are competing outcomes; shipped/processing could be unresolved or omitted outcomes. No extraction timestamp establishes definitive follow-up, and maximum observed event date does not prove complete observation.

Delivered-only evaluation estimates risk conditional on eventual delivery; it omits failures and can bias operational conclusions. Outcome-maturity purging also removes long-duration outcomes near boundaries and can bias rate estimates. The baseline reports below are therefore conditional diagnostics; future validation should use fixed follow-up, purge/embargo boundaries and compare monthly excluded versus retained cohorts.

'''+pretty(s['temporal'])
 delivery='''**CONDITIONAL GO — MVP with explicit prediction contract.** Target A: actual delivery calendar date > promised estimated calendar date. This is better aligned to customer promises than an arbitrary duration threshold. Literal timestamps would count 1,292 additional purchase-population same-day deliveries as late. Target B: purchase-to-delivery >30 elapsed days; this threshold is an illustrative audit configuration, not a business-approved service level. Separate carrier-transit or approval-to-delivery targets need their own thresholds and population.

Purchase eligibility: status delivered, actual and estimated dates present, delivery at/after purchase. Approval adds known approval between purchase and delivery. Carrier adds known handoff between approval and delivery. Known historical label population is not the full online population; unknown/canceled records do not become negatives.

Purchase predictors: calendar features, promised lead time, customer state, cart prices/freight/counts, catalog dimensions/categories, seller/customer locations. Availability of final cart records and original estimated date at purchase is an assumption because the extract has no version history. Approval may add elapsed approval duration; payments require instrumentation for when records were known. Carrier may add elapsed fulfillment duration, but excludes subsequent delivery outcomes. Historical seller/regional lateness must use only outcomes actually observed before prediction and exclude current order.

Prohibit actual delivery, eventual status, review fields, future aggregate performance, identifiers as numeric features and any target-derived duration at purchase. Train dummy and logistic before RF/gradient boosting; evaluate CatBoost/XGBoost/LightGBM only after their dependencies and contracts are justified. MLP is a comparison, not a promised improvement. Use chronological folds, point-in-time histories, group all item rows of each order, calibrated probabilities and validation-selected thresholds. Report AP (a PR summary), ROC-AUC, precision/recall/F1, Brier/reliability curves and top-K capture; accuracy is insufficient.

'''+pretty(s['targets']['delivery'])+'Approximate geographic support and missingness:\n\n'+pretty(x['item_feature_missingness'])
 review='''**CONDITIONAL GO — Advanced.** Low-score target = unanimous observed score 1–2 versus 3–5; 3-star treatment requires stakeholder sensitivity analysis. This is low-rating risk, not verified emotional sentiment. Missing reviews have no label. The 202 conflicting-score orders are excluded rather than arbitrarily averaging or selecting a favorable score.

Eligibility by scenario: purchase/handoff/delivery timestamp present and at/after purchase, unanimous label, earliest review creation strictly after prediction event. Post-delivery excludes reviews generated before/on exact delivery time and includes records with a delivery timestamp regardless of final status; a stricter status-and-chronology sensitivity is required before production. Carrier counts likewise enforce stage ≥ purchase but do not enforce approval-to-carrier consistency; use stricter delivery-stage chronology for implementation. Earliest review creation is a conservative boundary; answer is when the rating is actually submitted.

Purchase uses pre-outcome cart/catalog/location/calendar features. Handoff can add elapsed fulfillment. Post-delivery can add known lateness/duration only while review is still unavailable. Never use review text, score, answer date, final status or later outcomes to predict a future review. Missing-response selection and delivered population shifts are major risks: low-rating prevalence changes substantially across scenarios. Lightweight purchase logistic evidence shows modest lift and low recall at 0.5; no claim of commercially useful prediction follows. Benchmark dummy/logistic/trees and tune a threshold on validation only. Chronological maturity rules and order grouping apply.

'''+pretty(s['targets']['review'])
 customer='''**Descriptive intelligence: GO; traditional RFM clustering: CONDITIONAL GO; future CLV: NO-GO for current scope.** Customer IDs are anonymized marketplace identifiers, not a complete omnichannel customer ledger. 96,096 unique customers; 3.12% have multiple recorded orders. Frequency is nearly constant, so do not present K-Means as validated loyal-customer discovery.

RFM reference date is 2018-09-01, delivered orders only; monetary is summed recorded payment, not net revenue or profit. Raw all-status customer payment summaries are separately provided. No refunds, margins or cancellation payment reversals exist. Missing payment must remain explicitly unknown in production instead of blindly treated as zero. Apply log transforms/robust scaling on training data, compare descriptive recency/monetary bands to K-Means, assess silhouette, bootstrap stability and interpretable segment sizes. Consider seller reliability/value segmentation, category mix and order behavior, avoiding features that merely encode the proposed label.

Future windows use preceding 180 days of purchase activity and following 90 days of purchases at three cutoffs. A no-purchase label means no purchase observed in this extract, not no purchase anywhere. All horizons finish before conservative September coverage, but completeness is still an assumption. Window populations overlap; do not sum their counts as independent examples or random-split person/window rows. Amounts are future recorded payment proxies; they are not lifetime CLV. Positive labels are fewer than 300 per window with >99% zeros in two windows. Defer regression and repeat-purchase modeling; optional exploratory work needs grouped rolling windows, horizon maturity and PR metrics.

'''+pretty(s['customers'])
 nlp='''**Primary DL recommendation: Portuguese post-review low-rating text classification, benchmarked against TF-IDF + logistic regression.** Text is submitted evidence available after the review; it cannot predict that same review at purchase. Labels 1–2 versus 3–5 are rating proxies; 3-star exclusion and human sentiment annotation are needed for a sentiment claim. Five-star classification is harder, ordinal and optional; topic discovery/clustering are exploratory and need human Portuguese validation rather than invented complaint labels.

Measured lengths are Unicode characters and regex words, not transformer tokens. Preserve accents and negation; spelling, informal Portuguese and sarcasm need error analysis. Language proportions were not measured by a validated detector. Repeated template texts and conflicting ratings demonstrate weak supervision noise. Public reports export no review messages; deployed demos should mask names/contact patterns and manually inspect examples.

Classical baseline: train-only TF-IDF vocabulary and logistic regression. Small embedding + CNN is the fallback DL experiment, suitable for short texts; train-only vocabulary, padding and regularization, compare macro-F1/AP, do not claim improvement. LSTM/BiLSTM is possible but sequential cost and short messages give little reason to prioritize it. BERTimbau is a stronger pretrained Portuguese candidate with a 110M-parameter base model; fine-tune a classification head with short maximum length after token profiling, early stopping and GPU budget approval. A multilingual encoder is useful only if validated language diversity requires it. Parameter-efficient fine-tuning can reduce trainable weights but still requires backbone memory and a measured deployment budget. No pretrained weights or DL framework was downloaded.

Resource estimates (not measured): 110M float32 parameters are ~440 MB for weights alone; training gradients/optimizer/activations require substantially more. GPU training is preferred; CPU inference may be feasible after latency benchmarks. Small CNN may train on CPU, but actual timing remains unknown. Tabular MLP is optional: standardized numeric features and train-only categorical embeddings/one-hot, missing indicators, early stopping and fair boosted-tree comparisons. No evidence here establishes a tabular neural advantage.

Sources checked 2026-10-10: [BERTimbau model card](https://huggingface.co/neuralmind/bert-base-portuguese-cased), [authors' repository](https://github.com/neuralmind-ai/portuguese-bert). These support model identity and architecture, not performance on Olist.

'''+pretty(s['nlp'])
 features=[]
 def feature(name,table,columns,transform,grain,stage,task,missing,risk,complexity,recommendation):
  features.append(dict(feature=name,source_table=table,source_columns=columns,transformation=transform,grain=grain,earliest_availability=stage,target_task=task,missingness=missing,leakage_risk=risk,complexity=complexity,recommendation=recommendation))
 feature('catalog category/dimensions','products','product_category_name; product_weight_g; product_length_cm; product_height_cm; product_width_cm','item-level then count/weighted summaries','order','Before purchase (static snapshot assumption)','delivery/review',json.dumps(x['item_feature_missingness']),'catalog updates not timestamped','medium','retain with missing indicators; verify version availability')
 feature('purchase calendar','orders','order_purchase_timestamp','hour/weekday/month','order','At purchase creation','delivery/review','0','low; timezone unspecified','low','retain')
 feature('promised lead time','orders','order_estimated_delivery_date; order_purchase_timestamp','elapsed days','order','At purchase creation (assumption)','delivery/review','0','estimated promise may have changed','low','verify original promise contract')
 feature('cart totals/counts','order_items','price; freight_value; order_item_id; seller_id; product_id','sum/count/distinct','order','At purchase creation (assumption)','delivery/review',str(s['relational']['missing_items'])+' orders missing items','final cart snapshot lacks event history','medium','retain only confirmed purchase-known values')
 feature('customer geography','customers','customer_state; customer_zip_code_prefix','state/ZIP lookup','order','At purchase creation','delivery/review','no missing state/ZIP; '+str(s['relational']['foreign_keys'][-2]['unmatched_nonnull_rows'])+' ZIP lookup misses','static identity; geography reidentification','low','state preferred; exclude raw customer IDs')
 feature('seller geography','sellers','seller_state; seller_zip_code_prefix','aggregate item sellers','order','Before purchase (snapshot assumption)','delivery/review','7 seller lookup misses','multi-seller aggregation','medium','retain aggregate, not arbitrary first seller')
 feature('approximate distance','geolocation; customers; sellers','ZIP prefix; latitude; longitude','deduplicate/screen/median then Haversine','item to order','At purchase creation (static proxy)','delivery/review',json.dumps(x['item_feature_missingness']['distance_km']),'raw ZIP join amplification; version unknown','medium','conditional retain')
 feature('payment features','order_payments','payment_value; payment_type; payment_installments','order-level sums/count/max','order','After payment approval (unverified)','delivery/review','1 order missing payments','no record timestamps; future payment additions','medium','excluded from purchase baseline; instrument first')
 feature('approval elapsed','orders','order_approved_at; order_purchase_timestamp','elapsed days','order','After payment approval','delivery/review','160 missing approval','post-purchase leakage','low','approval/carrier only')
 feature('fulfillment elapsed','orders','order_delivered_carrier_date; order_approved_at','elapsed days','order','After carrier handoff','delivery/review','1783 missing carrier; 1359 negative intervals','post-purchase leakage; chronology errors','low','carrier only after chronology validation')
 feature('actual duration/lateness','orders','order_delivered_customer_date; order_estimated_delivery_date','duration/calendar comparison','order','After delivery','post-delivery review risk','2965 missing actual','direct delivery-target leakage','low','prohibit delivery model; conditional post-delivery review only')
 feature('review text','order_reviews','review_comment_message; review_comment_title','TF-IDF/tokenization','review','After review creation, specifically answer submission','NLP',str(s['nlp']['missing_messages'])+' missing messages','direct future-review leakage','medium','NLP only; never pre-review risk')
 feature('review score/answer','order_reviews','review_score; review_answer_timestamp','label and maturity only','review/order','After review creation, specifically answer submission','review/NLP','768 orders missing review','direct target leakage','low','labels/split eligibility only')
 feature('historical seller/region performance','orders; order_items; customers','seller_id; state; actual_delivery; promise','as-of outcome-known aggregates excluding current order; smoothing','seller/state to order','Before purchase only for prior observed outcomes','delivery/review','not computed; cold-start coverage unknown','future aggregation/CV leakage','high','future work with point-in-time joins')
 feature('historical customer behavior','customers; orders; payments','customer_unique_id; purchase; payment','past-only RFM window','customer','Before purchase for known prior activity','future purchase','few repeats; window evidence in customer report','identity/CV/window overlap leakage','high','defer prediction; descriptive RFM')
 feature('final status/identifiers','orders; customers','order_status; order_id; customer_id; customer_unique_id','none','order','After outcome (final status); IDs at purchase','delivery/review','0','future status; identity memorization; duplicate-order CV','low','exclude final status/IDs from predictors; IDs for grouping only')
 with (OUT/'feature_leakage.csv').open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(features[0]));w.writeheader();w.writerows(features)
 leakage='''The matrix distinguishes observed source missingness from unknown point-in-time missingness. The extract has no event history for cart, catalog, address or estimated-promise revisions. Purchase-time feature availability is a retrospective assumption, not proven online feasibility. Source aggregates are measured in supplement.json; historical feature coverage was not computed and must not be presented as known.

Direct leakage: target score, actual delivery for delivery target, review text for future review. Temporal leakage: elapsed fulfillment before handoff, final status, late-recorded payments. Aggregation leakage: full-history seller rates, unsafe item/payment/review joins. Identity leakage: memorizing customer/order IDs. Cross-validation leakage: full-data scaling/vocabulary/history, overlapping customer windows and repeated text. Duplicate-order leakage: item rows or multiple reviews split independently. Split whole orders, purge unavailable labels and fit transformations on training only.

'''
 for f in features: leakage+='## '+f['feature']+'\n\n'+'\n'.join(f'- **{k}:** {v}' for k,v in f.items() if k!='feature')+'\n\n'
 baseline='''Three bounded experiments were executed: dummy versus logistic for purchase-time delivery and review risk, and dummy versus TF-IDF logistic for post-review NLP. Fixed seed 42, no search, no model artifact. Numeric median imputation/scaling and categorical one-hot are fit on train only; text vocabulary/IDF are fit on train only. No review text enters pre-review tasks. The tabular input fields are enumerated below; final payments were deliberately excluded.

Chronology: train before 2018-01-01, validation 2018-01-01 to before 2018-04-01, test 2018-04-01 to before 2018-09-01. Labels must be known before each partition end: delivery timestamp or latest review answer. Partitioning uses purchase time for tabular tasks and answer time for NLP. No tuning used test data. NLP excludes every globally repeated normalized message and every multi-review order before splitting; this is a conservative corpus eligibility rule using full-corpus duplicate detection, not train-fitted vocabulary. It reduces template leakage but uses later-corpus information and changes population; a prospective held-out evaluation should freeze dedup rules and report novel/repeated-text metrics separately. Customer identity overlap is possible across periods; IDs are excluded but grouped-customer sensitivity remains unrun.

Outcome maturity excludes slow deliveries at boundaries and can inflate apparent performance. Tabular sample availability at purchase is assumed; these are diagnostics, not deployment validation. AP is average precision rather than trapezoidal PR-AUC. Top-K sorts ties stably; dummy top-K capture is an incidental ordering result, not actionable ranking. Threshold is fixed 0.5, not optimized. No calibration fitting, confidence intervals, full rolling folds or fairness evaluation was performed. Delivery F1 is zero at 0.5 despite ranking lift; validation-only threshold/calibration work is mandatory. NLP baseline strength makes DL scientifically interesting only as a fair comparison, not an assumed improvement.

'''+pretty(b)
 risks='''## Risk register and mitigations

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

'''+ '\n'.join(f'## {n}\n\n**{v}; {tier}.** {reason} Scientific/engineering condition: validate population and evaluation gates before claiming usefulness; difficulty '+('high' if n in ['Future Customer Value Prediction','Tabular Deep Learning','Review Risk Prediction'] else 'medium')+'.\n' for n,v,tier,reason in verdicts)
 provenance='''## Provenance and license

Source: [Olist Kaggle dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce), checked 2026-10-10. Local file SHA-256 hashes identify this audit snapshot; they do not prove it is an unmodified publisher release, and download/version metadata was not supplied. Publisher page was accessible but its dynamic license field did not render in the browsing tool. CC BY-NC-SA 4.0 is the reported dataset license in available search metadata/independent references, but primary publisher metadata confirmation remains an explicit release gate. Do not treat this audit as a definitive licensing determination.

If confirmed, [Creative Commons BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/) requires credit, license link, indication of changes, noncommercial use and compatible sharing of adaptations. Public access does not mean unrestricted redistribution. Keep raw data and generated derivatives out of Git, link the publisher, and verify terms before publishing data, review examples or commercial services. Model-card licensing does not override dataset obligations.

'''
 architecture='''## H. Architecture implications

SQL: keep order facts, item facts, payments and review events separate; use validated keys, a customer identity mapping and derived ZIP lookup. Exact currency should use decimal/cents. ETL: immutable raw layer with hashes, typed staging, error quarantine and aggregate order views. Preserve unknown labels and provenance, not silent imputation of outcomes.

Feature pipelines: event-time contracts per prediction scenario, prior outcome-known histories, train-fitted encoders and explicit cold-start behavior. Model artifacts later require serialized preprocessing, model, schema, training snapshot, target definition and thresholds together. FastAPI should validate cart inputs and scenario/time, return calibrated risk with explanations and model version, and reject unavailable features. No FastAPI code exists in this audit.

Frontend: separate observed analytics, pre-outcome delivery risk, future-review risk and submitted-review NLP; show eligible populations and historical coverage rather than implying live commerce. Explainability describes model association, not causation. MLflow can track small experiments and provenance; local reproducibility precedes Docker/CI/deployment. Measure artifact size, CPU latency, memory, privacy and dependency compatibility before deployment. React choice and hosting remain open.

## I. Proposed scope

- **MVP:** relational SQL analytics and reproducible ETL; descriptive customer/cohort intelligence; delivery calendar risk with baseline/chronological validation; post-review text analysis and a classical-vs-small-DL comparison; FastAPI, dedicated frontend, explainability and tests in later implementation.
- **Advanced:** validated pre-review risk (prefer delivery-stage contract), point-in-time seller histories, tree comparisons, calibration, lightweight experiment tracking and an approved Portuguese transformer experiment.
- **Optional:** stable seller/order/category clustering, tabular MLP comparison, validated complaint topics and richer deployment automation.
- **Rejected/deferred:** lifetime CLV claims, production repeat-purchase/value regression, complex recommenders (no browsing/exposure or explicit nonpurchase data), heavy tabular DL without evidence, current-market/general commercial claims.

## K. Open questions

Instructor approval; approved business threshold/cost for late risk; original promise/cart availability; review 3-star policy; extraction/version and license metadata; GPU availability; frontend and deployment budget; retained-versus-purged monthly bias; human Portuguese annotation and privacy review. No exact DEPI dates or final member assignments are known.

## L. Master Planning Handoff

Plan only Olist Intelligence in this repository. Confirmed facts: nine readable local tables, 99,441 orders, 96,096 customer identities, low observed repeat activity, 40,950 nonempty review messages, substantial multi-child join hazards and chronology defects. Dataset is historical and incomplete at its tail. Use Python 3.10.20 in existing .venv. FastAPI and a dedicated frontend are intended; no production implementation or final models exist yet.

Recommended workstreams: typed ETL/SQL and reconciliation; analytics/customer profiles; calendar delivery risk and point-in-time feature contracts; submitted-review NLP with classical/DL comparison; later API/frontend integration, explainability, tracking and validation. These are planning inputs, not a final Master Execution Plan or team allocation.

Reject assumptions that all customers repeat, spending equals CLV/profit, all missing deliveries are on-time, review text is available before the review, static snapshot fields prove purchase-time availability, full-history seller aggregates are safe, or a neural model must outperform classical baselines. Quality gates: immutable raw hashes, unique grain/validated joins, outcome eligibility, no future-feature leakage, chronological maturity and bias sensitivity, train-only preprocessing, monthly metrics, calibration/threshold chosen on validation, privacy/license verification and measured serving resources. Obtain instructor approval and settle outstanding target, compute and deployment decisions before expanding scope.

'''
 reproduce='''## Reproduction and validation

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
'''
 chapters=[('00_EXECUTIVE_SUMMARY',exec_text),('01_DATASET_PROFILE',profile_text+provenance),('02_RELATIONAL_INTEGRITY',relational),('03_TEMPORAL_DATA_QUALITY',temporal),('04_DELIVERY_TARGET_FEASIBILITY',delivery),('05_REVIEW_TARGET_FEASIBILITY',review),('06_CUSTOMER_INTELLIGENCE_FEASIBILITY',customer),('07_DEEP_LEARNING_NLP_FEASIBILITY',nlp),('08_FEATURE_LEAKAGE_MATRIX',leakage),('09_BASELINE_EXPERIMENTS',baseline),('10_RISKS_AND_DECISIONS',risks+provenance+reproduce)]
 for name,content in chapters:(DOC/f'{name}.md').write_text('# T-00 — '+name.replace('_',' ')+'\n\n'+content)
 final='# T-00 — Final Olist Dataset Audit Report\n\nAudit date: 2026-10-10 (Africa/Cairo). Scope: pre-implementation due diligence.\n\n'
 for title,content in [('A. Executive Summary',exec_text),('B. Dataset Inventory',profile_text+provenance),('C. Data Relationships',relational),('D. Data Quality',temporal),('E. Predictive Tasks',delivery+review+leakage+baseline),('F. Customer Intelligence',customer),('G. Deep Learning Strategy',nlp)]:final+='## '+title+'\n\n'+content+'\n'
 final+=architecture.replace('## K. Open questions','## J. Risk Register\n\n'+risks+'\n## K. Open questions')+reproduce
 (DOC/'FINAL_DATASET_AUDIT_REPORT.md').write_text(final)
 (DOC/'README.md').write_text('# T-00 audit reproduction\n\n'+reproduce)
 print('Generated 12 required reports, README, and feature_leakage.csv')
if __name__=='__main__':run()
