# Olist Intelligence

Explainable E-Commerce Analytics & Predictive Intelligence Platform — DEPI Round 5 Data Scientist graduation project.

**Current recorded baseline: V2.2 remains in force until the V3 transition is reviewed and merged. The team leader reports that the instructor approved the simplified V3 scope; no written evidence has been supplied, and this is not independently verified here. V3-01 contract freeze and implementation kickoff have not occurred. No V3 implementation is authorized by this local preparation.** See the [historical concept brief](docs/concept_brief.md) and [V2.2 approval record](docs/approval/T-01_instructor_approval.md); that record concerns the earlier project concept, not the V3 scope.

## Start here

- [Team Start Here — Wageeh, Hamza, Hasnaa and Rana](docs/planning/TEAM_START_HERE.md)
- [Official Master Execution Plan V2.2](docs/planning/OLIST_INTELLIGENCE_MASTER_EXECUTION_PLAN_V2_2.md)
- [Canonical Task Ledger V2.2](docs/planning/OLIST_INTELLIGENCE_TASK_LEDGER_V2_2.csv)
- [V2.2 validation and limitations](docs/planning/OLIST_INTELLIGENCE_V2_2_VALIDATION.md)
- [Initial publication review checklist](docs/planning/PUBLICATION_CHECKLIST.md)
- [T-00 dataset audit](docs/audits/FINAL_DATASET_AUDIT_REPORT.md)

## Proposed V3 transition (review only)

V3 is intended to become the active execution baseline only after the transition is approved and merged. Until then, V2.2 and its canonical task ledger remain the recorded baseline and are preserved unchanged. The V3 proposal covers SQL analytics, cleaning/EDA, delivery ML with a small MLP comparison, and one FastAPI/Jinja2 application; it does not authorize implementation. Its instructor approval status is recorded as team-leader-reported, without written evidence. The team leader reports that Hamza did not start historical T-02; the original V2.2 ledger remains `Planned`, and the transition record explains the proposed supersession without rewriting that history.

- [V3 Master Execution Plan](docs/planning/v3/MASTER_EXECUTION_PLAN_V3.md)
- [Wageeh execution plan](docs/planning/v3/WAGEEH_EXECUTION_PLAN.md)
- [Hamza execution plan](docs/planning/v3/HAMZA_EXECUTION_PLAN.md)
- [Hasnaa execution plan](docs/planning/v3/HASNAA_EXECUTION_PLAN.md)
- [Rana execution plan](docs/planning/v3/RANA_EXECUTION_PLAN.md)
- [V3 Shared Contracts](docs/planning/v3/SHARED_CONTRACTS.md)
- [V2.2-to-V3 Transition Plan](docs/planning/v3/V2_TO_V3_TRANSITION_PLAN.md)
- [Versioned V3 Task Ledger](docs/planning/v3/OLIST_INTELLIGENCE_TASK_LEDGER_V3.csv)

The existing [V2.2 Master Plan](docs/planning/OLIST_INTELLIGENCE_MASTER_EXECUTION_PLAN_V2_2.md), [canonical V2.2 Task Ledger](docs/planning/OLIST_INTELLIGENCE_TASK_LEDGER_V2_2.csv), approval state and project history remain intact. The V3 ledger is additive and does not alter V2.2 task records.

Raw datasets, generated data, virtual environments, credentials and model binaries stay out of Git. The dataset source is [Olist on Kaggle](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce); publisher license confirmation remains open. This repository is not a dataset distribution. Existing audit scripts/tests need local inputs for full reproduction. No V3 technical implementation is authorized until the transition is approved and merged and V3-01 contract freeze/kickoff is completed. No CI or production-readiness claim is made.
