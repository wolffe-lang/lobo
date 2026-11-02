# ws74 — the open-issue sweep

## 1. Forbidden

Planning is read-only. No kasumi, maintainer data, host signal probes,
process-group kills, host package installation, attribution, labels, merge,
release, tag, issue filing or closing. nginx is a black-box oracle.
Bench and doors stay unchanged. All execution is from committed copies.

## 2. Inputs, verified

Base `3f493391`, wolf 0.2.36 / lupin 0.1.58 / std 78b9d3cb.
Read the lane rules, contract, RULES §1–§10, README, ws73 note and r41p's
prediction commit `eff47f5`. The open issue set is exactly eleven:
#68, #72, #78, #82, #87, #90, #91, #95, #100, #101, #102.

## 3. Prediction

Before any implementation change: #101's master's unconditional success
reply is independently fixable without changing privilege policy. Predict
a root-only reloaded configuration will leave both dropped workers at the
old generation and make the current master incorrectly say `reload
complete ... workers=0/2`. Add a regression committed before the fix;
report incomplete worker application explicitly and make the control CLI
exit nonzero. Keep full success unchanged. This does not implement parsed
configuration/credential transfer and will not close #101.

The other issues need historical release bookkeeping, a targeted
reproduction/measurement, or a larger design decision; record each
separately after inspecting its current witnesses. Do not claim a failed
reproduction as a fix. Predict no pin, benchmark, door or public behavior
change apart from truthful reload failure reporting.

A separate plant will restore the unconditional success reply and must
make the named incomplete-reload regression red. Final gauntlet wrapper
will stop at the first failure and preserve every END line.

## 4. Evidence index

No build or test has run. No green or red verdict is claimed.

Comment-ready triage, one line per open issue:

- #68: Still open: ws73's measurements concern proxy exchanges, not this parsing/bookkeeping/head-route profile; the old percentages need a new same-host profile before selecting a change or claiming recovery.
- #72: Still open, runtime-owned per ws59's issue comment: 300 loaded four-CPU native rounds with eight busy loops had zero hangs, and every lobo blocking call was deadline-armed to at most two seconds. The captured forty-second futex sleep was not a lobo-loop wait; a wolf-only witness needs a recurrence under memory/IO pressure. No kasumi evidence was revisited.
- #78: Already fixed in 0.1.3 by b256d2e / #75; the open issue is an upgrade advisory, not an unfixed trunk defect. Closure is the orchestrator's decision.
- #82: Still open: current tests explicitly preserve the later-server warnings and nonmatching regex name; per-server frozen effective configuration, ordered regex matching and master-owned listener changes remain separate implementation work, not a one-line warning fix.
- #87: Still open: this is a bundle of independent limit follow-ups, not a single resolved defect; master descriptor reserve, admission distribution, metrics and the named TLS/ENFILE/no-/dev/null/reload-limit witnesses still need individual rows. Not yet implemented by this lane.
- #90: Already fixed in 0.1.4 by ws64 / #86; this issue documents affected released binaries and the need to replace the process. No new trunk fix is owed; closure is the orchestrator's decision.
- #91: Already fixed in 0.1.4 by ws63 / #83; the open issue is a release advisory. No new trunk fix is owed; closure is the orchestrator's decision.
- #95: Still open: the old macOS negative-control discrepancy is not evidence of current runtime failure; park_at_limit_e2e still proves only that at least one download began, not that descriptor exhaustion preceded the first parked write. Needs a historical 0.2.29 macOS negative control and an instrumented stronger witness; no assertion was weakened.
- #100: Still open: ws73 retained the existing persistent pool after measured alternatives regressed other shapes; its one-client recovery target remained unmet, with wolf-lang#835/#836 named as upstream boundaries. No bench or door changed here.
- #101: Confirmed source defect: main.lu unconditionally says reload complete after fan_out even when zero workers accepted; control_exit treats every non-rejected reload reply as success. Truthful incomplete application and nonzero CLI status are a safe partial fix; parsed configuration/key transfer and generation consistency remain outstanding, so do not close the whole issue.
- #102: Still open: config/userconf.lu deliberately exempts cert auto from the implicit root drop, but explicit user still drops; acme.store_write/account_key/install run in the owning hand and write the store. Verify cold issuance, root-owned existing keys, renewal and sibling pickup as root inside a container before choosing ownership/privileged-renewal policy. No chmod/chown workaround or credential-policy change was made.

Host prerequisite checked on hasu: neither localhost/r41-toolchain:1 nor
localhost/px75-ubuntu:2 nor localhost/px78-ubuntu:1 contains ApacheBench;
command -v ab on the host is also empty. The complete gauntlet includes
tools/lobo-proxy-throughput, so it cannot be honestly called green in
these environments. No package was installed. wolf and lupin published
Linux archive digest metadata was read twice, identical:

- wolf: d383c74c8cd123b9d9dfaa268271d4f004294f85c2b230237d0ef07027d9500d
- lupin: 34f52792bb59bc7565e0edc1235cd47d9a6ad13d5e6528993627f2e699b62193

These are release API digests, not claims that bytes were downloaded or
hashed locally. No build job or block waiter was submitted.

## 5. Handoff

The first checkpoint handed back for missing ApacheBench. On resume the
orchestrator pointed out that the lane rules already permit constructing a
lane-prefixed image: build localhost/ws74-ab:1 from localhost/px75-ubuntu:2
with ApacheBench. The host is unchanged; image-local dependencies are not
host package installations. Also stage jq and OpenSSL development headers,
missing from the base and required by the documented gauntlet/oracle build.

R-ws74-1 A was approved on resume: implement truthful incomplete-worker
reporting and nonzero CLI exit, red first; leave full configuration/key
transfer as a named follow-up. Test full success, all-worker rejection,
continued old-worker serving and a subsequent readable-config recovery.
Keep master generation semantics unchanged and describe the mixed state
rather than falsely promise rollback. Keep this first fix to the approved
incomplete-count reply and CLI status; stricter acknowledgement framing
is a separate follow-up. Predict the deliberately false-acknowledgement
plant will fail the named row.

The existing test tool is lobo-local, not shared CI infrastructure:
`ci/tiers.py classify` calls it gauntlet, and lane-audit's module path
rules admit it. No CI, pin, runtime, loader or spec path changes.

Committed checkpoint:

- `542c970`: prediction before changes.
- `2cac119`: eleven-issue triage and initial host-tool finding.
- `a074b5b`: approved R-ws74-1 A and image-build prediction.
- `7b8c12e`: regression for #101, committed before any implementation.
- `5cd6fe6`: queued baseline and deliberate-plant checkpoint.
- `7c9493e`: correct the regression's native status command.

The regression checks both workers ready at generation 1, a full reload
(exit 0, 2/2), root-only config rejection (explicit incomplete 0/2, exit
1), continued serving at the workers' old generation, and restored
readability. It explicitly preserves the remaining master/worker generation
number divergence rather than claiming the transfer problem fixed.

An off-line plant branch `ws74-plant-reload` at `0e6820b` deliberately
reports N/N even when the actual acknowledgement count is zero. Its
named expected red is `reload_root_only: incomplete workers=0/2 is
explicit and exits 1`; no red has been observed yet.

Hasu execution is queued behind existing block holders, not stuck in a
build. Setup chose A after counting both queues; the waiter stays there.
At the latest observation it had waited eleven minutes. The recorded jobs
are under `/home/mfwolffe/lanes/ws74/`:

- Setup waiter PID 3853900, log `logs/setup.log`; success ends with `END setup exit=0`. The setup is still owned by the live background SSH call, not a detached setsid job; no durable exit marker exists for it.
- Detached red job PID 4153050, log `logs/red.log`, terminal marker `logs/red.exit`; waits for setup before choosing the emptier block and builds only committed `7b8c12e`.
- Detached plant job PID 47399, log `logs/plant.log`, terminal marker `logs/plant.exit`; requires the baseline's named red before queuing committed `0e6820b`.

Review caught a fixture error before execution: `-s` accepts nginx's four
verbs only, so the readiness helper must use `lobo status`, not `-s status`.
`7c9493e` corrects it; plant `c61c483` carries the same correction. The
already queued earlier commits are not cancelled, rewritten or used as
clean negative evidence. They may produce unrelated fixture failures.

Detached corrected-control job PID 406612 waits for that earlier attempt,
then runs baseline `7c9493e` and plant `c61c483`, choosing the emptier block
each time. It accepts each negative only if the named root-only reload
check is the **sole** failed check. Evidence: `logs/red2.log` +
`logs/red2.exit`, `logs/plant2.log` + `logs/plant2.exit`; wrapper
`logs/corrected.log` + `logs/corrected.exit`.

The approved fix is queued conditionally, not claimed executed: detached
PID 469924, `scripts/approved-fix-queue.sh`, `logs/fix.log` and
`logs/fix.exit`. It first verifies the corrected baseline's unique actual
red, then creates a separate `ws74-approved-fix` worktree, applies only
the approved incomplete reply / nonzero CLI change, formats behind the
block lock, commits only main.lu, and runs the root-container green rows
from that commit. It never pushes. On execution, `logs/fix.sha` and
`approved-fix.bundle` name and preserve its commit. Until those records
exist, no implementation or green is claimed. Do not concurrently edit
that reserved worktree; fetch/cherry-pick its commit into ws74 on resume.

Setup waiter 3853900 was still queued at nineteen minutes forty seconds.
Detached setup watcher PID 282639 records `logs/setup.exit` from its
terminal success marker (or records failure if none); it does not change
or kill the existing waiter. All recorded paths above are under
`/home/mfwolffe/lanes/ws74/`.

Draft PR #116 is the test-only checkpoint, not merge-ready. Deliberate
plant draft PR #117 is at `c61c483`. Each immediate run-id lookup returned
an empty list; no CI id or verdict is invented and no CI was awaited.
The orchestrator owns the watches. Neither draft has been audited yet.

No completed build, image digest, observed red/green, final gauntlet or
audit is claimed at this checkpoint. R-ws74-1 A is approved and its guarded
execution awaits the first real red. No issue is claimed fully fixed.
README read, current against the committed test-only diff. After the fix,
refresh its reload limitation, docs/CONTROL.md, docs/WORKERS.md and the
Unreleased CHANGELOG, leaving historical release observations intact.

Test targets:

- [x] `bash -n tools/lobo-user`.
- [ ] Red baseline's root-container `lobo-user` row.
- [ ] Local deliberate plant's named red.
- [ ] Implement #101 partial fix, then green root-container rows.
- [ ] Complete gauntlet at final head, with END lines and counted SKIPs.
- [ ] PR head CI handed to the orchestrator; one final lane audit.

Footprint: module.
