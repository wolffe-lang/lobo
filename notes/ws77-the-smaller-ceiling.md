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
