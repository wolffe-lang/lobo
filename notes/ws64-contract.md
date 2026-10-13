# ws64 — the descriptors

Wave 53, lane ws64 (Opus). Written 2026-10-13 on lobo trunk `1d23471`
(ws63's head), after the inputs below were re-derived and nginx was
measured at its limits, and before any edit to `src/`, `tools/`,
`tests/` or `docs/`. The planning contract is
`sprints/wws/33-the-descriptors/ws64-the-descriptors.md` in
`wolffe-lang/wolf` (planning commit `42ae4fb`); rules are
`sprints/wave-53.md` down to `wave-45.md`. The oracle is the pinned
nginx 1.30.4 (ws47's bytes, `65595ac2…`), run as a black box; its
documentation is the other reference. Its source is never read.

One deliverable: lobo#84 closed as nginx behaves.

1. nginx measured at its limits (parity rows in `tools/lobo-shell`);
2. `worker_connections` applied per worker;
3. descriptors held in reserve so the control endpoint always answers,
   shown unanswered at trunk first;
4. accept failures logged, at a bounded rate, in nginx's shape;
5. recovery when descriptors return;
6. the parity and memory gates re-taken; the limits documented.

## 1. Forbidden, absolutely

- **nginx's source is not read.** Its documentation and runs of the
  pinned binary are the references. No kernel or libc source either.
  wolf's own runtime source is read where a finding needs its line.
- **Nothing here deploys or serves anything public.** lobo serves no
  site of ours; lupp.us is nginx on almanta (`sprints/HOSTING.md`).
  Never almanta, any Cloudflare tunnel or its configuration, DNS, or
  host ports 8080 and 8088; never a listing of `cloudflared`'s
  arguments. Every server this lane starts binds 127.0.0.1 on a
  kernel-chosen port or one of 18830–18849 and is stopped through its
  control endpoint or by its recorded pid.
- **A descriptor limit is lowered for the test's own processes only**:
  `ulimit -n` in the subshell that starts one server, never a
  host-wide or user-wide limit, never a sysctl. The load applied and
  its duration are written beside each measurement.
- No release, no tag, no Homebrew tap or AUR change (ws65 cuts 0.1.4).
  No merge. No issue filed or closed (they are listed in the report).
- The toolchain is the pin's, from the release archives by digest,
  each digest read twice.
- No literal signal bit and no host signal number in `src/` or
  `tests/` (the gauntlet's `signal names` step).
- No `rm` outside `~/lanes/ws64/` (nomad-1 and kasumi); no scratch in
  `/tmp`; no `git add -A`; nothing under `~/.claude`; no package
  installs; no commit trailers or PR attribution of any kind; the
  branch asserted before every commit; no `2>/dev/null` on a checkout.
- No build on nomad-1 (macOS gates run in CI). kasumi: remote commands
  in `bash -c`, `setsid` with a pid file, kill by recorded pid only
  (never a name, a pattern or a process group), outputs pruned.
- Strict evidence (wolf-lang#571): `WOLF_PAIRING_REQUIRE_SIBLING=1`,
  stdout and stderr together, every SKIP line counted; a `wolf build`
  that exits 2 is a compile error; the limit rows also under
  `taskset -c 0-3`. No "seen red" without a run id, sha, path or
  digest. Checksums carry a trailing `…`.
- At most two CI runs of this lane at once; never cancel another
  lane's. If the harness refuses an action, stop and report.

## 2. Inputs, verified (re-derived 2026-10-13)

| input | what was found |
|---|---|
| lobo trunk | `1d234718a84b…` (ws63's head, PR #83); no later commit |
| wolf 0.2.29 | tag `v0.2.29` → wolf-lang `6ffe7c6056ee…` (the tag object is `6f732110…`); release 411040788, not a draft; linux x86-64 `ae466e85…`, read twice from the API. Staged on kasumi, `sha256sum -c` twice (`kasumi:~/lanes/ws64/dl/digest-check.txt`): `wolf` 07f12158…, `libwolf_rt.a` fa0a0ae5…; `wolf 0.2.29 (wolfgang, pin 6ffe7c6)` — ws63's bytes |
| lupin 0.1.52 | tag `v0.1.52` → wolf-interp `025428b725a3…`; release 410845419; linux x86-64 `f5194b74…`, twice; `lupin` 74043b0a… |
| `[std]` | wolf-std `9e5bd6b16bee…`, archived into the staged toolchain |
| the oracle | nginx 1.30.4, `65595ac2…` (copied from ws63's lane by digest), configure line the pin's |
| lobo#84 | open. Its text holds, with two additions below |
| **trunk out of descriptors, idle connections** | one process, `ulimit -n 32` for that launch, 40 idle loopback connections for 5 s (`kasumi:~/lanes/ws64/logs/lb-trunk-idle.log`): 16 descriptors at start, 32 held, 24 connections left in the kernel's queue; a fresh GET unanswered in 3 s; **`lobo status` unanswered** (2.0 s, "did not answer"); nothing logged; and **the loop spins**: 293 cpu ticks in about 4.5 s where an idle lobo uses 0. The listener stays ready, the accept fails at once, and nothing waits. When the connections close it answers again |
| **drift: trunk out of descriptors with downloads aborts** | the issue says "505 served, then silent". At `ulimit -n 32` with 12 slow downloads (`logs/lb-trunk-dl.log`, `lb/trunk-dl/st.out`): eight are served, the ninth is reset and **the process is gone**: `thread … panicked at crates/wolf_rt/src/reactor.rs:139:13: epoll_create1 failed`, `panic in a function that cannot unwind`. The runtime makes its one readiness set at the first call that parks, here the first write to a slow client, and asserts on the descriptor. ws63's 1,024 run did not meet it because its first park came long before the limit. So at trunk the limit can end the process, not only silence it. A stale `unix:` control socket is then left behind and refuses the next start by name |
| `worker_connections` at trunk | a `planned(ws02)` row: parsed, never read. `worker_connections 16` with 24 slow downloads: all 24 served (`logs/lb-trunk-wc16-dl.log`). `-t` accepts `0`, `1`, `x`, `-1` and `1k` (exit 0) |
| `worker_rlimit_nofile` at trunk | a `named_error` row: the start and `-t` refuse it by name |
| a file that cannot be opened for want of a descriptor | `serve.classify` reads the open's `io` as kind 5, which the router answers **404** |
| what wolf offers | `net_accept` answers `{timeout, io}`; a failed accept for want of a descriptor is `io`, at once (`crates/wolf_rt/src/net.rs`). `os_error()` is set by the fs family only (`[os.fs.error]`: "the net and os families do not set it at this pin"), so the accept's own number cannot be read. No builtin reads or sets a resource limit |
| kasumi | 16 cpus, load 1–14 from other lanes while these ran (written beside each), `/home` 23–29 G free, `ulimit -n` 2048 |

### nginx at its limits, measured

One master and one worker unless said, 127.0.0.1:18830,
`error_log … info`, a 24 MiB file, the client
`kasumi:~/lanes/ws64/scripts/climit.py` opening connections one after
another on loopback and holding them 1.5 s (4 s for one row). Each row
is one run of a few seconds; the logs are
`kasumi:~/lanes/ws64/logs/ng-*.log`.

**At `worker_connections`.**

| what | measured |
|---|---|
| how many clients | `worker_connections 16`, one `listen`: **14** slow downloads are served (`ng-download-wc16.log`); two `listen`s: 13 (`ng-dl-wc16-2l.log`); `master_process off`: 15 (`ng-dl-wc16-nomaster.log`); two workers: 28 (`ng-dl-wc16-wp2.log`). So a worker serves `worker_connections − listening sockets − 1` clients, the one being the worker's channel to its master, and the limit is each worker's own |
| past it, every connection busy | the next connection is **accepted and closed at once** (the client reads end-of-stream, or a reset when it had already sent its request), and the worker logs `[alert] 16 worker_connections are not enough`, one line a refused connection, not rate-limited: 187 lines for 187 refusals inside 2 s (`ng-dl-wc16-n200.log`). It does not stop accepting and nothing waits in the kernel's queue (Recv-Q 0) |
| past it, idle connections present | a connection that has sent nothing yet, or a keep-alive connection between requests, is **closed to make room** (the client reads end-of-stream), least recently used first, and the new connection is served. The worker logs `[warn] 16 worker_connections are not enough, reusing connections`, at most one line a second: 9 lines in 10 s for 27 closes (`ng-idle-wc16-gap.log`) |
| how many it closes at a time | after a connection takes a slot, when fewer than `worker_connections / 16` slots are free, it closes `max(min(32, idle / 8), 1)` of the idle ones (the new one not counted); when no slot is free at all it does the same first. Fitted on fourteen runs and exact on each: closed 1 of 14, 2 of 15 and 11 of 24 at 16; 3 of 30 at 32; 7 of 61, 62 and 63 and 42 of 100 at 64; 9 of 79 at 80; 12 of 103 at 104; 12 of 106 at 112; 32 of 285 at 300; 2 of 8 at 8; 2 of 4 at 4; 2 of 3 at 3 (`ng-idle-*.log`) |
| a request under way | a connection whose request has begun arriving is not idle and is not closed (`ng-partial-wc16.log`) |
| after | when connections close, the next one is served at once (every run's `probe[after-close]`) |
| `-t` | `worker_connections 0` or `1` with one `listen`, `2` with two: `[emerg] N worker_connections are not enough for L listening sockets`, exit 1. `x`, `-1`, `1k`: `[emerg] invalid number "x" in <file>:<line>`, exit 1. Outside `events`: `"worker_connections" directive is not allowed here` (lobo's table says the same already). Twice: `"worker_connections" directive is duplicate` |

**Out of descriptors** (`ulimit -n 32` for that launch,
`worker_connections 1024`).

| what | measured |
|---|---|
| at start and at `-t` | `[warn] 1024 worker_connections exceed open file resource limit: 32` |
| the accept fails | `[crit] accept4() failed (24: Too many open files)`, **twice a second** (10 lines in 5 s, `ng-emfile-idle.log`): the worker stops accepting for half a second after each failure. The connections it cannot take **wait in the kernel's queue** (Recv-Q 17) and get no answer (a fresh GET: none in 3 s). It closes no idle connection to make room: all 23 stayed open |
| a file cannot be opened | the request is answered **500** and the worker logs `[crit] *N open() "<path>" failed (24: Too many open files), client: …, server: …, request: "GET /big.bin HTTP/1.1", host: "…"`, one line a request (`ng-emfile-dl.log`): 11 downloads served, the next 19 answered 500 |
| after | when descriptors return, the queued connections are served (`probe[after-close]` 200 at once) |
| `worker_rlimit_nofile 32;` | the worker's limit becomes 32 whatever it inherited, and the start warning is not printed (`ng-rlim-idle.log`). Raised past the hard limit: `[alert] setrlimit(RLIMIT_NOFILE, 4096) failed (1: Operation not permitted)` and the worker runs on (`ng-rlim-up.log`) |

Load applied for all of the above and the trunk rows: at most 285
loopback connections for under 10 s a run, 30 runs, one server at a
time; the downloads were stalled (the client stops reading), so no
bytes moved.

## 3. Prediction, committed before the first change

### 1. nginx at its limits, as parity rows

- `tools/lobo-shell` gains rows that drive both servers with one
  client (a wolf rig program, `tests/rig/climit.lu`: no new host tool)
  and compare what the client saw and each server's log line shape:
  the `-t` verdicts above (five rows, exit codes), the clients served
  at `worker_connections 16`, the refusal and its `[alert]`, the reuse
  and its `[warn]`, the start `[warn]` under a lowered limit, the
  accept failure's `[crit]` at a bounded rate with the queue left
  waiting, and the answer after the connections close. **At trunk the
  five `-t` rows and every limit row are red**; at head every row is
  parity except those named below. 22 probes today; about 36 at head.
- Named deltas, each with its reason in the table: lobo's line says
  `accept()` where nginx's says `accept4()` (the call is the
  runtime's); a hand's "channel" slot is its control endpoint.

### 2. `worker_connections` applied

- Default 512, nginx's. A lobo process serves
  `worker_connections − listeners − 1` plaintext connections at once.
  Past that it does what nginx does, by the rule fitted above: idle
  connections are closed least-recently-used first in nginx's batch,
  with `[warn] N worker_connections are not enough, reusing
  connections` at most once a second; with none idle the new
  connection is closed at once with `[alert] N worker_connections are
  not enough`, one line each.
- **The closed-connection counts equal nginx's in every row measured
  above** (1/14, 2/15, 11/24 at 16; 42/100 at 64; 2/8 at 8) and the
  same connections are the ones closed (the oldest). This is the
  number that falsifies the fit.
- `-t` and the start refuse `worker_connections` values nginx refuses,
  with its text.
- `worker_rlimit_nofile` stays a `named_error`: wolf has no call that
  sets a limit, and nginx's behaviour past `worker_connections` does
  not need it. Its reason line is rewritten to say so. Reported as a
  wolf finding, not built.
- `parked_downloads_e2e.lu` still passes (128 downloads on 16 cpus is
  under 509).

### 3. The reserve and the control endpoint

- A new test, `tests/shell/control_exhausted_e2e.lu`, starts lobo
  under `ulimit -n 40` (the limit is the child shell's own), fills it
  with idle connections until a fresh GET is left unanswered, and asks
  `status`. **Red at trunk**: `status` gets no reply inside 1000 ms.
  Green at head: lobo holds two descriptors in reserve (`/dev/null`,
  or the configuration file where there is no such device); when the
  control accept fails it lets one go, takes the order, answers and
  takes the reserve back; a `reload` or `reopen` has the second while
  it reads files.
- `status` answers inside 1000 ms under exhaustion; `reload` takes;
  `stop` stops.
- **The abort.** lobo makes the runtime's readiness set at start (one
  parked read of 1 ms on its own pipe), so the first slow download
  can no longer be what creates it. At `ulimit -n 32` with 12 slow
  downloads the process stays up at head (it is gone at trunk).
  Predicted cost: two descriptors at start (the set and its wake
  descriptor) that trunk took later.

### 4. Logging

- An accept that fails for want of a descriptor is logged
  `[crit] accept() failed (24: Too many open files)` and the process
  stops accepting for 500 ms, so at most two lines a second however
  many connections wait (nginx: 10 lines in 5 s; lobo within 8–12).
  The number and text are the host's, read by opening `/dev/null`
  after the failure (`os_error` serves the fs family only); when that
  open succeeds the line carries no number rather than a guessed one.
- The loop no longer spins: under 20 cpu ticks over 4.5 s of
  exhaustion (trunk: 293).
- A file that cannot be opened for want of a descriptor is answered
  500, as nginx answers it (trunk: 404), with a `[crit] open() "<path>"
  failed (24: Too many open files)` line.
- At start, and at `-t`, `[warn] N worker_connections exceed open file
  resource limit: M` when the limit is lower, on linux (the limit is
  read from `/proc/self/limits`) and, where there is no such file,
  from a child shell's `ulimit -n`.

### 5. Recovery

- When the held connections close, a GET that waited in the queue is
  answered and a fresh one answers inside 1000 ms; no restart, no
  operator action. In the e2e and as a parity row.

### 6. Parity, memory, docs

- Runner VM, nginx ÷ lobo (bar 1.10): close 1.00–1.05x, keepalive
  0.90–0.95x (ws63: 1.016x and 0.916x); this ÷ trunk inside
  0.98–1.02x on both: the admission check is two integer compares an
  accept.
- Membudget 24/24, the master row 0 KB; a process's resident size
  within 5 % of ws63's 4,380 kB (two more descriptors, no new table).
- Docs: README's Limits, `docs/WORKERS.md`, `docs/CONTROL.md`,
  `docs/LOGGING.md`, the directive table and CHANGELOG: two
  descriptors, two threads and about 153 kB a parked download (ws63's
  figures, not re-measured), the default of 512, what happens past it.

### The planted break

A branch `ws64-plant` on the head with the reserve never let go (the
control accept is not retried): red in CI on both hosts at
`control_exhausted_e2e.lu` and nowhere else.

### What would make this wrong

- If lobo's reading of "idle" differs from nginx's on some row (a
  connection whose bytes are in the kernel but not yet read), a closed
  count is off by the difference.
- If the runtime needs another descriptor at some later first use (as
  it did for the readiness set), the process can still end at the
  limit. The exhaustion rows are run with downloads, keep-alive and
  idle connections to find one.
- macOS: the limit is not readable from `/proc`; the child-shell path
  has not run anywhere yet. kqueue's set is made by the same first
  park.
