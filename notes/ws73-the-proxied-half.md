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

### Against the measurements: choice and limits

**Chosen: (a), the existing persistent pool at the rebased base. No
experimental server change is retained.** None of the alternatives
recovers every tested shape. The pre-#81 target remains unmet with one
client; #100 stays open. This is a measured ceiling and new regression
witnesses, not a throughput fix relabelled as one.

All candidate binaries were built at the unchanged pin, from `3d1c191c`
plus the candidate alone. Each was committed after a complete green
gauntlet and before this comparison:

- C `b177203`: **finite 32-exchange proc with a bounded queue of one, a negative probe**.
  This is **not a multi-job wire batch**. A deeper queue was
  not implemented: it cannot amortize a wake for a client waiting for its
  current response, and would need queued-client abort/drain accounting.
  R-ws73-2 was taken as recommended: accept this bounded negative probe
  and keep A. Do not claim a tested deeper-queue state machine.
- D `ce0eebc`: lend the immutable response body to a separate write instead
  of copying head+body together. Chunked responses keep their old path.
  This trades a copy for another send; it does not lend a pass's region
  across an unjoined proc.
- E `6e9c5a6`: read the next job directly, removing its preceding poll.
- F `72c9dc8`: 8 KiB job-read chunks instead of 64 KiB; no frame-size cap.
  A new 128-POST test checks >32 KiB request and response bodies. The
  smaller scratch belongs to the one job-reading worker, not every CPU.
- B remains unavailable by name (#835 and TLS's blocking record reads).

The complete retake: five rounds, 2,000 warm-up and 20,000 measured
requests per cell, rotated/reversed server order. Proxy, backend and
client **all inherit the common four-CPU set 12–15**. This is not the
first retake's three disjoint CPU sets. `ab1`/`ab32` use ApacheBench;
`padded` is a Python client with a 4 KiB header and 400 requests per
connection. Every response was validated; no partial run was admitted.

The corrected controller required load1 <8 continuously for two minutes.
It started at **16:49:50Z, load 7.1045**, and ended at **16:55:59Z, load
11.1753**. Per-row load reached 13.563. Thus this is **quiet-admitted,
not quiet-throughout**: **quiet-admitted at 7.10, end 11.18, max 13.56**.
The spreads are large and the ratios are qualified, not precise speedup claims. The orchestrator held sh24's
workers for this window. No 17:05 fallback was used.

Medians [minimum, maximum], req/s:

| source / candidate | ab1 | ab32 | padded |
|---|---:|---:|---:|
| pre-#81 `9a4723c` | 13,205.94 [3,819.91, 14,718.40] | 12,887.69 [2,307.21, 15,327.00] | 10,141.24 [4,949.67, 12,207.17] |
| frozen pool `f32a1b7` | 4,660.92 [3,284.48, 11,672.70] | 13,007.21 [6,278.07, 14,320.49] | 7,410.08 [6,934.50, 8,074.09] |
| rebased pool A `3d1c191c` | 7,032.70 [2,096.23, 11,742.60] | 13,689.38 [6,692.98, 15,169.29] | 6,803.58 [3,272.65, 8,919.87] |
| C, finite 32 | 5,040.93 [2,860.38, 12,772.18] | 13,003.17 [8,346.66, 14,388.84] | 9,872.76 [7,561.72, 10,513.75] |
| D, borrowed reply | 9,152.28 [3,860.55, 11,410.63] | 10,459.24 [8,657.90, 15,002.22] | 8,634.24 [6,978.69, 9,576.64] |
| E, direct job read | 10,598.54 [5,847.43, 12,288.43] | 8,523.04 [7,138.11, 13,137.49] | 7,763.38 [4,697.54, 9,541.55] |
| F, 8 KiB chunks | 10,074.42 [2,868.37, 14,064.06] | 8,281.67 [6,837.96, 15,089.41] | 6,364.57 [1,521.85, 8,685.67] |
| nginx | 13,209.93 [11,079.26, 14,671.05] | 12,962.50 [8,171.28, 14,700.22] | 10,929.72 [3,839.16, 13,516.31] |

| candidate / pre-#81 | ab1 | ab32 | padded |
|---|---:|---:|---:|
| **A, kept** | **0.533×** | **1.062×** | **0.671×** |
| C | 0.382× | 1.009× | 0.974× |
| D | 0.693× | 0.812× | 0.851× |
| E | 0.803× | 0.661× (**fails 0.9 gate**) | 0.766× |
| F | 0.763× | 0.643× (**fails 0.9 gate**) | 0.628× |

E's ab1 median was 1.507× A, near the prediction, but its ab32 median
was only 0.623× A: not kept. C's padded median met 0.95× the reference,
but short-head ab1 fell to 0.717× A. D and F likewise show mixed or
negative cells. A is retained rather than shipping a regression or
claiming that a wide-spread cell is a universal gain.

**Prediction scored.** E did not win overall; single-client recovery
was not achieved. The initial 75/20/5 cause split was not independently
identifiable and is not presented as a measured partition. The loaded
CPU census measured 46 µs extra user CPU and 75.5 µs extra kernel CPU per
request, with a persistent exchange worker consuming 102 µs CPU and
about 703 µs in the run queue per request. Main-loop CPU was 71 µs;
remaining helpers/transient threads 27 µs. Those are measured buckets,
not a copy-only price. No new job socket or wolf proc is created per
steady-state request. #835/#836 remain the relevant upstream boundaries.

### #106: reproduce the old red without widening the row

The original rigback/memdrive was rerun with 400 warm-up requests and
60,000 driven requests, sampling at 0/400/2,400/20,400/60,400. At the
frozen persistent-pool baseline, growth after warm-up was −24 / +16 /
+4 KiB on 4 / 8 / 16 CPUs, all under the unchanged 512 KiB bound.
Historical pre-pool source `251b6db`, compiled at the **same 0.2.34 pin**,
grew 216 / 336 / **2,288 KiB**; its 16-CPU short row grew **1,316 KiB**.
The instrument's generic “exchange pool” row label describes today's
fixture, not the historical binary's architecture.

A raw 2,400-request receive trace found ten distinct worker TIDs reading
64 KiB job buffers before pooling, one afterward. Positive read counts
were 2,400 and 2,401 (the pool's extra receive is its quit control byte).
The 8 KiB candidate also had one reader. The pool already bounds the job
reader population for this sequential workload; scratch/allocator
warm-up on many short-lived job workers must not be mistaken for a body
retained by each request. The trace does not price every retained byte.

A proxy-only cgroup separated kernel charges from RSS. At rest, anonymous
RSS on 4/8/16 CPUs was 616/728/948 KiB, kernel stack charges 128/192/320
KiB, page-table charges 124/160/216 KiB. The CPU curve includes roughly
28 KiB/cpu of anonymous resident initialization and 16 KiB/cpu of charged
kernel stacks, not an RSS leak per request. Kernel slab charges rose
across the connection drive; they are outside the RSS gate. The initial
thread's stack may be charged before cgroup attachment, so these are
charges, not a complete per-process kernel-memory sum.

The 128 KiB/cpu bound prediction was **not adopted**. The existing pool
already keeps the tested row green at 16 CPUs, and the original failure
can be reproduced at the same pin without it. The new census reports
`os_cpus()` rather than installed CPUs and retains the original bound.
The actual-head reruns and final gauntlet below retain that bound.

### Failures and measurement boundaries retained

- Perf's security refusal was respected; no capability/seccomp workaround
  was run. A failed perf-stat command did not drive ab and supplies no
  CPU measurement.
- The first baseline gauntlet shared a reaper scope with two measurement
  processes. Its log names pids 104536 and 108854; it was tainted and
  stopped (143), not called green. The clean rebased run exited 0.
- C/D/E's first wrapper file was edited while those Bash scripts were
  running, breaking their trailing parser. C/D's actual container exits
  were 0, preserved in podman events, and their complete logs end GREEN.
  E's actual first exit was 1: one native stale-socket assertion after
  the live-socket section. That row does not exercise proxy exchanges;
  the unchanged diagnostic and a complete 0–3 rerun passed. The original
  red is preserved, not erased or described as fixed.
- A malformed early shell wrapper reached the local shell and failed at
  missing `taskset` before invoking wolf. No build ran on nomad-1.
- The CPU helper initially used `print(n)` and failed compilation. It was
  corrected to interpolation; native answers 4/8/16 were checked. Exit 2
  was a compile red, never a skip.
- The first new-layout loaded run lacked nginx's default log directory;
  its partial data were excluded. A copied integration tool lost its
  executable bit; mode was corrected explicitly. Neither failure was
  hidden as a server result.
- A first quiet controller added an unrequested mid-run load veto,
  invalidating partial attempts after valid starts. Those files remain.
  The corrected controller follows the prescribed start-only rule and
  records the complete start/end loads above; no product bar was lowered.

### Actual final binary: the kept pool, with no server-code change

The final-tree release binary is **byte-identical** to the rebased pool
used in the admitted comparison, SHA-256
`26ab0755e1b1c6e1790b12e7a0368f270b52c6ae54b647c29e6ed6d8a3dca890`.
`git diff -- src` is empty. No experimental server change was retained.
All quoted candidate medians remain **quiet-admitted at 7.10, end 11.18,
max 13.56**, not quiet-throughout.

The full ws67-style silent-upstream drive was retaken with the actual
final binary: proxy cpus 0–3, 50 asynchronous fresh-connection static
clients on 8–15 for ten seconds, one or eight accepted silent upstream
requests. The read budget remains one second per complete static request:

| silent upstreams | static answered | missed | p99 / max ms | status ms | stop ms |
|---:|---:|---:|---:|---:|---:|
| 1 | 97,573 | 0 | 8.75 / 17.88 | 1.15 | 11.29 |
| 8 | 100,477 | 0 | 7.82 / 10.45 | 1.27 | 11.77 |

Both `-s stop` calls exited 0, the server ended, every proxied client
read zero bytes and EOF, and every upstream connection closed. SigBlk and
SigIgn were both zero in the actual server, read before the verdict.
This client/close shape and loaded host are stated rather than pretending
its count is directly comparable with ws67's 179,588.

The actual head's original rigback/memdrive curve, same unchanged bound:

| CPUs | RSS 0 / 400 / 2,400 / 20,400 / 60,400 (KiB) | growth after warm-up |
|---:|---|---:|
| 4 | 4,472 / 4,936 / 4,940 / 4,940 / 4,944 | +8 |
| 8 | 4,648 / 5,056 / 5,060 / 5,072 / 5,072 | +16 |
| 16 | 4,848 / 5,276 / 5,280 / 5,280 / 5,280 | +4 |

Seven **preset**, independent unpinned 16-CPU short censuses then grew
**140, 4, 4, 140, 140, 4, 4 KiB**, all <512. These were seven requested
observations, not retries until green. Alongside the same-pin historical
red control, these are #106's closing evidence. The limit was not widened.

### Gates and plants

- Final local gauntlet: `logs/final-gate-r2.log`, exit 0, last line
  `lobo-gauntlet: GREEN`, under `taskset -c 0-3`, 392/392 corpus,
  shell 46 probes (45 parity, one named delta), membudget 25/25,
  proxy-differential 8/8, zero SKIP lines. Its default frozen-source
  throughput row read **0.969×**, above 0.900×. This is that gate's own
  later four-CPU window, not the all-candidate dataset.
- Eight Python ratchet unit tests pass; every candidate release binary
  passed the 128-large-body test under native and checked test drivers.
- A local isolated plant added a 1 ms dispatch sleep and made a 4 KiB job
  read erroneously terminate an incomplete frame. The body test was RED
  (`trap(assert)`) on native and checked drivers. The real throughput
  row was RED at **0.064×** (reference 13,888.44, planted head 884.73
  req/s), not at a missing tool or an ab timeout. Evidence:
  `logs/plant-body-{native,checked}.json`, `logs/plant-throughput.log`,
  `logs/plant-probe.log`; the witness wrapper exited 0 because both
  intended negatives were observed. The plant itself was not green.
- The first final-tree attempt failed only formatting of the new CPU
  helper. Canonical formatting was applied; the red log remains
  `logs/final-gate.log`, exit 1. No assertion or timeout changed.
- `ci/tiers-test.py` passes, including the actual changed workflow and
  path classification. Linux CI declares ApacheBench/Python explicitly;
  macOS verifies their presence. No pool package was installed by this
  lane (the earlier ab installation was the orchestrator's).
- Official wolf/lupin archives were independently downloaded into fresh
  verification directories and each digest checked twice. Their driver,
  runtime, interpreter and complete std tree are byte-identical to the
  measured tools (`logs/archive-verify.log`, exit 0). This verifies rather
  than merely trusting the tools copied from ws72.

## 4. Evidence index

Kasumi `/home/mfwolffe/lanes/ws73/`: `logs/build-base.log`,
`logs/bench-base.log`, `ev/bench-pre81-baseline-nginx.json` and raw ab
outputs in `ev/bench/`; `logs/profile.log`, `ev/profile/*.strace`.
Scripts: `scripts/setup.sh`, `bench.py`, `profile.py`, `proc.py`,
`proc-isolated.py`, `trace-isolated.py`, `bench-pinned.py`, the quiet
controllers, `memory.sh`, `kernel.py`, `readers.py`, `silent.py`, the
head-measurement and final-gauntlet wrappers. Completed idle-subtracted trace
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
The clean local baseline gauntlet exited 0 at `3d1c191c`; its last line
is `lobo-gauntlet: GREEN`. The earlier contaminated run is not green
evidence.
