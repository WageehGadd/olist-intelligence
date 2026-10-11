# Olist Intelligence — V2.2 targeted patch changelog

Date: 2026-10-12 (Africa/Cairo). Inputs: all five user-supplied V2.1 files in `/Users/wageehgadd/Downloads/`. They were read as reference material, not as authorization to execute their future implementation tasks. Originals were preserved. The full V2.2 plan keeps 19 parts, 42 IDs including T-22B, FastAPI/React architecture, four members and all owner estimates/assignments/scopes/priorities.

## A — Actual audit paths and integration state

- **Defect/evidence:** V2.1 Parts 3/7 and T-00 described a root report, root numbered scripts and t00_reports as committed. `git ls-files` listed only `.gitignore` and `README.md`; actual audit files are locally untracked under docs/audits, scripts/audit and tests/audit, with aggregates ignored under data/processed/t00.
- **Root cause:** a planning directory narrative was treated as observed repository state.
- **Correction:** preserve actual paths, correct all reproduction commands, distinguish local T-00 completion from review/commit/PR/merge, and explicitly assign that future integration to T-02. Existing audit tests include raw-dependent cases; T-02 must mark/isolate them for Tier B rather than assume CI is fixture-safe today. Remote visibility/default branch/protection remain NOT VERIFIED after GitHub CLI connection failed.
- **Affected tasks:** T-00, T-02, T-03, T-37; Parts 3, 7, 14, 15.
- **Validation:** V-09 path/structure check; actual Git/filesystem/ignore inspection and raw hashes; no Git mutation performed.

## B — Approval response is not implementation permission

- **Defect/evidence:** T-01 DoD allowed approval OR handled rejection, but T-03 depended on task closure. Conditional approval could also pass without accepted revisions.
- **Root cause:** administrative response recording and milestone success were conflated.
- **Correction:** six states, distinct administrative closure and approval_gate_passed predicate. Rejected always false; conditional approval requires incorporated AND accepted changes plus evidence. Ledger annotation, T-03 precondition, first sprint, academic invariant, release gate and risk mitigation updated. Pending state has no evidence; submission itself is not verified.
- **Affected tasks:** T-01, T-03 and downstream formal implementation; Parts 1, 13, 17–19.
- **Validation:** V-07 verifies document/state consistency; truth-table and bypass mutation tests. `--require-approval` exits 2 while pending. Text/CSV cannot authenticate instructor evidence; external decision remains OPEN.

## C — Delivery training/serving input consistency

- **Defect/evidence:** Part 8 omitted purchase timestamp while claiming weekday derivation and included untimestamped installments. T-11 listed features absent from inference inputs. T-26 depended implicitly on unfinished T-11 despite its earlier-start DAG.
- **Root cause:** proposed feature inventory was not frozen to an inference snapshot/schema.
- **Correction:** primary purchase_creation / purchase-v1 contract derives exactly the ten T-00 baseline features from explicit timestamp, original promise, state and unit cart rows. Product/seller keys supply distinct counts only. No required payments, dimensions, distance or live lookup. Forbid server-time replacement and unsupported fields. Shared transformation/package requirement and frozen fixture parity criteria added; T-26 uses this already specified planning contract rather than a hidden T-11 dependency. Availability of original cart/promise remains a retrospective assumption. Future revised feature sets require versioned contracts.
- **Affected tasks:** T-11, T-19, T-26, T-28, T-31; Part 8/9 schemas/forms and quality gates.
- **Validation:** V-08 verifies feature ordering, input coverage and independent frozen-fixture arithmetic. It does NOT claim product training/serving parity was executed: that pipeline does not exist yet. Product parity tests are required during those future tasks.

## D — Meaningful validator checks and mutation tests

- **Defect/evidence:** V2.1 C-08/22/23/26 mostly computed values or searched IDs without comparing detailed document claims. C-24 reported 61/62 regex-extracted edges as PASS; its regex missed source nodes with inline labels and did not require complete coverage. C-25 knew only six phantom routes.
- **Root cause:** descriptive outputs were labeled tests of stronger conditions than implemented.
- **Correction:** stdlib validator checks every task summary/spec field, statuses, owner/collaborator/reviewer budgets and role metadata; displayed member/scope/effort summaries and member task tables; exact 62-edge task DAG/spec/ledger sets and cycles; full registry/definition/screen and all active HTTP method/path references. Historical paths require explicit delimiters. Unknown values/missing inputs fail nonzero. Nine composite checks replace misleading check-count inflation; computation-only details are evidence, not separate PASS assertions.
- **Affected tasks:** planning quality checks only; no product implementation.
- **Validation:** synthetic mutations include all nine requested cases and additional cycles, registry omissions, extra edges, summary/assumption errors, approval bypass, nonfinite hours and inference input omissions. Both API result and subprocess exit 1 are tested for the eighteen core mutations. Pending academic gate has a separate exit code.

## E — Schedule arithmetic and honest feasibility

- **Defect/evidence:** V2.1 applied all-scope 53/39 overhead to mandatory work, called 384h capacity versus ~404h “barely achievable”, and said all tasks fit 480h while omitting the stated contingency.
- **Root cause:** scopes/overheads/buffers were not defined in one machine-readable schedule contract.
- **Correction:** mandatory = 312 owner + 48 collaboration + 34 review + 20 shared + 46.8 contingency = 460.8h. All-scope = 358 + 53 + 39 + 20 + 53.7 = 523.7h. Four people ×12h/week: six=288, eight=384, ten=480. Six/eight mandatory exceed capacity; ten mandatory fits aggregate capacity with 19.2h margin; ten all-scope exceeds by 43.7h. This is not a resource-constrained/dependency-feasible calendar. No deadline invented.
- **Affected tasks:** no estimates or owners changed; Part 16 and adoption limitations.
- **Validation:** V-04/V-05 compare all displayed quantities, assumptions, scenario calculations and verdicts against ledger/config. Mutation tests alter both totals and assumptions.

## F — Independent scientific corrections

- **Defect/evidence:** V2.1 called review_id unique and claimed 217 orphan reviews, 2,117 missing dimensions, first-review NLP deduplication, prior/stratified baseline confusion and RFM requiring delivery timestamp.
- **Root cause:** claims diverged from actual T-00 code/measurements.
- **Correction:** 814 duplicate review-ID excess; 0 review-orphan rows; 2 missing values in each physical dimension/weight column (610 missing categories separate). Delivery target keeps exact delivered/nonmissing/chronology/calendar logic: 96,470 labels and 6,534 late. T-00 test is 32,092 with 1,363 late, so dummy prior AP is 0.04247, not global 0.0677. NLP excludes ALL globally repeated normalized texts and ALL multi-review orders, splits by answer timestamp, and uses rating proxy, not true sentiment. Procedure A exact preprocessing and maturity filters retained; revised Procedure B policies explicit. Calibration/model selection/threshold data are separated with maturity/overfitting disclosures. RFM Recency uses latest purchase; delivered-only is a population decision. Delivered customer count 93,358 independently verified. Monetary KPI is delivered-only gross item value plus charged freight, not company revenue/profit; recorded payments are separately aggregated. Gate 1 metric evidence now uses same-phase T-05, not future T-07.
- **Affected tasks:** T-03–T-11, T-13–T-17, T-20–T-22B, T-24, T-30 and scientific gates.
- **Validation:** real CSV computations and T-00 source/results reconciliation; protocol semantics reviewed manually. No retraining performed for this patch.

## Ledger changes and preserved estimates

T-00 status changed Completed → Completed locally; deliverable paths corrected. T-03 dependency qualifier changed approval → approval_gate_passed. Previously blank collaborator names were reconciled with the detailed specifications; “All team” expands to named nonowner collaborators, and T-39/T-40 include the collaborators the existing detailed specs intended. Collaboration hours remain pooled task budgets, not equal per-person estimates. Summary titles now use exact canonical titles (T-19/T-22B no abbreviation). All 42 task IDs, owner roles, reviewer roles, scopes, priorities and all three numeric estimates remain unchanged. Totals: owner 358h, collaboration 53h, review 39h, assigned effort 450h; scope owner totals MVP 294 / Governance 18 / Advanced 24 / Optional 22.

No authentic CSV, existing T-00 file or V2.1 input was modified; no commit, push, merge or production implementation was performed.
