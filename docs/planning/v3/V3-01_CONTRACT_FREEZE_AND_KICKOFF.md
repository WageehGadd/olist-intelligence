# V3-01 Contract Review and Team Kickoff Record

**Status: V3-01 COMPLETED; SHARED CONTRACTS V1 FROZEN BY DELEGATED TEAM-LEAD APPROVAL.** This records the team leader's approval authority delegated by the members; it does not claim independent individual sign-off on the contract text. Teammate-specific local data/environment checks remain required before each member's first implementation task. No implementation task is authorized until the team lead coordinates its start. This record is on `task/v3-01-contract-freeze`, based on preserved commit `c5d80fa62d1f7e64736b8ba00474abe346e99fd6` (parent: local `main` baseline `97f874d974b402b077e57a0361dda485c838adc5`).

## Scope and approval provenance

V3 is the current planning baseline. The team leader reports instructor approval of the simplified V3 scope; no written evidence was supplied and this report is not independently verified. The team leader reports that Hamza, Hasnaa and Rana received their execution plans and the dataset ZIP, agreed with their plans, and delegated authority to the team leader to define and approve the plan and technical contracts. The team leader explicitly approves Shared Contracts v1 and the workflow below. This is delegated team-lead approval, **not** independent or written approval of Shared Contracts v1 by each member. No successful dataset extraction or environment setup on a teammate's machine is claimed. These statements were supplied on 2026-11-14. Hamza's historical T-02 status remains team-leader-reported as not started; other workspaces, remote branches and PRs have not been independently checked. The V2.2 Master Plan, approval records and canonical ledger are unchanged. The V2.2 ledger retains T-02 as `Planned`; the transition record attributes its reported supersession to the team leader.

The project remains the approved 15-task scope: SQL analytics, cleaning/EDA, delivery ML with a small MLP comparison, and one FastAPI/Jinja2 application. No scope, architecture, task owner, estimate or dependency changes are proposed here.

## Owners and first tasks

| Member | Accountable work | First implementation task after V3-01 |
|---|---|---|
| Hamza | SQLite and authoritative SQL KPIs; sole publisher of shared KPI values, including `delay_rate_calendar` | V3-02 |
| Hasnaa | Data profiling/cleaning and EDA chart outputs; may independently reconcile but does not publish shared KPI values | V3-04 |
| Wageeh | Delivery target/features/models, FastAPI, and integration; independent target reconciliation does not supersede Hamza's KPI ownership | V3-06 |
| Rana | Jinja2/Bootstrap/Plotly templates, synthetic mock fixtures and browser interactions | V3-10 |

The task ledger remains the source for all task IDs, estimates and dependencies. The team-leader-reported plan agreements and delegation establish the ownership/decision process for V3-01; they are not represented as individual sign-off on the contract text. The team lead must still coordinate each task start, and each member must complete their local setup check before their first implementation task.

### Required per-member pre-start setup checks

Wageeh's local Python environment and nine-file dataset are verified below. Hamza's, Hasnaa's and Rana's local machines have not been independently checked; the team leader's report that the ZIP was received is not evidence of extraction or environment setup. Before each first implementation task, the member and team lead must confirm Python 3.10.20 is available in the project environment, the task's documented dependencies are present, the required original CSVs are readable from ignored `data/raw/`, and no raw or generated data is staged. Record the result in the task PR or progress update. These are start gates, not claims of current readiness.

| Member | First task | Local setup status |
|---|---|---|
| Hamza | V3-02 | **Pre-start check required; not independently verified** |
| Hasnaa | V3-04 | **Pre-start check required; not independently verified** |
| Rana | V3-10 | **Pre-start check required; not independently verified** |
| Wageeh | V3-06 | Python 3.10.20 and original CSVs verified in this checkout; task-specific dependency readiness remains to be confirmed before the team-lead start |

## Frozen interfaces — Shared Contracts v1

The detailed canonical definitions are in [`SHARED_CONTRACTS.md`](SHARED_CONTRACTS.md). Cross-document review found these interfaces consistent. The team leader approved v1 under the delegated decision process described above. The approved target-population rule is recorded below:

- **Hamza → Wageeh → Rana:** `data/processed/sql_kpis.csv` and `sql_category_item_value.csv`; Wageeh maps the exact schemas to the summary, delivery-monthly and category-item-value JSON routes; Rana consumes those routes.
- **Hasnaa → Wageeh → Rana:** `eda_category_item_counts.csv` and `eda_item_price_distribution.csv`; Wageeh maps them to the two chart JSON routes; Rana consumes the returned series.
- **Wageeh → Rana:** server-rendered Jinja2 contexts for `GET /`, `/sales`, `/delivery`, `/predict`; browser fetches only for Sales period changes, Delivery period changes, and `POST /api/v1/predict`.
- **Prediction:** strict request fields are `purchase_timestamp`, `estimated_delivery_date`, `customer_state`, and a nonempty `items` list whose entries contain only numeric `price` and `freight_value`. Training and inference use the same eight ordered features and shared derivation function. Synthetic examples are fixtures only, never observed Olist results.
- **Wageeh → V3-07/Hasnaa:** order-grain `delivery_population.csv`, documented label, counts and exclusions. Eligibility uses the team-lead-approved delivery-delay rule below.

## Approved delivery-delay population rule

**Approved by team-lead direction in this task:** for both the shared `delay_rate_calendar` KPI and ML delivery-delay target population, exclude any order whose estimated delivery calendar date is earlier than its purchase calendar date. Preserve delivered-order eligibility, valid required timestamps, and actual delivery calendar date not before purchase. Label `late=1` only when normalized actual delivery calendar date is strictly later than normalized estimated delivery calendar date. This population exclusion does not automatically apply to unrelated commercial KPIs such as revenue proxies or customer counts. Apply the approved rule consistently in Hamza's KPI and Wageeh's target implementation; report reproduced counts against T-00 rather than hard-coding them.

### Verified local environment and dataset

- `.venv/bin/python` is Python 3.10.20. System `python3` remains Python 3.9.6; the project uses the virtual environment consistently for these checks.
- The only dependency manifest is `scripts/audit/requirements.txt` for T-00. Its four pinned packages are installed and import at the declared versions: pandas 2.3.3, numpy 2.2.6, scikit-learn 1.7.2, pytest 9.1.1. `pip check` reports no broken requirements. No V3 app dependency manifest exists; FastAPI, Pydantic, Jinja2 and Plotly are not installed. No additional packages were installed for this dataset audit.
- The team reports downloading the original dataset from [Kaggle's Olist dataset page](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce). The files' names, schemas, row counts and T-00 profile values match; no archive/hash was supplied, so provenance is reported rather than cryptographically authenticated. Kaggle lists the dataset as nine CSVs under CC BY-NC-SA 4.0.
- All nine expected CSVs are present, readable with pandas, and match the T-00 reference row counts. Headers below are exact; each file has all expected columns and no unexpected columns.

| File | Rows × columns | Exact header |
|---|---:|---|
| `olist_customers_dataset.csv` | 99,441 × 5 | `customer_id, customer_unique_id, customer_zip_code_prefix, customer_city, customer_state` |
| `olist_geolocation_dataset.csv` | 1,000,163 × 5 | `geolocation_zip_code_prefix, geolocation_lat, geolocation_lng, geolocation_city, geolocation_state` |
| `olist_order_items_dataset.csv` | 112,650 × 7 | `order_id, order_item_id, product_id, seller_id, shipping_limit_date, price, freight_value` |
| `olist_order_payments_dataset.csv` | 103,886 × 5 | `order_id, payment_sequential, payment_type, payment_installments, payment_value` |
| `olist_order_reviews_dataset.csv` | 99,224 × 7 | `review_id, order_id, review_score, review_comment_title, review_comment_message, review_creation_date, review_answer_timestamp` |
| `olist_orders_dataset.csv` | 99,441 × 8 | `order_id, customer_id, order_status, order_purchase_timestamp, order_approved_at, order_delivered_carrier_date, order_delivered_customer_date, order_estimated_delivery_date` |
| `olist_products_dataset.csv` | 32,951 × 9 | `product_id, product_category_name, product_name_lenght, product_description_lenght, product_photos_qty, product_weight_g, product_length_cm, product_height_cm, product_width_cm` |
| `olist_sellers_dataset.csv` | 3,095 × 4 | `seller_id, seller_zip_code_prefix, seller_city, seller_state` |
| `product_category_name_translation.csv` | 71 × 2 | `product_category_name, product_category_name_english` |

**Null and parse findings:** no nulls in customers, geolocation, order items, payments, sellers, or category translation. Orders have 160 null `order_approved_at`, 1,783 null `order_delivered_carrier_date`, and 2,965 null `order_delivered_customer_date`; purchase and estimated dates have no nulls. Reviews have 87,656 null titles and 58,247 null messages (plus 2 and 27 whitespace-only values respectively, matching T-00). Products have 610 nulls each in category/name length/description length/photo count and 2 nulls each in weight/length/height/width. All non-null order, review, and item `shipping_limit_date` timestamp values parsed successfully; parse failures were zero. Missing optional dates and product/review fields are preserved, not edited.

**Keys and relationships:** `order_id` (orders), `customer_id` (customers), `product_id` (products), `seller_id` (sellers), (`order_id`,`order_item_id`) (items), (`order_id`,`payment_sequential`) (payments), and source category (translation) have zero duplicate excess and zero null key rows. `customer_unique_id` has 96,096 distinct values among 99,441 rows (3,345 repeated identities; expected, not a key failure). `review_id` has 814 duplicate excess (98,410 distinct among 99,224; matches T-00). Geolocation has 19,015 distinct ZIP prefixes and 981,148 duplicate-key excess; it also has 261,831 exact duplicate rows. Do not join geolocation directly by ZIP prefix. Orphan rows were zero for orders→customers, items→orders/products/sellers, payments→orders, and reviews→orders. Of product rows with non-null categories, 13 rows use two untranslated source categories (`pc_gamer`, `portateis_cozinha_e_preparadores_de_alimentos`); use the Shared Contracts' `unknown` fallback. The 610 products with missing category remain missing/unknown as specified.

**Approved delivery-delay population check:** the orders file contains the required status, purchase timestamp, estimated delivery date, and delivered timestamp fields. It has 96,478 `delivered` status rows; 96,470 have all three required timestamps valid. No valid delivered row has actual date before purchase or estimated date before purchase. Applying the approved rule yields 96,470 eligible rows and 6,534 late rows (`actual calendar date > estimated calendar date`), a 6.77309% rate. This exactly matches T-00's 96,470/6,534 (6.7731%). Thus the delivery-delay eligibility rule is implementable and reproduced; no raw data was changed.

- `git check-ignore -v` confirms the nine CSVs under `data/raw/` are ignored. `git ls-files` shows none of the raw files tracked. No raw files, generated outputs, databases, model artifacts, secrets, or environment files are staged or tracked.
- Schema/readability and T-00 comparison checks above were read-only. `git diff --check` passes. No new tests or implementation were run.

Team-leader-reported delivery of the plans and ZIP, plan agreement, and delegation support the Master Plan ownership criterion. They do not establish individual contract-text sign-off. Dataset ZIP receipt is reported, but local CSV access, Python/dependency setup, and successful extraction on Hamza's, Hasnaa's and Rana's machines have not been verified. These are pre-start checks and must be completed before each member begins implementation. Wageeh's local audit environment and raw CSVs are verified above. No V3 application dependency manifest exists; resolve and document any required application dependencies before the task that needs them. No implementation task is authorized until the team lead separately coordinates its start.
## Handoffs and working rules

- Hamza is the only owner of authoritative shared KPI values. Hasnaa and Wageeh may reconcile independently and report discrepancies to Hamza; dashboard values and definitions remain Hamza's.
- Each producer hands off exact path/schema/version, generation command, counts, assumptions, tests and limitations. Wageeh owns route/context integration; each producer fixes defects in that producer's output.
- The team leader reports agreement on one feature branch per task, PRs into `main`, team-lead review before merging, no direct pushes to `main`, and brief daily progress updates. These are reported team agreements, not verified GitHub enforcement. After V3-01 freezes them, Shared Contracts is the source of truth; report integration blockers before proposing any shared-interface change. Inspect the full diff, run relevant local checks and `git diff --check`, and stage explicit paths.
- Keep raw datasets, generated outputs, local databases, secrets, virtual environments, caches and model binaries out of Git. Synthetic fixtures must be visibly labeled as synthetic.
- Estimates are task effort; the one-week/19-hour integration reserve is calendar contingency, not work automatically assigned to junior members. The owner and team lead agree any defect work or move the date.

## V3-01 acceptance status

| Criterion | Status | Evidence / remaining work |
|---|---|---|
| Approved V3 scope and provenance recorded | Satisfied with limitation | Team-leader-reported instructor approval (reported 2026-11-14); no written evidence or independent verification |
| Individual execution-plan agreement recorded | Satisfied with limitation | Team leader reports Hamza, Hasnaa and Rana agreed with their plans and received the plans and dataset ZIP; this is not a written acknowledgement or proof of local setup |
| All four owners acknowledge ownership (Master Plan acceptance criterion) | Satisfied with limitation | Team leader reports the three members agreed to their assigned plans and delegated planning/contract authority; Wageeh is the V3-01 accountable owner. This is attributed evidence, not a record of individual written sign-offs |
| Branch/PR and daily coordination workflow recorded | Satisfied with limitation | Team leader reports team agreement to task branches, PRs to `main`, lead review before merge, no direct `main` pushes, and brief daily updates; enforcement was not verified |
| Team-lead approval and freeze of Shared Contracts v1 recorded | Satisfied with limitation | Team leader explicitly approves v1 under delegated authority. No individual explicit contract acknowledgements are claimed |
| Cross-document task IDs, owners, estimates and dependencies checked | Satisfied | Master Plan and 15-row V3 ledger; no task inventory changes |
| Approved delivery-delay population rule consistently documented | Satisfied | Hamza KPI specification, Wageeh target specification, Shared Contracts and this record match; rule is limited to the delivery-delay population |
| Nine-file dataset prerequisite in this checkout | Satisfied | All files readable; rows, columns, expected fields, key checks, timestamps, relationships and T-00 delivery counts verified as documented above |
| Formal data/KPI/API/UI contract freeze | **Satisfied with limitation** | Shared Contracts v1 is frozen by explicit team-lead approval under the reported delegation; individual contract-text sign-offs are not asserted |
| Kickoff accepted | **Satisfied with limitation** | V3-01 closure and workflow are accepted under the delegated team-lead process; no implementation start is authorized by this record |
| Local setup and dataset verified | **Satisfied for Wageeh; teammate checks are pre-start gates** | Wageeh's Python 3.10.20 `.venv`, audit dependencies and nine CSVs pass the documented checks. The three teammates' local access/setup remains unverified and must be checked before their first task |
| Individual explicit acknowledgement of the same contract version | **Not claimed; not required under the delegated approval process** | The team leader's approval is based on reported delegation, not individual contract-text sign-offs |

**Ledger:** V3-01 is `Completed` under the Master Plan's acceptance criterion that all four owners acknowledge ownership, supported by team-leader-reported plan agreement/delegation and Wageeh's accountable ownership. Shared Contracts v1 is frozen by team-lead approval under that delegation. Teammate local setup is not claimed verified and remains a pre-start gate. V3-02 through V3-15 remain `Planned — Not Started`.
