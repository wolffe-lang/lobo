# The drain you can watch (ws08)

nginx's `-s reload` is a shrug: the old workers drain in the dark. wws
narrates it. An operator can see which config generation is live, how
many connections each older generation still holds, how long it has been
draining, and the moment it retires — from a `wws status` command and
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

`wws status` reads the stanza off the running master's control channel
(the pid file records the control endpoint at this pin). Two formats:

### `wws status` (human text, one fact per line)

```
wws status
current generation: 3
quitting: false
generation 1: draining live=2 age-ms=1840 id=0f96da4e7e7c072a shutdown-in-ms=28160
generation 3: current live=5 age-ms=1840 id=623a301150e5f3a3
```

- `age-ms` is time in the generation's current role: since load for the
  current generation, since drain start for a draining one.
- `shutdown-in-ms` appears only for a draining generation under a
  configured `worker_shutdown_timeout` (the remaining budget, clamped at
  0); it is omitted for the current generation and when no timeout is
  set.

### `wws status --format json` (single line, schema-versioned)

```json
{"schema":1,"current":3,"quitting":false,"generations":[
  {"gen":1,"state":"draining","live":2,"age_ms":1840,"id":"0f96da4e7e7c072a","shutdown_remaining_ms":28160},
  {"gen":3,"state":"current","live":5,"age_ms":1840,"id":"623a301150e5f3a3","shutdown_remaining_ms":-1}
]}
```

The wire is ONE line (rendered here with breaks for reading). `schema` is
the version — currently **1**; it bumps only on a breaking shape change.
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

Emitted through the logging seam (ws02 — `wws: [notice] <event>` on
stderr today; ws09 reformats these into JSON, ws12 into metrics). The
event NAMES and FIELD KEYS are a stable contract. Five events:

| event | fields | emitted when |
|-------|--------|--------------|
| `generation-loaded` | `gen`, `id` | a config generation is parsed and frozen (start, or a successful reload) |
| `generation-activated` | `gen` | a generation becomes the live, accepting one |
| `generation-draining` | `gen`, `held` | a generation stops accepting and begins draining, still holding `held` connections |
| `connection-retired` | `gen`, `remaining` | one connection on a draining generation closed; `remaining` still held |
| `generation-retired` | `gen`, `drained`, `aborted`, `age-ms` | a draining generation reached zero (or timed out): `drained` closed cleanly, `aborted` force-closed by the timeout |

Example lifecycle of one reloaded-away generation holding two
connections, both closing cleanly:

```
wws: [notice] generation-draining gen=1 held=2
wws: [notice] connection-retired gen=1 remaining=1
wws: [notice] connection-retired gen=1 remaining=0
wws: [notice] generation-retired gen=1 drained=2 aborted=0 age-ms=1840
```

## Trigger disposition (control channel vs signal)

The drain is triggered by a `reload`/`quit` over the CONTROL CHANNEL —
ws04's shipped path, the working trigger at this pin and the Windows
reload story. Signal RECEPTION (a real `SIGHUP`/`SIGQUIT` triggering the
same verbs) is wolf-lang #126 / s114; the wws toolchain pin is s109,
which does NOT include it, so the signal path is the campaign's named
deferral. Both triggers flow through the SAME verb dispatch, so the
signal path joins these same tests the sprint after #126 lands on the
pin — no drain logic changes, only the trigger.

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
  the hash, the timeout parse, the event vocabulary, the stanza builders.
