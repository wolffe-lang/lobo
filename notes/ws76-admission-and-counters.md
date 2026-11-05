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
| fixed `ab1d0c4` | 20 green / 0 red | 20 green / 0 red | none |

No oracle-precondition failures or timeouts occurred in these 80
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

An expired pause buys one immediate queue probe. If the sibling took
the queue, the full hand clears that permit; a later arrival must
get a new pause. HTTP bursts check fullness again before every take,
so a hand becoming full inside a burst cannot skip the yield. TLS
listeners share the yield, but TLS accounting retains its documented
one-at-a-time limitation. The 16-combination pure scope row keeps
single-process, reuseport, non-full and idle-evictable cases at zero.

### Counters and gates

Each connection-counter drive was red for its missing named series
before production source changed: refusal, idle eviction and EMFILE.
The fixed drive reads exactly one refusal, exactly eleven idle
evictions after 24 idle accepts, and a positive EMFILE failure count
at a 48-descriptor limit. The refusal/eviction drives leave the other
counter at zero. A directed two-worker scrape reads one refusal on
the driven worker and zero on its sibling, with each scrape's
`lobo_worker_id` checked. All four live rows passed twice at the fixed
head (directly, then inside `tools/lobo-metrics`). Both pure files
passed native, checked and interpreter lanes: 6/6, no warnings.
The exposition checker passed every clause, and prefork passed 40/40.

Evidence retained outside the source tree:
- `red-ready.log`: three named missing-counter reds;
  SHA-256 `a2bc0405ee79988e738573ef14ebce42bceefe22918bcba7f321baa2ec620f53`.
- `redesigned-base.log`: the valid 20+20 baseline;
  SHA-256 `8f4a683d3b9504127016e27a09df4d713d0db35b75e77398202f0811d3ea2662`.
- `fixed-counts.log`: builds, pure/live suites and fixed 20+20;
  SHA-256 `2f1fe4a473f29734db02d329a8f6d2a3a63e0c9c69955991120149719f05ed76`.
- `entry.log`: unmodified-base entry gauntlet;
  SHA-256 `0a85989d7c98be72257ab0c0528dd217c5c687e5883a1380c6e101e2505a5354`.

The final-head green and off-line plant records, their SHA-256s and
every END line accompany the PR. Parser-shape smoke records were
verified separately before the locked take; they are not merge evidence.
README read in full and updated for admission and counter visibility.

## 5. Limits and follow-ups

No new policy is chosen here: the shared-listener pause and the
three counter families implement the specified follow-up scope.
Host-wide ENFILE is not safe to induce on a shared host; its reason
mapping is covered by a pure row in addition to the live EMFILE witness.
A live ENFILE or non-descriptor accept failure, and TLS at the limit,
have not been driven.

Independent review of the first candidate found completion-blocking
holes not covered by the successful first-28 rows: re-arming after
each refusal serializes queued refusals and can starve later listeners;
a TLS re-arm after a plaintext accept failure can defeat the resource
backoff and spin. An inherited listener with only one worker also
pauses, and TLS pause eligibility includes proxied exchanges that its
existing admission calculation excludes. These are verified control-flow
findings, not reproduced rows yet. The generated-doc drift at that
candidate was fixed by regeneration. No final gate or merge-readiness
claim is made until the remaining defects have red-first witnesses and
repairs. Fresh accepts remain idle until their request is read, retaining
the existing eviction semantics; the burst comment needs to say so.

Footprint: module
