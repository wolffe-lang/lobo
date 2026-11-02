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

Pending execution; no test result claimed by this prediction.

## 5. Handoff

Pending. Footprint: module. No issue closure claimed yet.
