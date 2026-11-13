# V2.2 to V3 Transition Plan

**Status: local transition preparation; proposal pending review.** V2.2 and its history remain intact and are the current recorded baseline until the transition is reviewed and merged. The team leader reports that the instructor approved the simplified V3 scope; no written evidence or date has been supplied, and this report is not independently verified here. The V3-01 contract freeze and implementation kickoff have not occurred. This document does not authorize code work, publication, team notification, or implementation-task status changes.

## 1. Local repository snapshot and verification limits

At transition preparation, the local checkout was `/private/tmp/olist-intelligence-v3`, with `HEAD` at `11beba207ae1f942dd8b23b2ceeaf1fe3853cb1e` on `planning/v3-simplified-master-plan`; local `main`/`origin/main` refs were at `636ed34`. GitHub DNS resolution failed during this execution, so no fetch, `ls-remote`, or current remote verification was possible. PR #2's current base/status/diff, current `origin/main`, and current remote branches are therefore **not independently verified**. Do not treat local refs as current remote state.

The local snapshot contains the T-00 audit package, V2.2 planning package and T-01 approval documentation. No project application source/DB/model was observed. The seven V3 planning documents are present at the proposal commit. Transition preparation now adds this attributed status record, a versioned V3 task ledger, and a README pointer on a separate local branch; no V2.2 record, approval state, application source, test, or validator is changed.

## 2. Historical status: T-00, T-01, T-02

### T-00

V2.2 records T-00 **Completed locally** and the final audit/report/scripts/tests are committed in the merged baseline. The validation record documents all nine CSVs read, audit results, nine local tests passing on 2026-10-10, and sensitive/raw data staying untracked/ignored. The audit is historical evidence; this task did not rerun full-data tests because raw CSVs are not in the clone.

### T-01 and PR #1

PR #1 was merged to `main`; the main history includes the T-01 base and follow-up correction commits. The approval record says the team leader reported that the original project proposal was sent, discussed verbally, and verbally approved on October 26, 2026. No written approval, instructor identity, signature, authenticated evidence, original submitted proposal copy, or submission date is supplied. The later `docs/concept_brief.md` was created afterward and was not separately submitted. The canonical “Brief submitted” criterion remains pending equivalence confirmation. V2.2's state JSON still reads Approved and gate passed per the documented attributed user-report predicate; neither that state nor PR merge proves the V3-reduced scope was approved.

### T-02

The canonical V2.2 ledger remains unchanged: it says T-02 Planned and assigns Hamza T-00 integration/CI foundation. The team leader reports that Hamza did not start T-02 and that no completed implementation is reported. This is attributed team-leader information, not independently inspected evidence. The local snapshot showed no `feature/T-02-*` branch, but current remote branches, PRs, other workspaces, and unpushed work could not be checked because GitHub was unavailable. Do not claim independent verification or alter the historical V2.2 status. Once V3 is formally adopted, this transition record will identify T-02 as **`Not Started — Superseded by V3`** on the basis of that report; until then, T-02 remains shown as Planned in the historical ledger.

The team leader's report is the current stated provenance for T-02 not-started status; it is not remote/workspace verification. Before merging the transition, when connectivity is restored, inspect latest `origin/main`, remote T-02 branches and PRs, and any owner-identified workspace. Preserve any discovered work and compare it to original T-02 acceptance criteria (audit source/reports/tests integrated by PR, Tier A fixture-only CI, raw/full-data tests kept out of Tier A, ignore rules, green CI). Record evidence and reconcile any conflict with the team leader before merge. Once V3 is adopted by an approved and merged transition, record T-02 in this transition record as **`Not Started — Superseded by V3`**, explicitly attributed to the team-leader report; retain the V2.2 ledger's historical `Planned` value unchanged. Never delete, reset, force-push, silently cherry-pick, or claim independent verification based only on the report or branch listing.

## 3. Reuse and preservation

Reuse T-00 dataset inventory, join integrity, temporal quality, delivery eligibility, feature leakage, baseline, and risk evidence as background. Reuse T-01's historical approval provenance only as evidence for the earlier proposal. Preserve all original V2.2 documents, JSON configs, CSV ledger, audit reports, tests, scripts, Git history, PR history, and existing branches unchanged. Do not change the approval-state JSON to imply V3 approval. The proposed seven documents remain in a clearly labeled `v3/` folder so they cannot be mistaken for the existing baseline.

## 4. Proposed task mapping

This is a proposal mapping, not a ledger mutation. V2.2 task IDs are not reused; V3 uses new `V3-XX` IDs. Many V2.2 tasks are split, consolidated, or explicitly removed. Preserve the old IDs/statuses in the original ledger until an approved versioned transition records the mapping.

| V2.2 area/task | V3 treatment |
|---|---|
| T-00 Dataset audit | Completed historical prerequisite; preserve and reuse findings |
| T-01 Concept brief/approval | Preserve historical V2.2 record; V3 scope approval is separately reported by the team leader and is not inferred from T-01 |
| T-02 T-00 integration/CI | V2.2 ledger stays Planned as historical record; team leader reports not started. Upon adoption, this transition record will state `Not Started — Superseded by V3`; remote/workspace status still needs verification when available |
| T-03 schema/contracts | Consolidated into V3-01 contract freeze and V3-02 SQLite schema |
| T-04 ETL | Removed as complex pipeline; simple local CSV cleaning/loading in V3-02/04 |
| T-05 through T-09 SQL/RFM/geographic analytics | Core KPIs consolidated into V3-03; RFM/geographic extras removed |
| T-10 through T-19 delivery model chain | One target remains; population/features/split V3-06/07, LR/RF V3-08, MLP comparison V3-09; advanced boosted-tree experiments, calibration/explainability modules and separate packaging scope reduced |
| T-20 through T-25 review NLP/CNN/BERT/review risk/tracking | Removed from mandatory V3 |
| T-26 through T-28 API design/core/prediction | Shared contracts V3-01, one integrated app V3-12/13 |
| T-29 through T-32 React screens | Replaced by Jinja2/Bootstrap/Plotly UI V3-10/11 |
| T-33 through T-40 integration/release/deploy/presentation | Minimal local integration/tests/report/demo V3-14/15; CI/CD/deploy/release engineering removed |

## 5. Existing branches, PRs, and conflict handling

Do not reset, delete, force-push, or merge any branch. The locally visible T-01 branch is historical and PR #1 is merged in the local snapshot. The team leader reports that T-02 was not started; remote branches/open PRs and other workspaces remain unverified here. When connectivity is restored, verify latest `origin/main`, PR #2, branches and any T-02 work before transition merge. Preserve any discovered V2.2 task work and decide its disposition only with the owner/team lead; never transplant code silently. This local prep proposes only an additive V3 ledger, provenance/status changes in this V3 transition record, and README navigation. Do not alter V2.2 task/approval records or contracts.

## 6. Approval provenance

The team leader reports that the instructor approved the reduced V3 scope. Record this only as **team-leader-reported instructor approval**; no written evidence, date, instructor identity, or independent confirmation has been supplied. Do not use V2.2's approval record as evidence for V3, and do not claim that this V3 plan was submitted to the instructor. If additional evidence or conditions are later supplied, append their provenance accurately without overwriting this report. The seven-document plan is accepted by the team leader for transition preparation, subject to review/merge and contract kickoff.

## 7. Approval checklist

### Team lead

- [ ] Complete formal review of the transition package, including task IDs, assignments, scope, effort, interfaces and gates. The team leader accepted the seven-document plan for transition preparation; this does not constitute transition approval/merge.
- [ ] Confirm Wageeh can support 12.5h/week for a four-week stretch or about 10h/week over the provisional five-week schedule; otherwise extend the target.
- [ ] Confirm four team members agree their responsibilities and time assumptions.
- [ ] Resolve dependencies and ensure no T-02 work is discarded.
- [ ] Check raw-data license, privacy, and data access plan.
- [ ] Verify current GitHub status/branches/rules when connectivity is available.
- [ ] Authorize any proposed baseline/ledger/README changes as a separate publication step.

### Instructor

- [x] Scope approval for SQL analytics + cleaning/EDA + delivery ML/MLP + FastAPI/Jinja2 is reported by the team leader; no written evidence is supplied and this has not been independently verified here.
- [x] The same team-leader report describes approval of the simplified scope, including its reductions from V2.2; no separate written confirmation of individual removed modules is supplied.
- [ ] Record any additional instructor conditions/evidence if they are supplied later; do not invent details or use V2.2 approval as V3 evidence.

Until these gates are met, all V3 tasks remain **Not authorized / blocked**. Existing V2.2 state does not automatically unlock V3 implementation.

## 8. Exact pre-implementation sequence

1. Keep this transition package on its separate local review branch; do not stage, commit, push, create a PR, merge or notify members as part of this preparation.
2. Review all transition files and the new V3 ledger; reconcile comments without changing V2.2 history.
3. The team leader's T-02 not-started statement is recorded as attributed provenance. When connectivity returns, inspect latest remote `main`, PR #2 and T-02 refs/PRs; reconcile any conflicting evidence before transition review/merge.
4. Record the V3 instructor approval only as team-leader-reported; add no date, identity, signature, written evidence or submission claim unless supplied.
5. Resolve the remaining capacity, license/privacy, Python/DL framework, GitHub rules and KPI decisions.
6. Submit a separate transition PR only after current remote state and PR #2 are verified. Include the V2.2-to-V3 baseline decision and versioned ledger; do not edit historical V2.2 files in place.
7. Obtain explicit team-lead review and the user's separate authorization for publication/merge. Merge only after the transition review is complete.
8. After merge, re-verify latest `main`, PR/branch status, T-02 evidence and owner acknowledgements. Then run V3-01 contract freeze and kickoff; neither is complete in this preparation.
9. Only after V3-01 contract freeze/kickoff is completed and explicit coordination may members begin V3 implementation tasks.

## 9. What must not change before approval

Do not alter the V2.2 Master Plan, canonical Task Ledger, approval records, T-00 audits, validators, tests, or application source. The README change in this local branch is only a conditional pointer to the proposed successor and explicitly keeps V2.2 current until transition approval/merge; it does not activate V3. Do not mark V3 tasks started/completed, change historical T-02 status, present the team-leader report as independently verified evidence, notify members to begin work, or treat this local branch as published. No implementation, data import, training, app development, installation, commit, push, merge, collaborator invitation, or permissions change is authorized by this preparation.
