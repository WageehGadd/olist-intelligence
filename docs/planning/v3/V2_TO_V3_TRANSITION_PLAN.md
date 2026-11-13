# V2.2 to V3 Transition Plan

**Status: proposal only.** V2.2 and its history remain intact. V3 is not an approved replacement baseline until team-lead review and instructor confirmation of revised scope. This document does not authorize code work, repository publication, team notification, or changes to current task records.

## 1. Verified current repository state

At review, the local fresh clone was `/private/tmp/olist-intelligence-v3`, repository remote `https://github.com/WageehGadd/olist-intelligence.git`. `main` was clean at `636ed34`, the merge commit for PR #1. The clone exposed `origin/main` and historical `origin/feature/T-01-instructor-approval`; no T-02 branch was listed. The clone succeeded and therefore supplied a snapshot, but an explicit later `git ls-remote`/fetch failed because GitHub DNS was unavailable. The remote was not independently rechecked after clone. Do not treat this as proof that no remote work has appeared since that snapshot.

Tracked `main` includes the T-00 audit package, V2.2 planning package and the T-01 approval documentation. No project application source/DB/model was observed in this clone. This planning proposal currently adds only seven Markdown files under `docs/planning/v3/` on local branch `planning/v3-simplified-master-plan`; it does not change README, V2.2, ledger, tests, validators, source code, or approval records.

## 2. Historical status: T-00, T-01, T-02

### T-00

V2.2 records T-00 **Completed locally** and the final audit/report/scripts/tests are committed in the merged baseline. The validation record documents all nine CSVs read, audit results, nine local tests passing on 2026-10-10, and sensitive/raw data staying untracked/ignored. The audit is historical evidence; this task did not rerun full-data tests because raw CSVs are not in the clone.

### T-01 and PR #1

PR #1 was merged to `main`; the main history includes the T-01 base and follow-up correction commits. The approval record says the team leader reported that the original project proposal was sent, discussed verbally, and verbally approved on October 26, 2026. No written approval, instructor identity, signature, authenticated evidence, original submitted proposal copy, or submission date is supplied. The later `docs/concept_brief.md` was created afterward and was not separately submitted. The canonical “Brief submitted” criterion remains pending equivalence confirmation. V2.2's state JSON still reads Approved and gate passed per the documented attributed user-report predicate; neither that state nor PR merge proves the V3-reduced scope was approved.

### T-02

The canonical V2.2 ledger in `main` still says T-02 Planned and assigns Hamza T-00 integration/CI foundation. The observed clone had no `feature/T-02-*` branch. **Actual T-02 progress remains unknown**: a ledger status and one branch snapshot cannot prove the presence or absence of unpushed local work, a newly created remote branch, a draft PR, or work outside Git. The network could not refresh GitHub after clone. Do not describe T-02 as started, abandoned, complete, or definitely unstarted.

Before the transition decision, ask Hamza to identify every T-02 workspace and provide its branch/ref, `git status`, latest commit, staged/unstaged/untracked file list, and any open/draft PR or CI run. When remote access is available, fetch latest `origin/main`, enumerate remote T-02 branches and PRs, and compare commit ancestry/files. Preserve any local work by keeping its workspace/ref unchanged and making a separate backup or review branch only with the owner's agreement. Review each artifact against the original T-02 acceptance criteria (audit source/reports/tests integrated by PR, Tier A fixture-only CI, raw/full-data tests kept out of Tier A, ignore rules, green CI). Mark each criterion verified/pending/not verified with evidence. Then the team lead and instructor decide whether compatible work is reusable under V3, whether remaining T-02 governance must be closed/superseded, and how history is recorded. Never delete, reset, force-push, silently cherry-pick, reassign ownership, or claim completion based only on files existing.

## 3. Reuse and preservation

Reuse T-00 dataset inventory, join integrity, temporal quality, delivery eligibility, feature leakage, baseline, and risk evidence as background. Reuse T-01's historical approval provenance only as evidence for the earlier proposal. Preserve all original V2.2 documents, JSON configs, CSV ledger, audit reports, tests, scripts, Git history, PR history, and existing branches unchanged. Do not change the approval-state JSON to imply V3 approval. The proposed seven documents remain in a clearly labeled `v3/` folder so they cannot be mistaken for the existing baseline.

## 4. Proposed task mapping

This is a proposal mapping, not a ledger mutation. V2.2 task IDs are not reused; V3 uses new `V3-XX` IDs. Many V2.2 tasks are split, consolidated, or explicitly removed. Preserve the old IDs/statuses in the original ledger until an approved versioned transition records the mapping.

| V2.2 area/task | V3 treatment |
|---|---|
| T-00 Dataset audit | Completed historical prerequisite; preserve and reuse findings |
| T-01 Concept brief/approval | Historical approval record remains; new reduced V3 scope needs fresh confirmation |
| T-02 T-00 integration/CI | Still shown Planned in V2.2; reconcile Hamza's actual work before deciding replacement |
| T-03 schema/contracts | Consolidated into V3-01 contract freeze and V3-02 SQLite schema |
| T-04 ETL | Removed as complex pipeline; simple local CSV cleaning/loading in V3-02/04 |
| T-05 through T-09 SQL/RFM/geographic analytics | Core KPIs consolidated into V3-03; RFM/geographic extras removed |
| T-10 through T-19 delivery model chain | One target remains; population/features/split V3-06/07, LR/RF V3-08, MLP comparison V3-09; advanced boosted-tree experiments, calibration/explainability modules and separate packaging scope reduced |
| T-20 through T-25 review NLP/CNN/BERT/review risk/tracking | Removed from mandatory V3 |
| T-26 through T-28 API design/core/prediction | Shared contracts V3-01, one integrated app V3-12/13 |
| T-29 through T-32 React screens | Replaced by Jinja2/Bootstrap/Plotly UI V3-10/11 |
| T-33 through T-40 integration/release/deploy/presentation | Minimal local integration/tests/report/demo V3-14/15; CI/CD/deploy/release engineering removed |

## 5. Existing branches, PRs, and conflict handling

Do not reset, delete, force-push, or merge any branch. The locally visible T-01 branch is historical and PR #1 is already merged. T-02 work is unknown beyond the clone evidence; ask its owner, then verify latest `origin/main`, branches, open PRs, and local work before transition. If V2.2 task work exists, preserve its branch and PR and decide whether to finish, close with rationale, or adapt via a new branch only after team lead/instructor approval. Never transplant code silently. Check for README, task ledger, approval-state and contract conflicts; keep V3 documents isolated until approved.

## 6. Communicating revised scope

After the team lead reviews the proposal, send the complete version to the instructor through the team's normal channel and request explicit confirmation that the reduced deliverables satisfy DEPI Project #7. Record the actual date, channel/evidence type, instructor response and any conditions only when supplied. Do not infer approval from the earlier verbal approval, silence, or PR merge. The original proposal's contents and exact sent date are not preserved here; do not claim the new V3 plan is the submitted proposal.

## 7. Approval checklist

### Team lead

- [ ] Read all seven V3 documents and verify task IDs, assignment, scope, effort, interfaces and gates.
- [ ] Confirm Wageeh can support 12.5h/week for a four-week stretch or about 10h/week over the provisional five-week schedule; otherwise extend the target.
- [ ] Confirm four team members agree their responsibilities and time assumptions.
- [ ] Resolve dependencies and ensure no T-02 work is discarded.
- [ ] Check raw-data license, privacy, and data access plan.
- [ ] Verify current GitHub status/branches/rules when connectivity is available.
- [ ] Authorize any proposed baseline/ledger/README changes as a separate publication step.

### Instructor

- [ ] Explicitly confirm that SQL analytics + cleaning/EDA + delivery ML/MLP + FastAPI/Jinja2 fulfills course requirements.
- [ ] Confirm removal of review NLP, CNN/BERT, React, deployment and advanced modules is acceptable.
- [ ] Provide any conditions and evidence of acceptance; record accurately.

Until these gates are met, all V3 tasks remain **Not authorized / blocked**. Existing V2.2 state does not automatically unlock V3 implementation.

## 8. Exact pre-implementation sequence

1. Retain this proposal as local, uncommitted planning review material; do not publish/notify/invite.
2. Wageeh reviews all seven documents; team members may review their own plans when coordinated.
3. Contact Hamza to establish actual T-02 state and preserve any work; inspect latest remote state after network is available.
4. Request instructor confirmation of the changed/reduced V3 scope. Record only the response and evidence actually received.
5. Resolve the capacity, license/privacy, Python/DL framework, GitHub rules, and KPI open decisions.
6. If scope is approved, create a separately reviewed transition PR with explicit V2.2-to-V3 baseline decision; do not edit historical V2.2 files in place. Update official source pointers and task ledger only under separate authorization and with verified consistency.
7. Obtain team-lead approval of the transition PR and complete any required instructor conditions. Merge only after the user's separate publication/merge authorization.
8. Re-verify latest `main`, status, remote branches, and owner acknowledgements; run V3-01 kickoff and freeze contracts.
9. Only then notify members that V3 implementation may begin. Start Hamza V3-02, Hasnaa V3-04, Wageeh V3-06, and Rana V3-10 in parallel.

## 9. What must not change before approval

Do not alter V2.2 Master Plan, canonical Task Ledger, approvals, T-00 audits, validators, tests, README or source code. Do not mark any V3 task started/completed, repurpose T-02, announce revised work as instructor-approved, or treat this branch as published. No implementation, data import, training, app development, installation, commit, push, merge, PR, collaborator invitation, or permissions change is authorized by this proposal.
