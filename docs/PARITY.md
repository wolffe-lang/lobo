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

### 2026-09-10 · linux x86-64 · the CI runner (ubuntu-latest, 4 cpus) · ws28: the head memo and the byte views ÷ the pin, ONE VM · **VALID** · **NOT MET on both shapes** (close 1.161x, keepalive 1.286x on the slow class)

The ws25 instrument, run 34536710553 (`parity=true ref_tree=c58b4f1
ref_name=pin this_name=ws28`, the profile leg on the keepalive shape
and the count leg in the same job), load 1.72, nginx close **25.2k**
— the runner's SLOWEST class (the ws27 pin set's, 25.2k), so the
ratios sit where that class puts them and the DELTA is the number.
`ws28` is `8a14d2a` (the ws28 CHANGELOG entry: the response head
memoized beside the kind table, the path and the header names as
views, the reader adopting the read, no trace lists on the route, no
histogram list per observation), `pin` is trunk `c58b4f1`, both at
wolf 0.2.9, nginx 1.30.4, 5 pairs × `ab -t 5`, c=32 over 4
generators:

| cell | shape | ws28 req/s | pin req/s | nginx req/s | nginx ÷ ws28 median [min, max] | nginx ÷ pin | **ws28 ÷ pin** median [min, max] | ws28 / pin / nginx cores |
|---|---|---|---|---|---|---|---|---|
| **N=4 c=32** | close | 21,920 | 20,273 | 25,242 | **1.161x** [1.134, 1.168] | 1.247x [1.225, 1.265] | **1.081x** [1.074, 1.089] | 1.79 / 1.92 / 1.62 |
| **N=4 c=32** | keepalive | 66,790 | 51,044 | 85,874 | **1.286x** [1.281, 1.298] | 1.687x [1.657, 1.693] | **1.306x** [1.288, 1.322] | 2.62 / 2.84 / 2.46 |
| N=1 c=32 | close | 14,688 | 12,028 | 14,851 | 1.021x [0.987, 1.041] | 1.240x [1.214, 1.267] | **1.218x** [1.190, 1.256] | 1.00 / 1.00 / 0.99 |
| N=1 c=32 | keepalive | 29,307 | 18,394 | 33,748 | 1.163x [1.145, 1.190] | 1.824x [1.791, 1.870] | **1.551x** [1.534, 1.624] | 1.00 / 1.00 / 1.00 |

PREDICTED before the dispatch (the CHANGELOG entry): N=1 keepalive
+8% [+4, +14], N=4 keepalive +7% [+3, +12], N=4 close +3% [0, +6],
N=1 close +3% [0, +6]; the ratio on the fast class keepalive 1.82x →
~1.70x. MEASURED: **+30.6% on the N=4 keepalive cell, +55.1% at N=1
keepalive, +8.1% and +21.8% on the close cells** — every cell past
the top of its band by a factor of two to four, with the bands
[1.288, 1.322] and [1.534, 1.624] not touching 1.0 anywhere. The
prediction priced the string runtime at the ~13% of a keepalive
request ws27's `perf` leaves had summed (`malloc`/`cfree`/`realloc`
~4.7, `ambient_alloc` + `strbuf_str` 3.2, `find`/`to_lowercase` 2.2,
the page faults 3.1) and took ~80% of that; what it did not price is
what those leaves were NOT counting — the inclusive cost of ~110
arena bumps behind a mutex, ~245 libc calls and 6.4 KB of copies per
request spread over the kernel's own `brk`/fault path and the cache
lines they pushed out — and the profile leg in the same job says so:
one hand under `ab -k` answered **31,047 req/s** (ws28) against
**18,625** (pin) in the perf window, the dso split moved from kernel
64.1 / lobo 22.6 / libc 13.1 to **74.4 / 18.2 / 6.9**, and the count
leg read the syscalls per request UNCHANGED (keepalive 6.37 against
nginx's 6.14, close 12.38 against 10.13; `brk` 0.04 → 0.01 is the
arena growing slower). NOT MET on both shapes; what moved is the
keepalive cell on this class, **1.687x → 1.286x** on one VM, and the
close cell 1.247x → 1.161x. W8's linux standing after ws28: NOT MET,
close ~1.16x and keepalive ~1.29x on the slow class (the fast class
is not re-measured this sprint); macOS: ws26's MET, indicative at
ws28 (the entry below).

### 2026-09-10 · macOS arm64 · nomad-1 (18 cpus) · ws28: the head memo and the byte views ÷ the pin, two trees · **REFUSED** (load 5.26; indicative, not a result)

The ws25 two-tree instrument on the box the user's daemons held all
day (no quiet window confirmed), 22:18Z, load(1m) 5.26 at the start,
refused by the tool on load and on nginx's N=18 keepalive spread
(1.182), read for SHAPE only: `ws28` is `8a14d2a` (the ws28 CHANGELOG
entry — the response head memoized beside the kind table, the path
and the header names as views, the reader adopting the read, no
trace lists on the route, no histogram list per observation), `pin`
is trunk `c58b4f1`, both at wolf 0.2.9 with the same staged pair,
nginx 1.30.4, 5 pairs × `ab -t 5`, c=32 over 4 generators:

| cell | shape | ws28 req/s | pin req/s | nginx req/s | nginx ÷ ws28 median [min, max] | nginx ÷ pin | **ws28 ÷ pin** median [min, max] | ws28 / pin / nginx cores |
|---|---|---|---|---|---|---|---|---|
| N=18 c=32 | close | 18,752 | 18,652 | 18,382 | 0.977x [0.922, 1.004] | 0.977x [0.955, 0.995] | **1.017x** [0.973, 1.058] | 4.54 / 4.69 / 3.09 |
| N=18 c=32 | keepalive | 101,357 | 97,668 | 103,243 | 1.007x [0.985, 1.091] | 1.045x [0.992, 1.058] | **1.038x** [0.909, 1.054] | 8.46 / 8.56 / 9.76 |
| N=1 c=32 | close | 29,504 | 28,828 | 29,906 | 1.065x [1.002, 1.296] | 1.016x [0.957, 1.167] | 0.956x [0.868, 1.096] | 0.70 / 0.78 / 0.60 |
| N=1 c=32 | keepalive | 68,499 | 53,528 | 75,453 | 1.115x [1.034, 1.546] | 1.419x [1.344, 1.440] | **1.280x** [0.918, 1.300] | 0.95 / 0.95 / 0.95 |

PREDICTED (the CHANGELOG entry, before the set): N=1 keepalive +8%
[+4, +14], N=4/18 keepalive +7% [+3, +12], close +3% [0, +6] on both.
Read: the one-hand keepalive cell — the cell the profile was taken
on — moved **+28%** (median; the band is the P/E-core swing this box
puts on every N=1 row), past the top of its band; the eighteen-hand
cells +1.7% and +3.8%, the shape predicted (the hands are not cpu-
bound on this box: 8.5 cores for 100k req/s, the herd and the kernel
in front of the strings); the N=1 close cell is noise either way.
The cores column is the reading the load cannot fake: ws28 serves the
same req/s with fewer cores on every cell (4.54 vs 4.69, 8.46 vs
8.56, 0.70 vs 0.78). The macOS standing remains ws26's (MET on both
shapes; indicative at 0.2.9 and at ws28).

### 2026-09-10 · linux x86-64 · the CI runner (ubuntu-latest, 4 cpus) · ws27: the warm kind table ÷ the pin, ONE VM · **VALID** · **NOT MET on both shapes** (close 1.365x, keepalive 1.822x on the fast class)

The ws25 instrument, run 34506393898 (`parity=true ref_tree=9a24fde
ref_name=pin this_name=warm`, the count leg in the same job), load
1.95, nginx close **77.2k** — the runner's fastest class (ws24 met it
once at 75.4k), so the ratios sit where that class puts them and the
DELTA is the number. `warm` is `e568707` + its interface commit (the
router remembers a path's regular-file answer for one second; the
CHANGELOG's ws27 entry), `pin` is `9a24fde` (the v0.2.9 pin, nothing
else), both at wolf 0.2.9:

| cell | shape | warm req/s | pin req/s | nginx req/s | nginx ÷ warm median [min, max] | nginx ÷ pin | **warm ÷ pin** median [min, max] | warm / pin / nginx cores |
|---|---|---|---|---|---|---|---|---|
| **N=4 c=32** | close | 56,369 | 55,357 | 77,200 | **1.365x** [1.346, 1.409] | 1.398x [1.365, 1.449] | **1.021x** [1.011, 1.049] | 2.02 / 2.03 / 1.60 |
| **N=4 c=32** | keepalive | 129,474 | 125,874 | 233,456 | **1.822x** [1.744, 1.834] | 1.855x [1.820, 1.884] | **1.027x** [0.993, 1.049] | 2.88 / 2.93 / 2.38 |
| N=1 c=32 | close | 32,789 | 32,601 | 48,325 | 1.481x [1.438, 1.497] | 1.471x [1.468, 1.499] | 1.003x [0.983, 1.027] | 0.99 / 0.99 / 0.99 |
| N=1 c=32 | keepalive | 46,666 | 46,211 | 87,761 | 1.880x [1.849, 1.934] | 1.899x [1.855, 2.085] | 1.006x [0.979, 1.109] | 1.00 / 1.00 / 1.00 |

One syscall fewer per request (`tools/lobo-syscalls`, same job:
`statx` 2 → 1, keepalive 6.31 vs nginx 6.13, close 12.41 vs 10.13)
read as **+2.1% on the close cell and +2.7% on the keepalive cell**
at N=4, inside the bands predicted before the dispatch (+1.5% [0, 3]
and +3.5% [1.5, 5.5]); the N=1 cells +0.3% and +0.6% (the keepalive
one under its +3% [1, 5] band). ws25's ~3.5% per call was three
calls on the 28k class; one call on the 77k class is ~2–3%. NOT MET
on both shapes. What the count leaves: 6.31 calls against 6.13 and
1.82x slower on keepalive — the gap on this cell is not in the
number of calls (`docs/PROFILE.md`, ws27's addendum: a third of the
request is the string runtime, the rest the kernel's per-call cost
and the transmit path nginx pays too). macOS, the same two trees,
indicative (load 6.18, refused): warm ÷ pin N=18 close 0.993x
[0.977, 0.998], N=18 keepalive 1.035x [0.965, 1.306], N=1 close
0.997x, N=1 keepalive 1.025x — the same sign on keepalive, noise on
close.

### 2026-09-10 · linux x86-64 · the CI runner (ubuntu-latest, 4 cpus) · ws27: the v0.2.9 pin, ONE tree · **VALID** · **NOT MET on both shapes** (close 1.255x, keepalive 1.718x)

The pin moved (wolf 0.2.8 → 0.2.9, lupin 0.1.27 → 0.1.29; nothing on
the request path — the ws27 CHANGELOG entry classes the train) and
the linux standing was re-taken as a single-tree set, run 34504504973
(`parity=true`, plus the profile and count legs in the same job),
load 1.99, lobo `9a24fde` (0.1.0+dev at wolf 0.2.9 pin 4c60946),
nginx 1.30.4, 5 pairs × `ab -t 5`, c=32 over 4 generators. nginx's
own close rate names the VM class: **25.2k**, the slowest class ws24
met (its control run read 25.6k; the ws25 rows sat on the 28–29k
class), so the ratio and not the rate is the number:

| cell | shape | lobo req/s | nginx req/s | nginx ÷ lobo median [min, max] | lobo cores | nginx cores | ab max |
|---|---|---|---|---|---|---|---|
| **N=4 c=32** | close | 20,086 | 25,214 | **1.255x** [1.245, 1.262] | 1.96 | 1.57 | 0.71 |
| **N=4 c=32** | keepalive | 49,711 | 85,423 | **1.718x** [1.704, 1.752] | 2.87 | 2.46 | 0.71 |
| N=1 c=32 | close | 11,979 | 14,925 | 1.246x [1.229, 1.296] | 1.00 | 0.99 | 0.41 |
| N=1 c=32 | keepalive | 19,332 | 34,415 | 1.771x [1.658, 1.883] | 1.00 | 1.00 | 0.41 |

PREDICTED before the dispatch (the CHANGELOG entry): close 1.26x
[1.22, 1.32], keepalive 1.65x [1.58, 1.75] on the 28–29k class;
measured 1.255x and 1.718x on a slower class, both inside the
bands, the keepalive cell at the band's top edge — the pin carries
nothing, and a slower VM widens the keepalive cell (ws24's series
read 1.78–2.09x on keepalive across classes). The generators sat at
0.71 cores on the N=4 cells, under the 0.90 ceiling and the highest
this ledger has recorded on the runner (a slow VM class costs ab
too). NOT MET on both shapes; W8's linux standing is unchanged by
the pin. The count leg and the profile leg of the same run are in
`docs/PROFILE.md` (ws27's addendum).

### 2026-09-10 · macOS arm64 · nomad-1 (18 cpus) · ws27: the v0.2.9 pin · **REFUSED** (load 5.31; indicative, not a result)

The box carried the user's daemons all day (the Photos indexer,
per the orchestrator) and no window was confirmed, so the pin's
macOS set is indicative by the rule: lobo `9a24fde` at wolf 0.2.9,
nginx 1.30.4, 16:50Z, load(1m) 5.31 at the start, 5 pairs × `ab -t
5`, c=32 over 4 generators, refused by the tool on load only (exit
3; the oracle held, nothing failed, ab at 0.36 cores):

| cell | shape | lobo req/s | nginx req/s | nginx ÷ lobo median [min, max] | lobo cores | nginx cores |
|---|---|---|---|---|---|---|
| N=18 c=32 | close | 20,595 | 21,306 | 1.032x [1.002, 1.091] | 5.52 | 3.79 |
| N=18 c=32 | keepalive | 106,929 | 118,550 | 1.066x [0.995, 1.169] | 9.77 | 11.53 |
| N=1 c=32 | close | 32,734 | 33,078 | 0.995x [0.943, 1.125] | 0.77 | 0.59 |
| N=1 c=32 | keepalive | 55,174 | 87,068 | 1.522x [1.477, 2.970] | 0.96 | 0.97 |

Read for shape only: ws26's VALID standing (close 1.033x, keepalive
1.072x, N=1 close 0.985x, N=1 keepalive 1.474x) to the hundredth on
every cell, on a box three times as loaded — the pin moves nothing
here either. The macOS standing remains ws26's (MET on both shapes);
a VALID set at 0.2.9 is owed to the ledger by the next lane that
gets a quiet window.

### 2026-09-09 · macOS arm64 · nomad-1 (18 cpus) · ws26: THE QUIET SET · **VALID (3 of 4)** · **MET on both shapes** (close 1.033x, keepalive 1.072x)

The set this ledger has owed since ws22. The box went quiet at
20:20Z — the first time in three waves — and four sets were taken at
trunk `d0a1e67` (lobo 0.1.0+dev, wolf 0.2.8 pin 5c729e8, nginx
1.30.4), load(1m) read and recorded before each, the box let back
down to under 3.0 between them. THREE were VALID and one was
REFUSED by the tool on the gating cell's oracle spread; the refused
set is named below and is not averaged into anything:

| set | load(1m) at start | N=18 close | N=18 keepalive | N=1 close | N=1 keepalive | verdict |
|---|---|---|---|---|---|---|
| 1 · 20:32Z | **1.83** | **1.033x** [1.026, 1.074] · 21,476 vs 22,183 | **1.071x** [1.052, 1.093] · 114,063 vs 122,499 | 0.985x [0.965, 1.042] | 1.474x [1.437, 1.517] | **VALID** |
| 2 · 20:38Z | **2.71** | **1.032x** [1.010, 1.077] · 21,508 vs 22,206 | **1.084x** [1.066, 1.090] · 112,123 vs 121,937 | 0.989x [0.959, 0.998] | 1.483x [1.469, 1.529] | **VALID** |
| 3 · 20:43Z | **2.65** | **1.056x** [1.014, 1.060] · 21,173 vs 22,352 | **1.072x** [1.069, 1.075] · 113,241 vs 121,333 | 0.964x [0.909, 1.051] | 1.431x [1.338, 1.928] | **VALID** |
| 4 · 20:49Z | 2.81 | 1.009x [0.908, 1.114] | 1.064x [1.027, 1.160] | 0.986x | 1.482x | **REFUSED** — nginx N=18 close spread 1.168 > 1.15 |

Cores (Σ cpu ÷ wall over the server's tree, `ps(1)`), the three
valid sets: N=18 close lobo 6.04–6.10 against nginx 4.15–4.26; N=18
keepalive lobo 9.93–10.37 against nginx **12.46–12.62**; N=1 both
shapes lobo 0.78–0.99, nginx 0.58–0.97. Every generator sat at
0.26–0.38 cores, far under the 0.90 ceiling; nothing failed on any
run of any set.

**The standing, from the VALID rows only.** Median of the three set
medians, with the across-set range and the per-pair envelope beside it:

| cell | shape | nginx ÷ lobo (median of 3 sets) | across-set range | per-pair envelope | bar | verdict |
|---|---|---|---|---|---|---|
| **N=18 c=32** | close | **1.033x** | [1.032, 1.056] | [1.010, 1.077] | 1.10 | **MET** |
| **N=18 c=32** | keepalive | **1.072x** | [1.071, 1.084] | [1.052, 1.093] | 1.10 | **MET** |
| N=1 c=32 | close | 0.985x | [0.964, 0.989] | [0.909, 1.051] | — | (does not gate) |
| N=1 c=32 | keepalive | 1.474x | [1.431, 1.483] | [1.338, 1.928] | — | (does not gate) |

**W8 is MET on macOS arm64, on both shapes**: close 1.033x is 6.1%
inside the 1.10 bar, keepalive 1.072x is 2.5% inside it. Three
independent sets agree to ±1.2% (close) and ±0.6% (keepalive), which
is tighter than the bar's own margin on the keepalive cell — the
verdict does not rest on one set landing well.

Read against every macOS row below it, the finding is that **the load
was the whole story on this host.** lobo's N=18 keepalive rate is
113k req/s here against ~85k in ws24's and ws25's indicative sets on
a box at load 5–11, while nginx's own number moved only 115k → 122k;
the keepalive gap that read 2.76x (ws22, load 2.55), 1.62x (ws24's
baseline) and 1.36–1.39x (ws24's pin and gather rows) is **1.07x**
when nobody else is on the box. Nothing in lobo changed between
ws25's macOS sets and these — trunk `d0a1e67` is ws25's docs commit,
and the last source commit under it is ws25's `0f2aa93`. The prior
macOS numbers were a measurement of the other lanes, which is
precisely what the quiet-rig rule was written to refuse, and it
refused them.

Two things on this table are new and are not the bar's business:
on the keepalive gating cell lobo reaches 1.07x while burning
**fewer** cores than nginx (10.2 against 12.5), the first cell in
this ledger where it is nearer on both axes at once; and at N=1 on
the close shape lobo is **faster** than nginx (0.985x median, 34.4k
against 34.0k), the first sub-1.0 cell the informative row has held.
The N=1 keepalive cell remains the one place this host is 1.47x
adrift, and it is the per-request read/serve cost with no
distribution in the way — the number a profile leg should take next.

**W8 overall is NOT met**, because W8 is both hosts and linux is not
met: ws25's rows read close 1.258x and keepalive 1.652x on the CI
runner's VM class. macOS is met; linux is the gap, and the keepalive
cell there is the larger half of it.

*The oracle had to be rebuilt to take these sets.* The pinned
nginx binary was absent from this box (`tests/differential/bin/` is
gitignored and the machine's copy was gone; the cached source tree
under the shared scratchpad had been emptied by a disk reclaim), and
`tools/lobo-parity` refused every set by name — `REFUSED — pinned
nginx missing`, exit 1 — until it was restored. It was rebuilt by
`docs/DIFFERENTIAL.md`'s one-time recipe at the pinned version, the
tarball's SHA-256 verified against `tests/differential/NGINX-PIN`
(`4261dc9…a08b`, exact match) and `bin/nginx -v` reading
`nginx/1.30.4`. The build was `make -j6` and cost the box under a
minute at load 2.3; the sets began from load 1.83.

### 2026-09-09 · linux x86-64 · the CI runner (ubuntu-latest, 4 cpus) · ws25: TWO TREES ON ONE VM · **VALID** · the gather read (lobo#6 closed)

The instrument ws24 said nobody had: `tools/lobo-parity` with
`LOBO_REF` (and `ci.yml`'s `ref_tree`) builds two lobos beside each
other with the same staged toolchain and runs THREE fresh servers per
pair on one VM — this tree, the reference, nginx, the two lobos
alternating their order pair by pair — so the delta this ÷ ref is a
same-box statistic with its own min and max, read against that VM's
own nginx. Run 34355608599 (`parity=true ref_tree=ws25-copy-arm`),
load 1.81, 5 pairs × `ab -t 5`, c=32 over 4 generators, nginx 1.30.4;
`gather` is trunk `7c99905` (ws24's `net_writev`), `copy` is the
throwaway `ws25-copy-arm` `965ddda` (the same tree with ws23's
byte-by-byte copy back on the plaintext small arm), both at wolf
0.2.8:

| cell | shape | gather req/s | copy req/s | nginx req/s | nginx ÷ gather median [min, max] | nginx ÷ copy | **gather ÷ copy** median [min, max] | gather / copy / nginx cores |
|---|---|---|---|---|---|---|---|---|
| **N=4 c=32** | close | 21,924 | 21,696 | 28,337 | **1.301x** [1.282, 1.315] | 1.310x [1.286, 1.334] | **1.005x** [1.003, 1.017] | 2.00 / 2.01 / 1.60 |
| **N=4 c=32** | keepalive | 53,509 | 52,708 | 97,812 | **1.820x** [1.809, 1.876] | 1.857x [1.843, 1.900] | **1.020x** [1.001, 1.034] | 2.95 / 2.95 / 2.43 |
| N=1 c=32 | close | 13,255 | 13,206 | 18,984 | 1.433x [1.424, 1.553] | 1.447x [1.399, 1.520] | 0.998x [0.977, 1.031] | 1.00 / 1.00 / 0.99 |
| N=1 c=32 | keepalive | 23,571 | 23,063 | 43,651 | 1.846x [1.820, 1.881] | 1.872x [1.825, 1.926] | 1.014x [0.971, 1.058] | 1.00 / 1.00 / 1.00 |

The delta's own pair spread on the gating cells is ±1.5%: this
instrument reads to ~2% where the six-VM series spread 13%. The
gather is +0.5% (close) and +2.0% (keepalive) over the copy on this
host, within noise at N=1 — not the ~10% worse lobo#6 was filed on
(two VM classes, as ws24's correction said) and not the +10–15%
this sprint predicted from macOS's refused N=1 cells. The number is
the PARITY leg's; the profile leg (`tools/lobo-profile`, `strace -c`
on the one serving process under the close shape, same run) confirms
the shape without a rate: 10,972 `writev` where the copy has 11,065
`sendto`, every other count per request identical. Beside the ws24
series: this VM's nginx close 28.3k is the pin run's class, and the
ratio 1.301x is that run's 1.300x to a thousandth. NOT MET on both
shapes; W8's linux standing is unchanged by a lane that built an
instrument and moved two path stats.

### 2026-09-09 · linux x86-64 · the CI runner (ubuntu-latest, 4 cpus) · ws25: `fs_fstat` ÷ the gather, ONE VM · **VALID** · **NOT MET on both shapes** (close 1.258x, keepalive 1.652x)

The same instrument, run 34362397588 (`parity=true ref_tree=7c99905`),
load 1.95, nginx close 28,860 (the same VM class as the row above),
`fstat` = ws25 `0f2aa93` (open first, kind/size/mtime off the handle,
every arm reads through it), `gather` = trunk `7c99905`:

| cell | shape | fstat req/s | gather req/s | nginx req/s | nginx ÷ fstat median [min, max] | nginx ÷ gather | **fstat ÷ gather** median [min, max] | fstat / gather / nginx cores |
|---|---|---|---|---|---|---|---|---|
| **N=4 c=32** | close | 22,956 | 22,094 | 28,860 | **1.258x** [1.240, 1.277] | 1.306x [1.288, 1.326] | **1.038x** [1.036, 1.041] | 1.94 / 2.00 / 1.60 |
| **N=4 c=32** | keepalive | 59,626 | 53,985 | 98,291 | **1.652x** [1.638, 1.671] | 1.832x [1.806, 1.846] | **1.105x** [1.094, 1.111] | 2.86 / 2.95 / 2.43 |
| N=1 c=32 | close | 14,277 | 13,286 | 19,190 | 1.347x [1.304, 1.396] | 1.434x [1.401, 1.487] | 1.090x [1.023, 1.100] | 1.00 / 1.00 / 0.99 |
| N=1 c=32 | keepalive | 26,887 | 23,318 | 42,806 | 1.601x [1.576, 1.633] | 1.841x [1.779, 1.883] | 1.129x [1.127, 1.171] | 1.00 / 1.00 / 1.00 |

Three syscalls fewer per file request (`strace -c`, same run: `statx`
4 → 2, `read` 2 → 1, ~15.3 → ~12.2 calls per request) read as
**+3.8% on the close cell and +10.5% on the keepalive cell** at
N=4, +9–13% at N=1, every delta's spread under ±2%. ws23's "within
noise" does NOT hold on the syscall-first runtime on linux: with
the reactor trips gone, three kernel entries are a tenth of a
keepalive request. Above this sprint's prediction (~1.03x) by the
same reasoning error as lobo#6's, in the other direction — a
syscall on this VM costs more of a request than a macOS `sample`
leaf share suggested. W8's linux cells move 1.301x → 1.258x and
1.820x → 1.652x on this VM class; NOT MET on both, the keepalive
cell still the larger gap.

### 2026-09-09 · macOS arm64 · nomad-1 (18 cpus) · ws25's two-tree sets · **ALL REFUSED** (load 7.8–8.2; indicative, not a result)

The same two-tree tool on this box, `LOBO_THIS`/`LOBO_REF` naming
two scratch worktrees' binaries, taken under the other lanes'
gauntlets with no window announced (the orchestrator said the floor
had not moved). The N=1 cells refused on their own spread as ever:

| trees (this ÷ ref) | load(1m) | N=18 close | N=18 keepalive | this ÷ ref N=18 close | this ÷ ref N=18 keepalive | N=1 close (refused) | N=1 keepalive (refused) |
|---|---|---|---|---|---|---|---|
| gather `7c99905` ÷ copy `965ddda` | 7.81 | 0.991x · 20,085 vs nginx 19,403 | 1.375x · 85,599 vs 115,830 | **0.989x** [0.976, 1.036] | **0.999x** [0.986, 1.095] | 0.998x [0.491, 1.109] | 1.126x [0.618, 1.176] |
| fstat (ws25, `fs_fstat` on the small and streamed arms) ÷ gather `7c99905` | 9.77 | 1.008x · 11,781 vs nginx 11,723 | 1.145x · 58,502 vs 69,980 | **1.016x** [0.998, 1.026] | 1.102x [0.628, 1.544] | 0.980x [0.920, 1.019] | 1.082x [1.002, 1.104] |

Read for shape only: the gather is nothing at eighteen hands here
(ws24's reading, again), and the fstat arm is +1.6% on the close
cell with a tight spread and unreadable on the keepalive cell (the
box was at load 9.8 with nginx's own numbers swinging 2x between
pairs). The linux rows above are the result; these say the two hosts
do not disagree.

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
