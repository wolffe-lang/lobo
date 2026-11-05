# ws75 — the sweep: the flaky rows, the master's spin, the limits follow-ups

## 1. Forbidden

No nginx source, and no other web server's: nginx is a black-box oracle,
run from a binary built once from the pinned, digest-checked tarball.
Loopback only, on ports the tests choose. No label, merge, tag, release
or issue closure from the lane, and no attribution trailers. Stress rows
run only on the cpus the lane holds.

## 2. Inputs, verified

- Base: trunk `64e7339`, branch `ws75`.
- Toolchain: wolf 0.2.36 (`wolf 0.2.36 (wolfgang, pin 5adf3d9)`), lupin
  0.1.58, std `78b9d3cbc41d51db44d18c40b6694403644d1c83`. These are the
  published linux archives, each hashed twice against the digests in
  `wolf-toolchain.toml` (wolf `d383c74c…`, lupin `34f52792…`).
- Oracle: nginx 1.30.4, tarball `4261dc90…` (hashed twice), with the
  configure line `NGINX-PIN` names (`nginx -V` read back). Binary sha256
  `5a08ef7f65591bcf51fe43ef43f3a1ee664ccf5665532b4351efde6b9c38eaff`.
- Linux image: Ubuntu 24.04 with apache2-utils 2.4.58, jq 1.7.1,
  netcat-openbsd 1.226 and strace 6.8 added, image id `7f82fbf7bc4e`.
  The rig needs nc, and the earlier lane's first image lacked it.

## 3. Prediction (committed before any source change)

Base: lobo trunk `64e7339` (0.1.5+dev, wolf 0.2.36, lupin 0.1.58, std
`78b9d3cb`). Every reproduction below runs on a Linux host inside a
container pinned to one block of six cpus. "Under load" means two busy
loops per cpu of that block, pinned with the test; "build load" adds a
release compile of lobo in a loop beside them. Each row runs at least
20 times, and the count is the evidence. Nothing changes before its
count is in.

### lobo#119: the distribution row

- **Expected at trunk:** `tools/lobo-prefork`'s distribution check reds
  in at least 1 of 25 runs under load: one hand reads `accepted=0`
  after 90 sequential connections. In every red run that hand still
  answers its own control endpoint, and the three counts still sum to
  90 (or 91 with the GET before the run).
- **Expected cause:** the row's assumption, not distribution. With one
  socket and three accepters, which process takes a connection is the
  kernel's choice. Nothing in `accept` promises a share to each waiter,
  and a hand that is descheduled, or keeps losing the wake, can
  legitimately get none. The only bound the spec supports is the sum:
  every connection is accepted once, by some hand.
- **The change:** the row asserts what lobo controls. (a) The counts
  over the run sum to exactly the number of connections, and the split
  is printed, not asserted. (b) Each hand accepts when it is the only
  accepter awake: its two siblings are stopped (SIGSTOP), one GET is
  sent, and the woken hand must serve it and its own `accepted=` must
  move by one; then the siblings continue (SIGCONT). That is a directed
  connection per hand, the issue's "every worker alive and able to
  accept".
- **Expected after:** the new rows hold 25 of 25 under the same load.
  **Wrong if:** a hand with its siblings stopped does not take the
  connection (distribution would then be broken, not the row), or the
  sum differs from the number sent.

### lobo#118: the pre-print trap in binary_identity_e2e

- **Expected:** the native lane reds under build load at a low rate,
  perhaps 0 to 2 of 25. ws74's diagnostics now print which pre-print
  assertion failed. The likely site is the readiness wait
  (`deadline-ms=15000`).
- **Candidates, in order:**
  1. The master, or a hand, is stalled in the runtime (the #72 shape),
     so `status` never shows both hands serving.
  2. `free_port()` is called twice and may return the same port, or a
     port taken before lobo binds it, so lobo fails to bind and never
     serves. Its own error log would say so.
  3. A slow start that really needs more than 15 s.
- **The change:** none to the deadline until a failure names its cause
  (the issue's own ask). If the cause is lobo's (2, or a lobo wait),
  fix it with its row. If it is the runtime's or the compiler's, file
  it on wolf-lang with the witness. **Wrong if:** 25 loaded runs show
  no red. Then the count is the result, and the issue stays open with
  it.

### lobo#72: the control socket after a burst of closes

- **Expected:** `carry_e2e` native under build load reds 0 to 2 times in
  25 (ws58 saw 2 of 25 on a build-loaded host; ws59 saw 0 of 300 under
  CPU load alone). On a hang, the runner snapshots every lobo thread's
  syscall, wchan and descriptors, and a gdb backtrace.
- **Expected cause, if it reproduces:** a thread parked in the runtime,
  not a lobo wait (every lobo wait is deadline-armed). That would be
  filed on wolf-lang with the snapshot. **Wrong if:** the snapshot shows
  the main thread in a lobo-owned blocking call (an accept or read with
  no deadline). That would be lobo's to fix here.

### lobo#91: the master with no control directive

- **Expected at trunk:** not true any more (fixed by ws63, #83). An idle
  master with `worker_processes 2` and no `control` directive uses well
  under 10 % of a cpu over a 3 s window. A real `kill -HUP` makes both
  hands activate generation 2, and `kill -TERM` stops the tree.
- **The change:** a row in `tools/lobo-signal` that measures exactly
  that: cpu ticks from `/proc/<pid>/stat` on linux (`ps -o time` on
  macOS), the HUP fan-out and the TERM. It is the row this lane's plant
  breaks.
- **Wrong if:** the row reds at trunk. Then #91 is live again, and the
  fix comes before the row is trusted.

### lobo#87: the limits follow-ups

- **The master's reserve:** expected to be unreachable at sane limits,
  because the master accepts no clients. It may be reachable at
  `ulimit -n` 12 to 16. There a probe or a control accept can fail for
  want of a descriptor, and a failed probe is read as a silent hand,
  three of which reap it. Measured before anything is decided. A
  healthy hand reaped, a spin, or an unanswered `status` is a bug and
  is fixed with its row. A clean master is a ruling (R-ws75-N:
  recommend no reserve).
- **A full hand winning a sibling's connection:** a design decision.
  It needs a pause, during which a full hand leaves the listener to its
  siblings, traded against a later refusal when every hand is full.
  Recommended as an R-ws75-N with options, and implemented only if the
  maintainer's answer arrives in the lane.
- **/metrics counters, TLS at the limits, ENFILE, no `/dev/null`, a
  reload at the limit:** named follow-ups, each triaged in §5.

### The rest (#102, #100, #95, #90, #82, #78, #68)

- **#90 and #78:** each is fixed at the commit its body names. The
  witness row that proves it still runs green at trunk. Recommend
  closing both.
- **#91:** as above. Recommend closing it once the new row is green.
- **#102, #100, #95, #82, #68:** expected still open, each with what
  blocks it.

### The plant

One commit on the final green head, on its own `ws75-plant-*` branch,
with one file and one hunk. The master's signal pipe joins its wait set
only when there is a control listener, which is ws62's bug. Predicted
red by name: the new #91 row. The master spins (well over 10 % of a
cpu) and the HUP is not heard.

## Recommendations for follow-up lanes (lobo#87)

These are recommendations only; this lane does not implement them.

- **R-ws75-1: a full hand takes a connection a sibling had room for.**
  ws64 measured it with two hands at `worker_connections 16`: lobo
  served 28 of the first 29 connections, and the oracle served the
  first 28. The options:
  - A: keep it, documented as a delta. The total refused is nginx's;
    which connection is refused is not.
  - B: a full hand with nothing idle to close leaves the shared
    listener out of its wait for a short pause (about 20 ms) before it
    takes and refuses a connection. A sibling with room then wins it.
    When every hand is full, each refusal comes up to one pause later.
    This is for hands on an inherited listener only: not a single
    process, and not `reuseport`.
  - C: the master decides admission, since it knows each hand's room.
    That needs a channel from the master to its hands, which lobo does
    not have.

  **Recommended: B,** in its own lane, with a two-hand row at
  `worker_connections 16` held to the oracle's measured first 28.
- **R-ws75-2: `/metrics` counters for refused, evicted and
  accept-failure connections.** Their names, types and labels must
  pass `tools/lobo-metrics`' clause-by-clause exposition check.
  **Recommended:** three per-process counters, each stamped with the
  worker like the existing series:
  - `lobo_connections_refused_total`;
  - `lobo_connections_evicted_total`;
  - `lobo_accept_failures_total{reason="emfile|enfile|other"}`.

  This is for a follow-up lane.

## 4. Evidence index

Every count below ran on Linux, inside the lane container, pinned to one
block's cpus. "cpu load" means two busy loops per cpu of that block;
"build load" adds a release compile of lobo in a loop. The run logs stay
with the lane.

### lobo#119, trunk `64e7339`, the old row (counted before the change)

- **25 full prefork steps under cpu load, six cpus, load1 9 to 21: 24
  green, 1 red.**
  - The 24 green runs split 25 to 37 connections per hand. None read a
    hand at zero.
  - The red run (run 4) is **not** the zero-hand shape. The master
    answered its first `status`, then nothing for more than 10 s. Every
    row that reads `status` failed together; the distribution row read
    empty counts (`//`). Meanwhile every GET was served.
  - Status returned once hand 1 had been killed (`kill -9`) and
    replaced, and the rest of the run passed: 30 of 38 rows.
  - That is a control-path stall under load, the family of lobo#72,
    not of #119.
- An earlier 6-run count is void. A runner bug overwrote its run count
  with the cpu count.
- The zero-hand shape itself was seen twice by ws74, on another shared
  Linux host: 54/37/0 at trunk and 36/0/55 at a branch, each time with
  the zero hand answering its own endpoint.
- The change (`8af2674`) does not wait on that shape recurring. It
  removes an assertion that `accept` does not support, and replaces it
  with two that lobo controls (see `docs/WORKERS.md`).

### lobo#119, after the change (`8af2674`)

- **The new rows: 25 of 25 runs green under cpu load** (load1 6 to 18),
  and **25 of 25 green with no load.**
  - `[distribution-sum]` moved by exactly 90 in all 50 runs.
  - `[distribution-directed]` passed for all three hands in all 50.
  - The printed splits ran from 16/35/39 to 34/23/33.
- **Trunk's old row with no load: 25 of 25 green.**
- On macOS the new rows pass too (39/39), and so does the #91 row
  (27/27). Both ran at a local commit equal in source to these.

### lobo#118 and lobo#72, trunk `64e7339`, under build load (eight cpus, the package at 100 °C)

- **`binary_identity_e2e` native: 25 of 25 green.** Runs took 30 to
  35 s; no failure message was printed.
- **`carry_e2e` native: 25 of 25 green.** Runs took 10 to 13 s.

### lobo#87, the master's descriptors, trunk `64e7339`

`worker_processes 2` with a control endpoint. The tree was started
under `ulimit -n` at each limit below. At each, the probe asked
`status` 20 times, sent a GET between asks, and then watched 6 idle
seconds.

| `ulimit -n` | what happened |
|---|---|
| 11 to 15 | the hands never came up: `no free endpoint for its control listener`, or, at 13 and 15, the master's own `spawn failed (io)`; the master stayed alive |
| 16 | a hand came up at its own limit (`accept() failed (24: …)`), and the tree never reached two serving hands |
| 18, 20 | serving; `status` 20/20; idle master 0 to 2 of 600 cs; no hand reaped; 186 `accept() failed (24: …)` lines from the hands, none from the master |
| 24, 32, 64 | serving and clean; `status` 20/20; idle master at most 1 of 600 cs |

The master rests at 14 descriptors at every limit, and a hand needs
about 20. So wherever a hand can serve, the master has room for a
control connection and for its probes. A failed probe never reaped a
healthy hand.

**R-ws75-3, recommended:** no master reserve. Document the master's
14 at rest beside the hands' 20 in README's Limits, and close that item
of #87.

### lobo#90 and lobo#78, their witnesses re-run at trunk `64e7339`

`tools/lobo-corpus` over `tests/http/split_scalar.lu`,
`tests/http/scalar_fuzz.lu`, `tests/serve/split_scalar_e2e.lu` (#78,
fixed at `b256d2e`), `tests/serve/park_at_limit_e2e.lu`,
`tests/shell/control_exhausted_e2e.lu` and
`tests/shell/start_at_limit_e2e.lu` (#90, fixed at `f9fea550`): **13 of
13 lane-runs green**, every declared lane of each.

### lobo#91

The new row (`60018dd`, its match corrected in `5be2e32`) is green on
macOS. On linux it is green in the final gauntlet below. An idle master
with two hands and no control directive used 0 of 300 hundredths of a
cpu-second; a real HUP reached both hands; a real TERM ended the tree.
The plant (one hunk: the signal pipe joins the master's wait set only
with a control listener, which is ws62's bug) is red by name at
`nocontrol-idle-cpu`, `nocontrol-hup` and `nocontrol-term`. Its record
is in the PR.

## 5. Done-when and handoff

**Fixed here:** lobo#119. The distribution row now asserts the accept
sum and a directed accept per hand, not the kernel's split.

**Recommend closing:**
- **#91:** fixed at `1d234718` (#83). It now has a row that measures the
  master's idle cpu, its HUP and its TERM, and the plant shows that row
  turns red if the bug comes back.
- **#90:** fixed at `f9fea550` (#86); witnesses green at trunk.
- **#78:** fixed at `b256d2e` (#75); witnesses green at trunk.

**Still open, each with what it needs:**
- **#118:** not reproduced. 25 of 25 green under build load, plus 9 of
  9 isolated runs by ws74. The one red was a full-corpus run on a
  shared host. ws74's diagnostics will name the failing assertion, with
  its values, at the next red. No witness, so nothing is filed upstream
  and no deadline is raised.
- **#72:** `carry_e2e` was 25 of 25 green under build load. A new
  sighting of the same family: one trunk prefork step under cpu load
  (load1 21) where the master answered no `status` for more than 10 s
  while GETs were served, and recovered once a hand was replaced. The
  prefork loop now keeps that run's server log and takes a thread
  snapshot at the stall. The next sighting can name the parked thread
  and be filed on wolf-lang if it is the runtime's.
- **#87:** the master's reserve is not needed (R-ws75-3, documented in
  README). Two items are recommendations for follow-up lanes: R-ws75-1
  (admission across hands) and R-ws75-2 (`/metrics` counters). Still
  undriven: TLS listeners at the limits, ENFILE, a host with no
  `/dev/null`, a reload at the limit, and macOS's dropped connection
  after a failed accept (the host's behaviour, seen under nginx too).
- **#102:** cert auto under a dropped user still needs a root-container
  ACME witness, combining `tools/lobo-user` and `tools/lobo-acme`, and
  a policy on who owns the ACME store and renewals. Not verified here.
- **#100:** blocked upstream. wolf-lang#835 (a connect that does not
  block the thread) and #836 are both open.
- **#95:** a macOS-only CI observation on a 0.2.29 build. It needs an
  instrumented macOS run. Not driven here.
- **#82:** three named deltas: per-server limits, regex `server_name`,
  listeners at reload. Implementation work, unblocked. Not taken here.
- **#68:** the user-space levers need a fresh same-host profile before
  any change is chosen.

**Commits:**
- `d141062`: the prediction, before any change.
- `60018dd`, `df6f5b9`, `5be2e32`: the #91 row, its docs and its match
  fix.
- `8af2674`: the #119 rows and `docs/WORKERS.md`.
- `5994b30`, `a753480`: the trunk evidence and the master's
  descriptors in README.
- `db3d095`: R-ws75-1 and R-ws75-2 as recommendations.

**Test targets:**
- [x] Trunk old prefork row: 25 runs under cpu load (24 green; the red
  is a control stall, not #119's shape) and 25 with no load (25 green).
- [x] New #119 rows: 25 under cpu load and 25 with no load, all green.
- [x] `binary_identity_e2e` and `carry_e2e`: 25 each under build load,
  all green.
- [x] #87 master probe at `ulimit -n` 11 to 64.
- [x] #90 and #78 witnesses: 13 of 13 lane-runs.
- [x] #91 and #119 rows on macOS.
- [ ] One gauntlet at the final head, with every END line (in the PR).
- [ ] The plant, red by name at `nocontrol-*` (in the PR).
- [ ] The audit, once.

Footprint: module
