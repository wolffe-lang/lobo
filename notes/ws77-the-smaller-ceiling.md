# ws77 — the throughput instrument under a smaller TIME_WAIT ceiling

## 1. Forbidden

No nginx, ApacheBench or other proxy or load-tool source: the pinned
nginx and `ab` are black boxes. No host network setting changes: a
TIME_WAIT capacity is set only inside a test container's own network
namespace. Tests bind loopback only. No labels,
merges, tags, releases or issue closures from this lane, no push to
trunk, and no attribution trailers.

## 2. Inputs, verified

- Base: trunk `e63bf31`, branch `ws77`, a fresh clone.
- The red: trunk run 42121284008, job `gauntlet`. Its reference-self
  pairing drove five times; the namespace TIME_WAIT count read 12,912,
  26,296, 39,583, 52,763 and then 65,536 after the fifth drive, against
  the runner's reported capacity of 65,536. The after-pairing settle
  recorded `before 65536, after 65536, status saturated`, and the gate
  printed `FAILED — [reference-self] collection failed: [tcp-state]
  namespace TIME_WAIT 65536 reached capacity 65536; pairing refused;
  candidate not judged`. That job is the first to drive the settled
  instrument on a hosted runner; the same run's macOS gauntlet passed
  (it reports no capacity, so no saturation check applies there).
- Pins: wolf 0.2.36, lupin 0.1.58, std `78b9d3cb`, nginx 1.30.4, as in
  `wolf-toolchain.toml` and the differential pin. The staged binaries'
  SHA-256s equal the previous lane's: compiler
  `f7b73fba526e06116cc5eeda146cc80c8a42cd1f7a198d574e8a961f6c7a57ef`,
  interpreter `47c646a61b9fd0dfe7d4565a74e22428a259eb54642f6d0d6ef3c1c0abe01ada`,
  oracle `5a08ef7f65591bcf51fe43ef43f3a1ee664ccf5665532b4351efde6b9c38eaff`.
- A rootless container given `--sysctl net.ipv4.tcp_max_tw_buckets=65536`
  reads 65,536 in its own namespace while the host's value is unchanged
  (probed before any row: host 131,072 before and after; the container
  namespace differs from the host's).

| environment | hardware and bounds |
|---|---|
| Linux x86-64, Ubuntu 24.04 container | Intel Core i7-10870H, 16 logical CPUs; an eight-CPU affinity (four cores, both threads), 12 GiB memory cap |
| Linux x86-64, Ubuntu 24.04 container | Intel Core i7-12700KF, 20 logical CPUs; a six-CPU affinity, 12 GiB memory cap, nothing beside it |
| GitHub hosted runner (the red) | `ubuntu-latest`, TIME_WAIT capacity 65,536 |

## 3. Prediction (committed before any source change)

**The red, reproduced.** At `e63bf31`, `tools/lobo-proxy-throughput` in a
container whose namespace capacity is 65,536 will refuse exactly as the
runner did: each drive (2,000 warm-up plus 20,000 measured requests)
leaves roughly 13,000–15,000 TIME_WAIT entries, since each proxied
exchange opens a fresh upstream connection; the fifth drive's after
count reaches 65,536; and the gate prints the same `[tcp-state]` refusal
before any ratio. Settles run only between pairings, so nothing within
the reference-self pairing can make room.

**The fix.** Before every drive of a fresh-backend pairing, after every
owned child has stopped and before the drive's backend starts (so outside
the warm-up and outside the timed 20,000-request window), the instrument
reads the namespace TIME_WAIT count. Where the kernel reports a capacity
and the count plus one drive's measured increment would pass **0.75 of
that capacity**, it waits until the count is at most 0.75 of capacity
minus the increment. The increment is the largest growth any earlier
drive cycle of the same pairing showed. The pairing's opening settle
leaves the namespace at zero, so the first cycle's growth is exact and
the first drive needs no estimate. The wait is the existing bounded
settle: 120-second ceiling, one-second polls, and the before and after
counts, elapsed time, target, increment and fraction logged and kept
as JSON. It refuses by name if the target isn't reached in time,
if the namespace saturates, or if one drive's increment alone exceeds
the fraction (no wait could meet it). The settles before and after each
pairing, the saturation checks around each drive, the fresh backend and
port per drive, SHA-256 symmetry, the one-sided 0.900 rule, five pairs,
2,000 warm-up and 20,000 measured requests all stay as they are.

**Why 0.75.** Below the capacity the kernel keeps TIME_WAIT entries
normally; at the capacity it destroys new ones at once, which is the
changed resource state the previous lane measured (raw rates jumped from
about 17,000 to 28,000–33,000 req/s). That lane also measured equal rates
across namespace counts from 35,023 to 182,133 at a 262,144 capacity.
So the fraction only needs to leave a margin for a drive larger than the
largest one measured. A quarter of the capacity is 16,384 entries at
65,536, more than one whole drive, and 65,536 at 262,144. A half would
cost one more settle in every three drives and add no soundness that
the margin doesn't already give. Settling to zero before every drive
would cost about a minute per drive (twenty minutes for the gate's two
pairings), past the runner's job budget.

**What each row should show:**
- **65,536, after the fix:** the whole gate completes. The threshold is
  49,152, so about three drives fit in one 60-second TIME_WAIT lifetime.
  Each pairing takes about three per-drive settles of under 60 seconds;
  no drive's after count passes 49,152; reference-self passes the 0.900
  budget in both directions, as at the larger capacity. The step takes
  several minutes longer than an uncapped one; the time is the TIME_WAIT
  lifetime, not the drives.
- **262,144:** the threshold is 196,608 and ten drives leave about
  150,000 entries, so no per-drive settle triggers. The gate behaves as
  before: settles only around pairings.
- **Deliberate saturation (the previous lane's witness):** a namespace
  filled to 262,144 still refuses `[tcp-state]` at the pairing's opening
  settle, before any drive or ratio.
- **Unit rows, red at base and green after:** the guard's boundary
  (exactly at 0.75 passes, one more entry settles), the impossible
  increment refused by name, the per-drive timeout refused by name, a
  simulated 65,536 namespace in which a whole pairing completes without
  saturating, and a timeline row proving that every settle falls while
  no owned child runs and never between a drive's warm-up and its
  measured requests.
- **macOS:** no capacity is reported, so the guard never reads a count
  and the macOS path is unchanged.
- **On the runner:** the same `gauntlet` job goes green at the PR head.
  The throughput step grows from about 2.5 minutes before the previous
  lane to about 10 minutes, and the job from about 28 to about 37 of
  its 45 minutes. If the 65,536 reproduction here says otherwise, the
  job's timeout is a separate decision (recorded below), not part of the
  instrument fix.

**The plant:** one hunk in `tests/rig/proxy_throughput/measure.py` skips
the per-drive settle. The new unit rows go red by name, and the 65,536
drive refuses `[tcp-state]` exactly as at base.

## 4. Evidence index

### The red at base, reproduced (i7-10870H)

At `e63bf31`, `tools/lobo-proxy-throughput` ran in a container namespace
holding 65,536 entries; the host's value read 131,072 before and after.
The namespace count after each reference-self drive:

| drive | runner, run 42121284008 | here |
|---|---|---|
| reference, round 0 | 12,912 | 14,322 |
| head, round 0 | 26,296 | 28,664 |
| head, round 1 | 39,583 | 43,029 |
| reference, round 1 | 52,763 | 57,385 |
| reference, round 2 | 65,536 | 65,536 |

Then, as on the runner, the after-pairing settle read `before 65536,
after 65536, status saturated`, and the gate printed the same line byte
for byte: `FAILED — [reference-self] collection failed: [tcp-state]
namespace TIME_WAIT 65536 reached capacity 65536; pairing refused;
candidate not judged`. The saturated drive read 16,523 req/s against
14,515–14,792 for the four before it, the changed state the capacity
check exists to refuse. Log `red-base.log`, SHA-256
`5e4ef3dbc7974aa7a40dc4d315a3ecafc1dac522225f7a48719d9d743ab49283`.

### The rows, red first

`64765c7` added five rows to the instrument's self-test. At that commit
26 ran with 5 errors: the simulated 65,536 pairing refused with the
runner's own `[tcp-state] namespace TIME_WAIT 65536 reached capacity
65536; pairing refused`, and the other four found no guard to call. Base
`e63bf31` ran its 21 rows green in the same take. After the fix in
`38a9a2b`, all 26 pass.

### The fixed instrument at 65,536 (`cb80055`, i7-12700KF)

The whole gate completed in 591 seconds, the reference build included:

| pairing | waits before drives | largest count after a drive | ratio | paired range |
|---|---|---|---|---|
| reference-self | 4 (60.0, 1.0, 60.0, 58.0 s) | 45,292 | 1.003 | 0.995–1.012 |
| comparison | 3 (61.0, 62.0, 61.0 s) | 47,553 | 1.009 | 1.003–1.017 |

No count passed the 49,152 threshold. The measured increment was 14,944
in reference-self and grew from 14,800 to 16,429 in the comparison, whose
head drives leave about 1,600 more entries each than the reference's;
the largest-growth estimate carried that. Each pairing's closing settle
reached zero in 64 seconds. Every wait was recorded with its count,
target and increment, and each ran before its drive's backend started,
with every owned child stopped (the timeline row holds that order).

### 262,144, unchanged

The gate completed in 226 seconds, and no drive waited. The largest
counts were 148,682 and 156,043, under the 196,608 threshold.
Reference-self read 1.000 (paired 0.994–1.005) and the comparison 1.012
(paired 1.007–1.019), in line with the previous lane's settled take on
the same hardware (reference-self 0.996–1.003).

### The previous lane's saturation witness

A namespace filled to 262,144 by direct oracle drives refused at the
pairing's opening settle, `[tcp-state] namespace TIME_WAIT 262144
reached capacity 262144; pairing refused`, before any drive or ratio, in
9 seconds. The witness is that lane's own, copied with only its paths
changed.

Validation log `valid-cb80055.log`, SHA-256
`d353f00060377a819798902ceceda3c4ee163948b4673579a57f7c506d44c04d`.
The host's value read 262,144 after every step. A second validation of
the same commit, queued on the i7-10870H before the move to the other
machine (`fixed-cb80055.log`), is not evidence: the final records come
from the i7-12700KF.

### On the runner

The 65,536 gate's time is the TIME_WAIT lifetime, about three drives per
60 seconds, not the drive rate. The runner drives at about 6,150 req/s
against 17,200 here, which adds about a minute. So its throughput step
should take 10–11 minutes, against 2.5 before the previous lane, and its
gauntlet job about 36 of its 45 minutes.

## 5. Done-when, limits and follow-ups

Done when the final-head record is green, with the 65,536 reproduction,
the 262,144 gate, the saturation witness and the unit rows in it, and
when the one-hunk plant (the per-drive settle skipped) is red by name.
The records, their SHA-256s and every END line accompany the PR.

Decisions, recommended here and accepted:
- **R-ws77-1, the fraction: 0.75.** The options were 0.5, 0.75, or
  settling to zero before every drive. 0.5 costs one more wait in every
  three drives for no soundness the margin doesn't give, and zero costs
  about twenty minutes, past the runner's job budget.
- **R-ws77-2, the runner's job timeout: unchanged at 45 minutes.** The
  estimate above is about 36. If the labelled run measures over about
  40, raising it is a separate CI change.

Limits:
- The increment is an estimate: the largest growth measured so far in
  the pairing. A drive larger than that by more than a quarter of the
  capacity would still saturate, and is then refused by name, never
  judged.
- macOS reports no capacity, so no drive there is guarded; its path is
  unchanged and its short window is still reported, not gated.
- The runner's time is a prediction until the labelled run measures it.

README read: its one sentence on settling now names the per-drive wait.

Footprint: module
