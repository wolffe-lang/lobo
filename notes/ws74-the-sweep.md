# ws74 — the open-issue sweep

## 1. Forbidden

Planning is read-only. No maintainer data, process-group kills, host package
installation, attribution, labels, merge, tag, release or issue action.
nginx is a black-box oracle. Bench, doors and pins are unchanged.

Kasumi was explicitly reopened on resume. Only its authorized 4–7 or 8–11
slot, one long flock, taskset inside, 12 GiB containers and closed stdin;
nothing on /dev/sda, /mnt/steamlib or the rpc-server on :50052. Old hasu
waiters were neither edited nor killed. All lane files are under ws74.

## 2. Inputs, verified

Base `3f493391`; wolf 0.2.36, lupin 0.1.58, std
`78b9d3cbc41d51db44d18c40b6694403644d1c83`. Read the lane rules (including
the reopened kasumi block), contract, RULES §1–§10, README, ws73's note,
r41p's prediction `eff47f5` and all eleven issue bodies/discussions.

The published Linux archive digests were read twice from the release API,
then the downloaded archives were hashed twice successfully on hasu:

- wolf: `d383c74c8cd123b9d9dfaa268271d4f004294f85c2b230237d0ef07027d9500d`.
- lupin: `34f52792bb59bc7565e0edc1235cd47d9a6ad13d5e6528993627f2e699b62193`.
- nginx 1.30.4: `4261dc90e9e47c1c4041276e9aaa3d48ebe2e664f728e14fa95ae6c67d57a08b`.

Built `localhost/ws74-ab:1` from `localhost/px75-ubuntu:2`, installing only
image-local apache2-utils, jq and libssl-dev. No host package was installed.
Hasu image ID `2102932cf0a90c7f709d8a0c429c673e4c756ef13dfcadc34f1de9b3e4315580`,
digest `sha256:2c73b11adf739bbc4151f380eae5e2ec13e04fb76f3fd3edabda65ebd51d55b9`.
Transferred with podman save/load; kasumi's ID matches exactly. Copied the
lane's verified toolchain and oracle, and hashed their binaries twice on
kasumi. nginx was built without inspecting its source. Setup ended:

```
END setup exit=0
```

## 3. Prediction and decision

The prediction `542c970` preceded all implementation. A root-only reload
would validate in the root master, be rejected by both dropped workers,
and falsely answer `reload complete ... workers=0/2`, exit 0. The regression
was committed before the fix. A deliberately false N/N acknowledgement
count on an off-line plant would fail the same named check.

**R-ws74-1 A, approved and implemented:** report incomplete worker
application explicitly and make the control CLI exit 1; keep full success
unchanged. The other option is full master-to-worker configuration/key
transfer and generation reconciliation; that remains a named follow-up,
not secretly implemented or claimed fixed.

Before the corrected runner change, the kasumi prediction `b9f33f0` said
an explicit root supplementary group would preserve every existing
Groups: 0 assertion. One short probe printed Uid 0/0/0/0, Gid 0/0/0/0,
Groups 0. Baseline and plant were then each uniquely red; the approved
fix made all thirty root checks green. No assertion or timeout was weakened.

R-ws74-2 diagnostic prediction: shorten only the test's copied image to
one byte, after a successful copy and before the existing size predicate.
At frozen old main 61de89e, native conformance should report trap(assert)
and empty inline stdout. The new #118 diagnostic assertion should keep
that same predicate false but name the original/copy paths and sizes in
its retained failure message. Copy and readiness checks must likewise
report their observations; readiness remains 15000 ms and reports elapsed
wall time. Print failure messages only on failure because native records
do not retain assert text. Keep plant #117 untouched. Then push one new
main head and run one full short-path gauntlet, not retries to green.

## 4. Evidence index

Authoritative execution is kasumi slot **4–7**, under
`/home/mfwolffe/lanes/ws74/`. Committed copies only:

- Baseline `a35e08b`, `logs/k-baseline.log`: **1 of 30 checks RED**, solely
  `reload_root_only: incomplete workers=0/2 is explicit and exits 1`.
  Actual reply: `reload complete (generation 3) workers=0/2`, exit 0.
- Deliberate plant `831b600`, `logs/k-plant.log`: **the same single red**.
  Actual reply falsely said `workers=2/2`, exit 0. Draft PR #117 is never
  merge evidence; its deliberate false count is absent from the fix.
- Guarded fix `f05371f2536789f2d331bfdb55d5772766460d26`,
  `logs/k-sequence.log`: **30/30 green**. Root-only reload answers
  `reload incomplete (generation 3) workers=0/2: ...`, exit 1; full reload
  remains exit 0, 2/2. Rejected workers still serve their prior generation.
  Restoring readability recovers acknowledgements, but intentionally does
  not repair the existing master/worker generation-number divergence.
- The reviewed fix was cherry-picked as `1f3bf09`; source is identical.
  The sequence's completion sentinel `logs/k-sequence.exit` is 0.

Every END from the authoritative red/plant/green sequence:

```
END root-group-probe exit=0
END stage-baseline exit=0
END build-baseline exit=0
END baseline-root exit=1
END stage-plant exit=0
END build-plant exit=0
END plant-root exit=1
END format-approved-fix exit=0
END stage-green exit=0
END build-green exit=0
END green-root exit=0
END kasumi-sequence exit=0
```

The two exit-1 rows are the intended, individually checked negatives, not
application passes. The final-head full gauntlet is still pending when
this note is committed; its actual head, END lines, SKIPs and verdict will
be recorded in PR #116's five-section body after it runs. No earlier green
will be substituted for that run.

**Superseded hasu attempts, not evidence:** the first fixture used invalid
`-s status` (corrected in `7c9493e`), and rootless podman supplied an empty
supplementary group where the unchanged tests require Groups: 0. The first
baseline had 8/30 failed checks. Later unique-red guards correctly refused
to apply the fix when unrelated fixture failures remained. All existing
jobs were left alone. Their terminal END lines are preserved here:

```
# logs/red.log
END build-release exit=0
END user-reload exit=1
END red-job exit=1
# logs/plant.log
END build-release exit=0
END user-reload exit=1
END plant-job exit=1
# logs/red2.log
END build-release exit=0
END user-reload exit=1
# logs/corrected.log (includes that same red2 attempt)
END build-release exit=0
END user-reload exit=1
END corrected-witness-job exit=2
# logs/fix.log
END approved-fix-job exit=2
```

`plant2` never ran: its predecessor's strict guard stopped first. The old
hasu exit-2 rows are fixture/guard outcomes, not product skips or greens.

## 5. Handoff

PR #116 addresses **the diagnostic/CLI part of #101 only**. Do not close
#101. The eleven-issue triage is complete; the broader implementation
sweep is not claimed complete. Comment-ready lines for every issue left:

- #68: Still open; the old parsing/bookkeeping/head-route percentages need a new same-host profile before selecting a change or claiming recovery. ws73 measured proxy exchanges, not these levers. No new profile here.
- #72: Runtime-owned per ws59's issue comment: 300 loaded four-CPU rounds with eight busy loops had no hang; every lobo wait was bounded to two seconds, unlike the captured forty-second futex sleep. A wolf-only witness needs a recurrence under memory/IO pressure. No new reproduction here.
- #78: Already fixed in 0.1.3 by b256d2e / #75; this open issue is a release advisory, not an unfixed trunk defect. No issue action here.
- #82: Still open; per-server frozen configuration, regex server names and master-owned listener changes remain separate implementation work. Current warnings remain explicit. Not implemented here.
- #87: Still open; master descriptor reserve, admission distribution, metrics and the named TLS/ENFILE/no-/dev/null/reload-limit witnesses are independent follow-ups. Not implemented or newly verified here.
- #90: Already fixed in 0.1.4 by ws64 / #86; this issue documents affected released binaries and replacement of the running process. No new trunk fix owed by this finding.
- #91: Already fixed in 0.1.4 by ws63 / #83; this is a release advisory. No new trunk fix owed by this finding.
- #95: Still open; the historical macOS 0.2.29 negative-control discrepancy needs an instrumented stronger witness. At least one download beginning does not prove exhaustion preceded the first parked write. No new macOS control here.
- #100: Still open; ws73 retained the persistent pool after alternatives regressed other shapes. Single-client recovery remains unmet, with wolf-lang#835/#836 named as upstream boundaries. No bench or door changed.
- #101: Incomplete worker application now has a truthful reply and nonzero control CLI exit. Root-only configuration/key transfer and generation consistency remain outstanding; this is explicitly partial, not grounds to close the issue.
- #102: Still open; the implicit root drop exempts cert auto, explicit user does not. The owning hand writes the ACME store. Cold issuance, root-owned keys, renewal and sibling pickup under a drop need container verification and an ownership/privileged-renewal policy. Not verified here; no chmod/chown or credential-policy change.

Commit references:

- `542c970`: prediction before changes.
- `7b8c12e`, `7c9493e`: regression first, then native status-command correction.
- `b9f33f0`, `a35e08b`: corrected-runner prediction and explicit root group / inside-container CPU pin.
- `1f3bf09`: approved partial #101 fix, after uniquely observed negatives.
- `09af7ff`: control/worker docs and Unreleased CHANGELOG.
- `8720ac0`: README-only refresh. README read against the pass; counts, modules, install/build instructions and pins remain current.

Test targets:

- [x] `bash -n tools/lobo-user`.
- [x] Short container Uid/Gid/Groups probe.
- [x] Corrected baseline's single named root-container red.
- [x] Deliberate plant's same single named red.
- [x] Approved fix, thirty root-container checks green.
- [ ] Full gauntlet at final committed head; count every SKIP.
- [ ] Update PR evidence and read the current-head CI id once; orchestrator watches.
- [ ] One final lane audit, exact last line reported.

Footprint: module.
