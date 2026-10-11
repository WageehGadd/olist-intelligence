# Initial team-sharing publication checklist

**Proposal only — awaiting Wageeh's approval. Nothing is staged, committed or pushed; no invitations are created.** This sharing package does not implement or complete T-01–T-40. V2.2 remains unchanged as the official planning source of truth.

## Exact proposed publication allowlist

Publish ONLY these 36 reviewed text/source files in the proposed initial sharing commit:

- `.gitignore`
- `README.md`
- `docs/audits/00_EXECUTIVE_SUMMARY.md`
- `docs/audits/01_DATASET_PROFILE.md`
- `docs/audits/02_RELATIONAL_INTEGRITY.md`
- `docs/audits/03_TEMPORAL_DATA_QUALITY.md`
- `docs/audits/04_DELIVERY_TARGET_FEASIBILITY.md`
- `docs/audits/05_REVIEW_TARGET_FEASIBILITY.md`
- `docs/audits/06_CUSTOMER_INTELLIGENCE_FEASIBILITY.md`
- `docs/audits/07_DEEP_LEARNING_NLP_FEASIBILITY.md`
- `docs/audits/08_FEATURE_LEAKAGE_MATRIX.md`
- `docs/audits/09_BASELINE_EXPERIMENTS.md`
- `docs/audits/10_RISKS_AND_DECISIONS.md`
- `docs/audits/FINAL_DATASET_AUDIT_REPORT.md`
- `docs/audits/README.md`
- `docs/audits/VALIDATION.md`
- `docs/planning/OLIST_INTELLIGENCE_MASTER_EXECUTION_PLAN_V2_2.md`
- `docs/planning/OLIST_INTELLIGENCE_TASK_LEDGER_V2_2.csv`
- `docs/planning/OLIST_INTELLIGENCE_V2_2_CHANGELOG.md`
- `docs/planning/OLIST_INTELLIGENCE_V2_2_VALIDATION.md`
- `docs/planning/PUBLICATION_CHECKLIST.md`
- `docs/planning/TEAM_START_HERE.md`
- `docs/planning/approval_state_v2_2.json`
- `docs/planning/delivery_contract_v2_2.json`
- `docs/planning/schedule_config_v2_2.json`
- `docs/planning/validation_results_v2_2.json`
- `scripts/audit/baselines.py`
- `scripts/audit/config.json`
- `scripts/audit/core.py`
- `scripts/audit/report.py`
- `scripts/audit/requirements.txt`
- `scripts/audit/run.py`
- `scripts/audit/supplement.py`
- `scripts/planning/validate_master_plan_v2_2.py`
- `tests/audit/test_core.py`
- `tests/planning/test_master_plan_validator.py`

## Review by category

- **README / onboarding:** project context, navigation, unchanged owner/dependency summaries and start gates. Every technical task requires team-lead coordination; instructor approval is still pending.
- **Ignore rules:** raw/processed/generated/interim/export data, environments, secrets, notebooks, local databases and common model-weight formats excluded. Root `/models/` is ignored while future `src/models/` Python source remains publishable. `.env.example` is permitted only with placeholder content; no such file is currently proposed.
- **Audit documentation:** aggregate evidence and limitations, not authentic CSV records/review messages. Includes historical local paths and team names intentionally; verify you are comfortable publishing those details. Raw datasets and machine-readable generated dataset statistics remain local.
- **Audit scripts/config/dependencies:** reproducible research source only, no serialized models or credentials. `baselines.py` can run lightweight training when deliberately invoked later; publishing its source does not run it. Do not run audit/training scripts during onboarding.
- **Tests:** synthetic planning mutations and existing audit tests are publishable source. Some audit tests require ignored raw data/aggregate manifests and are not currently clean-clone/CI-safe. Tier A/B isolation is future T-02 work, not silently completed here.
- **V2.2 planning documents/JSON:** full plan/ledger, changelog, validation record, pending approval state, synthetic inference fixture, schedule configuration and captured document-check results. The JSON here contains planning contracts/results, not generated dataset extracts or secret credentials.
- **Planning validator:** standard-library document checks and approval predicate; no ETL or training. Its default exit 0 means consistency, not instructor approval; `--require-approval` remains blocked while pending.

## Excluded from publication

Do not stage `data/raw/`, `data/processed/` (including `t00/` statistics, hashes, CSV matrix), generated/interim/export data, `.venv/`, `.pytest_cache/`, `__pycache__/`, `.env`/credentials/private keys, model weights/artifacts, exploratory notebooks or local databases. Downloaded V2.1 originals are outside this repository and are not part of this commit. Do not use `git add .` as a substitute for the allowlist.

## Checks before approval

- [x] Full eight-file V2.2 package present; original plan/ledger/config/results hashes unchanged by onboarding.
- [x] Planning-only validator succeeds (nine composite checks); planning mutation suite passes (36 tests). No audit baselines, ETL, API, frontend or new model training executed during onboarding.
- [x] Guide covers all 42 tasks under their existing owners, in topological order, with exact direct dependencies and current blockers.
- [x] Ignore probes protect data/env/secret/model paths while preserving `.env.example`, synthetic fixture CSV and model source paths. No probe files created.
- [x] Candidate source/docs inspected; no private-key or common cloud/GitHub/OpenAI token signatures or raw 32-hex identifiers detected. This is a bounded scan/manual review, not an exhaustive privacy or credential certification.
- [x] Root README/guide/checklist navigation checked; no staged changes or tracked data/binaries observed.
- [ ] **Wageeh approves this exact publication allowlist and the local-path/team-name disclosure.**
- [ ] After approval, stage ONLY the allowlisted paths and review `git diff --cached --name-status` and `git diff --cached --check`; confirm no excluded content.
- [ ] Make the authorized initial sharing commit. Suggested message: `docs: publish T-00 audit, V2.2 planning and team onboarding`.
- [ ] Push only with separate authorization; verify repository visibility/access before sharing or inviting Hamza, Hasnaa and Rana.

Instructor approval remains an independent OPEN gate. A documentation-sharing commit, future push or team access does not pass the gate or imply completed CI/development tasks. GitHub visibility and branch protection are not verified here.
