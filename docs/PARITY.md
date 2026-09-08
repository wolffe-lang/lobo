# Parity (W8) — the bar, written before the measurement

**Dated 2026-09-08 (ws22).** Everything under *The bar* below was
written BEFORE this sprint ran a single benchmark. The numbers the
repo already held — 0.1.0's 1.50x on the close shape and 2.15x on
keepalive, from ws18's table in `docs/WORKERS.md` — are the reason a
bar is needed, not its input. A sprint that moves the bar does so in
a commit that says why, and any closeout reporting against it names
the bar's date. A campaign that picks its bar after seeing results
has measured nothing.

The tool that measures the bar exactly as written is
`tools/lobo-parity`. It is NOT a gauntlet step: a number depends on
the box. Its table goes into the ledger at the foot of this page,
dated, host-named, load-quoted.

## The bar

### The workload — the differential's own

- One static file, **1 KiB** (sixteen 64-byte lines — the file
  `tools/lobo-prefork-bench` has served since ws16), `text/html`,
  `GET /index.html HTTP/1.1`, loopback.
- **No access log on either side.** nginx: `access_log off`. lobo:
  no `access_log` directive, and absent one lobo writes no access
  log (`src/config/logconf.lu`'s named delta). Logging is a cost
  and a different shape; it is not this one.
- The oracle is the **pinned nginx** (`tests/differential/NGINX-PIN`),
  the same binary the differential runs, `worker_processes N`, the
  `events` block empty (the platform default: kqueue here, epoll on
  linux), every other directive nginx's default.
- lobo is the **release-tier binary the gauntlet builds**
  (`target/lobo-release`; `WOLF_MIDEND=0` until wolf-lang#146 closes
  — the shipped build, flag for flag), `worker_processes N`, every
  other directive lobo's default.

### The shapes — both gate

- **close** — one connection per request (`ab` without `-k`; the
  client closes after each reply). The accept path plus one request.
- **keepalive** — `ab -k`; every connection is reused for the whole
  run. The read/serve path.

lobo's gap is not one number — 1.50x on one shape and 2.15x on the
other at 0.1.0 — and a bar that averaged them would hide the worse
one. Each shape is met or not met on its own.

### The cells

| cell | N (`worker_processes`, both servers) | c (`ab -c`) | gates? |
|---|---|---|---|
| the bar | the host's cpu count | 32 | **yes** |
| per-process | 1 | 32 | no — reported every time |

- **N = cpus** is the stranger's configuration (`worker_processes
  auto` is what a twenty-year nginx user writes), and it is the cell
  where lobo's distribution across hands is part of the answer.
- **N = 1** is informative and always printed: the two event loops
  side by side with no distribution question in the way. It is the
  per-request cost, and it is where a profile's finding shows first.
- **Cores used** (Σ cpu seconds over the server's process tree ÷ the
  run's wall, read off `ps(1)` after the run — the host's accounting,
  not the server's claim) is printed for EVERY cell and gates
  nothing. A server that reaches parity by burning several times the
  cpu has reached a different thing, and the number is on the table
  so nobody has to argue about it later.

### The hosts — both, or it is a sentence about one

- **linux x86-64** — where a stranger runs a server. The only linux
  x86-64 the org has hands on is the CI runner (`ubuntu-latest`, four
  vcpus, a shared VM); N there is 4, and the runner's noise is why
  the statistic below is a RATIO taken on one box in one session and
  never an absolute carried between boxes.
- **macOS arm64** — the development box (nomad-1: Apple M5 Pro,
  18 cpus = 12 performance + 6 efficiency, macOS 26.4.1 at ws22).

**W8 is met only when the bar holds on both.** Hosts disagree — s137
measured `reuse_port` distributing on linux and NOT on macOS, and the
accept path is half of one shape — so a result on one host is that
host's result and carries that host's name.

### The runs, and what confidence means

- **A run** is `ab -t 5 -n 1000000 -c 32 [-k]`: five seconds of wall
  clock against one server, the request cap out of reach. (ws16–ws18
  ran `-n 20000`, which is under a quarter of a second at nginx's
  keepalive rate — a measurement of the timer, not the server.)
- **A set** is **five pairs, interleaved**: lobo then nginx, lobo
  then nginx, …, each server started fresh for its pair, both shapes
  run against each fresh server. Drift — thermal, a background job,
  a file cache warming — lands on both sides of a pair, not on one.
- **The statistic** is the ratio nginx ÷ lobo **per pair**, and the
  number reported is the **median of the five ratios**, with the
  minimum and maximum beside it. The repo's prior habit (three runs
  of each, a median of each side) could not tell a ten percent
  difference from noise: ws18's three close-shape runs spread
  21,443–25,470 around 23,663, ±8.5%.
- **Validity** — checked by the tool, refused by name, a refused set
  is not a result:
  - *quiet rig*: `uptime`'s one-minute load before the set is printed
    in the header; a set taken above **3.0** does not count (this box
    idles near 2 with its editors up; the bogus `timeout` a lane once
    recorded came at 46+).
  - *the generator is not the ceiling*: `ab` is single-threaded, and
    `docs/WORKERS.md`'s own table has nginx at 52k (one worker) and
    86k (eighteen) on the keepalive shape — a shape of number that is
    as likely to be `ab`'s limit as nginx's. The tool prints the
    generator's own cpu seconds ÷ wall for every run; a run where
    that exceeds **0.90** is a measurement of `ab` and the set is
    refused (split the load across k generators and take it again).
  - *the oracle is stable*: the five nginx numbers on a shape must
    satisfy max ÷ min ≤ **1.15**, else the box was not quiet and the
    set is discarded.
  - *nothing failed*: `ab`'s `Failed requests` and `Non-2xx` are
    zero on every run, or the set is refused.

### What counts as met

**W8 is met when, on both hosts, on both shapes, at N = cpus and
c = 32, the median of the five per-pair ratios nginx ÷ lobo is
≤ 1.10** — lobo within ten percent of nginx — from a valid set as
defined above, measured by `tools/lobo-parity`, whose table is in
the ledger below and in the campaign closeout.

Ten percent is one noise floor above the oracle's own run-to-run
spread; nearer than that this method cannot see, and a bar the method
cannot see is not a bar. Not met is any gating cell above 1.10.
"Met on macOS" is a sentence about macOS.

## Ledger

Sets appended newest first. A row is here because its set was
VALID; a refused set is named in the sprint's closeout, not here.

(empty at the bar's writing — ws22's first set is appended when it
is taken, after this file is committed)
