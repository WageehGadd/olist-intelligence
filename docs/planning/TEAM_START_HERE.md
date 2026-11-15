# Olist Intelligence V3 — Team Start Here

For Wageeh, Hamza, Hasnaa, and Rana. **V3 is the official execution baseline on `main`.** This guide points to the frozen V3 plan and ledger; it does not authorize a task start by itself.

## What we are building

A bounded academic demonstration using the historical Brazilian E-Commerce Public Dataset by Olist: SQLite business analytics, data cleaning and EDA, retrospective delivery-delay prediction, and one FastAPI application serving Jinja2/Bootstrap pages. The ML stream compares Logistic Regression and Random Forest with a small MLP on the same population and chronological evaluation design. The approved scope does not include React, CNN/BERT review modeling, RFM/customer prediction, or a production CI/CD/deployment platform.

The delivery label is retrospective and limited to eligible delivered orders. The historical extract cannot prove that every feature was available at purchase time, and the result is not a live all-order operational risk estimate. This is an academic demonstration, not a production service or causal/business-impact claim.

## Official V3 references

- [Master Execution Plan](v3/MASTER_EXECUTION_PLAN_V3.md) — scope, task specifications, dependencies, acceptance criteria, workflow, and limitations.
- [Shared Contracts v1](v3/SHARED_CONTRACTS.md) — canonical frozen data, KPI, file, API, and UI interfaces.
- [Canonical V3 Task Ledger](v3/OLIST_INTELLIGENCE_TASK_LEDGER_V3.csv) — task owner, dependencies, status, and deliverables.
- Individual plans: [Wageeh](v3/WAGEEH_EXECUTION_PLAN.md), [Hamza](v3/HAMZA_EXECUTION_PLAN.md), [Hasnaa](v3/HASNAA_EXECUTION_PLAN.md), and [Rana](v3/RANA_EXECUTION_PLAN.md).
- [V3-01 contract and kickoff record](v3/V3-01_CONTRACT_FREEZE_AND_KICKOFF.md) — approval provenance, agreed workflow, and per-member setup gates.
- [V2.2-to-V3 transition record](v3/V2_TO_V3_TRANSITION_PLAN.md).
- [Historical V2.2 onboarding archive](archive/TEAM_START_HERE_V2_2.md), [V2.2 Master Plan](OLIST_INTELLIGENCE_MASTER_EXECUTION_PLAN_V2_2.md), and [V2.2 Task Ledger](OLIST_INTELLIGENCE_TASK_LEDGER_V2_2.csv).

If this guide and the Master Plan or ledger differ, the Master Plan and canonical V3 ledger govern task scope, ownership, dependencies, and status; Shared Contracts v1 governs interfaces.

## Approval and current ledger status

The team leader reports that the instructor approved the simplified V3 scope. No written approval evidence was supplied, and this report is not independently authenticated here. V3-01 and Shared Contracts v1 are recorded complete/frozen under delegated team-lead approval; this does not replace separate coordination for each task. The earlier V2.2 approval record concerns the original concept and is not evidence of V3 instructor approval.

On the verified `main` baseline, **V3-01, V3-06, V3-07, and V3-08 are Completed**. The ledger lists the following remaining tasks as `Planned — Not Started`; that is the recorded ledger state, not independent verification of anyone's private workspace or out-of-repository progress.

| Member | Assigned V3 tasks and dependency order |
|---|---|
| **Wageeh** | **Completed:** V3-01 scope/contracts/kickoff; V3-06 delivery population; V3-07 features/split; V3-08 classical models. **Remaining:** V3-09 MLP comparison/model selection (after V3-07 and V3-08 evaluation contract); V3-12 FastAPI analytics routes (after V3-01 contracts; Hamza outputs are an integration input); V3-13 prediction endpoint/inference (after V3-09 and V3-01); V3-14 integration (after V3-03, V3-05, V3-11, V3-12, V3-13); V3-15 final verification/report/demo (after V3-14 and member handoffs). |
| **Hamza** | V3-02 SQLite schema and raw-table loading (after V3-01 and local raw CSV access); V3-03 SQL business KPIs/reconciliation (after V3-02). |
| **Hasnaa** | V3-04 profiling/cleaning outputs (after V3-01 and local raw CSV access); V3-05 EDA/charts/findings (after V3-04). |
| **Rana** | V3-10 UI shell/components/synthetic mock data (after V3-01); V3-11 pages/charts/prediction form (after V3-10). |

Check the ledger and each task's full Master Plan specification before work: completing a predecessor does **not** automatically authorize another member to begin. Wageeh must coordinate and authorize each task start, and every listed dependency and setup gate must be satisfied. Do not infer or report team progress from the plan alone.

## Before your first task

1. Wait for Wageeh's task-specific start coordination; confirm the task's dependencies are complete in the V3 ledger and read its Master Plan acceptance criteria and individual guide.
2. In your own checkout, verify the repository identity, update from the agreed `main`, and confirm a clean working tree before creating a task branch.
3. Check your local Python version with `.venv/bin/python --version` and compare it with the documented project baseline. The existing audit requirements file covers T-00 only; no complete V3 application/MLP dependency manifest is present. Do not invent a stack or install extra dependencies without coordination.
4. If your task needs the original data, verify that all nine expected Olist CSVs listed in the kickoff record are locally extracted under `data/raw/`, readable, and have the required contract columns. The team leader reports sending the dataset ZIP, but teammates' local extraction, data access, and environment setup have not been independently verified. Keep source data local; do not send record-level samples or commit it.
5. Confirm raw data and task-generated files are ignored with `git check-ignore`; keep local databases, processed outputs, model binaries, secrets, environments, and caches out of commits. Share setup pass/fail and version information, not private data.

If data, dependencies, a contract, or a predecessor is missing, stop and ask Wageeh to coordinate a resolution. Do not silently change a frozen interface.

## Branch and Pull Request workflow

Use one task-specific branch from the coordinated base, make focused changes, run the task's relevant tests and `git diff --check`, and inspect the staged file list. Open a Pull Request into `main`; do not push directly to `main`. The team lead reviews and explicitly coordinates merges. These are the agreed team workflow, not a claim that GitHub branch protection or CI enforcement is configured. Report blockers before proposing changes to Shared Contracts v1.

Authentic raw CSVs, generated data, SQLite databases, trained model binaries, secrets, virtual environments, and caches stay outside Git. Use clearly labeled synthetic fixtures when a task calls for mocks. Do not interpret a local test result as GitHub CI.
