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
