# ws67 — the stale socket, the privilege drop, the silent upstream (lobo#94, #96, #81)

Crawl 54, batch 9, lane ws67 (Opus). Written 2026-10-19 on lobo trunk
`9a4723c` (ws66's head), after the inputs below were re-derived and
measured (trunk's three reds and the pinned nginx as a black box), and
before any change to `src/`, `tests/`, `tools/`, `docs/` or
`.github/`. The planning contract is
`sprints/wws/36-lobo-three-fixes/ws67-lobo-three-fixes.md` in
`wolffe-lang/wolf` (planning trunk `b860faa`); rules are s243's
"Forbidden / rules" (`sprints/crawl-54.md`, `wave-53.md` down to
`wave-45.md`), with the toolchains named below.

Three deliverables:

1. **lobo#94**: a start that fails after binding its control socket
   removes what it made (in reverse: the pid file it wrote, the control
   socket, the listeners), and a start that finds a control socket
   nobody answers on, with no live pid behind it, takes the path over;
   a socket a live lobo answers on is never removed.
2. **lobo#96**: `user` drops privilege as nginx does: a master started
   as root keeps root and its workers serve as the configured user and
   group, supplementary groups too (`os_set_ids`, `os_euid`; wolf-std
   `d37c911`'s `std.env`, `std.process`, `std.os.users`); measured as
   root in a container. Not root: nginx's warning, as today.
3. **lobo#81**: a proxied request to a silent upstream no longer holds
   the serving loop: the exchange runs beside the loop, so concurrent
   static GETs are answered and `-s stop` is obeyed; the proxy suite
   unchanged.

## 1. Forbidden, absolutely

- **Nothing here deploys or serves anything public.** lobo serves no
  site of ours; lupp.us is nginx on almanta (`sprints/HOSTING.md`).
  Never almanta, the live nginx, any Cloudflare tunnel or
  `~/.cloudflared`, DNS, or host ports 8080 and 8088; never a listing
  of `cloudflared`'s arguments. Every server this lane starts binds
  127.0.0.1 on a kernel-chosen port or one of 18880–18899, or port 80
  INSIDE a throwaway container's own network namespace, and is stopped
  through its control endpoint, by its handle, or by its recorded pid.
- **Root only inside a container.** The `user` drop and port 80 are
  measured as root in a rootless podman container on kasumi (and, in
  CI, a docker container on the linux runner); never as root on a host.
  Signals and id changes only to processes the test started.
- **Clean-room against nginx's source**: its documentation
  (`user`, `worker_connections`, `proxy_read_timeout`, the log-rotation
  paragraph of "Controlling nginx") and black-box runs of the pinned
  1.30.4 (`65595ac2…`) only.
- No merge, no tag, no release, no tap or AUR change (0.1.5 is a later
  lane). No issue filed or closed (listed in the report). No
  attribution or co-author trailer in any commit or PR text.
- Toolchains only from the published release archives by digest, each
  digest read twice. lobo's pins do not move.
- No assertion deleted or weakened; no timeout or retry as a fix.
- No `rm` outside `~/lanes/ws67/` (nomad-1 and kasumi); no `git add -A`;
  nothing under `~/.claude`; no package installs on any host; the
  branch asserted before every commit; no build on nomad-1. kasumi:
  `bash -c`, `setsid` with a pid file, kill by recorded pid only.
- Strict evidence (wolf-lang#571): `WOLF_PAIRING_REQUIRE_SIBLING=1`,
  stdout and stderr together, every SKIP line counted; process, signal
  and descriptor rows also under `taskset -c 0-3`. No "seen red"
  without a run id, sha, path or digest.
- At most two CI runs of this lane at once; never cancel another
  lane's. If the harness refuses an action, stop and report.

## 2. Inputs, verified (re-derived 2026-10-19)

| input | what was found |
|---|---|
| lobo trunk | `9a4723c0f83c…` (ws66's notes, PR #93 merged); origin has nothing later |
| wolf 0.2.32 | tag `v0.2.32` (annotated `d21c4b28…`) → wolf-lang `72de141f…`; linux x86-64 archive `4c37f9c5…` (80,092,071 B), read twice from the API; staged on kasumi and `sha256sum -c` twice (`kasumi:~/lanes/ws67/dl/digest-check.txt`): `wolf` 81bdf8d4…, `libwolf_rt.a` 74d55d5f…, `wolf-cimport-worker` 0498e8e1…; `wolf 0.2.32 (wolfgang, pin 72de141)`; the archive's `std/STD-REV` is `d37c911f…` |
| lupin 0.1.54 | tag `v0.1.54` (annotated `9c98d445…`) → wolf-interp `0e536e8f…`; linux x86-64 `175df238…` (2,971,403 B), twice; `lupin` a9856dd4… |
| wolf-std | lobo's `[std]` is `d37c911` (ws66). It carries what #96 needs: `std.env.euid` / `std.env.groups` (`os_euid`, `os_groups`), `std.process.set_ids(uid, gid, groups)` (`os_set_ids`: one call, groups then gids then uids, read back; `unsupported` on every host but linux) and `std.os.users` (pure `passwd(5)`/`group(5)` parsing: `user_named`, `group_named`, `groups_of`) |
| the oracle | nginx 1.30.4, `65595ac2…`, copied from ws66's lane by digest (`toolchains.txt`) |
| trunk built at the pin | both tiers, zero diagnostics (`kasumi:~/lanes/ws67/logs/build-trunk.log`): dev `254370c8…`, release `6968be8b…` |
| trunk's gauntlet | GREEN, exit 0, 893 s under `taskset -c 0-3`, strict env, 0 SKIP lines (`kasumi:~/lanes/ws67/logs/g-trunk.log` 20a9c93e…): corpus 368/368 lane-runs, `lobo-shell` 41 probes / 40 parity / 1 named delta / 0 red, `lobo-signal` 22/22, `lobo-membudget` 24/24, `proxy-differential` 8/8. The measuring shell's mask: SigBlk `0x10000`, SigIgn `0x6` (`g-trunk.mask`) |
| **#94 at trunk** | `kasumi:~/lanes/ws67/ev/s94-trunk-rel.log`. Started under `ulimit -n N` (this shell holds one inherited socket more than ws66's, so each row is ws66's plus one): 9 exit 71 (the hub's line); 10 `configuration file … test failed`; 11 `bind() to control … failed`, nothing left; **12 `could not write pid file`, exit 1, `c.sock` left behind, and the next plain start exits 1: `something already exists at "…/c.sock"`**; 13 serves. A lobo ended by SIGKILL leaves `c.sock` and the pid file; the next start warns `removing stale pid file … (control … not responding)` and then **refuses on the socket**, exit 1. A live lobo: a second start with its config is refused (`a lobo master is already running`), a second config on the same socket is refused (`something already exists`), and the live one keeps serving. An ordinary file at the path: refused |
| #94, other refusals after the bind | `serve_main`: only the pid file write (`src/main.lu` 1677) after `bind_control`; `master_main`: the pid file write (4947) and a listener bind (5010–5023: it removes the pid file but leaves the control socket). Log outputs open lazily (first flush), so none is open at any of them |
| #94, nginx | `kasumi:~/lanes/ws67/ev/ng94.log`: `listen unix:` on a path that holds a stale socket, an ordinary file or a live listener is refused all three ways, `bind() … failed (98: Address already in use)` five times then `still could not bind()`, exit 1. A stale pid file is taken over: nginx starts and writes its own pid. The contract's takeover is the pid file's rule applied to lobo's own endpoint, which nginx has no twin of |
| **#96 at trunk** | as root in a container (`kasumi:~/lanes/ws67/ev/ng96-trunk.log`, podman, `archlinux:base-devel`): `user lw lwx;`, `user lw;`, `user nosuch;` and `user lw lwx; worker_processes 2;` all refuse to start, `[emerg] the "user" directive asks for a privilege drop and lobo cannot drop privileges at this pin (wolf has no setuid surface)`; with no `user` lobo serves as root (`Uid: 0 0 0 0`) and answers a root-only 0600 file 200 |
| #96, nginx as root (same log) | the master keeps `Uid: 0 0 0 0`; **`user lw lwx;`**: each worker `Uid: 1500 ×4`, `Gid: 1600 ×4`, `Groups: 1600`; **`user lw;`**: `Gid: 1500 ×4` (the group NAMED like the user), `Groups: 1500 1600` — the group list is the given group plus every group that lists the user as a member (`std.os.users.groups_of(text, user, gid)` exactly); port 80 answers 200; the root-only file 403 with `open() … failed (13: Permission denied)`; at start the logs are `root:root 644`, after `-s reopen` they are `lw:root` (the owner moves, the group does not; documented in "Controlling nginx": the master re-opens the logs and gives them to the workers' user). `worker_processes 2`: both workers dropped. **No `user` as root: the workers run as 65534:65534** (the documented default `user nobody nobody`). `master_process off`: no drop at all. `user nosuch;` → `[emerg] getpwnam("nosuch") failed in <file>:1`; `user lw nosuchgrp;` → `[emerg] getgrnam("nosuchgrp") failed in <file>:1`; as `lw` (not root): `[warn] the "user" directive makes sense only if the master process runs with super-user privileges, ignored in <file>:1` and it serves |
| #96, lobo's shape | `worker_processes 1` (or none) is ONE process (`docs/WORKERS.md`); 2+ is a master that binds the listeners and execs hands (`os_spawn_with`, the listeners as descriptors 3, 4, …). Hands bind their own control endpoint (`<path>.wN` beside a unix `control`), adopt the listeners, open their log outputs at the first flush. The master removes a hand's `.wN` after it is reaped (`forget_endpoint`). `master_process` is a `named_error` row |
| **#81 at trunk** | `kasumi:~/lanes/ws67/ev/s81-trunk-rel.log` (`scripts/silent81.py`, release binary, client on cpus 8–15): an upstream that accepts and never answers, one proxied request, then 50 concurrent clients GET a static file over and over (a fresh connection each, 2 s deadline) for 10 s: **0 answered, 250 not**; `-s stop` exits 1 (the endpoint did not answer) and **the server is still running 15 s later** (killed by its pid). The proxy runs inline in the step (`proxy.run` → `attempt` → `read_up_head`, parked in `net_read` under `proxy_read_timeout`) |
| #81, nginx | the same shape (`ev/s81-nginx.log`): **328,903 answered, 0 not**, p50 1.5 ms, p99 3.0 ms, max 5.8 ms; `-s stop` ends it at once |
| #81 and ws64's limits, nginx | `ev/ngwc.log`: `worker_connections 16`, one `listen`, a silent upstream: **7 proxied requests are held, the 8th connection is closed** with `[alert] 16 worker_connections are not enough` (each proxied request is two connections: 7 × 2 + the listener + the channel = 16), and a static GET then is refused too. nginx's `worker_connections` text: the number "includes all connections (e.g. connections with proxied servers, among others)" |
| the loop's shape | `src/main.lu`'s one poll loop; two things already leave it for a proc that reports one line down the loopback stream pipe: a large plaintext body (ws49, lobo#46; ws56's `StreamSlot` keeps the proc so a drain can kill it) and the ACME daemon (ws56, lobo#65). The resolver (ws13) is the one exchange the loop multiplexes itself, and it re-serves its request from the top once the name settles |
| what can cross into a proc | `[conc.proc.arg]` (s229, s233): an argument of a proc that is not joined in the frame must not name bytes a frame-local region owns (E1010); a `str` crosses as its view. The loop's strings live in `pass`/`step` regions, so a proc beside the loop can be given scalars only — the stream gets `(sock, fd, out, id)` |
| lobo#87 | open (ws64's limit follow-ups); not this lane's |
| kasumi | 16 cpus, load 0–1.4, `/home` 24 G free, `ulimit -n` 2048; podman 5, rootless, `uid_map` 0→1000 and 1→100000 (65536) |

## 3. Prediction, committed before the first change

### 1. lobo#94

- **The undo.** Every refusal after the control bind, in `serve_main`
  and in `master_main`, removes the pid file it wrote, closes the
  control listener (whose close unlinks a unix path) and closes the
  listeners it bound, in that order. At `ulimit -n 12` the start still
  exits 1 with `could not write pid file`, and `logs/` holds nothing
  it made; the plain start after it serves (trunk: exit 1). A master
  whose listener bind fails leaves no control socket (trunk: left).
- **The takeover.** At bind, a control path that holds a SOCKET that
  refuses a connection (`net_connect_unix` → `refused`), when the pid
  file names no live process (`os_signal_send(pid, 0)` → `not_found`,
  or no pid file), is removed with one line, `lobo: [warn] removing
  stale control socket "<path>" (no lobo answers on it)`, and bound.
  A SIGKILLed lobo's next start serves (trunk: exit 1), its two
  warnings the stale pid file's and the socket's.
- **Never.** A live lobo plus a second start with its config: refused
  as today (`a lobo master is already running`); a second config on
  the live socket: refused as today (`something already exists …`),
  because the connect succeeds; an ordinary file at the path: refused
  as today, not removed; a socket nobody answers on whose pid file
  names a live process: refused, not removed.
- Tests: `tests/shell/stale_socket_e2e.lu` (native, checked): the ws66
  shape (a start under the limit that fails at the pid file, then a
  plain start: served, nothing left after its stop), a SIGKILLed lobo
  then a start (served), and the three refusals above, each with the
  socket and the live server checked afterwards. Red at trunk on the
  first two, green on the refusals.

### 2. lobo#96

- **Who drops.** As root on linux with a `user` line: the process that
  ran `lobo serve` is a master and keeps root, and the hands drop —
  with `worker_processes 2+` as now, and **with `worker_processes 1`
  a master and one hand** (nginx's shape: it has a master unless
  `master_process off`, which lobo refuses by name). Without `user`,
  or not root, the single-process shape is untouched.
- **The ids.** A hand drops after it has adopted its listeners and
  bound its control endpoint and before its loop, with one
  `std.process.set_ids(uid, gid, groups)`: `uid` the user's from
  `/etc/passwd`, `gid` the named group's (else the group NAMED like the
  user, nginx's rule), `groups` = `std.os.users.groups_of(/etc/group,
  user, gid)`. Measured in the container as root: the master
  `Uid: 0 0 0 0`; each hand under `user lw lwx;` `Uid: 1500 1500 1500
  1500`, `Gid: 1600 1600 1600 1600`, `Groups: 1600`; under `user lw;`
  `Gid: 1500 ×4`, `Groups: 1500 1600` — nginx's lines exactly. Port 80
  bound by the master answers 200 from the hand; the root-only 0600
  file is **403** (trunk with no `user`: 200).
- **The logs.** The master (root) creates each log file the
  configuration names and gives it to the user (owner only, nginx's
  `lw:root`) before it starts the hands and again before it fans out a
  reopen, so a hand that is no longer root can open them. After
  `-s reopen` with the access log moved away: a fresh `access.log`,
  `lw:root` (nginx's). Delta, named: at start too, where nginx leaves
  them `root:root` until the first reopen (its workers inherit the
  master's descriptors; lobo's hands are exec'd and open their own).
- **The refusals.** An unknown user or group: `[emerg] getpwnam("x")
  failed in <file>:<line>` / `getgrnam("x") failed in <file>:<line>`
  at `-t` and at start, as root (nginx's text). As not-root: the
  `[warn]` and the config loads, unchanged. A host where the drop is
  `unsupported` (macOS, windows) as root with `user`: refused by name,
  as today (the reason updated). `os_euid` replaces the
  `/proc/self/status` read and the `id -u` probe (ws54).
- **No `user` as root**: a NAMED DELTA, not nginx's default. nginx
  drops to `nobody nobody`; lobo keeps the single root process it runs
  today and says so in one `[warn]` at start, so a root deployment that
  serves now keeps serving (the ACME store, the logs). The report
  names this as the maintainer's to rule.
- A gauntlet step `user` (`tools/lobo-user`): the measurement above in
  a container as root where linux has docker or podman, else a named
  SKIP. Red at trunk (every `user` row refused to start).

### 3. lobo#81

- **The choice: a proc beside the loop, one per exchange.** Argued
  against the alternative (the loop multiplexes a non-blocking
  upstream read, as the resolver does): the exchange is connect →
  write → read → relay, under three deadlines, with peer failover and
  an https leg whose handshake is several blocking reads of
  `std.x.tls.client`; multiplexing it means a state machine for each,
  per-row upstream buffers carried across passes as bytes (ws57's
  rule), and a re-entry of the request's step, and the relay to the
  client would still be written inside the loop. A proc keeps
  `proxy.attempt` and `attempt_tls` as they are (the suite unchanged),
  covers https and the client-ward write for free, and is the shape
  the loop already has twice (ws49's streams, ws56's ACME daemon):
  one proc, one line down the stream pipe, a `StreamSlot` so a drain
  can kill it.
- **What crosses.** The step plans the exchange (the plan's refusals,
  the trust anchors, the peers through the resolver copy, the upstream
  request per peer) and hands the loop a JOB as text; the loop makes a
  loopback connection to its own job listener (made once at start,
  beside the stream pipe), spawns the proc with four ints (client,
  job socket, stream pipe, id), and writes the job, followed by the
  request's access record packed as text. The proc reads them into its
  own region, runs the attempts, writes its details and the record
  back on the job socket, and reports `<sock> 0 <wcode> 0 <id>` down
  the stream pipe. So no byte a loop region owns enters the proc
  (`[conc.proc.arg]`), and the loop keeps only ints for the row. The
  access line, the counters and the generation's high water are
  written when the report arrives (the request's time is the whole
  exchange, as nginx's). Where the job listener cannot be made, or a
  job connection cannot (out of descriptors), the exchange runs in the
  step, as trunk does, said out loud once.
- **Measured** (`silent81.py`, the trunk row's shape): **all GETs
  answered, 0 not**, p99 under 20 ms on kasumi; `-s stop` ends the
  server inside 1 s; the proxied client gets its 504 at
  `proxy_read_timeout` when nothing stops it, and the connection
  closes at `-s stop`. The same with 8 proxied requests in flight.
  `tests/serve/silent_upstream_e2e.lu` (native, checked) holds a short
  form against the binary: a silent upstream at `proxy_read_timeout
  3s`, 20 concurrent static GETs each answered within 1 s, then
  `-s stop` obeyed within 2 s; red at trunk.
- **ws64's limits.** A proxied row counts as two connections against
  `worker_connections` while its exchange is out (nginx's accounting):
  at `worker_connections 16` with one listener, 7 proxied requests
  are held and the 8th connection is closed with `[alert] 16
  worker_connections are not enough`, as nginx (measured above). A
  parity row in `tools/lobo-shell`, red at trunk (its loop is held by
  the first).
- **Costs.** At rest one more descriptor (the job listener: 20 → 21).
  Per exchange in flight: the proc (two threads and two descriptors,
  ws63's figures for a parked proc), the job connection's two ends and
  the upstream. Proxied throughput against a prompt upstream, `ab -c 32`
  on kasumi, head ÷ trunk 0.6–1.0x (a loopback connect and accept and a
  spawn per request, against an exchange that was inline).
- **Drain.** A proxied row whose generation passes
  `worker_shutdown_timeout` is killed as a stream is (the client
  closed, the job socket's two ends closed, and an upstream the proc
  had open closed by the loop from the proc's own notes); `-s quit`
  waits for an exchange in flight, as nginx's graceful shutdown does.
- The proxy suite unchanged: `tests/proxy/*`, `tools/lobo-proxy-differential`
  8/8, `tests/resolver/*`, the log differential. Membudget gains a
  proxied row (RSS flat over 2,000 proxied requests); 24 → 25 rows.

### The gauntlet and the plants

- The gauntlet GREEN at the head on kasumi and both CI hosts, 0 SKIP
  lines on linux (macOS adds the `user` step's named SKIP).
- **Plants** (each a branch dispatched in CI, trunk's `src/` with the
  new tests and tools): `ws67-plant` — red on linux at
  `stale_socket_e2e.lu`, `silent_upstream_e2e.lu`, the `user` step and
  the new `lobo-shell` row; on macOS at the two e2e tests and the row.

### What would make this wrong

- A proc parked in `net_read` on the upstream holding a pool worker
  the loop's next spawn needs (wolf-lang#570's shape, retired at
  0.2.29 by s231): the static GETs would still be answered (the loop
  spawns nothing for them) but a second proxied request would wait.
- The job socket's two ends and the proc's threads at the descriptor
  limit: ws64's reserve rows (`control_exhausted_e2e.lu`) are where it
  would show.
- `set_ids` refusing inside rootless podman for an id outside the
  user namespace's map (1500 and 1600 are inside it).

## 3. The prediction against the measurement

Measured on kasumi (16 cpus; other lanes beside it, load 14–17 from
19:50Z on, written beside each number), the toolchains of §2; logs under
`kasumi:~/lanes/ws67/ev/` and `logs/` (digests in §4). §3 above is as it
was committed (`1a2521d`).

### lobo#94

**Held.**
- The undo: at `ulimit -n 12` the start exits 1 with `could not write
  pid file` and `logs/` holds nothing; the plain start after it serves
  (trunk: `c.sock` left, then exit 1, `something already exists`).
  Walking the limit up from 8, every start that fails leaves nothing
  (8–9 exit 71, 10–11 exit 1 before or at the bind, 12 the pid file,
  13 serves). A master of two hands whose pid file cannot be written
  leaves no socket either.
- The takeover: a lobo ended by SIGKILL leaves `c.sock` and its pid
  file; the next start prints the stale pid file's `[warn]` and then
  `[warn] removing stale control socket "<path>" (no lobo answers on
  it)`, and serves (trunk: exit 1).
- Never: a second start of a live lobo's configuration is refused (`a
  lobo master is already running`), a second configuration on the live
  socket is refused (`something already exists`), a socket nobody
  answers on whose pid file names a live process (the test's own) is
  refused and left, an ordinary file is refused and left untouched; the
  live lobo keeps answering throughout.
- `tests/shell/stale_socket_e2e.lu`: red at trunk on both lanes at the
  limit-12 assertion (`c.sock` left; `t94-trunk.log`), green at the
  head on both, under `taskset -c 0-3` (`t94-h94.log`).

**Wrong / not predicted.**
- The limit is 12 here where ws66 read 11: this shell holds one
  inherited socket more (ws66's own note on its fd 8).
- A pid file in a directory that does not exist is no failure at all:
  `shell.pid_write` makes the directory. The test's limit-free shape
  puts the pid file under an ordinary FILE instead, where no directory
  can be made.
- A failed pid write can leave `<pid>.new` (the write's sibling); the
  undo removes it too.

### lobo#96

**Held, to the line** (as root in podman, `ng96-h96-lobo.log`,
`user-h96.log`): the master `Uid: 0 0 0 0`; under `user lw lwx;` the
hand `Uid: 1500 1500 1500 1500`, `Gid: 1600 1600 1600 1600`, `Groups:
1600`; under `user lw;` `Gid: 1500 ×4`, `Groups: 1500 1600` — nginx's
workers' lines; `worker_processes 1` is a master and one hand,
`worker_processes 2` two dropped hands; port 80 answers 200 and the
root-only 0600 file 403 (trunk with no `user`: 200); the logs are
`lw:root` from the start (the named delta: nginx's are `root:root`
until the first reopen) and after `-s reopen` with the access log moved
away the fresh one is `lw:root` and holds the request; `user nosuch;`
is `[emerg] getpwnam("nosuch") failed in <file>:1` at `-t` and at
start; not root, `-t` warns and exits 0; root with no `user` line is
one root process with its `[warn]`. `tools/lobo-user` 14/14 at the
head; at trunk 6 of 8 red (every `user` row refused to start,
`user-trunk.log`).

**Not predicted.**
- A reload whose configuration only root may read (0600) is refused by
  every dropped hand, which keeps serving its generation, while the
  master answers `reload complete (generation 2) workers=0/2`
  (`reload96-h96.log`): a named delta now (the directive table and
  `docs/WORKERS.md`), and the master's "complete" beside `workers=0/2`
  is misleading.

### lobo#81

**Held.**
- The shape (`silent81.py`, the release binary, the client on cpus
  8–15): one request to a silent upstream and 50 concurrent clients for
  10 s: **179,588 answered, 0 not, p50 2.6 ms, p99 6.1 ms, max 12.8
  ms** (trunk 0 of 250; the pinned nginx 328,903, p99 3.0 ms); with
  **eight** silent requests out, 179,213 and 0, p99 6.0 ms. `-s stop`
  exits 0 and the server is gone at once (trunk: still running 15 s
  later). The proxied clients see their connections end at the stop.
- `tests/serve/silent_upstream_e2e.lu`: red at trunk on both lanes (0
  of 20 answered, `-s stop` exit 1, the server still running 2 s later;
  `t81-trunk.log`), green at the head (60 of 60, the slowest read 1
  ms, stopped in 20 ms; `t81-h81.log`).
- `worker_connections`: `tools/lobo-shell`'s new row at 16 with one
  listener and eight proxied requests: both servers `map=00000001
  held=closed` and both log the `[alert]` (oracle 2, lobo 3); at trunk
  the row is red (`map=00000000 held=none`: the first exchange held the
  loop; `shell-trunk.log`). 44 probes, 42 parity, 2 named deltas.
- The proxy suite unchanged: `proxy-differential` 8/8, the log
  differential, `lobo-resolver` 9/9 (the access line names the resolved
  `$upstream_addr`, so the record's round trip holds), `lobo-metrics`
  (`tools-h81.log`); corpus 372/372.
- At rest the process holds one descriptor more, the job listener (20
  by a harness that hands lobo no inherited socket; trunk 19).
- The drain: with `worker_shutdown_timeout 1s`, a reload while an
  exchange waits on a silent upstream ends it 1.25 s later, the
  upstream connection is closed by the loop from the proc's notes, and
  the descriptors return to 20 (`drain81-h81.log`). `-s quit` with an
  exchange out ends at the generation's shutdown timeout (1.27 s).
- Membudget 25/25: `flat, proxied` grew −1,572 KB over 2,000 proxied
  requests (`membudget-h81c.log`).

**Wrong.**
- **Throughput**: proxied requests a second against a prompt upstream
  are about HALF trunk's, not 0.6–1.0x. One client in turn, 20,000
  requests, three alternating runs: 6,601 / 7,109 / 6,811 (trunk)
  against 3,140 / 3,443 / 3,241 (head), 0.48x (`px81-tput.log`).
  `ab -k -c 32`, the pinned nginx as the upstream: 11,550 / 11,040 /
  10,264 against 6,590 / 6,124 / 4,492, 0.44–0.57x (`abpx-c32.log`);
  nginx as the proxy in the same shape 14,201 / 13,397 / 14,126
  (`abpx-ng-c32.log`). Load 15–17 throughout. Reusing an exchange's
  job socket for the next (an experiment, not kept: it holds idle
  descriptors at rest) gave 1.21x and 1.26x on two runs of three.
- One exchange out holds four descriptors more (24 against 20), not
  five.
- A client that closes while its exchange waits is not noticed: nginx
  (`proxy_ignore_client_abort off`) drops the exchange and frees both
  connections at once; lobo's proc is parked on its upstream, so the
  exchange (and its two connections) lasts until `proxy_read_timeout`.
  `lobo-shell` records it as a named delta (oracle `after=200`, lobo
  `after=closed`).

**Not predicted.**
- **A proc kept what it allocated outside a region block**: each
  exchange left about 27.5 kB behind (2,000 proxied requests grew the
  process 55 MB; threads and descriptors flat), with the proc joined at
  its report or not. Every allocation of `job_run` now lives in a
  `region job { }` block, and the growth is +12 kB. Suspected a wolf
  defect (a proc's ambient region not returned at its end); not reduced
  to a repro here.
- `spawn proc proxy.job_run(…)` does not compile (`a dotted proc
  path`, wolf-lang#655); main spawns a one-line trampoline.
- `net_deadline(fd, 0)` CLEARS a socket's budget: the first kill-path
  read of the job socket parked the whole loop (the drain measurement
  found it: `status`, `quit` and `stop` unanswered). The kill path asks
  `net_wait` with no wait before each read now.
- A killed exchange answers its client `502 Bad Gateway` before it is
  gone: the kill unparks its upstream read and the proc runs on to its
  next park (wolf-lang#683's shape), where nginx closes the connection.
- `keepalive_requests` (1000) ends a membudget drive of 2,000 on one
  connection; the proxied row drives five connections.

### Slips, named

- One scratch file was written to `/tmp` on nomad-1 and removed at
  once; one rigback helper of this lane's was stopped by a `pgrep -f`
  on this lane's own scratch path rather than by its recorded pid.
  Neither touched anything else.

## 4. Evidence index

kasumi `~/lanes/ws67/` (sha256 prefixes): `toolchains.txt`,
`dl/digest-check.txt`; the gauntlets `logs/g-trunk.log` 20a9c93e7e55…
(trunk, GREEN, 368/368), `logs/g-h81.log` fe93516e0a7f… (the #81 tree
before the shell row, GREEN, 372/372, 25/25, user 14/14, 0 SKIP),
`logs/g-head.log` (the head, see the PR); #94 `ev/s94-trunk-rel.log`
6f0da9872c4f…, `ev/s94-h94-rel.log` 0790e2eb2734…, `ev/ng94.log`
1fc65e7c17be…, `ev/t94-trunk.log` ddfefce974cf…, `ev/t94-h94.log`
c87859d2670c…; #96 `ev/ng96-trunk.log` 97d0ab397517…,
`ev/ng96-h96-lobo.log` 52acdd2b666e…, `ev/user-h96.log` de298ad5be33…,
`ev/user-trunk.log` e794a5992d91…, `ev/reload96-h96.log` cef5b831de41…;
#81 `ev/s81-trunk-rel.log` 6368615e7648…, `ev/s81-nginx.log`
99a421d9bf73…, `ev/s81-h81-rel.log` c5f5f83a71e5…,
`ev/s81-h81-rel-8.log` e9ec3405982c…, `ev/t81-trunk.log`
314d9733fdd7…, `ev/t81-h81.log` e00018453928…, `ev/ngwc.log`
dfffde7911a0…, `ev/shell-h81.log` 36df3039733f…, `ev/shell-trunk.log`
2112dfaf8990…, `ev/membudget-h81c.log` 6de3f2f4716d…,
`ev/drain81-h81.log` ad881aa85d19…, `ev/px81-tput.log` 06c7c25455fd…,
`ev/abpx-c32.log` 89624ee0b36d…, `ev/abpx-ng-c32.log` aec1c3d04ece…,
`ev/tools-h81.log` c13c891f2ec7…. Scripts: `scripts/` (stage, build,
g, t, q, sock94, ng94, ng96, reload96, silent81, ngwc, drain81, px81,
abpx, abpxng).

CI: the PR's runs, the plants `ws67-plant` (trunk's src and the two new
e2e tests) and `ws67-plant-user` (trunk's src and the `user` step) —
their ids and verdicts are in the PR.

## Not verified

macOS beyond CI (the drop is linux's; the stale socket's limit walk and
the silent upstream on the runner only); a master with hands at its
descriptor limit with exchanges out; an https upstream that never
answers (the same proc; not driven); a TLS listener's proxied request
(still a named 502); `cert auto` under `user` (the ACME store must be
the user's to write); a rootless engine without a subordinate id map;
the proc-memory finding in isolation.

## 5. Done-when

Branch `ws67`, the PR open and unmerged, CI green at its head with the
gauntlet's log read, `wolf/tools/lane-audit.sh lobo ws67 <PR>` run from
the org directory. lobo#94, #96 and #81 are the orchestrator's to close
by hand at the merge. `ws67-plant` and `ws67-plant-user` stay on origin
as evidence.
