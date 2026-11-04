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
