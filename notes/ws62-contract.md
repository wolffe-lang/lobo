# ws62 — the pin at 0.2.28, and what PAX found

Wave 53, lane ws62 (Opus). Written 2026-10-12 on lobo trunk `944edc1`
(0.1.3 with the channel flipped to `+dev`), after the inputs below were
re-derived and measured and before any edit to `src/`, `tools/`,
`tests/` or `wolf-toolchain.toml`. The planning contract is
`sprints/wws/31-the-pin-0228/ws62-the-pin-0228.md` in
`wolffe-lang/wolf`; rules are `sprints/wave-53.md` down to
`wave-45.md`. The oracle is the pinned nginx 1.30.4 (ws47's copy,
`65595ac2…`), run, never read.

One deliverable: lobo pinned to wolf 0.2.28 / lupin 0.1.51 with
`conn.sock_read` back to `net_read` (s228), and the four lobo findings
px25 made running lobo on PAX, each reproduced on Linux at trunk and
each fixed under a test red at trunk:

- **(a)** only the first `server` block is served;
- **(b)** a worker the master replaces comes back at `generation=1`
  while its siblings are at a later one;
- **(c)** the master's resident set grows under supervision (px25: about
  350 kB a minute);
- **(d)** the pid file holds no pid (wolf-lang#126).

Then lobo#68's remainder and lobo#72 if in reach, and the silent-upstream
proxy finding (ws61) fixed or drafted for filing.

## 1. Forbidden, absolutely

- nginx behaviour only from the pinned oracle; never read nginx's, any
  other server's, GNU's, glibc's, musl's or a kernel's source (PAX's
  own `kernel/procfs` is this org's wolf and was read for one field
  name, below).
- The pin is taken from the release archives by digest: never a clone,
  Homebrew or `~/.local/bin`; never a build of wolf-lang trunk.
- No `rm` outside `~/lanes/ws62/` (nomad-1 and kasumi) and this lane's
  own clones; no scratch in `/tmp`. No `git add -A`. Nothing under
  `~/.claude`. No package installs. No merge, tag or release; no issue
  filed or closed (they are listed in the report). No commit trailers
  or PR attribution of any kind. Checksums carry a trailing `…`. No
  "seen red" without a run id, sha, path or digest.
- Strict evidence (wolf-lang#571): `WOLF_PAIRING_REQUIRE_SIBLING=1`,
  stdout and stderr together, every SKIP line counted; a `wolf build`
  that exits 2 is a compile error, never a skip; process-spawning rows
  also under `taskset -c 0-3`.
- No new `spawn proc`, channel send, or bytes moved across a region
  block (wolf-lang#678's open half).
- kasumi: remote commands in `bash -c`, `setsid` with a pid file, kill
  by recorded pid only, outputs pruned (the disk is at 97 %). No build
  on nomad-1 beyond nothing: lobo's macOS gates run in CI. At most two
  CI runs of this lane at once; never cancel another lane's.
- Never touch the maintainer's tunnels, DNS, ports 8080 or 8088 (on any
  host), or hasu's `~/models`, `~/.local`, `~/pool-serve`, the :9308
  server. This lane's ports are 18700–18749 and kernel-chosen ones.
- No parity figure without the host's load beside it; the runner VMs
  give the numbers of record.

## 2. Inputs, verified (re-derived 2026-10-12)

| input | what was found |
|---|---|
| wolf 0.2.28 | tag `v0.2.28` → wolf-lang `f71ece8e1ad2…`; release 410118732. Asset digests from the API: linux x86-64 `3215f321…`, linux aarch64 `f2697a69…`, macOS arm64 `656ab553…`, windows `bb9e2f5f…`. Staged on kasumi by digest (`kasumi:~/lanes/ws62/dl/digest-check.txt`): `wolf` 39644daa…, `libwolf_rt.a` d856cb81…, `wolf-cimport-worker` d0e63dec…; `wolf 0.2.28 (wolfgang, pin f71ece8)`; highest glibc symbol GLIBC_2.34 |
| lupin 0.1.51 | tag `v0.1.51` → wolf-interp `f72e78d7a9d0…`; release 409991647; linux x86-64 `d8f62dd1…` (the PAIRING's digest), macOS arm64 `2b11a7d1…`, linux aarch64 `e29d02bf…`, windows zip `06ccce94…`, `lupin.exe` `3875deea…`. `lupin` 583c573b…, `lupin 0.1.51 (wolf-interp, reference interpreter at pin 294d626)` |
| 0.2.27 beside it | re-staged by digest for the trunk comparisons: `wolf` 6f5713a2…, `libwolf_rt.a` ab575b27…, `lupin` 3a476442… — ws58's and ws59's bytes |
| 0.2.28's CHANGELOG | read at the tag: the soundness section (#660, #665, #678's direct half: E1010 refusals), "Read this before you bump the pin" (four new refusal shapes; eight new prelude names), s228 (`net_read` allocates in the region it is called in; handle tables keyed by live numbers, #661; a finished proc's residue, #662), the bundled std `98e1b7b`, and the downstream line for lobo: "the toolchain digests; `conn.sock_read` can go back to `net_read`" |
| trunk at 0.2.28 | `src/` at `944edc1` builds on both tiers at `--error-limit=0` with **zero diagnostics** (`kasumi:~/lanes/ws62/build-t28.log`): no E1010 from the four new shapes, no W0304 from the eight names. Release 13,521,248 → 13,880,080 bytes (text 1,691,412 → 1,711,464) against 0.2.27, the runtime's bytes (`build-t27.log`, `build-t28.log`) |
| `[std]` | held at `14f0ab2c` (ws58's reasoning stands: lobo stages named members, then its own std). Whether it builds at 0.2.28 is the line above |
| `sock_read` | three sites: `conn.sock_read` (the serving loop's read), `proxy.lu`'s private twin (four upstream readers), `main.lu`'s `sock_line` (the control reader) |
| **(a)** reproduced | `kasumi:~/lanes/ws62/repro.sh` at trunk, 0.2.28 release build: three server blocks, two on 127.0.0.1:18711 (the second named `b.test`), one on 18712. `18711 → site-a`; `18712 → connection refused` (nothing bound); `18711 Host: b.test → site-a`. In the code: `parse.build_index` builds the location table and the route rows for `ix_server` only (the first `server` under `http`); `serve.listen_addr_plain` and `ssl_listen_addr` bind the first plaintext and first TLS `listen` in the whole config; `proxy.plan` has its own walk of the first server's locations; dryrun names `first-server` / `not-first-server` (docs/DRYRUN.md's named delta). Limits, access logs and metrics resolve "the first server's row, else http's" (`limitsconf`, `logconf`, `metricsconf`) |
| **(b)** reproduced | same script, `worker_processes 2`: two reloads put both hands at generation 3; hand 1 SIGKILLed (its pid read as the recorded master's child); the replacement reads `generation=1 … restarts=1` beside `generation=3`. In the code: `spawn_worker` hands the child `-c` and its ordinal only; the hand's `serve_main` pushes generation 1 |
| **(c)** measured | `kasumi:~/lanes/ws62/rss.sh`: four hands, idle, VmRSS every 10 s for 300 s. Master at 0.2.27: 8,692 → 10,392 kB, **+340 kB a minute** (px25's figure). Master at 0.2.28, same source: 4,684 → 5,980 kB, **+259 kB a minute**. Hands at 0.2.28: flat after the first minute (0.2.27: +16 kB a minute each, the per-socket table s228 fixed). Load average 27–32 (other lanes). The master loop runs a pass per 250 ms wait and probes each hand every 200 ms (a connect); every pass rebuilds `wprobe` and `wfail` per hand (`replace_int`: a new list), builds two wait lists and the probe's dial, all in the master's root region, never freed |
| **(d)** reproduced | the pid file's bytes at both shapes are `unix:logs/control.sock\n` — the configured control endpoint, no pid. 0.2.28 has **no** `os_pid` (s232's, on wolf-lang trunk after the tag, not released). What 0.2.28 has: `os_proc_pid(h)` (s219: a CHILD's pid, so the master can know each hand's), and the host's own answers — `/proc/self/status` (`Tgid:`) on Linux and on PAX (px34/px25's procfs prints `Tgid`; its `Pid` is the reading thread's id), and on macOS a child's `$PPID` (`/bin/sh -c 'echo $PPID'`), which is the caller's pid by POSIX |
| lobo#68 | open; ws59 took levers A–D (18,046 → 15,866 instructions a keepalive request; nginx 13,598); E (head and route) and the `fs_stat` floor (wolf-lang#690) remain |
| lobo#72 | open; ws59: not reproduced in 300 loaded rounds |
| the silent upstream | ws61's finding: a proxied request whose upstream accepts and never answers holds the whole process for `proxy_read_timeout` (0.1.2 the same); not filed |
| trunk's gauntlet | at `944edc1` on its own pin (0.2.27): `kasumi:~/lanes/ws62/g-gtrunk.log` (the baseline every later run is read against) |

## 3. Prediction, committed before the first change

### The pin, and `net_read` back

- Both tiers build with zero diagnostics at 0.2.28 (already measured on
  trunk's source: an input). The gauntlet is GREEN at the pin commit
  with the same per-step verdicts as trunk at 0.2.27.
- `net_read` back at the three sites: no verdict moves; the membudget
  gate holds 23/23 with growth per keepalive request ≤ 5 bytes and per
  connection ≤ 100 bytes (ws57: 4.6 and 70), the region ledger now
  charging `net_read`'s bytes where `sock_read` charged its own copy.
  User instructions per keepalive request fall by 50–300 (one decode
  pass and one list fewer per read).

### (b) the generation a replacement starts at

Cause as above. Fix: the master hands a replacement its current
generation and that generation's config id (`--generation G
--generation-id H`, internal flags beside `--worker`); the hand starts
its table at G. When the file on disk is no longer generation G's (an
edit with no reload since), the hand still serves the disk's config —
nginx's master keeps its own copy, lobo's hands read the file — and
says so in a `warn` line naming both ids: a named delta, not hidden.
Test: `tests/shell/replace_generation_e2e.lu`, two reloads then hand 1
told to stop, the replacement's row must read the master's generation:
**red at trunk** (`generation=1`), green after.

### (d) the pid file

The pid file holds the master's pid, `<pid>\n`, nginx's format, so
`kill -HUP "$(cat logs/lobo.pid)"` works: read from `/proc/self/status`
(`Tgid:`) on Linux and PAX, from `/bin/sh -c 'echo $PPID'` where there
is no `/proc` (macOS). The control endpoint is no longer in the file:
`-s`, `status` and the stale check derive it from the configuration
(`control`, resolved under `-p`), which they already read; only an
endpoint the config cannot name (`control 127.0.0.1:0`) is recorded, on
a second line. A host that answers neither keeps 0.1.3's form (the
endpoint alone) and says so at start. The master's status rows gain
each hand's pid (`pid=`, `os_proc_pid`). Test:
`tests/shell/pid_file_e2e.lu` (the file's first line equals the
spawned master's `os_proc_pid`; `-s`/`status` still reach it) — **red
at trunk** on both hosts. Windows is not built by lobo.

### (c) the master's memory

The growth is the master's per-pass allocations in its root region:
predicted shares, the two rebuilt tables per hand per pass 60 %, the
wait lists 20 %, the probe's dial and the stanza strings 20 %. Fix:
the master's pass runs in `region pass`, the hand table is stored in
place by index, and what must grow (a respawned hand's endpoint) is
aimed at a `life` region. Predicted after: **≤ 4 kB a minute** over
minutes 1–5 at four hands idle (≥ 98 % of the 259 removed), and flat
under a reload every 10 s. Gate: a membudget row, the master idle with
four hands for 60 s after a 20 s warm-up, bound 64 kB — **red at
trunk** (about 260 kB at 0.2.28).

### (a) every server block served

Design (no new process shape, no change to a one-server config's
path):

- `config` resolves the route rows (locations, `root`, `alias`,
  `index`, `proxy_pass`, `max_ranges`) for **every** `server` block
  under `http`, in row order, and a listener table: each distinct
  `listen` address (plaintext and `ssl` separately), its servers in
  row order, its default (`default_server`, else the first).
- Server selection is nginx's at a listener: the request's `Host`
  (lower-cased, port and a trailing dot stripped) against the
  candidates' `server_name`s — exact, then the longest leading
  wildcard (`*.example.com`, and `.example.com` for both), then the
  longest trailing wildcard (`www.*`); a regex name (`~…`) never
  matches here and is named at load; no match is the listener's
  default. A one-server config never compares a string.
- The master, the single process and the hands bind or adopt every
  plaintext address and every TLS address (descriptors 3, 4, … in the
  table's order; `--inherit N` takes any count); a connection row
  carries its listener, and the request is routed in its server.
  `proxy.plan` and the dry-run take the server; the dry-run's trace
  says `host-match`, `default-server`, `not-selected` (and the listener
  by the probe URL's port).
- What is still read from the first server only, at this lane:
  `client_max_body_size` and the other limits, `access_log`/`error_log`,
  `metrics`: each a named delta, warned at `-t` and at start when a
  later server sets one.

Tests, each **red at trunk**: `tests/serve/vhost_e2e.lu` (two ports,
two names on one port, a default; a reload that moves a name), unit
rows for the selection (`tests/config/server_pick.lu`, every lane), a
dry-run probe per selection reason; and differential rows against the
pinned nginx: the harness gains an `--- http` section (more server
blocks at `@PORT@`) so name-based selection is diffed byte for byte.
Predicted 0 differences on those rows.

### Parity and memory at the head

- Parity at four hands on the runner VMs (lower is better, bar 1.10):
  keepalive 0.90–0.94x, close 1.01–1.05x (ws59: 0.913x / 1.030x), no
  row worse than ws59's beyond the VMs' spread. The server pick costs
  nothing on a one-server config (a length test).
- Membudget 23/23 plus the new master row; RSS after 400,000 keepalive
  requests within 1 MB of ws58's 4.6 MB.

### lobo#68, lobo#72, the silent upstream

Taken only after (a)–(d) are green. Expected not in reach: lobo#68's
lever E and lobo#72 stay open with nothing new; the silent upstream is
drafted for filing (the proxy runs inline in the loop; making it
non-blocking is a lane of its own).

## 3. The prediction against the measurement

| item | predicted | measured |
|---|---|---|
| the pin | 0 diagnostics both tiers; gauntlet green with trunk's verdicts | 0 diagnostics (an input); gauntlet GREEN at the head, 0 SKIP (`kasumi:~/lanes/ws62/g-ga10.log`). **Not predicted:** the checked machine runs procs at 0.2.28 (s226), so the three `checked-refuses` files failed; `cap_shape.lu` declares `checked`, `budget_cap.lu` (ledger units per tier: `breach cls=0 rt=18`) and `body_join_kill.lu` (the runner's 60 s ceiling, once) declare native only (`kasumi:~/lanes/ws62/t-chk.log`) |
| `net_read` back | membudget 23/23, ≤ 5 B a keepalive request, ≤ 100 B a connection | 24/24 (the new master row included): 0 KB over 4,000 keepalive requests and over 2,000 connections; 400,000 keepalive requests in one process end at 4.98 MB resident (ws58: 4.6 MB). User instructions a request were **not measured** |
| (b) | red at trunk, the replacement at the master's generation; a warn on an edited file | red at trunk on both lanes (`red-b-trunk.log`: line 163, `generation=1`); green at head; the warn line seen by the test |
| (d) | `<pid>\n`; red at trunk on both hosts; rows carry `pid=` | red at trunk on linux (`red-d-trunk.log`, line 195: the file was `127.0.0.1:N`); green at head on linux; a port-0 control rides a second line; `tools/lobo-signal` now sends its SIGHUP to the file's pid (22/22). macOS: CI only |
| (c) | 60/20/20 shares; ≤ 4 kB a minute after; flat under a reload every 10 s | **0 kB** over 300 s idle at four hands (`rss-c1idle/`); the shares were not separated. **Wrong on reloads:** about 21 KB a reload (30 reloads: 4,572 → 5,208 kB), against about 92 at trunk on 0.2.28 (`rss-t28reload/`) — bounded by the reloads, as the hands' ws57 rule is; the hands grow about 27 KB a reload either way. Membudget's master row: 392 KB in 60 s at trunk on 0.2.27 (RED, `mb-t27.log`), 0 at head |
| (a) | every server served; red at trunk; 0 differential differences | nine `vhost_*` differential rows byte-identical to the pinned nginx (33/33); eight red at trunk (`red-a-diff-trunk.log`; `vhost_default_first` is first-server either way); `vhost_e2e.lu` red at trunk at step 1 (line 202), green at head on native and checked; `server_pick.lu` on three lanes. **Not predicted:** a port-0 `listen` is a socket of its own, so two of them must not merge (the ACME rig's config: red in `g-ga7.log`, fixed by keying them `addr#n`); the dry-run's probe of `netbox` now names the plaintext server nginx would (it named the TLS one) |
| parity | runner 0.90–0.94x keepalive, 1.01–1.05x close | kasumi (load 2.24, `par-k4.log`, exit 0): nginx ÷ ws62 close **1.026x**, keepalive **0.981x**; ws62 ÷ trunk 0.990x / 1.003x. Runner VMs: the PR names the run |
| lobo#68, #72, the silent upstream | not in reach; drafted | not taken; the silent-upstream issue is drafted in the report |

## 4. Evidence index

kasumi `~/lanes/ws62/`: `toolchains.txt`, `dl/digest-check.txt`;
`build-t27.log`, `build-t28.log`, `build-t28-alt.log`; `repro.sh` and
`repro-t28/`; `rss-{t27,t28,c1}idle/`, `rss-{t28,c1}reload/`;
`red-b-trunk.log`, `red-d-trunk.log`, `red-a-trunk.log`,
`red-a-diff-trunk.log`, `mb-t27.log` (reds at trunk); `t-*.log`
(lane runs); `g-gtrunk.log` (trunk's gauntlet, exit 0) and
`g-ga10.log` (the head's, exit 0, 0 SKIP); `par-k4.log`;
`r4-head/r4.txt` (400,000 requests). The plant: branch
`ws62-plant` (a replacement at generation 1 again), its CI run named in
the PR.

## Not verified

- The pid file on PAX (`/proc/self/status`'s `Tgid:` read there was
  read from pax's own source, not run).
- macOS beyond CI: the `$PPID` path, multi-listener hands.
- User instructions a request after `net_read` came back.
- The per-cause shares of the master's old growth.
- TLS on a second distinct `listen … ssl` address beyond the unit
  table (no TLS e2e row binds two TLS addresses).
- Whether the checked machine's hang on `body_join_kill.lu` repeats.
