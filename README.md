# Olist Intelligence

An academic e-commerce analytics and predictive-intelligence demonstration using the historical Brazilian E-Commerce Public Dataset by Olist.

**Official execution baseline: V3.** The baseline was introduced by the transition merge `97f874d974b402b077e57a0361dda485c838adc5`; that is a historical baseline commit, not the current repository HEAD. V2.2 remains preserved as historical project and audit context.

## Start here

- [V3 Team Start Here](docs/planning/TEAM_START_HERE.md)
- [V3 Master Execution Plan](docs/planning/v3/MASTER_EXECUTION_PLAN_V3.md)
- [Canonical V3 Task Ledger](docs/planning/v3/OLIST_INTELLIGENCE_TASK_LEDGER_V3.csv)
- [Frozen Shared Contracts v1](docs/planning/v3/SHARED_CONTRACTS.md)
- Individual execution plans: [Wageeh](docs/planning/v3/WAGEEH_EXECUTION_PLAN.md), [Hamza](docs/planning/v3/HAMZA_EXECUTION_PLAN.md), [Hasnaa](docs/planning/v3/HASNAA_EXECUTION_PLAN.md), and [Rana](docs/planning/v3/RANA_EXECUTION_PLAN.md)

## Project scope and status

V3 combines SQLite business KPIs, data cleaning and EDA, a retrospective delivered-order delivery-delay task, and one FastAPI application serving Jinja2/Bootstrap pages. The model work compares Logistic Regression and Random Forest with the required small MLP on the same chronological evaluation design. It does not reinstate React, CNN/BERT review modeling, RFM/customer prediction, or production CI/CD/deployment scope.

The V3 ledger records **V3-01, V3-06, V3-07, and V3-08 as Completed**. Other tasks remain `Planned — Not Started` in that ledger. Wageeh's remaining tasks are V3-09, V3-12, V3-13, V3-14, and V3-15; Hamza owns V3-02/03, Hasnaa V3-04/05, and Rana V3-10/11. See the ledger and [team guide](docs/planning/TEAM_START_HERE.md) for dependencies and start gates. A completed prerequisite does not itself authorize another task to start; Wageeh coordinates task-specific starts.

The team leader reports instructor approval of the simplified V3 scope; no written evidence has been supplied and the report is not independently verified here. V3-01 and Shared Contracts v1 are recorded completed/frozen under delegated team-lead approval. This is not a claim of individual written contract acknowledgements or verified teammate setup.

## Data and scientific limits

The target is retrospective and conditional on eligible delivered orders. Historical snapshots cannot establish complete follow-up or prove every predictor was available at purchase time. The model is not an all-order live risk estimate, and no causal or production-readiness claim is made. Instructor approval provenance, dataset acquisition, and remaining limitations are documented in the V3 plan and kickoff record.

Original datasets, generated outputs, local databases, trained model files, credentials, and local environments remain outside Git. The dataset is acquired separately; this repository does not redistribute it. Check the [V3 setup gates](docs/planning/v3/V3-01_CONTRACT_FREEZE_AND_KICKOFF.md) before beginning an authorized task.

## Historical V2.2 and audit records

- [Historical V2.2 Master Execution Plan](docs/planning/OLIST_INTELLIGENCE_MASTER_EXECUTION_PLAN_V2_2.md)
- [Historical V2.2 Task Ledger](docs/planning/OLIST_INTELLIGENCE_TASK_LEDGER_V2_2.csv)
- [V2.2-to-V3 transition record](docs/planning/v3/V2_TO_V3_TRANSITION_PLAN.md)
- [T-00 dataset audit](docs/audits/FINAL_DATASET_AUDIT_REPORT.md) and [reproduction guide](docs/audits/README.md)
- [Historical V2.2 Team Start Here archive](docs/planning/archive/TEAM_START_HERE_V2_2.md)
