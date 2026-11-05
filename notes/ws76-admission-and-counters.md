# ws76 — admission across hands and connection counters

## 1. Forbidden

No nginx or other web-server source. The pinned nginx binary is a
black-box oracle. Tests bind loopback only, on their own ports.
No labels, merges, tags, releases or issue closures from this lane;
no attribution trailers. Builds use committed, isolated trees and
bounded containers on assigned CPUs.

## 2. Inputs, verified

- Base: trunk `6b8b9ee`, branch `ws76`.
- Pins: wolf 0.2.36, lupin 0.1.58, std `78b9d3cb`;
  nginx 1.30.4, as recorded in the toolchain and differential pins.
- The ignored reference directory was copied into this fresh clone.
  Its API conventions differed from the canonical standard-library
  trunk; the canonical copy replaced it before implementation.
- The required entry gauntlet passed at the unmodified base. The
  reused pinned binaries were copied into the lane's own directory;
  their identities and standard-library marker passed the gate.
- Compiler binary SHA-256: `f7b73fba526e06116cc5eeda146cc80c8a42cd1f7a198d574e8a961f6c7a57ef`;
  interpreter: `47c646a61b9fd0dfe7d4565a74e22428a259eb54642f6d0d6ef3c1c0abe01ada`;
  oracle: `5a08ef7f65591bcf51fe43ef43f3a1ee664ccf5665532b4351efde6b9c38eaff`.

| environment | hardware and bounds |
|---|---|
| Linux x86-64, Ubuntu 24.04 container | Intel Core i7-12700KF, 20 logical CPUs; six-CPU affinity, 12 GiB memory cap |
| Unloaded drive | no added load on the held block |
| Loaded drive | twelve busy loops on the same six CPUs, each stopped and waited by its own PID |

The initial oracle counts used a mixed-core block; the redesigned
base and fixed counts used the same six-CPU P-core affinity. Neither
admission row is a wall-time or throughput comparison.

## 3. Prediction (committed before any source change)

With two workers sharing an inherited listener, a full worker with
no idle connection currently competes with a sibling that still has
room. A directed two-worker drive at `worker_connections 16` should
show a refusal among the first 28 connections on the base, while the
same-host pinned oracle admits those 28. The row will first measure
the oracle instead of assuming its capacity, then be run at least
20 times without added load and 20 times with CPU load.

A short listener-only pause should let the sibling take the pending
connection. The pause must expire once, permitting refusal when all
workers are full; control, signals and established connections must
remain serviceable. Single-process and reuseport admission should
stay unchanged, with explicit scope rows. A starting value of 20 ms
will be measured before it is retained. Elapsed-time observations
will not become scheduling-sensitive upper-bound gates.

The process counter block should retain refused and idle-evicted
connection totals and accept-failure totals for emfile, enfile and
other reasons. Only an actual refusal, idle eviction or failed
accept increments its corresponding counter. Timeout from an accept
race is not a failure. Failed recovery accepts must be counted too.
The metrics registry must declare bounded reason labels, generated
metric docs must match it, and worker stamping must remain intact.

A refusal, an idle eviction and a low-descriptor accept failure will
each have a red-first row. The existing exposition checker will see
the added series, and exact assertions will catch missing counters.
The final gate runs at the final head, with one off-line pause-removal
plant required to fail the admission row by name.

## 4. Evidence index

### First drive and row correction

The first paired drive at base was 2 green / 18 red unloaded and
0 green / 20 red under CPU load. Of its 38 reds, 30 were the oracle's
own failure to serve the first 28, five showed a full lobo worker
taking a sibling's connection while the oracle served 28, and three
were socket timeouts. The oracle's measured capacity is 28; its
per-connection distribution is not stable on this host. A fresh
oracle scheduling result is therefore no longer a row precondition.
The row holds lobo to those measured first 28 directly, unchanged
from the requested capacity, and reports its 29-connection map.
The separate `oracle` drive preserves the black-box measurement.

The three timeouts are **unknown cause**, not claimed as admission
defects: `base-cpu-3.log`, `base-cpu-13.log`, `base-cpu-20.log` in the
lane's evidence directory. Their saved fixture trees contain oracle
logs and no lobo directory: they timed out before lobo was started.
The old driver did not identify the particular connection. The
revised driver names the connection, prefix map and server log, and
reads a complete response head rather than assuming one recv
contains it. Its five-second socket deadline bounds a hang; it is
not a latency comparison gate.

### Redesigned row, before and after

| tree | unloaded | CPU-loaded | named failure |
|---|---|---|---|
| base `6b8b9ee`, redesigned row `f99befc` | 4 green / 16 red of 20 | 1 green / 19 red of 20 | all 35 reds: a full hand took a sibling's connection |
| first candidate `ab1d0c4` | 20 green / 0 red | 20 green / 0 red | none in this row; queue defects found below |
| queue-wave repair `a87c58f` | 20 green / 0 red | 20 green / 0 red | none |

No oracle-precondition failures or timeouts occurred in these 120
redesigned-row takes. Each green served the first 28 downloads and
refused the 29th, rather than merely counting 28 served somewhere.

### Why 20 ms

Twenty milliseconds is a bounded listener-only yield, separate from
the existing 500 ms accept-failure backoff. Without the yield the
same-block base was red in 35 of 40 takes; with it both 20-take sets
were green. The final connection's observed refusal time was
16.936 / 19.875 / 20.262 ms (minimum / median / maximum) unloaded,
and 7.680 / 18.017 / 22.552 ms loaded. These are observations, not
thresholds: a pending pause may already have partly elapsed, and
scheduling adds delay. Minimum observed child CPU across each
whole drive was 40.005 ms unloaded and 30.840 ms loaded, recorded
from child rusage, including control-CLI probes, rather than inferred
from the polling interval. The old log calls this field
`server-tree-cpu-ms`; the driver now names it `child-cpu-ms`.
No throughput or relative latency improvement is claimed. This
measurement supports retaining the specified starting value; it
claims neither that 20 ms is an optimum nor a latency guarantee.

After one pause for a nonempty eligible queue, the expired permit
carries across the existing bounded HTTP bursts and every other ready
listener. It re-arms only after an immediate probe finds every eligible
queue empty, not after every take. Resource-failure backoff clears the
permit, excludes further client accepts in that pass, and takes
precedence over admission wakeups. Full/no-idle eligibility is checked
inside HTTP bursts too; fresh accepts remain idle until step 3 reads
them, preserving the old eviction policy rather than promising to yield
while an idle candidate exists.

The master supplies a private sharing bit from its group size and the
actual inherit set. A one-hand master, fallback binder or reuseport
worker therefore cannot yield to a nonexistent sibling, and a child's
re-read configuration cannot override the scope. TLS's eligibility
matches its existing admission calculation, without adding proxied
exchanges to that calculation. The 16-combination pure scope row keeps
single-process, reuseport, non-full and idle-evictable cases at zero.

### Queue, backoff and one-hand regressions

The following rows were each run red, in order, before the repair:

| row | first candidate | repaired candidate |
|---|---|---|
| later-listener-progress | both extra plaintext and TLS still pending after 192 primary refusals | both completed after 71 primary refusals |
| all-full-burst-progress | 2 of 32 queued clients refused after two control barriers per worker | 32 of 32 |
| multi-listener-emfile-cpu | minimum idle CPU fraction 0.9549; repeated take 0.9499 | 0.0000 (samples 0, 0, 0.0050) |
| one-hand-master-scope | pending refusal still waiting after two control barriers | completed; root-container row green |

The later-listener and burst assertions use counts and control-message
barriers, not wall-time speed limits. The workers' own stopped states
are acknowledged before queues are populated. The CPU row lowers only
its stopped workers' soft descriptor limits, queues plaintext and TLS,
and restores each limit before cleanup. It sums their process CPU over
three one-second windows, divides by two workers' elapsed capacity,
and takes the minimum with a 0.10 bound. The block's light lock is held
too; the margin separates a near-full-core spin from the corrected
idle loop and keeps windows above timer grain. A one-hand master needs
a root Linux container: the ordinary non-root suite names that skip,
and the separate root take executes the row at the same binary.

### Counters and gates

Each connection-counter drive was red for its missing named series
before production source changed: refusal, idle eviction and EMFILE.
The fixed drive reads exactly one refusal, exactly eleven idle
evictions after 24 idle accepts, and a positive EMFILE failure count
at a 48-descriptor limit. The refusal/eviction drives leave the other
counter at zero. A directed two-worker scrape reads one refusal on
the driven worker and zero on its sibling, with each scrape's
`lobo_worker_id` checked. All four live rows passed twice at the fixed
head (directly, then inside `tools/lobo-metrics`), including after the
queue-wave repair. Three pure files, including the sharing-bit transport
surface, passed native, checked and interpreter lanes: 9/9, no warnings.
The exposition checker passed every clause, and the expanded prefork
suite passed 41/41. The first candidate's narrower suite had passed 40/40.

Evidence retained outside the source tree:
- `red-ready.log`: three named missing-counter reds;
  SHA-256 `a2bc0405ee79988e738573ef14ebce42bceefe22918bcba7f321baa2ec620f53`.
- `redesigned-base.log`: the valid 20+20 baseline;
  SHA-256 `8f4a683d3b9504127016e27a09df4d713d0db35b75e77398202f0811d3ea2662`.
- `fixed-counts.log`: builds, pure/live suites and fixed 20+20;
  SHA-256 `2f1fe4a473f29734db02d329a8f6d2a3a63e0c9c69955991120149719f05ed76`.
- `review-red.log`: the four ordered queue/backoff/scope reds;
  SHA-256 `98a763aae13ca1b1a0d62af170f4f12e40bef0f1ac1a3b12005b2000da20db77`.
- `review-red2.log`: repeated reds with stopped-state acknowledgements;
  SHA-256 `9db4d048023ab678384e60929069d433c6a0d9b0d854043c679c7983aedd8d32`.
- `repaired-counts.log`: builds, nine pure lane-runs, live rows,
  root scope and the repaired 20+20;
  SHA-256 `dd31d3871215045f10f418d69b2369f7df7ffb553e47e530d784244032d83e28`.
- `entry.log`: unmodified-base entry gauntlet;
  SHA-256 `0a85989d7c98be72257ab0c0528dd217c5c687e5883a1380c6e101e2505a5354`.

### Throughput instrument — prediction before method changes

The first full take at `5c62a88` stopped at the existing 0.900 proxied
throughput bar, reading 0.833. Unchanged-binary controls then read
head-self 0.956, head/reference 1.053 and reference-self 0.748; the last
alternated 0.72/1.37/0.74/1.36/0.75. Identical reference bytes were
compared, so the instrument can reject equality on this host. That is
not evidence that the admission implementation regressed throughput.

Before changing the method, the next take will measure destination-port
TCP state around every drive, comparing the persistent backend with a
restarted backend on the same port and a fresh backend/port per drive.
The hypothesis is per-destination connection-state carryover: restarting
the process alone should not clear it, while a fresh port should. The
method will be selected from those results, not from a threshold waiver.
Five alternating pairs, 2,000 warm-up and 20,000 measured requests, and
the 0.900 head/reference bar remain unchanged. Reference-self must pass
before candidate judgment; the same 0.900 budget applies with control
labels in either direction, and CI reporting cannot waive calibration.
Five reference-self repetitions, head-self and head/reference must pass.

### Throughput instrument — measured cause and selected repair

On the same block and the exact same reference binary, the persistent
backend read 0.722900 (first/second medians 16,751/12,076 req/s).
Restarting the backend process on the **same port** still read 0.738918
with the same low/high alternation. A fresh backend and **fresh port**
per drive read 1.002966; its five paired ratios were
1.002069, 1.002359, 1.004232, 0.997744 and 1.003480. Its first/second
medians were 16,995/17,043 req/s, without the prior two-level pattern.

The reused destinations retained 16,771 and 16,891 TIME_WAIT entries.
Fresh destinations each retained about 14,600, while the namespace-wide
count grew from 35,023 to 182,133 and the measurements stayed equal.
The order effect therefore follows per-destination state, not backend
process memory or total socket count. The exact kernel reuse algorithm
is not inferred, and no network settings were changed. Restarting alone
was insufficient; shuffling order would only average the contamination;
waiting for old connections to expire would add an arbitrary delay.
Fresh backend ports isolate the timed drives without changing their
request count, five pairs or the 0.900 bar.

The gate now requires a named reference-self control before collecting
the candidate comparison. That control applies the existing 0.900
budget with either label assigned to the identical binary; a favorable
bias is also unsound. It remains fatal even where CI retains its old
candidate-ratio reporting policy. No local reporting waiver is used.
The new pure tests went red first (16 tests, four missing-feature
errors), then all 18 passed after the repair. The two short unit takes
used a light slot and one Python worker: average busy CPUs 0.907 red
and 0.693 green, with a 6 GiB cap. Five reference-self repetitions,
head-self and the actual head/reference tool gate are the hard
precondition for the next full record; validation is pending here.

The causal take is `backend-diagnosis.log`, SHA-256
`fc30e581c1893bebeebb64d2339d78e045ca6b490948f69bd29799bc09e12631`.
The original instrument controls are `order-controls.log`, SHA-256
`ef8b52e588b41d3a820881f4abac4843b5dc4189bb6b0da6869806d9543e495b`.

### Extended instrument validation — namespace carryover

The five fresh-port reference-self ratios were 1.001142, 0.992843,
1.000234, 0.980495 and 1.026692. That was not a complete green: the
shared namespace subsequently reached 262,144 TIME_WAIT entries. An
identical-head comparison then read 1.598, and the actual comparison
read 0.829. Raw rates jumped from about 17,000 to 28,000–33,000 req/s
when the table reached that ceiling. The preflight had run below the
ceiling and later drives crossed it, so their starting resource states
were no longer comparable. This failed take is retained as
`instrument-validation.log`, SHA-256
`d99bc9e73387f95cfea23b280353b687ef1f8f27e6859e33c671fa341feb5e86`.

Before the next change, the prediction is that condition-based settling
of loopback TIME_WAIT before and after each complete pairing will remove
namespace accumulation as well as destination carryover. It will happen
outside timed drives, after every owned child has stopped. A 120-second
hang bound will refuse the instrument rather than waive the condition;
no sockets are forcibly flushed and no network setting is changed.
Reaching the kernel-reported TIME_WAIT capacity will also invalidate a
sample by name. An explicitly identical candidate/reference comparison
must meet the control budget in both directions, so a 1.598 reading
cannot masquerade as improvement. The five pairs, request counts and
0.900 candidate bar stay unchanged. All three validations remain required.

The final-head green and off-line plant records, their SHA-256s and
every END line accompany the PR. Parser-shape smoke records were
verified separately before the locked take; they are not merge evidence.
README read in full and updated for admission and counter visibility.

## 5. Limits and follow-ups

No new policy is chosen here: the shared-listener pause and the
three counter families implement the specified follow-up scope.
Host-wide ENFILE is not safe to induce on a shared host; its reason
mapping is covered by a pure row in addition to the live EMFILE witness.
A live ENFILE or non-descriptor accept failure, and TLS idle eviction,
have not been driven. TLS refusal at the limit is now exercised by the
later-listener row; the CPU row covers backoff with a TLS client queued.

Independent review found queue starvation, serial delays, a resource
backoff spin, one-hand scope and a TLS eligibility mismatch in the first
candidate. The four ordered red-first rows above reproduce the observable
failures, and the queue-wave repair passes them. Generated-doc drift
was fixed by regeneration; fresh-idle eviction semantics were retained
and the comment qualified. The final-head recorded gate and real pause
plant remain the merge evidence, not the earlier targeted takes.

Footprint: module
