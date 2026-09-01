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
Seven events (the sixth is wsm01's EXTENSION, the seventh ws10's —
each appended, nothing renamed); the LEVEL column is ws09's (§5: the
wws mapping is documented per event, not vibes):

| event | level | fields | emitted when |
|-------|-------|--------|--------------|
| `generation-loaded` | notice | `gen`, `id` | a config generation is parsed and frozen (start, or a successful reload) |
| `generation-activated` | notice | `gen` | a generation becomes the live, accepting one |
| `generation-draining` | notice | `gen`, `held` | a generation stops accepting and begins draining, still holding `held` connections |
| `connection-retired` | notice | `gen`, `remaining` | one connection on a draining generation closed; `remaining` still held |
| `generation-retired` | notice | `gen`, `drained`, `aborted`, `age-ms` | a draining generation reached zero (or timed out): `drained` closed cleanly, `aborted` force-closed by the timeout |
| `signal-received` | notice | `sig`, `verb` | a real OS signal arrived and was mapped to an operator verb (wsm01): `sig` is the meaning name (`reload`\|`terminate`\|`quit`), `verb` the dispatched verb — the line that tells a signal-driven reload from a control-channel one |
| `budget-exceeded` | error | `gen`, `site`, `budget`, `would` | a request was refused by its `memory_budget` (ws10): `site` the deterministic exceed-site (`head`\|`body`\|`body-chunked`\|`file`), `budget` the configured bytes, `would` what admitting it would have charged; the request also writes an ordinary 503 access line (docs/BUDGET.md) |

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
- **The control channel** (ws04) STAYS: the portable trigger, the
  Windows reload story, and the transport for `status`.

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
  drives the observable drain end-to-end; Linux, named skip elsewhere.
