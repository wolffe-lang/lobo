# ws74 — the open-issue sweep

## 1. Forbidden

Planning is read-only. No kasumi, maintainer data, host signal probes,
process-group kills, package installation, attribution, labels, merge,
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
- #72: Still open: the loaded-host control hang remains unlocated; reproduce the burst-of-closes shape at the current pin in an isolated container before assigning it to lobo or wolf. No kasumi evidence was revisited.
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
rather than falsely promise rollback. Count a reload acknowledgement only
when it begins with the actual reload-complete reply, not arbitrary busy
text. Predict the reverted diagnostic plant will fail the named row.

No issue is claimed fully fixed yet. README read, current at checkpoint.
Expected implementation footprint: cross-cutting (the existing test tool
changes); final classification will be checked by the audit.
