# ws69 — the exchange: its throughput, its watch, its clock (lobo#100, #104, #105)

Crawl 54, lane ws69 (Opus). Written 2026-10-20 on lobo trunk `251b6db`
(ws68's head, PR #103 merged), after the inputs below were re-derived and
measured (trunk, ws67's head and the pre-#81 tree on one box, the pinned
nginx as a black box, two shapes of the change tried and measured), and
before any change to `src/`, `tests/`, `tools/`, `docs/` or the CHANGELOG.
The planning contract is `sprints/wws/38-lobo-the-exchange/ws69-the-exchange.md`
in `wolffe-lang/wolf` (planning trunk `560c78f`); the rules are
`sprints/RULES.md`.

Three issues, all in the proxied exchange, and one regression found on the
way:

1. **lobo#100**: proxied throughput is about half the pre-#81 tree's with
   one client in turn. Recover it without holding the serving loop again.
2. **lobo#104**: an https upstream's wait does not watch the client, and a
   client that pipelines a request during a proxied wait gets
   `Connection: close` instead of a second answer.
3. **lobo#105**: an exchange ended by the client's close logs
   `$request_time` from the loop's pass clock.
4. **Found** (§2): since ws68 a draining generation cannot end a proxied
   exchange that waits on a silent upstream, and the loop is held while it
   tries — the thing #81 fixed.

## 1. Forbidden, absolutely

- **Nothing here deploys or serves anything public.** lobo serves no site of
  ours; lupp.us is nginx on almanta (`sprints/HOSTING.md`). Never almanta,
  the live nginx, any Cloudflare tunnel or `~/.cloudflared`, DNS, or host
  ports 8080 and 8088. Every server this lane starts binds 127.0.0.1 on a
  kernel-chosen port or one of 18940–18959, inside a throwaway rootless
  container's own network namespace for the throughput rows, and is stopped
  through its control endpoint or by its recorded pid.
- **Clean-room against nginx's source**: its documentation
  (`proxy_ignore_client_abort`, `proxy_read_timeout`,
  `worker_shutdown_timeout`, `$request_time`) and black-box runs of the
  pinned 1.30.4 (`65595ac2…`) only.
- No merge, no tag, no release (0.1.5 stays untagged), no tap or AUR
  change. No issue filed or closed (listed in the report). No attribution
  or co-author trailer in any commit or PR text.
- Toolchains only from the published release archives by digest, each
  digest read twice; lobo's pins do not move.
- No assertion deleted or weakened; no timeout or retry as a fix.
- No `rm` outside `~/lanes/ws69/` and the lane's `/tmp/ws69-*` scratch on
  kasumi; no `git add -A`; nothing under `~/.claude`; no package installs;
  the branch asserted before every commit; no build on nomad-1. kasumi:
  `bash -c`, `setsid -f` with a pid file, kill by recorded pid only.
- Strict evidence (wolf-lang#571): `WOLF_PAIRING_REQUIRE_SIBLING=1`, stdout
  and stderr together, every SKIP line counted; measurements under
  `taskset -c 0-3`, three runs or more, the spread given.

## 2. Inputs, verified (re-derived 2026-10-20)

Logs under `kasumi:~/lanes/ws69/` (`ev/`, `logs/`; digests in §4).

| input | what was found |
|---|---|
| lobo trunk | `251b6db0d699…` (ws68's notes, PR #103 merged); origin has nothing later. ws67's head `9e4ce7fc6b80…`; the pre-#81 tree `52a2ae7e7304…` (tl28's CI, the base ws67 rebased onto) |
| wolf 0.2.33 | tag `v0.2.33` (annotated `56110e4f…`) → wolf-lang `85dab5d7…`; linux x86-64 archive `4f955e8d…` (80,128,936 B), the API read twice; staged on kasumi and `sha256sum -c` twice (`dl/digest-check.txt`): `wolf` 58e4ade4…, `libwolf_rt.a` 5321ce86…, `wolf-cimport-worker` 57c41e39…; the archive's `std/STD-REV` `cceda631…` |
| lupin 0.1.54 | tag `v0.1.54` (annotated `9c98d445…`) → wolf-interp `0e536e8f…`; `175df238…` (2,971,403 B), twice; `lupin` a9856dd4… |
| wolf-std | lobo's `[std]` `cceda63` (ws68), unmoved |
| the oracle, ab | nginx 1.30.4 `65595ac2…` and ApacheBench 2.3 `05f2f6d5…`, copied from ws68's lane by digest, each checked twice |
| the trees built | release tier at 0.2.33 / `cceda63`, zero diagnostics (`logs/build-*.log`): pre-#81 `9e7261d1…`, ws67's head `33e8d02d…`, trunk `c5d72d94…` |
| kasumi | i9-11900K: 16 cpus, 8 cores, **cpu N and N+8 one core's two threads**; `powersave` governor; other lanes beside this one, load 0.5–22 over the day |
| the measuring rig | `scripts/tput.sh`: a rootless `archlinux:base-devel` container (its own network namespace, where the oracle and ab run), the proxy under `taskset -c 0-3`, the pinned nginx as a prompt upstream (2 workers, a 16-byte file) on cpus 4–5, the client on 6–7 — three disjoint sets of cores. Shapes: **`ab32`** and **`ab1`** (ws67's `abpx`: `ab -k`, 2,000 warm-up requests, 20,000 measured, 32 clients or one) and **`px`** (ws67's `px81.py`, `6ddc1608…`, as `px69.py`: 20,000 proxied keepalive requests over 20 connections in turn with a 4,000-byte header and a python upstream; the server under `taskset -c 0-3`). The nginx row is the pinned nginx as the proxy, one worker (ws67's `abpxng`). Rounds alternate the servers. `scripts/summ.py` gives each row's runs, median and spread |

**lobo#100, the baseline, re-measured first** (`ev/tput-base2.log`, load
0.6–2.0, three rounds; req/s, median and the runs' spread):

| shape | nginx | pre-#81 | ws67's head | trunk |
|---|---|---|---|---|
| px (one client in turn) | — | 23,211 (22,721–24,298) | 11,644 (11,638–12,016) | 13,241 (12,576–13,259) |
| ab1 (one client in turn) | 28,189 (16,754–29,017) | 26,740 (16,488–26,801) | 13,620 (13,592–13,638) | 13,989 (13,962–14,644) |
| ab32 (32 clients) | 18,144 (17,891–52,670) | 17,005 (16,854–30,931) | 22,501 (16,061–24,016) | 23,140 (16,082–24,698) |

- With one client in turn the head is **0.50–0.57x** the pre-#81 tree
  (px 0.57x, ab1 0.52x on the medians): ws67's 0.48x and ws68's 0.48–0.50x
  reproduce. With 32 clients the exchanges overlap and the gap is gone on a
  quiet box; ws67's 0.44–0.57x at `ab -c 32` was measured at load 15–17 on
  all sixteen cpus. Under load 10–13 (`ev/tput-e2.log`, five rounds) ab32
  reads pre-#81 15,639, trunk 15,192 (0.97x) and ab1 15,018 against 9,370
  (0.62x).
- The `ab` shapes are **bimodal** on this box (a run reads ~17k or ~27–52k,
  for nginx too): the upper mode is a run whose cores stayed out of deep
  idle. `px`, which spends its time in the python client, is not. A first
  layout put the upstream on cpus 8–11, the server's own cores
  (`ev/tput-base.log`), and is not used.

**Where trunk's time goes** (`scripts/prof.sh`, `sysc.sh`; `ab -k -c 1`):

- User instructions per proxied request (`perf stat -e instructions:u`
  over 20,000): **pre-#81 50,400, trunk 125,500** (two runs each, at load
  1 and 17: the counts agree to 1%). Task clock 54 µs a request against
  100 µs at load 1.
- Syscalls per proxied request (lobo started under `strace -f -c`, the
  difference of 10,000 requests and none): **pre-#81 9.25** (recvfrom 2.0,
  sendto 2.0, close, poll, socket, ioctl, connect 1.0 each), **trunk 44.6**
  (futex 9.3, sendto 7.0, recvfrom 6.0, close 3.0, poll 3.0, madvise 2.0,
  socket, ioctl, connect, epoll_ctl, epoll_wait 2.0 each, read, accept4,
  setsockopt, write 1.0 each). The job socket is a socket, a connect, an
  accept, a nodelay, two closes and two reactor registrations a request;
  the proc is a task, its scope and its stack's return (madvise); its end
  sends a pool worker into a steal scan of the whole worker table.
- The profile (`perf record`, user only): the runtime's net-table mutex
  contended 9.7% (two threads in `net_deadline` at once), pool workers
  scanning for work after each proc ends ~9% (`find_task`, `try_steal`),
  then strings.

**Two shapes tried, measured before one is chosen** (on trunk, not kept as
written; `t-e1/`, `t-e2/` on kasumi):

- **E1, the job socket kept**: a free list of job socket pairs, a spawn per
  exchange still.
- **E2, a pool of exchange procs**: procs that live across exchanges, each
  on its own job socket made once, handed a job by one write; a proc idle
  five seconds leaves.
- `ev/tput-e2.log` (load 10–13, five rounds, medians): px pre-#81 12,099,
  trunk 7,970, **E1 10,907, E2 12,692**; ab1 15,018 / 9,370 / **13,351 /
  14,125**; ab32 15,639 / 15,192 / **16,443 / 16,537**. E2 is at the
  pre-#81 tree's number in every shape; E1 is 0.89–0.90x with one client.

**The regression found** (`scripts/drain81.py`, ws67's, by digest;
`ev/drain-base.log`): a proxied request waits on a silent upstream
(`proxy_read_timeout 30s`) and a reload drains its generation under
`worker_shutdown_timeout 1s`.
- ws67's head: the client reads `502` 1.25 s after the reload, the
  upstream connection ends with it, `status` answers, `-s quit` with an
  exchange out ends the server in 1.27 s.
- **trunk: the client reads nothing for 10 s, the upstream connection is
  never ended, `status` gets no answer, `-s quit` is not obeyed in 3 s and
  `-s stop` not in 5 s (the server was put down by its pid).** ws68's
  watch (lobo#99) waits in `net_wait`, which is one `poll(2)`
  (`wolf_rt/src/poll.rs`); a kill reaches only the reactor's parks, so
  `stream_kill`'s join holds the serving loop until the poll's budget,
  `proxy_read_timeout`. No gauntlet row drives the drain of a waiting
  exchange; ws67 measured it by hand.
- nginx (`scripts/drainng.py`, `ev/drain-nginx.log`): the client reads
  end-of-stream and the upstream connection ends 1.10 s after the reload;
  the access log carries the request as `000 0`; a GET after it is 200.

**lobo#104 and #105, black box** (`scripts/probe69.py`, `ev/probe-e3.log`;
a silent plaintext upstream, a silent https one that accepts and never
answers its ClientHello, an upstream that answers after a delay; access
log `$status $body_bytes_sent "$request" up= ust= rt=$request_time`):

| shape | nginx | trunk |
|---|---|---|
| A: plaintext, the client closes 1.0 s after its request | upstream closed +0.000 s; `499 0 … ust=- rt=1.000` | +0.000 s; `rt=0.751` |
| B: https, the same | +0.000 s; `499 0 … rt=1.000` | **not closed in 2.5 s**, no line until the read deadline |
| C: a static GET pipelined 0.3 s into a proxied wait of 1.0 s | two responses at 1.01 s, no `Connection: close`, a third request served | **one response, `Connection: close`**; the third request reads end-of-stream |
| D: a static GET on a keepalive connection idle 1.0 s; a proxied GET answered in 0.5 s | `rt=0.000`; `rt=0.503` | **`rt=0.250`; `rt=0.750`** |

- **#105 is two clocks, not one.** The loop reads `now` at the top of a
  pass, BEFORE its wait. A request whose bytes arrive during the wait is
  started at that clock, up to `wait_budget` (250 ms) early, and an
  exchange reported during a wait is ended at it: a static GET on an idle
  keepalive connection logs 0.250 where nginx logs 0.000, and every
  proxied request on one is 0.25 s long. ws68's 0.751 was the end clock
  alone.
- **#104's https half**: the https leg's reads are `std.x.tls.client`'s
  (`read` reads a whole record with blocking reads, and skips a
  post-handshake message such as a NewSessionTicket inside the same call,
  `std/x/tls/client/client.lu` `read`, `read_record`, `read_exact` at
  `cceda63`). It buffers nothing past a record, so the upstream socket
  readable is the right gate before each call — except that a call which
  meets a ticket goes on to wait for the next record inside std.
- **#104's pipelined half**: the proc read the pipelined bytes in its
  watch and could not hand them back. In shape C the second request,
  answered, would still wait for the loop's next wait to end: a row whose
  carry holds a whole head is stepped only after a wait no byte ends (the
  wait does not know the row is owed an answer).

## 3. Prediction, committed before the first change

### 1. lobo#100: the exchange pool

- **The shape: E2.** The serving loop keeps a POOL of exchange procs
  (`PxSlot`: the proc, its job socket's two ends, the client and id of the
  exchange it runs, when it went idle, when it was asked to stop). A
  proxied exchange goes to an idle proc of the pool — one write, `j
  <client> <id> <joblen> <taillen>\n` and the job and the tail — and a new
  proc on a new job socket is made only when none is idle. The proc
  (`proxy.job_loop`) answers the client, writes its account on its job
  socket and its line on the stream pipe, and waits for the next job.
  `job_run` and the one-proc-per-exchange spawn go. A proc idle five
  seconds (`px_idle_ms`) leaves (`q`, and the loop closes its end), and
  the idle ones leave at once when an accept is refused for want of a
  descriptor.
- **Why not E1**: it keeps the spawn, the task's end and its steal scan,
  and measured 0.89–0.90x with one client. **Why not a job socket kept
  per connection, or the loop multiplexing the upstream**: the first holds
  descriptors for every idle keepalive connection that ever proxied; the
  second needs a non-blocking connect wolf does not have
  (`net_connect` blocks: a remote upstream that drops SYNs would hold the
  loop), and std's TLS client blocks (ws67's argument, re-read).
- **Measured** (`tput.sh`, the four trees and nginx, five rounds,
  alternating): **px and ab1 at least 0.95x the pre-#81 tree's median, and
  ab32 not below it**; trunk unchanged at 0.50–0.62x with one client.
  Syscalls per proxied request 44.6 → **at most 26** (no socket, connect,
  accept, nodelay or close of a job socket; no epoll registration; no
  spawn), user instructions per request at most 105,000.
- **What it costs**: at rest 20 descriptors as now; after proxied traffic
  two more per proc the busiest moment needed, for five seconds after the
  last exchange, then 20 again. Threads: an idle proc is parked in its
  wait (one thread and its compensation, ws63's figure), for those five
  seconds. ws64's limits unchanged: a proxied request is two connections
  against `worker_connections` while its exchange is out, as now.

### 2. The drain regression: a stop the proc's every wait watches

- Every wait of a proc of the pool — its wait for a job, and each of its
  exchange's waits on the upstream (`up_wait`) — has its job socket in the
  set. A drain past `worker_shutdown_timeout` writes ONE byte, `s`, on it:
  the wait ends, the upstream is closed, nothing more is written to the
  client, and the account says 497; the loop closes the row as aborted
  (logged and counted as ws67's kill was: not at all) and the proc goes
  back to the pool. A stop that has not landed in 100 ms (`px_stop_ms`: a
  proc parked in a write to a client that does not read, which no byte
  reaches) is a kill, as ws67's was: `k` first, so that a proc that runs on
  past the kill (wolf-lang#683) returns at its next wait instead of waiting
  for a job forever, then the kill, the join, and the notes' upstream
  descriptors and both job socket ends closed.
- **Measured** (`drain81.py`): the client reads end-of-stream (ws67: a
  `502`; nginx: end-of-stream) and the upstream connection ends ~1.25 s
  after the reload; `status` answers; descriptors return to 22 (the pool's
  one proc) and 20 five seconds later; `-s quit` with an exchange out
  ends in ~1.27 s. **A test, `tests/serve/exchange_drain_e2e.lu`**
  (native, checked): red at trunk (the upstream not closed in 3 s,
  `status` unanswered, `-s stop` not obeyed), green after.
- Not changed, named: nginx logs the cut request `000 0`; lobo logs
  nothing (ws67's posture).

### 3. lobo#104

- **https**: the https leg waits with `up_wait` too — for the server's
  first flight before the handshake's reads (an upstream that accepts and
  never answers), and before each record lobo asks std for (the head and
  the body). Shape B: the upstream closed +0.000 s after the client, `499
  0 … ust=-`, as nginx. **Named residue**: a read that meets a
  post-handshake message (a NewSessionTicket, which an OpenSSL server
  sends after every handshake) waits for the next record inside
  `std.x.tls.client`, where nothing is watched; the handshake's reads after
  the first byte, likewise. An ask for wolf-std (a read that returns after
  one record, or a way to know a record is buffered), to file.
- **Pipelining**: the bytes the watch reads go back with the account
  (`<carrylen>:<carry>`), and the loop puts them behind what the row
  already carried and steps it; the reply keeps the connection. A carry
  that holds a whole head makes the loop's wait budget zero. The same for
  the in-step exchange (no job socket) and `serve_conn`'s. Shape C: two
  responses at ~1.0 s, no `Connection: close`, the third request served.
- **Rows that pass**: `tools/lobo-shell` gains two, each against the
  pinned nginx: (G) eight proxied requests to a silent **https** upstream
  at `worker_connections 16`, the clients close: both `after=200` (trunk:
  `after=closed`); (H) a static GET pipelined during a proxied wait: both
  servers answer twice, no `Connection: close`, and a third request on the
  same connection (trunk: one answer, closed). 44 → **46 probes, 45
  parity, 1 named delta**. And two e2e tests (native, checked):
  `tests/serve/https_abort_e2e.lu` and `tests/serve/pipelined_exchange_e2e.lu`,
  red at trunk.

### 4. lobo#105

- The loop reads a second clock right after its wait (`tw`). A request
  whose first bytes were read in this pass starts at `tw`; one already in
  the carry keeps the start it had. A request served in the step ends at
  `tw`; an exchange ends at the clock its proc read when it finished — the
  reply written or the client's close seen (`<end_ms>` in the account).
  Shapes A, B and D: `rt=1.000`, `1.000`, `0.000` and `0.503` within a few
  ms, as nginx. **A test, `tests/serve/request_time_e2e.lu`** (native,
  checked): the three, red at trunk (0.250, 0.750, 0.751).

### The rest unchanged

- The proxy suite: `proxy-differential` 8/8, the log differential,
  `lobo-resolver` 9/9, `lobo-metrics`; `client_abort_e2e`,
  `silent_upstream_e2e` (and `silent81.py`: every static GET answered, 0
  missed, at the end), `lobo-shell`'s row F; membudget 25/25 (lobo#106's
  numbers reported, not made worse); corpus 374 → 382 lane-runs (four new
  tests, two lanes each).
- **Plants** (RULES.md §7: the PR run itself where it shows the row): the
  PR's first run, at the tests and rows on trunk's `src/`, red at the four
  e2e tests in the corpus step; a plant branch `ws69-plant-shell`
  (trunk's `src/` and the two `lobo-shell` rows) for the rows, which the
  corpus step would otherwise stop in front of.

### What would make this wrong

- The pool's procs, parked in their waits, holding pool workers the next
  spawn needs: the runtime compensates (s231), measured at ws63.
- A proc's poll racing the loop's own use of a descriptor: the loop does
  not wait on a client whose exchange is out (it never did), and a job
  socket's ends are each one side's.
- The stop byte read as a job, or a job read as a stop: a stop is written
  only to a proc with an exchange out, and its frame's first byte is `j`.

## 3. The prediction against the measurement

*(written after the change)*

## 4. Evidence index

kasumi `~/lanes/ws69/` (sha256 prefixes): `toolchains.txt` 331e35be59da…,
`dl/digest-check.txt` 3507bec4588e…; `ev/tput-base.log` 2523dd9e3fe5…,
`ev/tput-base2.log` 09e4cfe54dbd…, `ev/tput-e1.log` 995745015d5a…,
`ev/tput-e2.log` cf036cd463ab…, `ev/drain-base.log` 0869e635227a…,
`ev/drain-nginx.log` 392e75f8aaf8…, `ev/probe-e3.log` 921d1e74225d…,
`ev/prof-pre81-c1.log` 45fbe364439b…, `ev/prof-trunk-c1.log`
38af15dac2b9…, `ev/sysc-pre81-c1-n0.log` c596ba3c8b18…,
`ev/sysc-pre81-c1-n10000.log` f10075d92f19…, `ev/sysc-trunk-c1-n0.log`
e152bb3af5e4…, `ev/sysc-trunk-c1-n10000.log` 8bbc17e706e5…. Scripts
(`scripts/`): stage.sh 29c99406354d…, build.sh 8712c4c9f47c…, launch.sh
619fef23602e…, tput.sh e208754b7eeb…, tput-in.sh 67df184f92ce…, summ.py
941b8f8adfac…, prof.sh d78f15d20acf…, sysc.sh def0df154164…, px69.py
8efb62d375e7… (px81.py 6ddc1608604a…), drain81.py 9f6bb2161c42…
(ws67's), drainng.py 6e963937b645…, probe69.py c30f36229a83….
