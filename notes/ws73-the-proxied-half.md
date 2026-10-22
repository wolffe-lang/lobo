# ws73 — the proxied half, and the per-cpu budget

Crawl 54, lane ws73, GPT-6.1-Sol (Codex). The implementation directive is
`wolf/sprints/wws/42-the-proxied-half/ws73-the-proxied-half.md`; the rules
are `wolf/sprints/RULES.md`. This prediction precedes any source, test,
tool or CI change. The pins stay wolf 0.2.34 / lupin 0.1.55 / std e036bec.

## 1. Forbidden

nginx is an oracle and a black box, never source. No merge, tag, release,
AUR, issue filing or closing. Loopback only, inside a lane-owned container
on kasumi; no build on nomad-1. No change to `spawn_worker` or its callers
(ws72). No attribution trailers. Every new gate must be seen red first.

## 2. Inputs, verified

**The stale premise, corrected (R-ws73-1).** The planning contract's
candidate (a), a pool of persistent exchange procs, is already in pinned
trunk `f32a1b7`: ws69 landed `proxy.job_loop` and `PxSlot`. The orchestrator
accepted the correction: the recovery target is pre-#81 `9a4723c`, not
trunk compared with itself. `f32a1b7` is the pool baseline. The lane rebased
onto ws72's `3d1c191c` before its first implementation commit; its binary-
identity guard is outside these baseline measurements and stays untouched.
Candidates will be measured at that rebased base. ws69 had already
measured the remaining single-client wake/compensation cost and filed
wolf-lang#835 (blocking connect) and #836 (unconditional compensation).

The release binaries of both trees were built inside `ws73-rig`, at the
same 0.2.34 toolchain, with zero diagnostics. Published-archive binaries
were copied from ws72's rig and SHA-256s read twice: wolf `2bfaf7b8…`,
runtime `cc058247…`, lupin `ad52ee96…`; nginx 1.30.4 `bf6b151c…`, also twice.
The orchestrator installed ApacheBench 2.3 after the initial missing-tool
stop; no package was installed by this lane.

First retake: five alternating rounds, `ab -k`, 2,000 warm-up and 20,000
measured requests; proxy cpus 0–3, upstream 4–5, client 6–7. All responses
passed ab's failure count. Host load rose 15–39; these are **loaded**
measurements, not ws69's quiet numbers. Medians [minimum, maximum], req/s:

| shape | pre-#81 `9a4723c` | pool `f32a1b7` | nginx |
|---|---:|---:|---:|
| ab1 | 3,647.68 [1,450.39, 5,152.72] | 481.79 [372.78, 1,116.54] | 3,698.05 [1,830.12, 5,133.89] |
| ab32 | 2,193.34 [1,311.25, 4,380.68] | 5,470.01 [3,743.47, 6,142.02] | 5,208.28 [2,955.88, 7,190.33] |

A separate strace drive (11,000 requests including warm-up; not yet
idle-subtracted) counted 19,481 `clone3` calls on the pool, **1.771 per
request**, against nine total on pre-#81; polls 4.003 vs 1.003 per request.
These are OS thread creations, not one wolf proc spawned per request:
the pool is already persistent. The thread-lifecycle measurement is the
next instrument, before choosing a candidate.

Perf was refused at the container security boundary; that route was
dropped, and the profile uses strace and /proc without changing security.

## 3. Prediction

### The exchange

- Of the extra single-client latency at this pin, predict 75% is the two
  cross-thread wakes plus runtime blocking compensation (#836), 20% job
  serialization/accounting and response materialization, 5% ordinary
  upstream/socket work; new job sockets and wolf proc spawn cost **zero
  per steady-state exchange** in the existing pool. The /proc CPU and
  schedstat split and idle-subtracted syscall count will test this, not
  ptrace's inflated elapsed times interpreted as normal latency.
- (a) The existing pool is the baseline, not a new optimization.
- (b) An in-loop nonblocking exchange is unavailable by name: #835's
  `net_connect` blocks, and the TLS client still has blocking record
  reads. No purported asynchronous loop will hide that boundary.
- (c) Finite batches of 32 exchanges, with at most one queued job per
  proc: predict 0.90–1.05× the persistent pool, not a single-client win;
  a client that waits for its reply cannot supply a second queued job.
- (d) Gather the response head and borrowed immutable body instead of
  building another full response string: predict 1.00–1.05× on the 16 B
  body, a larger allocation saving on large bodies. Never lend a pass's
  region across an unjoined proc; the job's socket is its ownership
  boundary, not removable copy ceremony.
- (e) Profile-led candidate: read a job directly rather than polling the
  job socket before its read. The read's fast path or reactor already
  knows readiness; the extra unconditional `net_wait` triggers #836.
  Predict 1.2–1.5× pool ab1 under load, less improvement at ab32. Keep the
  stop/quit/kill framing and the upstream's client/stop watches intact.
- Predict (e) wins, with (d) kept only if measured beneficial and all
  semantic rows stay green. The ≥0.95× recovery target may remain unmet
  with a single client; do not close #100 or weaken the number to hide it.

### The budget

Predict a bounded per-worker/thread allocator footprint, not bytes retained
per exchange: anonymous RSS and page tables grow as more compensation
threads touch stacks/allocator state, then plateau by 20,000 and 60,000
requests. Kernel page tables (`VmPTE`) are reported separately: they are
not included in process RSS. Thread counts at one instant alone will miss
short-lived compensation threads; count clone lifecycles as well.

Retake the `flat, proxied` phases on 4, 8 and 16 cpus, preserving the
400-request warm-up and 2,000-request row, plus the 20k/60k plateaus.
If this is runtime-owned and cannot be capped by lobo, predict a test
bound proportional to `os_cpus()` (128 KiB per schedulable cpu, minimum
four) will cover it; keep the 4-cpu 512 KiB bound and reject request-linear
growth with a separate long-drive check. This is a prediction, not a
measured justification for changing the bound yet.

### Baseline thread-lifecycle instrument

An untraced 20,000-request window with the 4 KiB padding header, proxy
cpus 0–3, read process-wide `/proc/<pid>/stat` deltas (100 Hz), the main
thread's own deltas, `/proc/<pid>/schedstat`, and Threads/TIDs every 20 ms.
The load was 60–69. CPU microseconds per request:

| part | pre-#81 | pool baseline |
|---|---:|---:|
| whole proxy user / kernel | 29.5 / 49.0 | 75.5 / 124.5 |
| proxy main thread user / kernel | 26.5 / 39.5 | 45.5 / 25.5 |
| other proxy threads, total CPU (difference) | 12.5 | 129.0 |
| upstream user / kernel | 16.5 / 31.5 | 31.0 / 54.0 |
| main-thread run-queue wait | 171.2 | 222.2 |

The main thread is the serving loop; the other threads include exchange
execution and runtime helpers, not independently identifiable wolf procs.
Do not call this an exact per-proc attribution. Instantaneous Threads was
11–12 on the pool, but the sampler saw 1,981 distinct TIDs; pre-#81 stayed
at nine. The sampled TID count is a lower bound, not a complete clone
count. This is why a flat Threads reading does not refute #836.

### The isolated memory curve (input, not a head result)

A first curve and trace shared the gauntlet checkout's reaper scope by
mistake. The gauntlet log explicitly records reaping measurement pid
104536, then flags trace pid 108854 as a leaked helper. Those runs and
the contaminated gauntlet are invalid. The measurement binaries were
copied outside that checkout before the following complete retake.

Python's padded keepalive drive reconnects every 400 requests, exactly
the membudget connection shape; the prompt backend here is the pinned
nginx. Numbers are kB; totals are cumulative requests. Load 28–35 was
printed by uptime at every phase (`ev/proc-isolated/*-phases.json`).

| cpus | total | RSS | anonymous RSS | file RSS | page tables (outside RSS) | Threads |
|---:|---:|---:|---:|---:|---:|---:|
| 4 | 0 / 400 / 2,400 / 20,000 / 60,000 | 4540 / 4952 / 4952 / 4956 / 4956 | 624 / 908 / 908 / 912 / 912 | 3916 / 4044 / 4044 / 4044 / 4044 | 124 / 144 / 144 / 148 / 148 | 9 / 11 / 11 / 11 / 11 |
| 8 | 0 / 400 / 2,400 / 20,000 / 60,000 | 4648 / 5060 / 5064 / 5172 / 5172 | 736 / 1020 / 1024 / 1132 / 1132 | 3912 / 4040 / 4040 / 4040 / 4040 | 156 / 176 / 184 / 192 / 192 | 13 / 15 / 15 / 17 / 15 |
| 16 | 0 / 400 / 2,400 / 20,000 / 60,000 | 4864 / 5264 / 5264 / 5264 / 5468 | 956 / 1228 / 1228 / 1228 / 1432 | 3908 / 4036 / 4036 / 4036 / 4036 | 200 / 212 / 212 / 212 / 220 | 21 / 23 / 23 / 23 / 25 |

This retake does not reproduce #106's >512 kB short-row growth: the
400→2,400 deltas are 0, 4, 0 kB. Nor does it prove a 16-cpu plateau at
20k: 20k→60k added 204 kB, all anonymous RSS, beside two more live threads
and 8 kB of page tables. A proposed bound still needs evidence at the
chosen head and the original rigback-backed membudget row, not just this
nginx-backed experiment. Kernel stacks/socket accounting have not been
measured per process; VmPTE is not their substitute.

## 4. Evidence index

Kasumi `/home/mfwolffe/lanes/ws73/`: `logs/build-base.log`,
`logs/bench-base.log`, `ev/bench-pre81-baseline-nginx.json` and raw ab
outputs in `ev/bench/`; `logs/profile.log`, `ev/profile/*.strace`.
Scripts: `scripts/setup.sh`, `bench.py`, `profile.py`, `proc.py`,
`proc-isolated.py`, `trace-isolated.py`. Completed idle-subtracted trace
outputs are in `ev/trace-isolated/`; the curve is in `ev/proc-isolated/`.
The failed perf-stat drive did **not** execute ab; its CPU deltas are not
evidence. The lifecycle and curve instruments use no perf.

## 5. Done-when

Candidates measured at separate commits; silent-upstream, ws64 limits,
proxy and memory rows green. A relative throughput CI row, its planted
red, and a CPU-aware memory row justified by the curve. Final gauntlet,
PR and audit. Decisive throughput retakes on cpus 12–15 below host load 8
(the orchestrator's correction after the loaded first retake).

The prediction-only commit changes no executable input; the rebased source's
linux gauntlet is green in run **39794877850** (`tier pr`, head `3d1c191c`).
A clean local baseline gauntlet is being retaken; the earlier contaminated
local run is not claimed green.
