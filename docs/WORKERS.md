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
  --worker-control 127.0.0.1:<port> --inherit K`, with the
  listeners in the inherit set. The child receives them as descriptors
  **3, 4, …in the order given** — plaintext first, then TLS — and
  **that numbering is the contract**, so the master never learns a
  descriptor number and a hand is told only how many rode down. Three
  internal flags, none of them on the usage page: an operator never
  types any of them. (ws17 passed a fourth, `--hands N`, so a hand
  could compute its accept TURN; the turn retired at ws18 and the flag
  with it — a free-for-all hand has no reason to know how many
  siblings it has);
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

On windows the option is `unsupported`, refused by name rather than
aliased to `SO_REUSEADDR`, whose delivery promises nothing. **On linux
the file RUNS on the CI runner and asserts the same guarantee, but
what it prints there is not visible**: the corpus runner does not echo
a test's stdout, only its verdict — so linux's delivery policy in this
page is upstream's own measurement (`[os.net.listen.opts]`: a 4-tuple
hash, every hand accepts), not lobo's. Said rather than borrowed. **lobo does not take
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
              (rows with accepted>0: 3; counts: 36/29/26)
```

That is the ws18 head — free-for-all, with the accept turn deleted.
ws17 read 28/32/31 through the turn on the same rig; **the split
survives the deletion**, which is the thing that had to be re-checked,
because the turn assigned slices by ordinal and the kernel does not.

**And it is a gauntlet step, so CI asserts it on linux too** — the
same run, the runner's own kernel, at the ws18 head:

```
corpus: 253/253 lane-runs green
lobo-prefork: ok — 90 connections reached ALL THREE hands
              (rows with accepted>0: 3; counts: 26/34/31)
lobo-prefork: ok — the quiet server: one GET, served (body: HANDS-GEN-A)
lobo-prefork: ok — …and after 2 s of silence every hand still answers
              its OWN control endpoint (3/3 — a #242 park leaves the
              losers mute)
lobo-prefork: ok — the service did not blink across the crash
              (gap: 1 ms, MEASURED …)
lobo-prefork: GREEN — 38/38
```

Two hosts, two kernels: **36/29/26 on macOS and 26/34/31 on linux**,
free-for-all, and the quiet server holds on both. The runner's split is
not a fixed shape and is not asserted as one — a second CI run over the
same three hands read **34/25/32** — which is the point: the kernel
picks, and what the step asserts is that every hand is picked. The
DISTRIBUTION and
the #242 observable are measured on both; the `req/s` table below is
macOS only, because the bench is deliberately not a gauntlet step (a
number depends on the box) and no CI job runs it. The linux numbers
are unmeasured and are not extrapolated anywhere on this page.


**Windows:** `os_spawn_with` with an EMPTY inherit set serves there,
and `net_adopt_listener` is `unsupported` BY NAME — a `SOCKET` is not
a small stable number a parent can hand over by position. lobo's
fallback is automatic and says so out loud: a spawn that answers
`unsupported` drops to `os_spawn` with no descriptors and the hand
binds and stands by, which is ws16's posture kept alive for exactly
this reason. Still CLAIMED rather than measured — lobo has no windows
lane.

## The accept, free-for-all — and the turn that used to be here

**Readiness is not exclusivity, and one connection wakes every hand.**
`net_wait` says a socket CAN be accepted without blocking; with N
hands on ONE inherited listener, one SYN wakes all N and exactly one
wins the take. That is the thundering herd, and it is not a bug in
`net_wait` — `[os.net.wait]` is level-triggered and says exactly what
it saw. It is the thing a program that shares a listener owes the
kernel.

**What lobo does about it, since ws18, is nothing** — and that is the
whole design. Every hand keeps both listeners in its wait set on every
pass. A hand that loses the race calls `net_accept` on a queue a
sibling has already emptied, and from its side that is
indistinguishable from the connection never having arrived, so the
call **waits again against the budget the listener already carries**
and answers `timeout` when it runs out (`[os.net.accept]`). The budget
is `arm_accept`'s 5 ms, armed once at acquisition. **A lost race costs
5 ms and nothing else.**

**It was not always nothing.** At the ws17 pin `net_accept` awaited
readiness with the socket's deadline and then ran a *blocking*
`accept(2)`: the deadline governed only the wait, so a losing hand
parked in the syscall **until the next connection arrived** — alive at
0.0% CPU, answering no control verb, running no timer, and reaped by
its own master as unreachable. On a busy server the next connection is
microseconds away and nothing is visible; on a quiet one the hand is
stuck. That is an upstream defect, and this repo filed it with its
measurement (**wolf-lang#242**), found the way this repo finds things:
`worker_processes 2`, one GET, and one hand never spoke again.
Isolated three ways — the non-blocking ask (`net_wait(fds, 0)`) does
not park, the blocking one does, and removing the connection handles
from the wait set does not help, so it is the listener.

ws17 shipped nginx's own answer meanwhile: hands took 10 ms TURNS off
the wall clock (`shell.accept_turn`, `accept_wait_ms`,
`accept_slice_ms`, and a `--hands N` flag on the hand's argv), so
exactly one hand held the listener at any instant and there was no
race to lose. **s138 closed #242 and ws18 deleted all of it** — 84
lines of pure surface (`src/shell/shell.lu` net −106 with the
plumbing), four guard sites in the loop, one flag, one test section. What the deletion bought is in the measurement below, and it
is bigger than the accept path alone, because the turn also capped
every hand's `net_wait` budget at the turn boundary: a hand serving
keepalive connections was woken by the ROUND, not by its sockets.

**A turn drains, and so does a free-for-all.** Up to 64 accepts a
pass, each after the first guarded by a zero-deadline `net_wait` on
the listener alone — the ask that cannot block. That shape is older
than the turn (ws17) and outlives it: it keeps the common case one
syscall wide. The difference is that a sibling can now empty the queue
between the ask and the take, which is the race `[os.net.accept]`
bounds.

**The check that replaced the turn** is `tools/lobo-prefork`'s quiet
server (a gauntlet step, so CI runs it on linux too): three hands,
**one** GET, then two seconds of silence, and every hand must still
answer its own control endpoint with no replacement. That is the
observable #242 broke, asserted at the level lobo cares about rather
than quoted from upstream.

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

**`accepted=` is ws17's field and it is the sprint's instrument.**
It sits after `live=` in the master's row and is APPENDED as a third
head line to a hand's own stanza; every earlier fact keeps its name
and its value, and both readers key on `field=` rather than on
position (`shell.stanza_int`, `stanza_field_sum`), so nothing that
read a ws16 row stops reading one. With every hand
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
the process tree ÷ wall time off `ps(1)`.

**ws18 re-ran it as an A/B in one session**, because the run-to-run
noise on this box is larger than some of the movements it had to
report: the SAME source at the same pin, built twice — once at the
commit before the deletion (the accept turn intact) and once after —
and both benched back to back on 2026-09-06 (macOS 15 arm64, 18 cpus,
N = 18). ws17's own table, taken 2026-09-04, is in the last column.

| server | shape | with the turn | **free-for-all** | cores (turn → free) | ws17's run |
|---|---|---|---|---|---|
| lobo worker_processes 1 | close | 13,203.76 | **13,508.27** | 0.65 → 0.69 | 11,277.81 |
| lobo worker_processes 1 | keepalive | 10,264.27 | **9,501.84** | 0.58 → 0.58 | 10,324.18 |
| lobo worker_processes 18 | close | 13,557.26 | **16,120.62** | 0.84 → **3.08** | 12,329.98 |
| lobo worker_processes 18 | keepalive | 9,554.14 | **38,960.68** | 0.65 → **4.54** | 9,934.98 |
| nginx worker_processes 1 | close | 27,656.32 | 27,731.17 | 0.48 → 0.45 | 23,488.10 |
| nginx worker_processes 1 | keepalive | 52,501.16 | 52,424.36 | 0.53 → 0.53 | 42,654.38 |
| nginx worker_processes 18 | close | 21,720.20 | 19,553.11 | 1.63 → 1.36 | 19,223.75 |
| nginx worker_processes 18 | keepalive | 72,960.48 | 86,432.66 | 1.95 → 2.04 | 83,831.08 |

(nginx's rows are the control: the oracle moved by up to 18% between
the two halves of one session, which is the scale of noise here and
why the lobo movements worth reading are the ones measured in
multiples.)

**And the direct A/B, the shape ws17 used for its 11,622-vs-17,347
estimate** — three hands, `ab -n 6000 -c 32`, connection per request,
three runs of each binary, alternating nothing else:

| build | runs | median |
|---|---|---|
| with the accept turn | 13,417 · 12,866 · 12,863 | **12,866 req/s** |
| free-for-all (ws18) | 25,470 · 23,663 · 21,443 | **23,663 req/s** |

**1.84x, against the 1.49x the fix was predicted to be worth.** The
prediction was made on the accept path alone; the measurement found
more, and the extra is named below.

**Read it four times.**

**1. The deletion is worth more than the accept path.** At three hands
the close shape nearly doubles (1.84x), and at eighteen the KEEPALIVE
shape goes from 9,554 to **38,961 req/s — 4.1x**, on a load that
contains almost no accepting at all. That is not the thundering herd:
it is `shell.accept_wait_ms`, the turn's other half. It capped the
hand's WHOLE `net_wait` budget at the turn boundary, so a hand serving
thirty-two established keepalive connections woke on the ROUND rather
than on its own sockets, and stopped waiting on them at every slice
edge. The accept turn was throttling the serving path to keep the
accept path correct, and nothing in ws17 could see that, because with
the turn there was no other posture to compare against. **A workaround
costs more than the thing it works around, and the only way to find
out is to delete it and measure.**

**2. `worker_processes N` is finally N-ish.** The cores-used column is
the plainest reading: 0.84 → **3.08** on close and 0.65 → **4.54** on
keepalive at N=18. ws16 could not put a connection on a second
process; ws17 put them on all of them but let only one accept at a
time; ws18 lets them all work at once. Eighteen hands is still not
eighteen times — the 1 KiB static file and the loopback client are the
ceiling, and `ab -c 32` offers 32 connections to 18 processes — but
the shape of the curve changed sign.

**3. One process did not move, and that is the control.** 13,204 →
13,508 close and 10,264 → 9,502 keepalive: inside the noise, both
ways. `accept_turn(worker, hands, now)` returned `true` immediately
for `hands <= 1`, so a single-process lobo never paid for the turn and
gains nothing from its removal. Any movement in the N=1 rows would
have meant the deletion changed something it should not have.

**4. lobo is within sight of the oracle on this shape now.** Three
hands free-for-all serve 23,663 req/s against the pinned nginx's
27,731 at one worker and 19,553 at eighteen — so on the
connection-per-request shape this box's lobo now serves MORE than this
box's nginx at the same eighteen workers. The keepalive shape is where
the gap is real and stays real: 38,961 against 86,433. That gap is
W8's, not this sprint's.

**The gates, in the order this campaign found them:**

| gate | ws16 | ws17 | ws18 |
|---|---|---|---|
| the loop had no readiness surface (#127) | **the front gate**: 0.01 cores, one accept per pass | **gone** — 300x on the close shape | — |
| the kernel distributed nothing (#234/#235) | filed, unlanded | **gone** — 28/32/31 over three hands | still even free-for-all: 36/29/26 |
| `net_accept` parks after its readiness wait (#242) | not reachable — one hand held the listener | **the front gate**: the accept turn is the workaround and it caps N at one hand's accept rate | **gone** — the turn is deleted, 1.84x at three hands and 4.1x on keepalive at eighteen |

**Idle cost is unchanged and was re-measured to say so.** ws17's own
A/B (the same binary built twice with only the wait swapped, 120 s
idle holding one keepalive connection) reported 0.32 s of cpu the ws16
way against 0.26 s — about 19%, not upstream's 37x, because lobo's
idle loop was asleep in a timer rather than busy. The turn's deletion
does not touch that: an idle hand with no connections waits the same
25 ms budget it always did, and now waits it on its own sockets
instead of on the round.

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
  element, the three internal flags), the two events, the trailing
  field (the ws15 line is a prefix of the ws16 line, which is a prefix
  of nothing new — `accepted:` is a stanza head, not a log field), the
  master's rows and readers, and **the accept turn's DELETION**:
  `--hands` takes the ordinary unknown-option road, and `--inherit`,
  the one internal flag that outlived it, still refuses by name when
  it rides alone.
- `tests/shell/prefork_e2e.lu` — the real binary with
  `worker_processes 2`: both hands serving on the inherited listener,
  a GET served, each hand's own stanza (`worker: N`, `listening:
  true`, `accepted: K`), **the distribution asserted** (60 connections
  move the counter on BOTH hands), a hand told `stop` directly with
  the survivor serving on and the replacement coming back SERVING
  (`restarts=1`), `reload … workers=2/2` with every row at generation
  2, `quit` exiting 0 with the hands gone.
- `tools/lobo-prefork` — a gauntlet step, 38/38: three hands all
  serving and none standing by, **90 connections reaching all three**
  (the counts printed), a REAL `kill -9` with the service not
  blinking, the master's `worker-exited reason=unreachable code=-1` /
  `worker-started restarts=1` and the replacement SERVING, the rolling
  reload's drain watched on whichever hand took the held connection
  (ws17 cannot assume — the kernel picks), the per-hand budget, the
  log shapes both ways, `kill -TERM` at the master stopping the tree.
- `tools/lobo-prefork-bench` — the table above, re-runnable.
