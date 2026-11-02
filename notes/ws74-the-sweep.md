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

**R-ws74-2, ruled and implemented:** the orchestrator filed the intermittent
native failure as lobo#118. Make the three pre-output assertions name their
observations, not change their predicates or deadlines. Copy failures name
both paths and sizes; size mismatches name the observed values; readiness
failures name paths, sizes, endpoint, the unchanged 15000 ms deadline and
elapsed time. The same failure message is printed only on failure before
asserting it, because native conformance does not retain assert text
(wolf-lang#150). Successful checks add no print.

The prediction was committed before the change (`27602f3`, cherry-picked
as `081e0d7`). A local one-byte copy plant first proved the old output was
empty, then the diagnostic candidate named the same false size predicate.
That deliberate shortening is absent from main and plant PR #117 is
unchanged. Push one new head, run one full short-path gauntlet, and audit
that head once only if it is green. #118 remains open; diagnostics do not
claim to fix its intermittent cause.

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

The two exit-1 rows above are intended, individually checked negatives,
not application passes. At the earlier main head **61de89e**, the first
full attempt was superseded after overly long worktree paths caused UNIX
control binds to fail (376/392 green). The short-path attempt stopped at
**391/392 green**: binary_identity_e2e [native] trap(assert), empty stdout;
its checked leg passed in 23 s. Zero SKIP lines in the executed portion.
Neither result was called green, and no downstream step was run after the
corpus failed. Both attempts had the same terminal END sequence:

```
END stage-final exit=0
END disk exit=0
END toolchain-pin exit=0
END manifest exit=0
END stamp exit=0
END signal-names exit=0
END fmt-check exit=0
END both-tiers-build exit=0
END directive-docs exit=0
END log-variable-docs exit=0
END metrics-docs exit=0
END interface-freshness exit=0
END corpus exit=1
END gauntlet exit=1
END final-job exit=1
```

The orchestrator verified CI **41516482696 green at that same 61de89e
head**, and filed #118. Before that ruling, exactly three unmodified
native legs at each path and three off-line logged probes all returned
exit(0), warnings=[] and diagnostics=[]. No reproduction or cause was
claimed, and those nine greens did not replace the original red. The
bare outputs contain all six GREEN cases; the probe protocol retains a
4096-byte prefix plus full stdout hash, not a reconstructed transcript.
Exact records are under /home/mfwolffe/lanes/ws74/logs/identity/ and
/Users/mfwolffe/lanes/ws74/identity-diagnostics/; the complete driver log is
/Users/mfwolffe/lanes/ws74/identity-nine.log, SHA-256
a59e2bef49c8a59ce037dcaaec9882ffeb63158e35e06956a1f0fc880a831d6a.
The debug seeds differed by 1480 bytes; every bare copy matched its own
seed size. Release seeds were byte-identical. Inputs stayed unchanged.

**#118 local forced-copy diagnostic proof:** old plant `72e3a9e` and new
plant `0af0566` each shorten only the copied image to one byte. Both native
records are trap(assert), but old stdout_inline is null and the new full
failure output is:

```
binary identity unchanged size: source=[/home/mfwolffe/lanes/ws74/g61de89e/target/lobo-debug] source-size=18343064 copy=[/home/mfwolffe/lanes/ws74/g61de89e/ws72_e2e/unchanged/lobo] copy-size=1
```

The native message-quality observation changed from red to green, not the
intentionally false size predicate. Records: /home/mfwolffe/lanes/ws74/logs/118/
and /Users/mfwolffe/lanes/ws74/118-message-proof/. Every END:

```
END forced-old-native exit=1
END old-message-quality exit=1
END forced-old-observation exit=0
END forced-old-job exit=0
END forced-new-native exit=1
END new-message-quality exit=0
END forced-new-observation exit=0
END forced-new-job exit=0
```

The main candidate is exactly the canonical new fixture with only that
plant statement removed; token equality to the queued candidate and a
read-only fmt check passed. wait_ready's predicate/deadline body and all
post-first-print assertions are byte-identical to 61de89e. The diagnostic
commit is `af5f623`, with lobo#118 in its message. No plant branch was
pushed to the main PR.

The new final-head full gauntlet is pending when this note is committed.
Its actual head, every END, SKIPs and verdict will be added to PR #116's
five-section body after its single run. No earlier green substitutes for
that run. An earlier audit at 61de89e failed on malformed footprint
punctuation and a missing done-when heading while CI was incomplete; this
note fixes both fields. R-ws74-2 authorizes one fresh audit at this new
head after a green gauntlet.

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

## 5. Done-when and handoff

PR #116 addresses **the diagnostic/CLI part of #101** and **test diagnostics
for #118**, not their outstanding causes. Do not close #101 or #118. The
eleven-issue triage is complete; the unimplemented #68, #82, #87, #95 and
#102 work remains deferred as explicitly accepted by the orchestrator.
Comment-ready lines for every original issue left:

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
- `8720ac0`: README-only refresh. README read against the pass; counts, modules, install/build instructions and pins remain current. The #118 diagnostic-only change moves none of them.
- `081e0d7`: #118 prediction, committed before changing the assertions.
- `af5f623`: lobo#118 failure-only assertion observations, after the silent old-message seed.

Test targets:

- [x] `bash -n tools/lobo-user`.
- [x] Short container Uid/Gid/Groups probe.
- [x] Corrected baseline's single named root-container red.
- [x] Deliberate plant's same single named red.
- [x] Approved fix, thirty root-container checks green.
- [x] #118 forced-copy old silent failure and new value-bearing failure, with the size predicate still false.
- [x] Ready predicate/deadline and all later assertions unchanged; no main shortening statement.
- [ ] One full gauntlet at the new final committed head; count every SKIP.
- [ ] Push once; identify the current-head CI id once, orchestrator watches.
- [ ] If the new gauntlet is green, one audit at that new head; report its exact last line.

Footprint: module
