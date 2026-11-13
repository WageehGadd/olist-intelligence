# V3-01 Contract Review and Team Kickoff Record

**Status: FORMAL CONTRACT FREEZE PENDING; V3-01 AND IMPLEMENTATION KICKOFF INCOMPLETE. Implementation is not authorized.** Prepared on branch `task/v3-01-contract-freeze` from the supplied local `main` baseline `97f874d974b402b077e57a0361dda485c838adc5`. The approved team-lead population decision is documented in the current Shared Contracts review draft; it does not mean the contracts have been formally frozen or accepted by the team. No network fetch was performed.

## Scope and approval provenance

V3 is the current planning baseline. The team leader reports that the instructor approved the simplified V3 scope; no written evidence was supplied and the report is not independently verified here. The team leader reports Hamza did not start historical T-02; other workspaces, remote branches and PRs were not independently checked. The V2.2 Master Plan, approval records and canonical ledger are unchanged. The V2.2 ledger retains T-02 as `Planned`; the transition record attributes its reported supersession to the team leader.

The project remains the approved 15-task scope: SQL analytics, cleaning/EDA, delivery ML with a small MLP comparison, and one FastAPI/Jinja2 application. No scope, architecture, task owner, estimate or dependency changes are proposed here.

## Owners and first tasks

| Member | Accountable work | First implementation task after V3-01 |
|---|---|---|
| Hamza | SQLite and authoritative SQL KPIs; sole publisher of shared KPI values, including `delay_rate_calendar` | V3-02 |
| Hasnaa | Data profiling/cleaning and EDA chart outputs; may independently reconcile but does not publish shared KPI values | V3-04 |
| Wageeh | Delivery target/features/models, FastAPI, and integration; independent target reconciliation does not supersede Hamza's KPI ownership | V3-06 |
| Rana | Jinja2/Bootstrap/Plotly templates, synthetic mock fixtures and browser interactions | V3-10 |

The task ledger remains the source for all task IDs, estimates and dependencies. The independent starts are conditional on V3-01 being accepted; none is authorized by this draft. The four members' acknowledgements of the same frozen contract version have not been supplied.

## Reviewed interfaces (formal freeze pending)

The detailed canonical definitions remain in [`SHARED_CONTRACTS.md`](SHARED_CONTRACTS.md). The audit found these interfaces consistent across the plans. Formal freeze remains pending V3-01 acceptance and owner acknowledgements; the approved target-population rule is recorded below:

- **Hamza → Wageeh → Rana:** `data/processed/sql_kpis.csv` and `sql_category_item_value.csv`; Wageeh maps the exact schemas to the summary, delivery-monthly and category-item-value JSON routes; Rana consumes those routes.
- **Hasnaa → Wageeh → Rana:** `eda_category_item_counts.csv` and `eda_item_price_distribution.csv`; Wageeh maps them to the two chart JSON routes; Rana consumes the returned series.
- **Wageeh → Rana:** server-rendered Jinja2 contexts for `GET /`, `/sales`, `/delivery`, `/predict`; browser fetches only for Sales period changes, Delivery period changes, and `POST /api/v1/predict`.
- **Prediction:** strict request fields are `purchase_timestamp`, `estimated_delivery_date`, `customer_state`, and a nonempty `items` list whose entries contain only numeric `price` and `freight_value`. Training and inference use the same eight ordered features and shared derivation function. Synthetic examples are fixtures only, never observed Olist results.
- **Wageeh → V3-07/Hasnaa:** order-grain `delivery_population.csv`, documented label, counts and exclusions. Eligibility uses the team-lead-approved delivery-delay rule below.

## Approved delivery-delay population rule

**Approved by team-lead direction in this task:** for both the shared `delay_rate_calendar` KPI and ML delivery-delay target population, exclude any order whose estimated delivery calendar date is earlier than its purchase calendar date. Preserve delivered-order eligibility, valid required timestamps, and actual delivery calendar date not before purchase. Label `late=1` only when normalized actual delivery calendar date is strictly later than normalized estimated delivery calendar date. This population exclusion does not automatically apply to unrelated commercial KPIs such as revenue proxies or customer counts. Apply the approved rule consistently in Hamza's KPI and Wageeh's target implementation; report reproduced counts against T-00 rather than hard-coding them.

### Local environment and data check

- `.venv/bin/python`: absent; there is no active project virtual environment to report a version for.
- System `python3`: Python 3.9.6 at `/Library/Developer/CommandLineTools/usr/bin/python3`.
- Available alternatives: `/opt/homebrew/opt/python@3.10/bin/python3.10` is Python 3.10.20; `/opt/homebrew/bin/python3.11` is Python 3.11.15; `/opt/homebrew/bin/python3.12` is Python 3.12.13. These are installed executables, not the project environment.
- `data/raw/`: directory absent. None of the nine expected files is available here: `olist_customers_dataset.csv`, `olist_geolocation_dataset.csv`, `olist_order_items_dataset.csv`, `olist_order_payments_dataset.csv`, `olist_order_reviews_dataset.csv`, `olist_orders_dataset.csv`, `olist_products_dataset.csv`, `olist_sellers_dataset.csv`, and `product_category_name_translation.csv`. File-readability and CSV-schema checks could not be performed. Individual team-member access is unknown.
- `git check-ignore -v` confirmed `.gitignore` excludes `data/raw/`, `data/processed/`, SQLite files, `.venv/`, the `models/` tree and `.env`. No dependencies were installed. GitHub branch protection and review settings were not queried; the workflow below records the team-lead-proposed process, not verified enforcement.

Other V3-01 confirmations remain outstanding: owner acknowledgements; project virtual-environment/dependency verification; individual raw-data access; weekly coordination time and actual capacity; and GitHub branch/review rules.

## Handoffs and working rules

- Hamza is the only owner of authoritative shared KPI values. Hasnaa and Wageeh may reconcile independently and report discrepancies to Hamza; dashboard values and definitions remain Hamza's.
- Each producer hands off exact path/schema/version, generation command, counts, assumptions, tests and limitations. Wageeh owns route/context integration; each producer fixes defects in that producer's output.
- Use one feature branch per task and open a Pull Request into `main`; no direct pushes to `main`. The team lead reviews before merging. Once V3-01 freezes them, use the Shared Contracts as the source of truth, and report integration blockers before proposing any shared-interface change. Inspect the full diff, run relevant local checks and `git diff --check`, and stage explicit paths. These are proposed team rules, not verified GitHub enforcement.
- Keep raw datasets, generated outputs, local databases, secrets, virtual environments, caches and model binaries out of Git. Synthetic fixtures must be visibly labeled as synthetic.
- Estimates are task effort; the one-week/19-hour integration reserve is calendar contingency, not work automatically assigned to junior members. The owner and team lead agree any defect work or move the date.

## V3-01 acceptance status

| Criterion | Status | Evidence / remaining work |
|---|---|---|
| Approved V3 scope and provenance recorded | Satisfied with limitation | Team-leader-reported instructor approval; no written evidence or independent verification |
| Cross-document task IDs, owners, estimates and dependencies checked | Satisfied | Master Plan and 15-row V3 ledger; no task inventory changes |
| Approved delivery-delay population rule consistently documented | Satisfied | Hamza KPI specification, Wageeh target specification, Shared Contracts and this record match; rule is limited to the delivery-delay population |
| Formal data/KPI/API/UI contract freeze | **Pending** | Population rule is documented, but owner acknowledgements and V3-01 acceptance remain outstanding; Shared Contracts is still a review draft |
| Kickoff accepted | **Pending** | Team-lead V3-01 acceptance remains outstanding pending setup verification and owner acknowledgements |
| Local setup assumptions verified | **Pending** | No project virtual environment or raw-data directory is present; system Python is 3.9.6, while Python 3.10.20 is available outside a virtual environment; raw-data access and cadence remain unverified |
| Four owners acknowledge the same contract version | Pending | No acknowledgements are present in this checkout |

**Ledger:** V3-01 remains `Planned — Not Started`; no other task status changed. Its documented acceptance criteria have not been met, so recording it as started or complete would be inaccurate. No implementation task is cleared to begin.
