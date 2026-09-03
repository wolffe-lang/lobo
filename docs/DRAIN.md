# The drain you can watch (ws08)

nginx's `-s reload` is a shrug: the old workers drain in the dark. lobo
narrates it. An operator can see which config generation is live, how
many connections each older generation still holds, how long it has been
draining, and the moment it retires — from a `lobo status` command and
from log events. This page is the CONTRACT for those two surfaces:
ws09's structured logs and ws12's metrics endpoint reuse the names and
the schema documented here, so a change to either is a change to this
file and a red test (`tests/shell/status_surface.lu` pins every shape).

## How the drain works

The server is one spawn-free poll loop (D7 — the release tier refuses a
task entry's address). The loop multiplexes the http listener, the
control channel, and every open connection, stepping each connection a
slice at a time so none blocks the loop. Every connection is TAGGED with
the generation it was accepted under, and each generation carries a
LIVE-CONNECTION COUNTER in the loop's own bookkeeping — no scan, no lock
across the accept path; the counter moves only at accept and close.

- **accept** → the current generation's counter increments.
- **reload** → the current generation begins DRAINING (it keeps its
  frozen model and its open connections; a request arriving on one of
  those connections still routes the OLD model — the frozen-model
  discipline, ws04) and the freshly parsed model becomes the new current
  generation, which serves all new connections.
- **close** (on any exit path — normal close, keepalive budget spent,
  keepalive idle timeout, error response, malformed request, or a
  worker_shutdown_timeout abort) → the owning generation's counter
  decrements.
- **retire** → a draining generation whose counter reaches zero (or
  whose worker_shutdown_timeout expires) leaves the table.

A debug assertion that a counter never goes negative stays in EVERY
profile (the checked-arithmetic spirit — a leak that made a generation
immortal is loud, not silent).

### Retirement semantics

A draining generation retires when **its live count hits zero OR its
`worker_shutdown_timeout` expires**. Connections still open when the
timeout bites are ABORTED (force-closed) and counted as such, so the
retirement event reads `drained=N aborted=M`: the operator sees that the
timeout, not a clean drain, ended it. With no `worker_shutdown_timeout`
(the directive absent, or `0` — the nginx default) a generation drains
FULLY, however long that takes.

`-s quit` reuses this machinery: it marks the current generation
draining, stops accepting new connections, and exits once everything has
drained. During a quit the status stanza carries `quitting: true`.

## `worker_shutdown_timeout`

The one directive ws08 adds to the compat table (main context, one
argument, nginx's semantics and units). `30s`, `500ms`, and a bare
number (seconds) all parse; absent or `0` means no forced timeout.

## The status surface

`lobo status` reads the stanza off the running master's control channel
(the pid file records the control endpoint at this pin). Two formats:

### `lobo status` (human text, one fact per line)

```
lobo status
current generation: 3
quitting: false
events: 9
generation 1: draining live=2 age-ms=1840 id=0f96da4e7e7c072a mem-hw=4213 budget-503s=1 shutdown-in-ms=28160
generation 3: current live=5 age-ms=1840 id=623a301150e5f3a3 mem-hw=812 budget-503s=0
```

- `age-ms` is time in the generation's current role: since load for the
  current generation, since drain start for a draining one.
- `mem-hw` / `budget-503s` (ws10, appended — every earlier fact keeps
  its place): the high-water admitted bytes of any single request the
  generation served, and its `memory_budget` refusal count. Always
  printed (`0 0` with no budget armed) so a parser never branches;
  docs/BUDGET.md is the model.
- `shutdown-in-ms` appears only for a draining generation under a
  configured `worker_shutdown_timeout` (the remaining budget, clamped at
  0); it is omitted for the current generation and when no timeout is
  set.
- `events` (ws11, appended — every earlier fact keeps its place): the
  count of vocabulary events emitted so far, which is the highest
  `seq=` stamped (see the vocabulary section). The completeness anchor
  for a bug report's attached log: a stream whose top seq matches
  `events` has no trailing hole (docs/REPLAY.md is the workflow).

### `lobo status --format json` (single line, schema-versioned)

```json
{"schema":1,"current":3,"quitting":false,"events":9,"generations":[
  {"gen":1,"state":"draining","live":2,"age_ms":1840,"id":"0f96da4e7e7c072a","mem_high_water":4213,"budget_503s":1,"shutdown_remaining_ms":28160},
  {"gen":3,"state":"current","live":5,"age_ms":1840,"id":"623a301150e5f3a3","mem_high_water":812,"budget_503s":0,"shutdown_remaining_ms":-1}
]}
```

The wire is ONE line (rendered here with breaks for reading). `schema` is
the version — currently **1**; it bumps only on a breaking shape change
(`mem_high_water`/`budget_503s` are ws10's ADDITIVE members, `events`
is ws11's — nothing renamed or moved, so the version holds;
docs/BUDGET.md is the model).
`shutdown_remaining_ms` is `-1` when none applies. ws12's metrics
endpoint serves this same object.

### The generation id

`id` is a content hash of the FROZEN model (16 hex chars). Identical
configs across a reload share an id — an operator can see a reload
changed nothing — and any content change changes it.

### Under `worker_processes N` (ws16)

The stanza above is ONE process's. With N hands the master answers
`lobo status` instead: the same head with the master's numbers
(`live-region-bytes` summed over the hands), `workers: N` appended,
and one `worker i: serving|standby|unreachable control=… generation=…
live=… events=… live-region-bytes=… budget-503s=… restarts=…` row per
hand, folded from each hand's own stanza over its endpoint; the JSON
twin carries `workers_configured`, an empty `generations` array and a
`workers` array (schema stays 1 — additive). A hand's OWN stanza is
the one above plus `worker: N` and `listening: true|false`. Every
shape is pinned in `tests/shell/worker_surface.lu`; docs/WORKERS.md
is the page, and it says why one hand serves while the others stand
by at this pin.

### Snapshot semantics (documented, by design)

A status read races the generation swap on purpose. The stanza is one
pass over the generation-list reference: a read that crosses a swap may
show a torn view ACROSS generations, but each per-generation count is
monotone-correct. This is a documented property, not a global lock — the
sprint deliberately does not serialize the accept path against a reader.

## The log-event vocabulary (FROZEN)

Emitted through the logging seam (ws02 — `lobo: [notice] <event>` on
stderr, UNCHANGED by ws09; when an `error_log` file is configured the
same events land there too, level-gated, in nginx's text shape or as
schema-versioned JSON lines — docs/LOGGING.md). The event NAMES and
FIELD KEYS are a stable contract; ws09's JSON door renders them
verbatim (`"event":"<name>"` plus one member per field, digit values
typed as numbers, keys byte-identical — `age-ms` stays `age-ms`).
Nine events (the sixth is wsm01's EXTENSION, the seventh ws10's, the
eighth and ninth ws13's — each appended, nothing renamed); the LEVEL
column is ws09's (§5: the wws mapping is documented per event, not
vibes):

| event | level | fields | emitted when |
|-------|-------|--------|--------------|
| `generation-loaded` | notice | `gen`, `id` | a config generation is parsed and frozen (start, or a successful reload) |
| `generation-activated` | notice | `gen` | a generation becomes the live, accepting one |
| `generation-draining` | notice | `gen`, `held` | a generation stops accepting and begins draining, still holding `held` connections |
| `connection-retired` | notice | `gen`, `remaining` | one connection on a draining generation closed; `remaining` still held |
| `generation-retired` | notice | `gen`, `drained`, `aborted`, `age-ms` | a draining generation reached zero (or timed out): `drained` closed cleanly, `aborted` force-closed by the timeout |
| `signal-received` | notice | `sig`, `verb` (+ `source`, ws15) | an operator TRIGGER arrived and was mapped to a verb (wsm01; ws15 appends `source`, nothing renamed): `sig` is the meaning name (`reload`\|`terminate`\|`quit`), `verb` the dispatched verb, `source` the door it came through — `signal` for a real OS signal, `control` for a verb on the control endpoint. Both doors run the SAME dispatch and emit through the same builder, so this line and every generation event after it are byte-identical but for `source`; the verbs with no signal twin (`status`, `reopen`, `ping`, `upgrade`) emit nothing, which is what keeps `sig`'s value set frozen. docs/CONTROL.md carries the paired logs and the diff that asserts them |
| `budget-exceeded` | error | `gen`, `site`, `budget`, `would` (+ `cap`, ws14, only at `site=region`) | a request was refused by its `memory_budget` (ws10): `site` the deterministic exceed-site (`head`\|`body`\|`body-chunked`\|`file`\|`admin`\|`region` — the last is the RUNTIME's refusal, ws14, and carries `cap`, the region cap in ledger units), `budget` the configured bytes, `would` what admitting it would have charged (`budget+1` at `region`: a killed proc's charge is unobservable); the request also writes an ordinary 503 access line (docs/BUDGET.md) |
| `upstream-resolved` | notice | `host`, `addrs`, `ttl-ms`, `took-ms` | the resolver answered an upstream name (ws13): `addrs` how many addresses, `ttl-ms` how long the cache holds them (the record TTL or `valid=`, floored at 1 s), `took-ms` the query's wall time (docs/RESOLVER.md) |
| `upstream-resolve-failed` | error | `host`, `reason`, `took-ms` | an upstream name did not resolve (ws13): `reason` one of `nxdomain`\|`servfail`\|`refused`\|`noaddr`\|`malformed`\|`rcode`\|`timeout`\|`io`\|`dial`; the failure is held 1 s and the requests parked on the name answer 502 |
| `worker-started` | notice | `worker`, `restarts` | the MASTER started a hand (ws16, docs/WORKERS.md): `worker` its ordinal, `restarts` how many times this slot has been replaced (0 at the first start) |
| `worker-exited` | notice | `worker`, `reason`, `code` | the master reaped a hand (ws16): `reason` is `exit` (it returned `code`), `signal` (it died without a code — crashed, or killed; `code` is -1) or `unreachable` (its endpoint refused past the supervision grace and the master killed it; `code` is what the reap answered) |

**The seq stamp (ws11, appended — nothing renamed).** Every vocabulary
event above carries one more trailing field, `seq=N`: the event's
ordinal in the one poll loop's emission order (1-based, monotone for
the life of the process — a reload never resets it). The stamp is
applied by the EMISSION SEAM, not the builders, so every shape in the
table is unchanged ahead of it and every prefix pin keeps matching;
the JSON door types it as a number member (`"seq":41`) through the
same generic k=v decode. What it buys: an attached log excerpt is an
ORDERED, GAP-VISIBLE event stream — the loop's own decision order,
quotable in a bug report, with any hole (a level-gated mirror, a
counted drop) visible as a seq gap instead of a silent absence. The
status stanza's `events` fact is the same counter read back. Prose
notices are never stamped: the seq stream IS the vocabulary stream.
docs/REPLAY.md teaches the bug-report workflow this feeds.

Beside the vocabulary, the prose notices ride the same seam with
their own levels: serving-on / signal-arming / reopen / ACME issuance
at `notice`; sink-drop reports at `warn`; ACME failures and
cert-keep errors at `error`; startup refusals at `emerg` (stderr —
they precede the sinks). docs/LOGGING.md is the full ladder story.

Example lifecycle of one reloaded-away generation holding two
connections, both closing cleanly:

```
lobo: [notice] generation-draining gen=1 held=2 seq=5
lobo: [notice] connection-retired gen=1 remaining=1 seq=6
lobo: [notice] connection-retired gen=1 remaining=0 seq=7
lobo: [notice] generation-retired gen=1 drained=2 aborted=0 age-ms=1840 seq=8
```

**The `worker=` stamp (ws16, appended after `seq` — nothing renamed).**
Under `worker_processes N` every line a HAND emits — the events above
and the prose notices alike — ends in one more trailing field,
`worker=N`, its ordinal; the master's own lines carry none, and
neither do a single-process lobo's (the default: byte-identical to
ws15). `seq` stays per PROCESS: a hand's stream is its own total
order, the master's is another, and a merged file holds N+1 streams
separable by the stamp and orderable across each other only by the
wall clock (docs/REPLAY.md states the consequence; docs/WORKERS.md
is the page). The two `worker-*` events are the master's.

Eleven events (nine through ws15, two appended at ws16), and
`signal-received`'s `source` is the ONLY thing in this
vocabulary that says which door an order came through. That is
deliberate: docs/CONTROL.md is the page, and its claim — a control verb
and a real signal are indistinguishable in the log but for that field —
is asserted as a diff by `tools/lobo-signal`, not left as prose.

## Trigger disposition (control channel AND signals — the wsm01 flip)

Both triggers are REAL now and flow through the ONE verb dispatch
ws04 built:

- **Signals** (wsm01, s114 in the s115 pin): a genuine `SIGHUP` is
  `reload`, `SIGTERM` is `stop` (fast shutdown), `SIGQUIT` is `quit`
  (graceful drain-then-exit) — the platform meanings. Delivery is
  Linux-full at this pin; other unixes follow wolf's task-layer port
  and Windows has no HUP/USR2 at all ([os.signal.platform]) — where
  the listen refuses, the server says so at startup and runs
  control-channel-only. The serve loop polls the signal queue
  spawn-free by SELF-RAISING the probe meaning (UPGRADE's bit) each
  pass and waiting once — FIFO delivery returns any real pending
  signal first and the probe bounds the wait. Named residue: a real
  outside `SIGUSR2` is indistinguishable from the probe and ignored
  until the binary-swap sprint claims UPGRADE; and with no getpid
  surface yet, the pid FILE still records the control endpoint, so
  `lobo -s reload` still sends over the channel while `kill -HUP`
  needs the pid from the process table.
- **The control channel** (ws04, made the ORDER DESK at ws15) STAYS:
  the portable trigger, the Windows reload story, and the transport
  for `status` — and now the whole verb set
  (`reload`/`quit`/`stop`/`reopen`/`status`/`upgrade`/`ping`), an
  optional shared-secret arm, and `lobo control <verb>` as its CLI
  door. **docs/CONTROL.md is that page**: the measured per-host
  listener posture (loopback TCP everywhere — wolf has no
  unix-domain socket at this pin, wolf-lang#227), the auth story and
  why lobo reads its token file rather than writing one
  (wolf-std#5), and the nginx differential's rows. Both triggers
  emit through one site, so a verb and a signal write the same log
  but for `source`.

### Windows: what lobo promises for `reload` and `upgrade` (ws14)

s60b landed `[os.signal.platform]`'s windows row in the 5f99b9f pin:
the console handler is the delivery — `CTRL_C` and `CTRL_CLOSE` are
`terminate` (lobo's `stop`), `CTRL_BREAK` is `quit` (the graceful
drain) — and **`RELOAD` and `UPGRADE` have no windows analog**; an
`os_signal_raise` there is in-process only, so lobo's own probe
self-raise (the spawn-free poll) works, and nothing outside the
process can raise `reload`. ws04's control-channel question is
therefore answered in one sentence, and this is the sentence lobo
promises:

> **On windows, `lobo -s reload` reaches a running lobo over its
> `control` endpoint or not at all; there is no signal that reloads
> it, and a config without a `control` directive cannot be reloaded
> without a restart.** `upgrade` (the binary-swap verb, unclaimed on
> every platform at this pin) will be a control-channel verb when it
> exists, and the only trigger for it on windows.

**ws15 flips this sentence from a windows promise to a MEASURED rule
on every host.** Two things changed, and both are witnessed on linux
and macOS rather than claimed:

1. `lobo -s reload` against a config with NO `control` directive now
   REFUSES BY NAME instead of dialling the http port — "a running lobo
   is reached ONLY over its control endpoint at this pin (there is no
   arbitrary-pid signal send — wolf-lang#126)". The second half of the
   windows sentence is therefore true everywhere, for the same reason,
   and `tools/lobo-shell` probes it.
2. `upgrade` EXISTS on the endpoint. It is dispatched, it answers by
   name (unclaimed at this pin), and it is the one verb the endpoint
   reaches that no signal does — on unix because UPGRADE's bit is
   lobo's own poll probe, on windows because there is no external
   UPGRADE at all. "It will be a control-channel verb when it exists"
   is now "it is a control-channel verb, and it says what it is."

What is still CLAIMED and not measured is the windows half itself: the
console-handler mapping, and that no external RELOAD arrives there. The
measured-versus-claimed paragraph below is unchanged by ws15 — lobo's
CI is still linux, and a windows lane is still a ws16-class decision.

What that means in the running server: `os_signal_listen` SUCCEEDS
on windows (unlike the hosts where delivery is unwired), so the
startup notice cannot use the listen's answer to tell the operator
which meanings will actually arrive — and the language has no
platform query to ask. The notice therefore names the MEANINGS and
the two platform maps in one line
(`signal reception armed by meaning … windows CTRL_C/CTRL_CLOSE=
terminate, CTRL_BREAK=quit, no external reload — the control channel
is reload's only trigger there`); an operator reads the line, not a
platform-detected variant of it. `lobo -s reload` already sends over
the channel on every platform (there is no getpid surface, so it
never did anything else — the wsm01 residue), which is why the
seam falls out small: nothing in lobo's dispatch changes, and the
control channel's tests (`tests/shell/control_e2e.lu`, `-s` against
a running master) are the reload witness windows would run.

**Measured versus claimed.** lobo's CI is linux-only and the local
gauntlet runs on linux+macOS; the windows-native tier at this pin
runs spawn/procs/select/net deadlines (s60b) but refuses `wolf build
--release` by name (the LLVM tier is s60c's), and lobo's gauntlet
builds the release tier on every commit — so **nothing on this page
about windows is measured by lobo**. The mapping is CLAIMED from
`[os.signal.platform]`'s normative table and wolf-lang's own
windows floor (261/278 rows, zero refused by construct name at s60b);
the control-channel path is measured on linux and macOS only. A
windows lane for lobo is a ws16-class decision (the CI matrix grows
when the repo goes public), and the first thing it would run is
`tools/lobo-signal`'s skip line and `control_e2e.lu`.

The real-signal witness is `tools/lobo-signal` (a gauntlet step): a
held connection, a real `kill -HUP`, the observable drain, retirement,
then `SIGQUIT`/`SIGTERM` shutdowns — including `SIGTERM` against a
server with NO control directive, because signals need no channel.

## Witnesses

- `tests/shell/drain_watch.lu` — the headline: gen1 drains (count
  falling) while gen2 serves new connections, gen1 retires on its last
  close. Ten-run.
- `tests/shell/overlap_reloads.lu` — three overlapping reloads, three
  generations draining at once, each retiring in order, counts exact.
- `tests/shell/counter_integrity.lu` — every exit path decrements; the
  worker_shutdown_timeout abort retires a stuck draining generation.
- `tests/shell/quit_drains.lu` — `-s quit` drains then exits, status
  shows `quitting: true`.
- `tests/shell/status_surface.lu` — the pure shapes (all three lanes):
  the hash, the timeout parse, the event vocabulary, the stanza
  builders, and the signal meaning/verb map.
- `tools/lobo-signal` — the REAL-SIGNAL witness (wsm01): `kill -HUP`
  drives the observable drain end-to-end; Linux+macOS, named skip
  elsewhere. ws15 adds the INDISTINGUISHABILITY witness: one server
  reloaded twice, once by verb and once by signal, and the two event
  blocks diffed line by line (one differing line, and none once
  `source` is normalized too).
- `tools/lobo-control-differential` — `nginx -s reload` beside `lobo -s
  reload` (ws15): the reload semantics that carry, and the transport /
  parse-locus / narration / idle-keepalive deltas measured rather than
  asserted. docs/CONTROL.md carries the table.
- `tests/shell/control_verbs.lu`, `tests/shell/control_e2e.lu` — the
  endpoint's pure surface and its live auth arm (ws15).
- `tests/shell/worker_surface.lu`, `tests/shell/prefork_e2e.lu`,
  `tools/lobo-prefork` — the many-hands surface, the real master with
  its hands, and the crash/reload/budget/log witness (ws16,
  docs/WORKERS.md).
