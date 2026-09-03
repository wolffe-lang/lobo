# Many hands (ws16)

nginx's `worker_processes N` is the directive that makes one server
use N cores: a master binds the listening sockets, forks N workers,
and the kernel hands each new connection to whichever worker accepts
it first. This page is the CONTRACT for lobo's version of that
directive under **D73** — prefork through `os.process`, with **D7
kept**: every process is still one spawn-free poll loop, and the task
layer is never involved. It states what carries, what the host can
and cannot do at this pin (MEASURED, with the probes), what the
master does, and the number the sprint was for.

## The directive

```nginx
worker_processes 4;      # four hands
worker_processes auto;   # one per cpu — where the host will say how many
worker_processes 1;      # the default: one process, ws15's lobo, untouched
```

Main context, one argument, nginx's grammar and nginx's `-t`
diagnostic (`"worker_processes" directive invalid value` for a word
that is neither a number nor `auto`, probed against nginx/1.30.4).
Two named deltas in the reader: `0` serves as 1 (nginx accepts a
master with no hands, which serves nothing), and `auto` on macOS is 1
with a startup notice — the count lives behind `sysctl(3)` there,
wolf has no cpu query and cannot read a child's stdout, so nothing
can ask (**wolf-lang#233**). linux answers through `/proc/cpuinfo`;
windows through `NUMBER_OF_PROCESSORS` (claimed, not measured — lobo
has no windows lane).

With `worker_processes 1` (or none) NOTHING on this page happens:
the process that ran `lobo serve` is the server, exactly as it was,
byte for byte in every log line and status fact.

## The processes

With N >= 2, the process that ran `lobo serve` is the **master**:

- it loads and validates the config, refuses a second master (the
  stale-pid check), writes the pid file, binds the config's `control`
  endpoint, and arms signal reception;
- it binds **no http listener** — see the next section for why the
  hands bind their own;
- it starts N **hands** through `os_spawn`: this same executable,
  `serve -p <prefix> -c <conf> --worker i --worker-control
  127.0.0.1:<port>` — the two internal flags that make a process a
  hand rather than a master (its ordinal, and the loopback control
  endpoint the master will reach it on; the master picks a free port
  for each). No secret crosses the argv: a hand reads the config's
  `token <file>` itself, so its endpoint is authorized exactly as the
  master's is;
- it supervises them (below) and fans every verb out.

A hand is `serve_main` — today's one poll loop — with three
differences: it never touches the pid file, its control endpoint is
the one the master chose, and every line it logs ends in `worker=N`.

## The listener, per host — measured, not assumed

nginx's workers share ONE listening socket, inherited across
`fork()`; a server that instead has every worker bind the same port
does it with `SO_REUSEPORT`. Neither is expressible at this pin, and
both were measured rather than read off a manual (macOS 15 / arm64,
wolf 0.2.3+dev.31170d1; the runtime's net.rs is unchanged since the
v0.2.3 tag):

```
# probe 1: a self-spawned child binds the parent's bound address
parent-bind: ok 127.0.0.1:64705
child-bind: io                 <- EADDRINUSE, coarsened: no SO_REUSEPORT
child exit: 0
parent-second-bind: io

# probe 2: a child's descriptor table while the parent holds a listener
tcp-fds-in-child: 0            <- every runtime socket is CLOEXEC;
                                  os_spawn passes only stdio
```

`crates/wolf_rt/src/net.rs` binds `std::net::TcpListener`, which sets
`SO_REUSEADDR` and never `SO_REUSEPORT`; Rust opens every socket
close-on-exec and `Command::spawn` inherits nothing but stdio; and
`std.net.Listener { fd }` is the runtime's TABLE INDEX, so there is
no call that could adopt an inherited descriptor even if one arrived.
Filed as **wolf-lang#234** (SO_REUSEPORT, or a listener option) and
**wolf-lang#235** (descriptor inheritance and adoption — the pair
`upgrade` will need too), with **wolf-std#6** for the std half.

**So at this pin the hands take turns rather than share.** Every hand
tries the bind at start and RETRIES it every pass: the first to win
it **serves**; the others **stand by**, and the moment the serving
hand dies — the kernel frees the port on its exit — a standby's next
retry binds it and serves. That is failover in one poll interval, and
it is what `tools/lobo-prefork` measures with a real `kill -9`:

```
lobo-prefork: ok — a standby took the listener after the crash
              (failover window: 78 ms, MEASURED — minus the clock
              driver's own 223 ms)
```

What it is NOT is throughput: N hands are N-1 standbys and one
server, and the section after next says so with a number. The day
#234 lands, every hand's bind succeeds, the same loop distributes
accepts across all of them, and this section shrinks to one
sentence — no lobo code moves, because the retry IS the
`SO_REUSEPORT` shape minus the kernel's cooperation.

**Windows:** nothing here is measured. `os_spawn` runs there and the
runtime's sockets are non-inheritable there too (`Command::spawn`'s
contract on every host), so the posture would be the same standby
posture — CLAIMED from the runtime's code, and stated as such until
lobo has a windows lane (still a repo-goes-public decision).

## Supervision

The master owns no `try_wait` (std.process F-0065: `os_wait` blocks
and there is no non-blocking form), so it cannot poll a child's
exit. It probes each hand's control endpoint instead — a CONNECT, not
a round trip: a dead process's port refuses at once, a live-but-busy
hand still completes the handshake from its backlog, so the probe
never parks on a hand serving a long connection. The rule:

- a hand gets a **3 s start grace**; after that, **three consecutive
  silent passes** is "gone";
- gone → `os_kill` (harmless on a corpse), `os_wait` (the reap), the
  `worker-exited` event with the master's reason and what the reap
  answered, then a fresh hand in the same slot with a fresh endpoint
  and `restarts` bumped — `worker-started … restarts=1`. A hand that
  died inside a second of starting is replaced after a 250 ms pause,
  so a config that kills every hand at once cannot spin the master;
- under `quit`, a gone hand is reaped and NOT replaced; the master
  exits once every hand is gone;
- a **SIGKILLed master leaves its hands serving** (nginx's workers
  notice a dead master through their socketpair channel; lobo's have
  none at this pin — named delta). `kill -TERM` at the master is the
  orderly path: TERMINATE is `stop`, and `stop` fans out first.

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

**Rolling replacement is NOT what a lobo reload does at this pin,
and this is a named delta from nginx.** nginx's reload STARTS new
workers on the new config and tells the old ones to finish; the new
workers accept on the inherited socket, so no connection is refused.
lobo cannot hand a socket to a new process (#235), so a
spawn-new-and-retire-old reload would refuse connections in the gap
between the old hand closing its listener and the new one binding —
and row 2 of the control differential (zero refusals across a reload)
is a row lobo keeps. The hands are therefore LONG-LIVED and reload
in place, one after another; `worker-started`/`worker-exited` are
the supervision's events, never a reload's.

## Status: a row per hand

`lobo status` (through the pid file, to the master):

```
lobo status
current generation: 2
quitting: false
events: 11
live-region-bytes: 196608
workers: 3
worker 1: standby control=127.0.0.1:52360 generation=2 live=0 events=9 live-region-bytes=65536 budget-503s=0 restarts=1
worker 2: serving control=127.0.0.1:52357 generation=2 live=1 events=14 live-region-bytes=65536 budget-503s=1 restarts=0
worker 3: standby control=127.0.0.1:52358 generation=2 live=0 events=9 live-region-bytes=65536 budget-503s=0 restarts=0
```

- the head is `status_head_text`'s, with the master's numbers:
  `current generation` is the master's configuration generation,
  `events` its own seq top, `live-region-bytes` the SUM over the
  hands; `workers:` is appended (every earlier fact keeps its place);
- one row per hand: `serving` (holds every listener the config asks
  for), `standby` (waiting for one another hand holds), or
  `unreachable` (answered nothing); its endpoint, so an operator can
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

A hand's OWN stanza is ws15's plus two head lines — `worker: N` and
`listening: true|false` — and, in JSON, two members ahead of
`generations`. The single process prints neither.

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

`/metrics` (ws12) is served by whichever hand holds the listener — at
this pin, the one serving hand — and reports THAT process's counters,
plus the gauge `lobo_worker_id` naming which. A scrape is one hand's
numbers; the sum lives in the master's `status`, not in the
exposition. When #234 lands and every hand serves, a scrape lands on
a random hand, and the honest next step is a master-served
aggregation or a `worker` label — named here, not built: the
cardinality fence (docs/metrics.md) is a decision to take at that
pin with the numbers in hand.

## The measurement

`tools/lobo-prefork-bench [N] [requests] [concurrency]` — not a
gauntlet gate (a number depends on the box) — runs lobo at
`worker_processes 1` and `N`, then the pinned nginx at the same two,
same 1 KiB file, same `ab -n 20000 -c 32`, in two shapes (a
connection per request; `-k` keepalive), and reads cores-used as Σ
cpu time over the process tree ÷ wall time off `ps(1)`. The table it
printed on this box, 2026-09-03 (macOS 15 arm64, 18 cpus, N = 18):

| server | shape | req/s | cpu s | wall s | cores used |
|---|---|---|---|---|---|
| lobo worker_processes 1 | close | 37.37 | 1.11 | 107.38 | 0.01 |
| lobo worker_processes 1 | keepalive | 576.21 | 0.35 | 7.18 | 0.05 |
| lobo worker_processes 18 | close | 69.60 | 11.90 | 57.77 | 0.21 |
| lobo worker_processes 18 | keepalive | 1117.68 | 1.06 | 3.82 | 0.28 |
| nginx worker_processes 1 | close | 38123.20 | 0.07 | 0.36 | 0.19 |
| nginx worker_processes 1 | keepalive | 73607.89 | 0.05 | 0.31 | 0.16 |
| nginx worker_processes 18 | close | 24158.09 | 0.80 | 0.47 | 1.70 |
| nginx worker_processes 18 | keepalive | 111383.38 | 0.28 | 0.34 | 0.82 |

Read the lobo rows twice. **Cores used: 0.01 at one hand, 0.21 at
eighteen** — lobo is not CPU-bound at all. The serving loop is
DEADLINE-bound: each idle pass blocks 25 ms in the control
listener's accept and 12 ms per open connection's read step (the
ws04 shape every hand inherits), so a connection-per-request load
gets about one accept per pass. And the 1.9x from 1 to 18 hands is
NOT a second core: exactly one hand holds the listener at N=18
(`lsof` shows one LISTEN socket; one row says `serving`) — the
master's per-pass CONNECT probe lands on the serving hand's control
listener and wakes its accept, removing the 25 ms idle stall, which
doubles that one hand's pass rate. The other 0.20 cores are seventeen
standbys retrying a bind and answering probes. nginx at 1 worker
does 1000x the close-shape rate on 0.19 cores; at 18 it spends 1.70
cores because the kernel spreads the accepts.

**The finding, stated as the numbers say it.** Two things stand
between lobo and the cores, and #234 is only the second. The first is
lobo's own: a spawn-free loop with no readiness surface can only
time-slice with deadlines (wolf has no poll/select over sockets —
wolf-lang#127 is the reactor ask, and this table is its customer
report), so ONE hand uses 0.01 of a core and would not use more with
the kernel's help. The second is the kernel's: with #234/#235 unlanded
N hands are one server and N-1 standbys, so `worker_processes N` is
supervision, not throughput. What the sprint built is witnessed either
way — supervision, failover, fan-out, a row per hand, a field per line
— and what a prefork that does not scale is worth today is the crash
row: a serving hand can die and the service does not. The order of
the two fixes is the order of the two numbers: the loop's stall first
(a maintenance row in the closeout), then the kernel's share.

## Witnesses

- `tests/config/worker_processes.lu` — the directive on all three
  lanes: the reader's table, the oracle's `-t` diagnostic, the
  cpu-count reader.
- `tests/shell/worker_surface.lu` — the pure surface: the hand's
  argv (no shell, one value per element), the internal flags' CLI
  rules, the two events, the trailing field (the ws15 line is a
  prefix of the ws16 line), the master's rows and the readers.
- `tests/shell/prefork_e2e.lu` — the real binary with
  `worker_processes 2`: the posture, a GET served by the hand that
  says so (`worker: N`, `listening: true`, `lobo_worker_id N`), the
  serving hand told `stop` directly → failover to the other ordinal
  and replacement (`restarts=1`), `reload … workers=2/2` with every
  row at generation 2, `quit` exiting 0 with the hands gone.
- `tools/lobo-prefork` — a gauntlet step: three hands, a REAL
  `kill -9` with the failover window measured, the master's
  `worker-exited reason=unreachable code=-1` / `worker-started
  restarts=1`, the rolling reload's drain watched on one hand's own
  stanza, the per-hand budget, the log shapes both ways, `kill -TERM`
  at the master stopping the tree.
- `tools/lobo-prefork-bench` — the table above, re-runnable.
