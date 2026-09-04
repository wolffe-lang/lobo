# Many hands (ws16, ws17)

nginx's `worker_processes N` is the directive that makes one server
use N cores: a master binds the listening sockets, forks N workers,
and the kernel hands each new connection to whichever worker accepts
it first. This page is the CONTRACT for lobo's version of that
directive under **D73** — prefork through `os.process`, with **D7
kept**: every process is still one spawn-free poll loop, and the task
layer is never involved.

**ws16 built the machinery and MEASURED that the cores stayed idle**:
wolf had no `SO_REUSEPORT` and no descriptor inheritance, so N hands
were one server and N-1 standbys, and the loop time-sliced with
deadlines rather than waiting on readiness. Three issues came out of
that page (wolf-lang#233, #234, #235) and one of them was #127's
customer report.

**ws17 is the sprint where they landed and lobo consumed them.** The
master binds the listeners and hands them down; every hand accepts on
the same socket; `auto` asks the host how many cores it has; and the
serving loop blocks on one `net_wait` instead of a deadline per
socket. What follows states what carries, what each host does
(MEASURED, with the probes), what the master does, the one upstream
thing that is still in the way, and the numbers.

## The directive

```nginx
worker_processes 4;      # four hands
worker_processes auto;   # one per cpu — where the host will say how many
worker_processes 1;      # the default: one process, ws15's lobo, untouched
```

Main context, one argument, nginx's grammar and nginx's `-t`
diagnostic (`"worker_processes" directive invalid value` for a word
that is neither a number nor `auto`, probed against nginx/1.30.4).
One named delta in the reader: `0` serves as 1 (nginx accepts a master
with no hands, which serves nothing).

**`auto` reads `os_cpus()`** (`[os.cpus]`, wolf-lang#233, landed at the
ws17 pin), and the number it answers is **schedulable cores, not
installed ones**: it honours a cgroup cpu quota and a cpu affinity
mask. A container given two cpus of quota on a sixty-four-core host
answers **2** — where ws16's reader counted `processor` rows in
`/proc/cpuinfo` and answered 64, starting sixty-two hands that would
never get a core between them. So the retirement of that reader is a
bug fix, not a shortening. **ws16's macOS notice retires**: the call
answers there (`hw.ncpu`), on linux, and on windows
(`GetSystemInfo`). A host that cannot answer at all is the `io` row
and lobo says so and runs one worker — which is a different sentence
from "this host has one core", and the issue was filed to keep the two
apart.

With `worker_processes 1` (or none) NOTHING on this page happens:
the process that ran `lobo serve` is the server, exactly as it was,
byte for byte in every log line and status fact.

## The processes

With N >= 2, the process that ran `lobo serve` is the **master**:

- it loads and validates the config, refuses a second master (the
  stale-pid check), writes the pid file, binds the config's `control`
  endpoint, and arms signal reception;
- **it binds the http and TLS listeners** (ws17) — nginx's shape, and
  reachable at this pin for the first time. It never ACCEPTS on them:
  they are not in its wait set. It holds them for its whole life,
  because a REPLACEMENT hand has to inherit the same socket;
- it starts N **hands** through `os_spawn_with` (`[os.proc.inherit]`):
  this same executable, `serve -p <prefix> -c <conf> --worker i
  --worker-control 127.0.0.1:<port> --inherit K --hands N`, with the
  listeners in the inherit set. The child receives them as descriptors
  **3, 4, …in the order given** — plaintext first, then TLS — and
  **that numbering is the contract**, so the master never learns a
  descriptor number and a hand is told only how many rode down. Four
  internal flags, none of them on the usage page: an operator never
  types any of them;
- it supervises them (below) and fans every verb out.

A hand is `serve_main` — today's one poll loop — with four
differences: it never touches the pid file, its control endpoint is
the one the master chose, every line it logs ends in `worker=N`, and
its listeners are **adopted** (`net_adopt_listener(3)`), never bound.

No secret crosses the argv: a hand reads the config's `token <file>`
itself, so its endpoint is authorized exactly as the master's is.

**Ownership at close** is `[os.proc.inherit]`'s: both processes hold
their own descriptor for the same socket, so the master closing its
copy does not disturb a hand, and a hand's `net_close` closes only its
own. What an adopted `AF_UNIX` listener does NOT do is unlink its
path — the process that BOUND a path owns it, which for an inherited
listener is the master.
## The listener, per host — measured, not assumed

The language offers two shapes for making N processes accept on one
port, and lobo measured both on this box rather than reading the
manual.

**`net_listen_with(addr, reuse_port, backlog)`** (`[os.net.listen.
opts]`, wolf-lang#234) is a `SO_REUSEPORT` group: N separate sockets
on one address. What the kernel does with the group is the host's, and
`tests/serve/reuse_port_posture.lu` asks it directly — three members,
thirty dials, `net_wait` over the set to see which member the kernel
woke:

```
reuse_port: 0/0/30 of 30 — ONE SOCKET TOOK ALL — the newest bound
member (macOS): a prefork built on reuse_port is one server and N-1
idle sockets
```

On linux the same file prints a spread (the 4-tuple hash); on windows
the option is `unsupported`, refused by name rather than aliased to
`SO_REUSEADDR`, whose delivery promises nothing. **lobo does not take
this shape.** On macOS it would be ws16's posture with a different
cause; on linux it would work — and a server that picks its
architecture per host is a server with two architectures.

**`os_spawn_with` + `net_adopt_listener`** (`[os.proc.inherit]`,
wolf-lang#235) is the shape lobo ships: ONE socket, N processes
accepting on it, which is nginx's own arrangement and the one that
distributes on **both** serving hosts. The witness is the whole
server: `tools/lobo-prefork` fires 90 connection-per-request GETs at a
master with three hands and reads each hand's own accept counter off
`lobo status`:

```
lobo-prefork: ok — 90 connections reached ALL THREE hands
              (rows with accepted>0: 3; counts: 28/32/31)
```

**Windows:** `os_spawn_with` with an EMPTY inherit set serves there,
and `net_adopt_listener` is `unsupported` BY NAME — a `SOCKET` is not
a small stable number a parent can hand over by position. lobo's
fallback is automatic and says so out loud: a spawn that answers
`unsupported` drops to `os_spawn` with no descriptors and the hand
binds and stands by, which is ws16's posture kept alive for exactly
this reason. Still CLAIMED rather than measured — lobo has no windows
lane.

## The accept turn — nginx's `accept_mutex`, and why it is here

**Readiness is not exclusivity, and one connection wakes every hand.**
`net_accept` awaits readiness with the socket's deadline and then runs
a **blocking** `accept(2)`: with N hands on one listener, one wins the
syscall and the losers block inside it — not for their deadline, which
governed only the readiness wait, but **until the next connection
arrives**. A hand parked there answers no control verb and runs no
timer, so its master reads it as gone and replaces it.

That is an upstream defect and it is filed with its measurement
(**wolf-lang#242**). It was found the way this repo finds things:
`worker_processes 2`, one GET, and one hand never spoke again — alive
at 0.0% CPU, a syscall park and not a spin. Isolated three ways: the
non-blocking ask (`net_wait(fds, 0)`) does not park, the blocking one
does, and removing the connection handles from the wait set does not
help, so it is the listener.

Under load it is invisible — the next connection is microseconds away
and unparks every loser, which is why `ab -n 4000 -c 32` across three
hands gives 1338/1336/1327 and looks perfect. It bites when traffic
stops, which is most of the time on most servers.

**What lobo does about it is nginx's own answer**: hands take TURNS.
`shell.accept_turn(worker, hands, now)` gives each hand a
`shell.accept_slice_ms()` slice (10 ms) of a round, assigned by
ordinal off the wall clock — which every hand on one host reads the
same — and a hand puts the listener in its wait set only during its
own slice. Exactly one hand can be in `accept` at any instant, so
there is no race to lose. Two details make it a mechanism rather than
a decoration:

- **the wait is capped at the turn boundary** (`shell.
  accept_wait_ms`). Without it a hand reads the clock, finds the turn
  is not its own, and then blocks for the whole 25 ms idle budget —
  sleeping through its own 10 ms slice, so the listener goes
  unattended for most of every round. Capping is what makes the round
  trip exact, and it was worth **2,725 → 11,622 req/s** when it landed;
- **a turn drains**, up to 64 accepts a pass, each after the first
  guarded by a zero-deadline `net_wait` on the listener alone — the
  ask that cannot block. One accept per pass was ws16's shape and it
  is what held a connection-per-request load to one accept per poll.

The RESIDUAL race is a hand that reads the clock inside its slice and
reaches the syscall after the boundary: microseconds wide, and it can
only bite while connections are ARRIVING, which is exactly when the
next one unparks it. **The turn retires the day #242 lands** — one
pure function and its twin come out, and the `--hands` flag with
them.
## Supervision

The master owns no `try_wait` (std.process F-0065: `os_wait` blocks
and there is no non-blocking form), so it cannot poll a child's
exit. It probes each hand's control endpoint instead — a CONNECT, not
a round trip: a dead process's port refuses at once, a live-but-busy
hand still completes the handshake from its backlog, so the probe
never parks on a hand serving a long connection. The rule:

- a hand is probed **at most every 200 ms** (ws17). The probe is a
  fresh TCP connection every time — there is no channel between a
  master and its hands (nginx has a socketpair; #235's inherited
  descriptor is what would give lobo one) — so probing every pass is
  N connections per pass, each leaving the master's side in
  TIME_WAIT. That is ephemeral-port pressure the master creates for
  itself, and a transient `connect` failure on a HEALTHY hand reads as
  silence: three of them reap a hand that was serving fine, which an
  e2e run did before the interval existed. 200 ms is the rate a
  supervisor needs, because since ws17 a dead hand costs no
  availability at all — its siblings are already accepting — and the
  probe governs how fast the slot is REFILLED, not how fast service
  returns;
- a hand gets a **3 s start grace**; after that, **three consecutive
  silent probes** is "gone";
- gone → `os_kill` (harmless on a corpse), `os_wait` (the reap), the
  `worker-exited` event with the master's reason and what the reap
  answered, then a fresh hand in the same slot — inheriting the SAME
  listeners, so it comes back `serving` — with a fresh endpoint and
  `restarts` bumped: `worker-started … restarts=1`. A hand that died
  inside a second of starting is replaced after a 250 ms pause, so a
  config that kills every hand at once cannot spin the master;
- under `quit`, a gone hand is reaped and NOT replaced; the master
  exits once every hand is gone;
- a **SIGKILLed master leaves its hands serving** (nginx's workers
  notice a dead master through their socketpair channel; lobo's have
  none at this pin — named delta, and #235's descriptor is what would
  close it). `kill -TERM` at the master is the orderly path:
  TERMINATE is `stop`, and `stop` fans out first.

**What a crash costs now.** ws16 measured a 78 ms FAILOVER window
here: the serving hand died, the port came free, and a standby's next
retry took it. ws17 has nothing to fail over — every survivor already
holds the same socket — so `tools/lobo-prefork` measures a REQUEST
instead of a failover, and prints it beside the clock driver's own
cost so the number is honest:

```
lobo-prefork: ok — the service did not blink across the crash
              (gap: 43 ms, MEASURED — minus the clock driver's own
              385 ms; ws16 measured 78 ms of FAILOVER here, ws17
              measures a request)
```
## The verbs fan out

Every verb the master takes reaches the hands over their endpoints,
in ordinal order (docs/CONTROL.md is the verb page):

| verb at the master | what the master does | what each hand does |
|---|---|---|
| `reload` | parses FIRST (D2: a rejected config reaches no hand and the reply names the generation that kept serving), advances its own configuration generation, then sends `reload` to hand 1, then hand 2, … | the ws08 in-process swap: a new generation serves, the old one DRAINS in place and retires — per process, watchable on that hand's own stanza |
| `quit` | fans out, then waits for every hand to go, reaps each, exits 0 | drains and exits |
| `stop` | fans out, gives each hand a moment, kills what is left | stops fast |
| `reopen` | fans out; cycles its own error log | cycles its outputs |
| `status` | folds every hand's stanza into a row (below) | answers its own stanza (with two extra lines) |
| `ping`, `upgrade` | answers itself | — |

The reply names the fan-out: `reload complete (generation 2)
workers=3/3`. The prefix is ws15's, so every script and every
differential row that reads it still reads it; the suffix is the
count of hands that took the verb.

**Rolling replacement is still NOT what a lobo reload does, and the
reason changed.** nginx's reload STARTS new workers on the new config
and tells the old ones to finish; the new workers accept on the
inherited socket, so no connection is refused. ws16 could not do that
at all — a socket could not be handed to a new process. **ws17 can**:
the master holds the listeners and `os_spawn_with` hands them to any
child it starts, which is exactly what the supervision path already
does when it REPLACES a hand. What stops lobo doing it for `reload` is
no longer the language; it is that the in-place generational drain
(ws08) is a better answer for the same money — an operator watches
generation 1 drain beside generation 2 on the SAME hand's stanza, with
no process churn and no window at all — and that row 2 of the control
differential (zero refusals across a reload) is a row lobo keeps
either way. The hands are therefore LONG-LIVED and reload in place,
one after another; `worker-started`/`worker-exited` stay the
supervision's events, never a reload's. The sprint that wants nginx's
literal shape now has the surface for it; it should say why it wants
it.

**And `upgrade` is now reachable.** The pair the binary swap needs —
spawn the new binary with the listeners in its inherit set, let it
adopt them by position — is the pair this page is built on. The verb
still answers "not implemented" (docs/CONTROL.md), but the sentence
under it changed: it is unclaimed work, not an unavailable one.

## Status: a row per hand

`lobo status` (through the pid file, to the master):

```
lobo status
current generation: 2
quitting: false
events: 11
live-region-bytes: 196608
workers: 3
worker 1: serving control=127.0.0.1:52360 generation=2 live=0 accepted=28 events=9 live-region-bytes=65536 budget-503s=0 restarts=1
worker 2: serving control=127.0.0.1:52357 generation=2 live=1 accepted=32 events=14 live-region-bytes=65536 budget-503s=1 restarts=0
worker 3: serving control=127.0.0.1:52358 generation=2 live=0 accepted=31 events=9 live-region-bytes=65536 budget-503s=0 restarts=0
```

**`accepted=` is ws17's field and it is the sprint's instrument**
(appended; every earlier fact keeps its place). With every hand
accepting on one socket, the only way to SEE the kernel distributing
the work is to ask each hand what it took — so an operator reads
distribution off `lobo status` the way this page's numbers were read,
and a lopsided column is a real signal rather than a guess. A hand's
own stanza carries it too, as a third head line after `worker:` and
`listening:`.

- the head is `status_head_text`'s, with the master's numbers:
  `current generation` is the master's configuration generation,
  `events` its own seq top, `live-region-bytes` the SUM over the
  hands; `workers:` is appended (every earlier fact keeps its place);
- one row per hand: `serving` (holds every listener the config asks
  for — under ws17 that is every hand), `standby` (waiting for one
  another hand holds: the windows fallback, and a hand whose adopt was
  refused), or `unreachable` (answered nothing); its endpoint, so an
  operator can
  address ONE hand (`printf 'status\n' | nc 127.0.0.1 52357` is
  what the rig does); its current generation; `live` summed over its
  generations; its own `events` (seq is per PROCESS — docs/REPLAY.md);
  its region bytes; its budget refusals; how many times the master
  has replaced it.

The JSON twin (`--format json`, schema 1, additive): the master's
object carries `"workers_configured":N`, an EMPTY `"generations":[]`
(a master holds no generation table; the array stays so a schema-1
reader never branches) and a `"workers":[…]` array of objects with
the row's facts (`live_region_bytes`, `budget_503s` — the generation
objects' spellings).

A hand's OWN stanza is ws15's plus three head lines — `worker: N`,
`listening: true|false` and `accepted: K` — and, in JSON, three
members ahead of `generations`. The single process prints none of
them.

## Logs: the trailing `worker=` field

A hand stamps ` worker=N` on the END of every line it emits —
vocabulary events after their `seq`, prose notices at their end:

```
lobo: [notice] signal-received sig=reload verb=reload source=control seq=8 worker=2
lobo: [notice] generation-draining gen=1 held=1 seq=9 worker=2
lobo: [notice] listener 127.0.0.1:8080 acquired (port 8080) — serving worker=2
```

Appended, nothing renamed: every prefix pin from ws02 to ws15 still
matches (the ws15 line is a PREFIX of the ws16 line, asserted in
`tests/shell/worker_surface.lu`), the JSON door types it as a number
member through the same k=v decode, and the master's own lines carry
no field at all — they are the single-process shape, byte for byte
(`tools/lobo-prefork` greps both). N hands appending to one
`error_log` file (`O_APPEND`, line-granular, nginx's own posture)
stay separable by it. Access logs are untouched: nginx's have no
worker id, and neither do lobo's.

Two events join the frozen vocabulary (docs/DRAIN.md's table), the
master's: `worker-started worker=N restarts=R` and `worker-exited
worker=N reason=exit|signal|unreachable code=C`.

## The meter and the cap are per hand; `lobo status` is the fold

`memory_budget` (ws10) admits a REQUEST; the region cap (ws14, D40)
bounds a body proc. Both live inside the process that serves the
request, so under `worker_processes N` they are **per hand** — a
budget of 64k is 64k in each of N processes, never 64k across them —
and so is `live_region_bytes()`, the runtime's per-process ledger.
The master's `live-region-bytes:` is the sum over the hands' readings
(a snapshot, one fetch per hand, on the control path); each row
carries its own. `tools/lobo-prefork` witnesses it: a 24 KiB file
under `memory_budget 4k` is 503 on the hand that served it, that
hand's row reads `budget-503s=1`, its siblings' read 0.

`/metrics` (ws12) is served by whichever hand takes the scrape — and
since ws17 that is **a random hand**, because every hand accepts. It
reports THAT process's counters plus the gauge `lobo_worker_id`
naming which, so a scrape is honest about whose numbers it is and a
scraper can tell two scrapes apart. It is not yet the SERVICE's
numbers, and that is the open decision ws16 named for the day this
one arrived: a master-served aggregation, or a `worker` label on every
series. **The numbers to decide it with are now in hand and they argue
for the aggregation**: a `worker` label multiplies the 61-series
exposition by N (18 hands on this box is 1,098 series for one server)
and the cardinality fence in docs/metrics.md exists to stop exactly
that, while the master already folds `live-region-bytes` and
`accepted` over the hands on the control path and could fold the rest
the same way. Routed, with the reasoning, rather than built in the
sprint that could finally see it.

## The measurement

`tools/lobo-prefork-bench [N] [requests] [concurrency]` — not a
gauntlet gate (a number depends on the box) — runs lobo at
`worker_processes 1` and `N`, then the pinned nginx at the same two,
same 1 KiB file, same `ab -n 20000 -c 32`, in two shapes (a connection
per request; `-k` keepalive), and reads cores-used as Σ cpu time over
the process tree ÷ wall time off `ps(1)`. The table it printed on this
box, 2026-09-04 (macOS 15 arm64, 18 cpus, N = 18), with **ws16's
numbers in the last column so the movement is readable**:

| server | shape | req/s | cores used | ws16 req/s |
|---|---|---|---|---|
| lobo worker_processes 1 | close | **11,277.81** | 0.69 | 37.37 |
| lobo worker_processes 1 | keepalive | **10,324.18** | 0.67 | 576.21 |
| lobo worker_processes 18 | close | **12,329.98** | 0.84 | 69.60 |
| lobo worker_processes 18 | keepalive | **9,934.98** | 0.68 | 1,117.68 |
| nginx worker_processes 1 | close | 23,488.10 | 0.47 | 38,123.20 |
| nginx worker_processes 1 | keepalive | 42,654.38 | 0.45 | 73,607.89 |
| nginx worker_processes 18 | close | 19,223.75 | 1.61 | 24,158.09 |
| nginx worker_processes 18 | keepalive | 83,831.08 | 2.18 | 111,383.38 |

(nginx's own numbers move between the two runs by up to 2x — same
binary, same config, a different day and a differently loaded box.
That is the honest scale of run-to-run noise here, and it is why the
lobo movements below are quoted as orders of magnitude and not as
percentages.)

**Read it three times.**

**1. The reactor gate is gone, and it was the whole story.** One
lobo process went from **37 to 11,278 req/s** on the connection-per-
request shape — about **300x** — and from 576 to 10,324 on keepalive.
Nothing about the process count did that: it is `net_wait`. ws16's
loop blocked 25 ms in the control listener's accept, then 25 in the
http listener's, then 12 per open connection, every pass, so a
connection-per-request load got about **one accept per 62 ms pass**.
The loop now wakes when a socket speaks. lobo at one process is
within **2x of nginx at one worker** on the close shape, which is a
sentence this repo has never been able to write.

**2. The kernel distributes, and that is measured elsewhere in this
page** — 90 connections over three hands as 28/32/31, every hand
`serving` on one socket, `accepted=` on every row. W6's first half is
true in the sense the charter meant it: the work reaches every
process.

**3. And `worker_processes N` is still not N x throughput** —
12,330 against 11,278, nine percent — because of the accept turn, and
the turn is there because of wolf-lang#242. Only ONE hand may be in
`accept` at a time, so the accept path is serialized however many
hands there are; what the other hands can overlap is the SERVING, and
with `-c 32` against a 1 KiB static file there is almost no serving to
overlap — the turn-holder drains the whole queue and answers it inside
its own slice. That is exactly what nginx's `accept_mutex` cost nginx,
and it is why nginx turned it off by default once its kernels grew
`EPOLLEXCLUSIVE` and `SO_REUSEPORT`. **The number the fix is worth was
measured directly**, three hands, `ab -n 6000 -c 32`, close shape:
**11,622 req/s with the turn against 17,347 free-for-all** — and
free-for-all is not a shippable posture, because it parks hands.

So the two gates ws16 named have both moved, and a third is now the
front one. In order:

| gate | ws16 | ws17 |
|---|---|---|
| the loop had no readiness surface (#127) | **the front gate**: 0.01 cores, one accept per pass | **gone** — 300x on the close shape |
| the kernel distributed nothing (#234/#235) | filed, unlanded | **gone** — 28/32/31 over three hands |
| `net_accept` parks after its readiness wait (#242) | not reachable — one hand held the listener, so there was never a race to lose | **the front gate**: the accept turn is the workaround and it caps N at one hand's accept rate |

**Idle cost, before and after — measured, and it is not the number
upstream measured.** s137 reported `net_wait` doing ~37x less idle
work than deadline time-slicing, in a synthetic loop. lobo's own loop
was measured the same way — one process, one held keepalive
connection, 120 s of nothing happening, the SAME binary built twice
with only the wait swapped for ws16's per-socket deadlines:

| loop | cpu over 120 s idle |
|---|---|
| ws16: a deadline on every socket, every pass | 0.32 s |
| ws17: one `net_wait` over the set | 0.26 s |

**About 19% less, not 37x**, and the reason is worth writing down
rather than quietly dropping: **lobo's idle loop was never busy.** It
was asleep in a `net_deadline`, which costs a timer and not a core —
roughly two to three milliseconds of cpu per wall second either way.
What the deadline cost was never idle cpu. It was **wake latency**:
the loop learned about a connection when a timer said to look, not
when the socket spoke, and that is the whole of 37 -> 11,278 req/s. A
page that quoted 37x here because upstream measured 37x there would be
quoting someone else's workload; the surface is worth exactly what it
is worth on this one, which is three hundred times more than the
number upstream put on it.

## Witnesses

- `tests/config/worker_processes.lu` — the directive on all three
  lanes: the reader's table, the oracle's `-t` diagnostic, and
  `auto`'s 0 sentinel (the RESOLVER left this surface at ws17 — it is
  `os_cpus()` in main's `serve` arm now, and the count is the
  runner's, so what is asserted is a relation, never a value).
- `tests/serve/reuse_port_posture.lu` — **why lobo does not take
  `reuse_port`**, measured on the host that runs the file: a live
  three-member group, thirty dials, and which member the kernel woke
  printed as the finding. Asserts only what `[os.net.listen.opts]`
  promises everywhere (the group binds; every dial is accepted by
  SOME member; the survivor takes the rest after the others close).
  native + checked — lupin 0.1.25 predates s137.
- `tests/shell/worker_surface.lu` — the pure surface: the hand's argv
  and the args builder `os_spawn_with` wants (no shell, one value per
  element, the four internal flags), the two events, the trailing
  field (the ws15 line is a prefix of the ws16 line, which is a prefix
  of nothing new — `accepted:` is a stanza head, not a log field), the
  master's rows and readers, and **the accept turn**: exactly one of
  three hands holds it at every millisecond of two whole rounds, the
  round walks the ordinals in order, a single hand always holds it,
  and the wait is capped at the boundary in both directions.
- `tests/shell/prefork_e2e.lu` — the real binary with
  `worker_processes 2`: both hands serving on the inherited listener,
  a GET served, each hand's own stanza (`worker: N`, `listening:
  true`, `accepted: K`), **the distribution asserted** (60 connections
  move the counter on BOTH hands), a hand told `stop` directly with
  the survivor serving on and the replacement coming back SERVING
  (`restarts=1`), `reload … workers=2/2` with every row at generation
  2, `quit` exiting 0 with the hands gone.
- `tools/lobo-prefork` — a gauntlet step, 35/35: three hands all
  serving and none standing by, **90 connections reaching all three**
  (the counts printed), a REAL `kill -9` with the service not
  blinking, the master's `worker-exited reason=unreachable code=-1` /
  `worker-started restarts=1` and the replacement SERVING, the rolling
  reload's drain watched on whichever hand took the held connection
  (ws17 cannot assume — the kernel picks), the per-hand budget, the
  log shapes both ways, `kill -TERM` at the master stopping the tree.
- `tools/lobo-prefork-bench` — the table above, re-runnable.
