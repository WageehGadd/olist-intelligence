> **Historical archive — V2.2 onboarding.** Original wording and historical claims are preserved; relative links were adjusted for this archive location. Its task status and scope statements are not current V3 instructions. See the [current V3 Team Start Here guide](../TEAM_START_HERE.md).

---

# Team Start Here — Olist Intelligence

For Wageeh, Hamza, Hasnaa and Rana. **Current stage: T-01 documentation under team-lead review. Instructor approval is user-reported, dated October 26, 2026; independent authentication is not claimed. No other task is authorized by this guide. Coordinate every technical task with Wageeh first, even if its dependencies appear satisfied.** See the [approval record](../../approval/T-01_instructor_approval.md) and [concept brief](../../concept_brief.md).

## What we are building

A DEPI Round 5 academic e-commerce intelligence platform: SQL analytics and descriptive customer intelligence, delivery lateness prediction, Portuguese submitted-review rating-proxy analysis with a classical/CNN comparison, explainability, a FastAPI backend and React frontend. It is an academic retrospective demonstration, not a production service. Review NLP is not gold-standard sentiment or purchase-time review-risk prediction; future customer value is outside the approved proposed scope.

## Official planning references

- [Full Master Execution Plan V2.2](../OLIST_INTELLIGENCE_MASTER_EXECUTION_PLAN_V2_2.md): architecture, detailed task specifications, scientific gates and Git workflow.
- [Canonical Task Ledger V2.2](../OLIST_INTELLIGENCE_TASK_LEDGER_V2_2.csv): ownership, reviewers, dependencies, scope, estimates and status.
- [V2.2 validation](../OLIST_INTELLIGENCE_V2_2_VALIDATION.md) and [changelog](../OLIST_INTELLIGENCE_V2_2_CHANGELOG.md).
- [Approval state](../approval_state_v2_2.json), [delivery input contract](../delivery_contract_v2_2.json) and [schedule assumptions](../schedule_config_v2_2.json).
- [T-00 final audit](../../audits/FINAL_DATASET_AUDIT_REPORT.md) and [audit reproduction guide](../../audits/README.md).

V2.2 remains the official planning source of truth. This guide summarizes it; it does not change assignments, dependencies, task status or scope. Consult Parts 10–11 and the ledger if a summary is unclear.

## What can happen now, and what is blocked

Now: read the plan/audit, understand your assignments, discuss skills/access and ask Wageeh about coordination. Only T-01 proposal/approval documentation is currently authorized. No training, ETL, API, frontend, CI implementation or T-02 repository integration is started by this update.

T-00 is completed locally, and its source/reports/tests are present in the published baseline. T-01 (Wageeh) is authorized for this documentation update; the new brief awaits review/submission confirmation. T-02 (Hamza) has its T-00 dependency met but still awaits a separate team-lead start decision and its own CI/fixture/integration deliverables. T-02 may later proceed before instructor approval as V2.2 allows; this guide does not authorize it or complete its CI/fixture/PR integration work.

T-03 additionally needs T-02 complete AND `approval_gate_passed=true`. A recorded rejection never unlocks implementation; conditional approval requires incorporated changes accepted by the instructor, with evidence. The current gate passes on the attributed user report; T-03 remains blocked by T-02 and its other preconditions. The list below retains the original task allocation and prerequisite summaries; it does not claim the approval gate is still pending. Every task also needs all listed predecessor tasks completed, the Part 11 preconditions and team-lead coordination. Optional/Advanced tasks require explicit scope/budget coordination and never block mandatory delivery. T-23 additionally needs confirmed GPU access. No academic deadline is assumed.

## Assigned owner tasks — dependency order

The lists below follow a topological order of the unchanged canonical graph, not a promised calendar or permission to start. “After” lists ALL direct dependencies, including other members' tasks. Reviewer/collaborator assignments remain in the ledger; review responsibilities are additional to these owner lists.

### Wageeh

- **T-00 — Dataset Feasibility Audit** (Governance, 0h). After: none. Completed locally; integration remains T-02.
- **T-01 — Concept Brief & Instructor Approval** (Governance, 6h). After: T-00. Authorized documentation update under review; newly prepared brief submission remains unverified.
- **T-03 — Data Contracts & DB Schema Design** (MVP, 12h). After: T-01(approval_gate_passed), T-02. Blocked by prerequisites / approval gate.
- **T-10 — Delivery Target & Population Builder** (MVP, 8h). After: T-04, T-06. Blocked by prerequisites / approval gate.
- **T-26 — API Design & Contract Specification** (MVP, 6h). After: T-03, T-05. Blocked by prerequisites / approval gate.
- **T-11 — Delivery Feature Engineering** (MVP, 10h). After: T-10. Blocked by prerequisites / approval gate.
- **T-23 — BERTimbau Fine-tuning (Optional)** (Optional, 14h). After: T-22. Blocked by prerequisites / approval gate.
- **T-14 — Delivery Baseline Models** (MVP, 10h). After: T-13. Blocked by prerequisites / approval gate.
- **T-16 — Gradient Boosted Trees (Advanced)** (Advanced, 8h). After: T-15. Blocked by prerequisites / approval gate.
- **T-17 — Calibration & Threshold Selection** (MVP, 8h). After: T-14, T-15. Blocked by prerequisites / approval gate.
- **T-19 — Delivery Model Packaging & Inference Contracts** (MVP, 8h). After: T-17, T-18. Blocked by prerequisites / approval gate.
- **T-38 — Demo Environment & Deployment** (MVP, 6h). After: T-37, T-35. Blocked by prerequisites / approval gate.
- **T-40 — Final Release & Handoff** (Governance, 4h). After: T-39. Blocked by prerequisites / approval gate.

### Hamza

- **T-02 — T-00 Integration & CI Foundation** (MVP, 10h). After: T-00. Dependency met; awaiting team-lead start decision.
- **T-05 — SQL Analytical Views** (MVP, 10h). After: T-04. Blocked by prerequisites / approval gate.
- **T-07 — Business Analytics Module** (MVP, 8h). After: T-05. Blocked by prerequisites / approval gate.
- **T-22 — DL Comparison (CNN)** (MVP, 10h). After: T-21. Blocked by prerequisites / approval gate.
- **T-27 — API Core Implementation** (MVP, 10h). After: T-26. Blocked by prerequisites / approval gate.
- **T-30 — Dashboard Screens** (MVP, 14h). After: T-27, T-07, T-08, T-09. Blocked by prerequisites / approval gate.
- **T-24 — Review Risk Prediction (Advanced)** (Advanced, 10h). After: T-20, T-11, T-13. Blocked by prerequisites / approval gate.
- **T-15 — Tree Model Experiments** (MVP, 10h). After: T-14. Blocked by prerequisites / approval gate.
- **T-33 — End-to-End Integration** (MVP, 10h). After: T-31, T-32. Blocked by prerequisites / approval gate.
- **T-36 — Documentation & Model Cards** (MVP, 8h). After: T-35. Blocked by prerequisites / approval gate.

### Hasnaa

- **T-04 — ETL Pipeline Implementation** (MVP, 14h). After: T-03. Blocked by prerequisites / approval gate.
- **T-08 — Customer RFM & Cohort Analysis** (MVP, 8h). After: T-05. Blocked by prerequisites / approval gate.
- **T-21 — NLP Preprocessing & Classical Baseline** (MVP, 12h). After: T-20. Blocked by prerequisites / approval gate.
- **T-12 — Customer Clustering (Optional)** (Optional, 8h). After: T-08. Blocked by prerequisites / approval gate.
- **T-22B — NLP Model Packaging & Inference Contracts** (MVP, 6h). After: T-22. Blocked by prerequisites / approval gate.
- **T-18 — Explainability Module** (MVP, 10h). After: T-17. Blocked by prerequisites / approval gate.
- **T-28 — API Prediction Endpoints** (MVP, 8h). After: T-27, T-19, T-22B. Blocked by prerequisites / approval gate.
- **T-31 — Prediction UI Screens** (MVP, 10h). After: T-28, T-30. Blocked by prerequisites / approval gate.
- **T-34 — Explainability Integration** (MVP, 6h). After: T-18, T-33. Blocked by prerequisites / approval gate.

### Rana

- **T-06 — Data Quality Test Suite** (MVP, 10h). After: T-04. Blocked by prerequisites / approval gate.
- **T-20 — Review Label Construction** (MVP, 8h). After: T-04. Blocked by prerequisites / approval gate.
- **T-09 — Geographic & Seller Analytics** (MVP, 8h). After: T-05. Blocked by prerequisites / approval gate.
- **T-37 — CI/CD Pipeline** (MVP, 8h). After: T-02, T-06. Blocked by prerequisites / approval gate.
- **T-29 — Frontend Scaffold & Routing** (MVP, 8h). After: T-26. Blocked by prerequisites / approval gate.
- **T-13 — Chronological Split Implementation** (MVP, 6h). After: T-11. Blocked by prerequisites / approval gate.
- **T-25 — Experiment Tracking (Advanced)** (Advanced, 6h). After: T-14, T-21. Blocked by prerequisites / approval gate.
- **T-32 — Model Insights Screen** (MVP, 6h). After: T-18, T-28. Blocked by prerequisites / approval gate.
- **T-35 — End-to-End Testing** (MVP, 8h). After: T-34, T-33. Blocked by prerequisites / approval gate.
- **T-39 — Presentation Preparation** (Governance, 8h). After: T-36, T-38. Blocked by prerequisites / approval gate.

## Branches, reviews and sharing

For future authorized task work, follow Master Plan Part 15: create a task branch from the coordinated base, named `feature/T-XX-short-description`; do not work directly on main. Commit messages and PR titles reference the task ID. Stage specific reviewed files, inspect the staged diff and never include authentic datasets, generated outputs, secrets or model weights. The assigned reviewer must approve before an authorized merge; describe changes, tests and limitations in the PR. CI/Tier A requirements apply once T-02 establishes CI; no green badge or branch protection exists by assumption today. Full-data Tier B checks stay local; audit tests currently include raw/aggregate-dependent cases awaiting T-02 isolation.

Do not commit/push this initial sharing package or invite collaborators until Wageeh approves the publication checklist. An initial documentation-sharing commit does not mark T-02 or any other project task complete. Existing scripts are audit evidence, not instructions to rerun training during onboarding.

For an optional planning-only consistency check (no raw data, ETL or model training):

```sh
.venv/bin/python -B scripts/planning/validate_master_plan_v2_2.py
```

Use the existing Python 3.10 virtual environment locally. Dataset files are obtained separately from their publisher after license review; they do not travel in Git. A clean clone will not contain local data/aggregates/model artifacts. Start with reading and coordination, not the audit reproduction/training commands.
