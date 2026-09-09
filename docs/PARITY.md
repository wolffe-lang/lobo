# Parity (W8) — the bar, written before the measurement

Dated 2026-09-08 (ws22). Everything under *The bar* below was
written BEFORE this sprint ran a single benchmark. The numbers the
repo already held (0.1.0's 1.50x on the close shape and 2.15x on
keepalive, from ws18's table in `docs/WORKERS.md`) are the reason a
bar is needed, not its input. A sprint that moves the bar does so in
a commit that says why, and any closeout reporting against it names
the bar's date.

The tool that measures the bar as written is
`tools/lobo-parity`. It is NOT a gauntlet step: a number depends on
the box. Its table goes into the ledger at the foot of this page,
dated, host-named, load-quoted.

## The bar

### The workload — the differential's own

- One static file, 1 KiB (sixteen 64-byte lines, the file
  `tools/lobo-prefork-bench` has served since ws16), `text/html`,
  `GET /index.html HTTP/1.1`, loopback.
- No access log on either side. nginx: `access_log off`. lobo:
  no `access_log` directive, and absent one lobo writes no access
  log (`src/config/logconf.lu`'s named delta). Logging is a cost
  and a different shape from this one.
- The oracle is the pinned nginx (`tests/differential/NGINX-PIN`),
  the same binary the differential runs, `worker_processes N`, the
  `events` block empty (the platform default: kqueue here, epoll on
  linux), every other directive nginx's default.
- lobo is the release-tier binary the gauntlet builds
  (`target/lobo-release`; `WOLF_MIDEND=0` until wolf-lang#146 closes,
  the shipped build, flag for flag), `worker_processes N`, every
  other directive lobo's default.

### The shapes — both gate

- close: one connection per request (`ab` without `-k`; the
  client closes after each reply). The accept path plus one request.
- keepalive: `ab -k`; every connection is reused for the whole
  run. The read/serve path.

lobo's gap is two numbers, 1.50x on one shape and 2.15x on the
other at 0.1.0, and a bar that averaged them would hide the worse
one. Each shape is met or not met on its own.

### The cells

| cell | N (`worker_processes`, both servers) | c (`ab -c`) | gates? |
|---|---|---|---|
| the bar | the host's cpu count | 32 | **yes** |
| per-process | 1 | 32 | no — reported every time |

- N = cpus is the stranger's configuration (`worker_processes
  auto` is what a twenty-year nginx user writes), and it is the cell
  where lobo's distribution across hands is part of the answer.
- N = 1 is informative and always printed: the two event loops
  side by side with no distribution question in the way. It is the
  per-request cost, and it is where a profile's finding shows first.
- Cores used (Σ cpu seconds over the server's process tree ÷ the
  run's wall, read off `ps(1)` after the run, so it is the host's
  accounting) is printed for EVERY cell and gates
  nothing. A server that reaches parity by burning several times the
  cpu has reached a different thing, and the number is on the table.

### The hosts — both, or it is a sentence about one

- linux x86-64: where a stranger runs a server. The only linux
  x86-64 the org has hands on is the CI runner (`ubuntu-latest`, four
  vcpus, a shared VM); N there is 4, and the runner's noise is why
  the statistic below is a RATIO taken on one box in one session and
  never an absolute carried between boxes.
- macOS arm64: the development box (nomad-1: Apple M5 Pro,
  18 cpus = 12 performance + 6 efficiency, macOS 26.4.1 at ws22).

W8 is met only when the bar holds on both. Hosts disagree: s137
measured `reuse_port` distributing on linux and NOT on macOS, and the
accept path is half of one shape, so a result on one host is that
host's result and carries that host's name.

### The runs, and what confidence means

- A run is `ab -t 5 -n 1000000 -c 32 [-k]`: five seconds of wall
  clock against one server, the request cap out of reach. (ws16–ws18
  ran `-n 20000`, which is under a quarter of a second at nginx's
  keepalive rate, so it measured the timer.)
- A set is five pairs, interleaved: lobo then nginx, lobo
  then nginx, …, each server started fresh for its pair, both shapes
  run against each fresh server. Drift (thermal, a background job,
  a file cache warming) lands on both sides of a pair.
- The statistic is the ratio nginx ÷ lobo per pair, and the
  number reported is the median of the five ratios, with the
  minimum and maximum beside it. The repo's prior habit (three runs
  of each, a median of each side) could not tell a ten percent
  difference from noise: ws18's three close-shape runs spread
  21,443–25,470 around 23,663, ±8.5%.
- Validity, checked by the tool. A set that fails any of these is
  refused with its reason, and a refused set is not a result:
  - *quiet rig*: `uptime`'s one-minute load before the set is printed
    in the header; a set taken above 3.0 does not count (this box
    idles near 2 with its editors up; the bogus `timeout` a lane once
    recorded came at 46+).
  - *the generator is not the ceiling*: `ab` is single-threaded, and
    `docs/WORKERS.md`'s own table has nginx at 52k (one worker) and
    86k (eighteen) on the keepalive shape, numbers as likely to be
    `ab`'s limit as nginx's. The tool prints the
    generator's own cpu seconds ÷ wall for every run; a run where
    that exceeds 0.90 is a measurement of `ab` and the set is
    refused (split the load across k generators and take it again).
    In practice the tool starts k `ab` processes together, each
    with c ÷ k connections (k = 4 by default, so eight connections
    each at c = 32); req/s is their sum, and EVERY generator's own
    cpu ÷ wall is held under the ceiling. k is printed in the set's
    header; the total concurrency c is the bar's number, not k.
  - *the oracle is stable*: the five nginx numbers on a shape must
    satisfy max ÷ min ≤ 1.15, else the box was not quiet and the
    set is discarded.
  - *nothing failed*: `ab`'s `Failed requests` and `Non-2xx` are
    zero on every run, or the set is refused.

#### Refusal scope (ws23, written 2026-09-09 before ws23's first set)

ws22's quiet-box set was refused by the tool on exactly one count,
nginx's N=1 keepalive spread, and left the question of scope open.
Settled here, before any ws23 number exists: the *quiet rig* rule
is the set's, since a loaded box loads every cell. The *generator*,
*oracle* and *nothing failed* rules are read **per cell**. A refusal
on the gating cell (N = cpus) refuses the set. A refusal on the
informative cell (N = 1) refuses that cell: its rows are marked
`(REFUSED)` in the table, they are not a result, and the gating
verdict stands. The reason is the one ws22 saw: a single process on
this box lands on a performance core or an efficiency core run to
run and its numbers swing 1.3–2x, which is a fact about the N=1 cell
and says nothing about the eighteen-hand cell it was refused beside.
`tools/lobo-parity` implements the scope (exit 3 only on a set-wide
or gating-cell refusal; the N=1 refusal is printed by name and exits
0). Every ledger row from ws23 on is read under this rule; ws22's
macOS row above was reported the same way by hand.

### What counts as met

W8 is met when, on both hosts, on both shapes, at N = cpus and
c = 32, the median of the five per-pair ratios nginx ÷ lobo is
≤ 1.10, which puts lobo within ten percent of nginx, from a valid
set as defined above, measured by `tools/lobo-parity`, whose table is
in the ledger below and in the campaign closeout.

Ten percent is one noise floor above the oracle's own run-to-run
spread; nearer than that this method cannot see. Any gating cell
above 1.10 is not met. "Met on macOS" is a sentence about macOS.

## Ledger

Sets appended newest first. A row is here because its set was
VALID; a refused set is named in the sprint's closeout, not here.

### 2026-09-09 · macOS arm64 · nomad-1 (18 cpus) · the ws24 baseline window · **REFUSED at the bound** (the box never quieted; one indicative set)

The first deliverable of ws24 was a QUIET set at trunk `1318cfe`
before any code moved. The window was announced to the orchestrator
at 03:38Z, the other lanes held their gauntlets, and a waiter polled
`uptime` for load(1m) < 3.0 for fifty minutes (03:38–04:28Z, the
bound stated in the announcement). It never saw it: the one-minute
load read 4.98, 11.37, 8.48, 7.07, 5.41, 4.09, 6.14, 5.06, 7.74,
8.00, 7.08 … 4.81 at the bound, and the residents were not lanes —
`mediaanalysisd` (the user's photo indexer, 15–123% cpu for the
whole window) and `XprotectService` (root, ~50%) — plus one sibling
lane's `cargo xtask ci` the orchestrator named. The quiet baseline
is therefore REFUSED, W8 stays UNMEASURED on macOS, and no macOS
number in the ws24 series is a result. ONE indicative set was taken
at the bound (04:29Z, load 3.92 at the start, rising to 20 as the
other lanes' gauntlets resumed during it), so the two hosts' series
can be read side by side; the tool refused it on load and on
nginx's N=18 keepalive spread (1.278). lobo 0.1.0+dev at wolf 0.2.6
pin 398e5f5, nginx 1.30.4 (`ws24-parity-baseline-macos-indicative.log`):

| cell | shape | lobo req/s | nginx req/s | nginx ÷ lobo median [min, max] | lobo cores | nginx cores | ab max | load(1m) during |
|---|---|---|---|---|---|---|---|---|
| N=18 c=32 | close | 19,093 | 20,919 | 1.096x [0.937, 1.183] | 6.24 | 3.28 | 0.34 | 3.92 → 20.3 |
| N=18 c=32 | keepalive | 60,950 | 113,353 | 1.623x [1.508, 1.971] | 8.57 | 9.38 | 0.34 | 3.92 → 20.3 |
| N=1 c=32 (REFUSED) | close | 12,083 | 28,110 | 2.271x [1.833, 2.990] | 0.85 | 0.60 | 0.27 | 16.8 → 8.4 |
| N=1 c=32 (REFUSED) | keepalive | 21,513 | 68,406 | 3.180x [2.450, 4.585] | 0.94 | 0.93 | 0.27 | 16.8 → 8.4 |

Read beside ws23's four refused sets (close 1.067x, keepalive
1.637x at loads 4.2–9.8): the same shape, on a box that has not
been quiet for two sprints. The orchestrator's call at the bound
was no further window that night; ws24's items 2–4 are measured on
the linux runner, and the macOS rows below are indicative by the
same rule.

### 2026-09-09 · linux x86-64 · the CI runner (ubuntu-latest, 4 cpus) · ws24's series, one VALID set per step · **NOT MET on both shapes**

Each set a `parity=true` dispatch of `ci.yml` on branch `ws24` at
the named commit, 5 pairs × `ab -t 5`, c=32 over 4 generators,
nginx 1.30.4; the pin is named per row because it is what row two
changes:

| commit (change) | pin | run | load | N=4 close | N=4 keepalive | N=1 close | N=1 keepalive |
|---|---|---|---|---|---|---|---|
| `1318cfe` (trunk, the baseline) | wolf 0.2.6 (398e5f5) | 34307802770 | 1.97 | **1.981x** [1.962, 2.028] · 14,380 vs 28,783 | **3.178x** [2.954, 3.496] · 30,361 vs 97,902 | 2.917x · 6,545 vs 18,999 | 4.475x · 9,558 vs 42,625 |
| `8859ac9` (the pin: #257 syscall-first, #254 TCP_NODELAY default) | wolf 0.2.7+dev.bd7caff | 34311866103 | 1.99 | **1.300x** [1.290, 1.310] · 21,879 vs 28,454 | **1.862x** [1.852, 1.870] · 52,818 vs 98,529 | 1.464x · 13,150 vs 19,208 | 1.821x · 23,748 vs 43,052 |
| `a61faee` (one gathered write; `tcp_nodelay` served) | wolf 0.2.7+dev.bd7caff | 34316912557 | 1.91 | **1.413x** [1.396, 1.421] · 53,768 vs 75,387 | **1.929x** [1.892, 1.943] · 118,854 vs 229,209 | 1.510x · 31,097 vs 46,548 | 2.081x · 42,871 vs 89,191 |
| `a61faee` (the same, a second dispatch) | wolf 0.2.7+dev.bd7caff | 34317432651 | 1.79 | **1.439x** [1.436, 1.450] · 39,205 vs 56,515 | **2.086x** [2.056, 2.117] · 85,193 vs 178,211 | 1.649x (cell refused) | 2.318x (cell refused) |
| `8859ac9` (the pin again — a CONTROL dispatched after the gather's two, throwaway branch) | wolf 0.2.7+dev.bd7caff | 34318089358 | 1.92 | **1.296x** [1.283, 1.313] · 19,661 vs 25,612 | **1.928x** [1.860, 1.991] · 45,136 vs 87,368 | 1.317x · 11,480 vs 15,072 | 2.023x · 16,956 vs 35,176 |
| `56fa6b2` (the re-pin at the v0.2.8 TAG; the gather tree, lobo's source unchanged) | wolf 0.2.8 (5c729e8) | 34321060660 | 1.88 | **1.273x** [1.245, 1.303] · 35,472 vs 45,342 | **1.784x** [1.754, 1.860] · 90,675 vs 163,157 | 1.485x · 21,342 vs 31,676 | 1.870x · 35,358 vs 66,868 |

Six VALID sets on six runner VMs whose own nginx close rate ran
25.6k–75.4k req/s. Read in the order they were taken, the gather's
first two runs (1.41x, 1.44x on the two fastest VMs) sat ~10% above
the pin's two (1.300x, 1.296x), and the entry filed that as lobo#6;
the re-pin at the v0.2.8 tag — the same lobo source, nine wolf-lang
commits that touch nothing on the request path — then read 1.273x
on a 45k VM, the best close ratio of the series. So the honest
statement is the one ws23 made: the ratio is a same-box statistic,
and across this runner's VMs it spreads 1.27x–1.44x on close and
1.78x–2.09x on keepalive with NO change to lobo, wider than any
delta the gather could carry (a 2 µs byte loop against one list and
one syscall). No linux delta for the gather is readable off this
runner, in either direction; lobo#6 stands as the instrument that
would read one (a profile leg on linux, which nobody has run),
downgraded from a regression to an unknown. The macOS N=1 cells
(+13–16% with the gather, indicative) are the only per-request
number this sprint has for it.

lobo's cores on the N=4 close cell went 2.39 → 2.01 at the pin
(the winner's path stopped parking) while its req/s rose 52%;
keepalive held at 3.0–3.2 cores and rose 74%. nginx's own numbers
held within 2% across the series. NOT MET on both shapes, and the
keepalive cell is now the larger gap on this host for the first
time since the stall: what remains there is the accept path's
share of nothing (this is the read/serve shape) — it is the
request itself, `open` + stat + the syscalls, side by side with
nginx's `open_file_cache`-less request at ~2x.

### 2026-09-09 · macOS arm64 · nomad-1 (18 cpus) · ws24's series, one INDICATIVE set per step · **ALL REFUSED** (load 3.9–7.5 at the start, 14–20 during)

Not results (the first section of the ledger says why); recorded
so the two hosts' series read side by side. `tools/lobo-parity`
under the ws23 refusal scope, 5 pairs × `ab -t 5`, c=32 over 4
generators, nginx 1.30.4, the load beside every row:

| commit (change) | pin | load(1m) start → peak | N=18 close | N=18 keepalive | lobo / nginx cores (close · keepalive) | N=1 close | N=1 keepalive |
|---|---|---|---|---|---|---|---|
| `1318cfe` (trunk, the baseline) | 0.2.6 | 3.92 → 20.3 | 1.096x [0.937, 1.183] · 19,093 vs 20,919 | 1.623x [1.508, 1.971] · 60,950 vs 113,353 | 6.24/3.28 · 8.57/9.38 | 2.271x (cell refused) | 3.180x (cell refused) |
| `8859ac9` (the pin) | 0.2.7+dev.bd7caff | 7.53 → 14.7 | **1.010x** [0.998, 1.043] · 19,829 vs 20,210 | **1.355x** [1.322, 1.385] · 85,375 vs 117,096 | 5.35/3.40 · 10.23/11.12 | 1.039x (cell refused) | 1.775x (cell refused) |
| `a61faee` (one gathered write; `tcp_nodelay` served) | 0.2.7+dev.bd7caff | 7.43 → 16.0 | **1.014x** [0.982, 1.025] · 20,100 vs 20,497 | **1.369x** [1.352, 1.404] · 84,154 vs 115,005 | 5.37/3.51 · 10.67/11.18 | 0.987x (cell refused) · 31,321 vs 31,165 | 1.627x (cell refused) · 50,842 vs 80,576 |
| `56fa6b2` (the re-pin at the v0.2.8 TAG) | 0.2.8 (5c729e8) | 5.26 → 14.3 | **1.016x** [0.804, 1.035] · 20,781 vs 20,496 | **1.387x** [1.363, 1.458] · 85,373 vs 118,260 | 5.23/3.46 · 10.34/11.69 | 1.044x · 31,469 vs 32,394 | 1.664x · 52,104 vs 82,012 |

Read against the refused baseline: the pin took the N=18 keepalive
cell 1.62x → 1.36x and N=1 keepalive 3.18x → 1.78x; the gather
moved the N=1 cells (keepalive lobo +16%, close +13% — the copy's
share of a single hand's request) and the N=18 cells not at all
(1.355x → 1.369x, within the pair spread); the re-pin at the tag
moved nothing (1.387x / 1.016x, the same source): at eighteen hands on
this box lobo answers ~85k keepalive req/s at ~10.5 cores against
nginx's ~115k at ~11.2 either way, so what separates them there is
not the copy. Indicative, every row; a quiet set is owed.

### 2026-09-09 · macOS arm64 · nomad-1 (18 cpus) · four sets, one per ws23 change · **ALL REFUSED** (load 4.2–9.8; indicative, not a result)

Not results; recorded, as ws22's refused sets were, so the two
hosts' series can be read side by side. The box carried other
lanes' work for the whole sprint (a four-core fuzzer, a VM, a
`rustc`, s141's own lobo bench, `mediaanalysisd`); the quiet-box
waiter never saw load(1m) under 2.8 in two hours, and the sets were
taken at the loads shown. The first set was also refused on nginx's
N=18 keepalive spread (1.526); in the other three the oracle held
on both gating cells (spreads under 1.15) and only the load rule
refused. `tools/lobo-parity` under the ws23 refusal scope; 5 pairs ×
`ab -t 5`, c=32 over 4 generators, lobo 0.1.0+dev at wolf 0.2.6 pin
398e5f5, nginx 1.30.4:

| commit (change) | load(1m) | N=18 close | N=18 keepalive | lobo / nginx cores (keepalive) | N=1 close | N=1 keepalive |
|---|---|---|---|---|---|---|
| `023ec64` (trunk, the baseline) | 7.24 | 1.105x [1.048, 1.229] · 17,232 vs 19,043 | 2.550x [2.370, 2.737] · 44,864 vs 110,366 | 9.98 / 8.91 | 2.875x (cell refused) | 3.083x (cell refused) |
| `092dbf8` (one buffer, one write) | 4.19 | 1.085x [1.029, 1.097] · 18,606 vs 20,179 | **1.990x** [1.986, 2.044] · 61,082 vs 121,715 | 12.09 / 11.82 | 2.018x (cell refused) | 3.240x (cell refused) |
| `2c393b3` (three stats, not four) | 9.84 | 1.079x [1.057, 1.113] · 18,417 vs 19,891 | 2.007x [1.917, 2.053] · 60,996 vs 123,422 | 11.09 / 11.00 | 1.890x (cell refused) | 3.369x (cell refused) |
| `0e36225` (the signal poll on a budget) | 8.25 | **1.067x** [1.064, 1.076] · 18,962 vs 20,200 | **1.637x** [1.602, 1.695] · 75,482 vs 123,477 | 11.66 / 11.53 | 1.934x | 3.259x |

Against ws22's quiet set (close 1.151x, keepalive 2.761x): the
keepalive cell on this host reads 1.64x after the three changes,
the close cell 1.07x, on a loaded box. A quiet-box set is owed
before either number is a result.

### 2026-09-09 · linux x86-64 · the CI runner (ubuntu-latest, 4 cpus) · four VALID sets, one per ws23 change · **NOT MET on both shapes** (keepalive 110.7x → 3.26x)

ws23's series, each set a `parity=true` dispatch of `ci.yml` on
branch `ws23` at the named commit, 5 pairs × `ab -t 5`, c=32 over 4
generators, lobo 0.1.0+dev at wolf 0.2.6 pin 398e5f5, nginx 1.30.4.
Every set VALID (load under 2.0 after the settle loop, generators
at 0.69–0.73 cores, oracle spreads under 1.15, nothing failed). The
runner is a shared VM and the fourth set landed on a faster host
(nginx's own close went 25.9k → 36.9k req/s between the third and
fourth), which is the reason the statistic is a same-box ratio:

| commit (change) | run | load | N=4 close | N=4 keepalive | N=1 close | N=1 keepalive |
|---|---|---|---|---|---|---|
| `023ec64` (trunk, the baseline) | 34294755111 | 1.91 | **2.267x** [2.203, 2.298] · 11,127 vs 25,221 | **110.7x** [110.1, 111.2] · **781** vs 86,329 | 3.410x | 44.1x |
| `092dbf8` (one buffer, one write) | 34296065145 | 1.90 | **1.971x** [1.941, 1.985] · 12,891 vs 25,281 | **3.315x** [3.215, 3.503] · 26,189 vs 86,903 | 2.695x | 4.525x |
| `2c393b3` (three stats, not four) | 34296624364 | 1.85 | **1.952x** [1.925, 1.983] · 13,253 vs 25,890 | **3.297x** [3.066, 3.522] · 27,102 vs 89,083 | 2.684x | 4.519x |
| `0e36225` (the signal poll on a budget) | 34297057715 | 1.71 | **2.038x** [1.939, 2.156] · 18,224 vs 36,935 | **3.258x** [3.183, 3.525] · 39,190 vs 127,701 | 2.968x | 4.419x |

lobo's cores on the N=4 keepalive cell went 0.18 (the stall: the
hands were idle) → 3.13–3.14; on close 2.52 → 2.35–2.45; nginx's
held at 1.56–1.59 and 2.45–2.46. The keepalive row is a throughput
number for the first time on linux; what remains there is the
runtime's reactor round-trip (wolf-lang#257) and, on the close
shape, the accept path.

### 2026-09-08 · macOS arm64 · nomad-1 (18 cpus) · QUIET BOX · **NOT MET on both shapes** (the set refused on the non-gating cell only)

Taken after the last sibling lane (is39) left the box: load(1m)
2.55 at the start, 5 pairs × `ab -t 5`, c=32 over 4 generators,
lobo 0.1.0+dev at wolf 0.2.6 pin 398e5f5, nginx 1.30.4
(`ws22-quiet-remeasure.log`):

| cell | shape | lobo req/s | nginx req/s | nginx ÷ lobo median [min, max] | lobo cores | nginx cores | ab max |
|---|---|---|---|---|---|---|---|
| **N=18 c=32** | close | 18,126 | 20,869 | **1.151x** [1.128, 1.189] | 8.17 | 3.65 | 0.36 |
| **N=18 c=32** | keepalive | 44,622 | 121,942 | **2.761x** [2.652, 2.771] | 12.73 | 11.95 | 0.36 |
| N=1 c=32 | close | 13,102 | 31,788 | 2.419x [2.243, 2.645] | 0.95 | 0.64 | 0.30 |
| N=1 c=32 | keepalive | 17,704 | 69,902 | 3.991x [3.056, 4.018] | 0.99 | 0.94 | 0.30 |

The tool refused the set on one count: nginx's five N=1
keepalive numbers spread 1.298 max/min, on the non-gating cell, and
that is the single-process P-core/E-core swing this box has shown in
every set today. Both gating cells were stable (spreads under 1.15),
the generators were at 0.36 cores, nothing failed, the load was under
the rule. The verdict on the gating cells is therefore reported:
close 1.151x and keepalive 2.761x at N=18, NOT MET on macOS,
with the caveat that the tool's refusal scope (any cell vs the
gating cells) is a definition question ws23 should settle BEFORE its
next set, in writing, and not by looking at this table. Read against
0.1.0's table: the close gap on this host narrowed from 1.50x to
1.15x with nothing changed in lobo (the old number was one
20,000-request run), and the keepalive gap is 2.76x, not 2.15x,
because the old nginx number was `ab`'s ceiling.

### 2026-09-08 · linux x86-64 · the CI runner (ubuntu-latest, 4 cpus) · **VALID** · **NOT MET on both shapes**

`ci.yml` run 34251691870 (workflow_dispatch, `parity=true`), load(1m)
1.89 after the settle loop, 5 pairs × `ab -t 5`, c=32 over 4
generators, lobo 0.1.0+dev at wolf 0.2.6 pin 398e5f5, nginx 1.30.4:

| cell | shape | lobo req/s | nginx req/s | nginx ÷ lobo median [min, max] | lobo cores | nginx cores |
|---|---|---|---|---|---|---|
| **N=4 c=32** | close | 11,067 | 25,031 | **2.269x** [2.198, 2.339] | 2.52 | 1.56 |
| **N=4 c=32** | keepalive | **781** | 86,528 | **110.9x** [110.0, 112.7] | 0.2 | — |
| N=1 c=32 | close | 4,461 | 15,006 | 3.394x [3.258, 3.584] | 0.99 | 0.99 |
| N=1 c=32 | keepalive | 781 | 34,445 | 44.1x [43.5, 44.8] | 0.17 | — |

The keepalive row measures a stall: 781
req/s over 32 connections is one request per 41 ms per connection,
which is linux's 40 ms delayed ACK meeting Nagle on lobo's two-write
response (lobo#3, wolf-lang#254). The cores column on this host is
the first-run `ps` whole-second reading; later sets read `/proc`. The
FIRST linux set (run 34250530750, one generator) was REFUSED on load
3.01 at start and `ab` at 1.00–1.04 cores, and its lobo keepalive
number was the same 780; its nginx close number (13,394) was the
single generator's ceiling, not nginx's: with four generators nginx
answers 25,031 on the same cell, and the close gap on linux is
2.27x, not the 1.26x the refused set had suggested. That is what the
generator rule is for.

### 2026-09-08 · macOS arm64 · nomad-1 (18 cpus) · **REFUSED** (one generator; the oracle unstable at N=1) · TAKEN UNDER SIBLING-LANE LOAD

Not a result; recorded because it is the first set ever taken against
the bar and the refusal is the bar working. load(1m) 2.52, 5 pairs ×
`ab -t 5 -c 32`, ONE generator:

| cell | shape | lobo | nginx | median [min, max] | lobo cores | nginx cores | ab max |
|---|---|---|---|---|---|---|---|
| N=18 c=32 | close | 19,426 | 20,993 | 1.167x [1.063, 1.270] | 7.40 | 3.26 | 0.93 |
| N=18 c=32 | keepalive | 43,927 | 112,100 | 2.533x [2.212, 3.480] | 12.48 | 8.46 | **0.93** |
| N=1 c=32 | close | 9,191 | 28,691 | 3.049x [2.250, 5.117] | 0.86 | 0.71 | 0.84 |
| N=1 c=32 | keepalive | 10,463 | 39,813 | 3.874x [2.422, 6.083] | 0.82 | 0.80 | 0.84 |

Refused on: `ab` at 0.93 cores on the N=18 keepalive runs (the
generator was the ceiling; nginx's 112k is `ab`'s number); nginx's
five N=18 close runs spread 1.215 max/min; nginx's N=1 runs spread
1.52 (close) and 2.05 (keepalive). Single-worker numbers on this box
swing 2x run to run (20.7k → 31.4k close; 28.6k → 58.7k keepalive),
which looks like the scheduler landing one process on an efficiency
core or a performance core, and is a host fact the N=1 cell will
have to live with here (the bar does not gate on N=1).

### 2026-09-08 · macOS arm64 · nomad-1 (18 cpus) · **REFUSED** (load 4.35; four generators) · TAKEN UNDER SIBLING-LANE LOAD

The k=4 set, armed behind a waiter for load < 2.9 that a sibling
lane's corpus loop never let clear; taken after a bounded wait at
load(1m) 4.35 so the sprint would at least have the shape of the
number, and refused by the tool on that load and on nginx's
spread (N=18 close 1.204, N=1 keepalive 1.819). Indicative, not a
result:

| cell | shape | lobo | nginx | median [min, max] | lobo cores | nginx cores | ab max |
|---|---|---|---|---|---|---|---|
| N=18 c=32 | close | 18,210 | 18,515 | **1.017x** [0.941, 1.099] | 7.59 | 3.21 | 0.33 |
| N=18 c=32 | keepalive | 43,205 | 117,023 | **2.593x** [2.587, 2.866] | 10.82 | 11.06 | 0.33 |
| N=1 c=32 | close | 11,628 | 27,925 | 2.373x [2.181, 2.502] | 0.91 | 0.65 | 0.30 |
| N=1 c=32 | keepalive | 16,123 | 58,744 | 3.734x [2.413, 3.927] | 0.95 | 0.90 | 0.30 |

Two things this refused set still says, to be confirmed on a quiet
box: with the generator out of the way nginx's keepalive at eighteen
workers is ~117k on this box (the 0.1.0 table's 83k was `ab`'s
ceiling), so the macOS keepalive gap is ~2.6x, not 2.15x; and on the
close shape at eighteen hands lobo and nginx are within noise of each
other here (1.02x, min 0.94) at 2.4x nginx's cpu, which the herd
(`docs/PROFILE.md`) accounts for. A valid macOS set needs a box
nobody else is using; the tool refuses until it gets one.
