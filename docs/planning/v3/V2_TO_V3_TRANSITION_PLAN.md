# V2.2 to V3 Transition Plan

**Status: V3 is the official planning baseline recorded on local `main` at `97f874d974b402b077e57a0361dda485c838adc5` during transition preparation.** V2.2 and its history remain intact. This transition snapshot reported instructor approval and V3-01 as pending at that time. Subsequent team-lead delegated approval and V3-01 completion are recorded in [`V3-01_CONTRACT_FREEZE_AND_KICKOFF.md`](V3-01_CONTRACT_FREEZE_AND_KICKOFF.md), [`SHARED_CONTRACTS.md`](SHARED_CONTRACTS.md), and the V3 ledger. The instructor approval remains team-leader-reported without written evidence or independent verification. Per-member setup checks and team-lead start coordination still gate implementation.

## 1. Local repository snapshot and verification limits

Historical proposal preparation used local `HEAD` `11beba207ae1f942dd8b23b2ceeaf1fe3853cb1e` on `planning/v3-simplified-master-plan`; at that time local `main`/`origin/main` refs were `636ed34` and GitHub could not be resolved. For this task, the supplied verified baseline is local `main` at `97f874d974b402b077e57a0361dda485c838adc5`, following the V3 planning and transition merges. No network fetch was made in this execution, so the current live remote and remote branches are not independently verified here.

The local snapshot contains the T-00 audit package, V2.2 planning package and T-01 approval documentation. No project application source/DB/model was observed. The seven V3 planning documents originated on the proposal branch; the merged transition added this attributed status record, a versioned V3 task ledger, and README navigation. No V2.2 record, approval state, application source, test, or validator was changed by that transition.

## 2. Historical status: T-00, T-01, T-02

### T-00

V2.2 records T-00 **Completed locally** and the final audit/report/scripts/tests are committed in the merged baseline. The validation record documents all nine CSVs read, audit results, nine local tests passing on 2026-10-10, and sensitive/raw data staying untracked/ignored. The audit is historical evidence; this task did not rerun full-data tests because raw CSVs are not in the clone.

### T-01 and PR #1

PR #1 was merged to `main`; the main history includes the T-01 base and follow-up correction commits. The approval record says the team leader reported that the original project proposal was sent, discussed verbally, and verbally approved on October 26, 2026. No written approval, instructor identity, signature, authenticated evidence, original submitted proposal copy, or submission date is supplied. The later `docs/concept_brief.md` was created afterward and was not separately submitted. The canonical “Brief submitted” criterion remains pending equivalence confirmation. V2.2's state JSON still reads Approved and gate passed per the documented attributed user-report predicate; neither that state nor PR merge proves the V3-reduced scope was approved.

### T-02

The canonical V2.2 ledger remains unchanged: it says T-02 Planned and assigns Hamza T-00 integration/CI foundation. The team leader reports that Hamza did not start T-02 and that no completed implementation is reported. This is attributed team-leader information, not independently inspected evidence. Remote branches, PRs, other workspaces, and unpushed work have not been checked in this execution. This transition record therefore records T-02 as **`Not Started — Superseded by V3` (team-leader-reported; not independently verified)** while retaining the V2.2 ledger's historical `Planned` value. Do not claim independent verification or alter the historical V2.2 status.

The team leader's report is the current stated provenance for T-02 not-started status; it is not remote/workspace verification. Before making any disposition of possible T-02 work, inspect current `origin/main`, remote T-02 branches and PRs, and any owner-identified workspace when connectivity is available. Preserve discovered work and compare it to original T-02 acceptance criteria (audit source/reports/tests integrated by PR, Tier A fixture-only CI, raw/full-data tests kept out of Tier A, ignore rules, green CI). Record evidence and reconcile conflicts with the team leader. Never delete, reset, force-push, silently cherry-pick, or claim independent verification based only on the report or branch listing.

## 3. Reuse and preservation

Reuse T-00 dataset inventory, join integrity, temporal quality, delivery eligibility, feature leakage, baseline, and risk evidence as background. Reuse T-01's historical approval provenance only as evidence for the earlier proposal. Preserve all original V2.2 documents, JSON configs, CSV ledger, audit reports, tests, scripts, Git history, PR history, and existing branches unchanged. Do not change the approval-state JSON to imply V3 approval. The seven V3 planning documents remain in a clearly labeled `v3/` folder and are the current planning baseline; they do not overwrite V2.2 history.

## 4. Proposed task mapping

This is a transition mapping, not a mutation of the historical ledger. V2.2 task IDs are not reused; V3 uses new `V3-XX` IDs. Many V2.2 tasks are split, consolidated, or explicitly removed. Preserve the old IDs/statuses in the original ledger.

| V2.2 area/task | V3 treatment |
|---|---|
| T-00 Dataset audit | Completed historical prerequisite; preserve and reuse findings |
| T-01 Concept brief/approval | Preserve historical V2.2 record; V3 scope approval is separately reported by the team leader and is not inferred from T-01 |
| T-02 T-00 integration/CI | V2.2 ledger stays `Planned` as historical record; this transition record states `Not Started — Superseded by V3` based on the team-leader report. Remote/workspace state has not been independently verified |
| T-03 schema/contracts | Consolidated into V3-01 contract freeze and V3-02 SQLite schema |
| T-04 ETL | Removed as complex pipeline; simple local CSV cleaning/loading in V3-02/04 |
| T-05 through T-09 SQL/RFM/geographic analytics | Core KPIs consolidated into V3-03; RFM/geographic extras removed |
| T-10 through T-19 delivery model chain | One target remains; population/features/split V3-06/07, LR/RF V3-08, MLP comparison V3-09; advanced boosted-tree experiments, calibration/explainability modules and separate packaging scope reduced |
| T-20 through T-25 review NLP/CNN/BERT/review risk/tracking | Removed from mandatory V3 |
| T-26 through T-28 API design/core/prediction | Shared contracts V3-01, one integrated app V3-12/13 |
| T-29 through T-32 React screens | Replaced by Jinja2/Bootstrap/Plotly UI V3-10/11 |
| T-33 through T-40 integration/release/deploy/presentation | Minimal local integration/tests/report/demo V3-14/15; CI/CD/deploy/release engineering removed |

## 5. Existing branches, PRs, and conflict handling

Do not reset, delete, or force-push any branch. The locally visible T-01 branch is historical and PR #1 is merged in the local snapshot. The team leader reports that T-02 was not started; remote branches/open PRs and other workspaces remain unverified here. When connectivity is restored, verify current `origin/main`, PRs, branches and any T-02 work before making a disposition. Preserve discovered V2.2 task work and decide its disposition only with the owner/team lead; never transplant code silently. This transition is additive; do not alter V2.2 task/approval records or contracts.

## 6. Approval provenance

The team leader reports that the instructor approved the reduced V3 scope. Record this only as **team-leader-reported instructor approval**; no written evidence, date, instructor identity, or independent confirmation has been supplied. Do not use V2.2's approval record as evidence for V3, and do not claim that this V3 plan was submitted to the instructor. If additional evidence or conditions are later supplied, append their provenance accurately without overwriting this report. The V3 planning package is present on the supplied verified `main` baseline; at transition time, V3-01 contract kickoff remained pending. Its later completion is recorded in the linked kickoff record.

## 7. Approval checklist

This checklist records the transition-preparation state. The later V3-01 closure record supersedes its pending status; per-member setup checks remain pre-start gates.

### Team lead

- [x] The transition package is present in the supplied verified `main` baseline; this does not constitute V3-01 contract freeze or kickoff.
- [ ] Confirm Wageeh can support 12.5h/week for a four-week stretch or about 10h/week over the provisional five-week schedule; otherwise extend the target.
- [ ] Confirm four team members agree their responsibilities and time assumptions.
- [ ] Resolve dependencies and ensure no T-02 work is discarded.
- [ ] Check raw-data license, privacy, and data access plan.
- [ ] Verify current GitHub status/branches/rules when connectivity is available; no live remote query was made during this task.

### Instructor

- [x] Scope approval for SQL analytics + cleaning/EDA + delivery ML/MLP + FastAPI/Jinja2 is reported by the team leader; no written evidence is supplied and this has not been independently verified here.
- [x] The same team-leader report describes approval of the simplified scope, including its reductions from V2.2; no separate written confirmation of individual removed modules is supplied.
- [ ] Record any additional instructor conditions/evidence if they are supplied later; do not invent details or use V2.2 approval as V3 evidence.

V3 scope approval is recorded only as team-leader-reported. The V3 planning baseline is present on `main`; all implementation tasks remain **blocked until V3-01 is accepted**. Existing V2.2 state does not automatically unlock V3 implementation.

## 8. Exact pre-implementation sequence

1. Treat the supplied verified `main` baseline as the V3 planning baseline; this execution did not query the live remote.
2. Preserve V2.2 documents and its canonical ledger unchanged. T-02 remains `Planned` there for historical traceability; this transition document records its reported supersession with provenance limitations.
3. Apply the approved delivery-delay population rule consistently. The team leader subsequently approved Shared Contracts v1 under reported delegation; do not claim individual explicit contract-text approvals.
4. Verify local setup assumptions, Python/dependencies and data access for each member before that member's first task; record actual results without installing packages or changing settings without authorization.
5. V3-01 is completed as recorded in the kickoff record and ledger. The team lead must separately coordinate each implementation start according to the dependency ledger.

## 9. What must not change before approval

Do not alter the V2.2 Master Plan, canonical Task Ledger, approval records, T-00 audits, validators, tests, or application source. The README identifies V3 as the current planning baseline but does not authorize implementation. The transition-preparation snapshot did not mark V3 tasks started/completed; V3-01's later completion is recorded in its kickoff record and ledger, while V3-02 through V3-15 remain Planned — Not Started. Do not change historical T-02 status, present the team-leader report as independently verified evidence, or treat local remote-tracking refs as current remote verification. No implementation, data import, training, app development, or permissions change is authorized by this transition snapshot.
