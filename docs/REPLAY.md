# Replay the race (ws11)

A concurrency bug is normally a war story: "it failed once under load,
never on my laptop." In this repo it is an ARTIFACT: a schedule you
can attach to a bug report and a maintainer can replay, byte for byte,
as many times as it takes. This page is the workflow, the pieces that
make it work, and, first because everything else is bounded by it,
the line between what is replayable here and what is not.

## The honesty boundary (read this before trusting a replay)

The deterministic scheduler is lupin's (`--seed`, `--schedule`,
`conform-run --explore`; the book's ch17 is the reader's tour). It
owns every scheduling decision of a program running under lupin:
every channel send/receive, `select`, spawn and join is a decision it
can pin with a seed, replay from that seed, and exhaustively permute
under `--explore` (DPOR, with the frontier's open/closed status stated
in the verdict). Three kinds of nondeterminism are OUTSIDE that space,
and each bounds what lobo can promise:

- Values. A seed replays scheduling decisions, not data. Hash
  seeds, OS identifiers, timestamps, request payloads: exploring
  schedules never varies them. Fuzzing and the corpus own that axis.
- Real time. Under the seeded scheduler time is virtualized; a
  replay validates the HANDLING of a timeout, never its calibration.
  Wall-clock questions belong to a load test against a real peer.
- The membrane. Anything the interpreter cannot see into: the OS,
  real sockets' peers, a spawned NATIVE binary. lobo's e2e suites
  (`drain_watch`, the signal witness, the differential) drive the
  real `target/lobo-debug` over real loopback TCP; that execution is
  the machine's, and it is not seed-replayable.

And the direct consequence for the server itself: lobo is spawn-free
(D7: one poll loop, no tasks), so a running lobo makes no
lupin-scheduling decisions at all. Its "schedule" is the ARRIVAL
ORDER of outside events (accepts, closes, reloads, signals) at the
loop. lobo therefore never prints a seed: it never draws one, and
a seed in the run banner would promise a replay the server cannot
deliver. What lobo's own surfaces carry instead:

- The event stream, ordered and gap-visible. Every vocabulary
  event (docs/DRAIN.md) carries `seq=N`, the loop's own emission
  ordinal. An attached log excerpt is thereby a total order over the
  events that decided the outcome, and a hole (a level-gated mirror,
  a counted drop) shows as a seq gap, never a silent absence.
- The completeness anchor. `lobo status` prints `events: N` (and
  the JSON stanza `"events":N`): the highest seq emitted. A report
  whose log tops out at `seq=N` with status saying `events: N` is a
  complete window.
- No production flight recorder, which is the ch17 posture:
  recording a live service's real schedule for offline
  replay is a different mechanism with a different cost, and neither
  wolf nor lobo has it (the contract's Tier 2; deferral recorded,
  asks filed upstream). What a production incident hands you is the
  seq-ordered event log plus status, enough to RECONSTRUCT the
  decisive order in the rig's model, which is what the
  workflow below automates for the drain shapes.

The multi-process boundary (ws16). Under `worker_processes N`
(docs/WORKERS.md) there are N+1 processes and therefore N+1 seq
streams: each hand stamps its own `seq` from 1 and ends every line
in `worker=N`; the master stamps its own and ends its lines in
nothing. A merged `error_log` is N+1 total orders interleaved at
line granularity (`O_APPEND`), and NOTHING in it orders one hand's
`seq=9` against another's `seq=9` except the wall clock, at
millisecond precision, which is not a total order. So the
completeness anchor is per
stream: a hand's row in `lobo status` carries ITS `events`, and a
bug report against a hand attaches that hand's lines (filter on the
stamp) with that row; the master's `events` bounds the master's
stream (the `worker-started`/`worker-exited` events, the fan-out's
`signal-received`) and nothing else. What crosses processes, the
order in which the master's fan-out reached the hands, is
reconstructible from the master's stream alone (it sends in ordinal
order, one reply at a time) and never from the hands' seqs. A
cross-process schedule is a different mechanism this repo does not
have, as a production flight recorder is.

What ws17 changed about that boundary. Under
ws16 the N+1 streams were N-1 quiet ones, one busy one and the
master: one hand held the listener, so every request in a run
was in one stream and a reader who found the serving hand had found
the whole story. Since ws17 every hand accepts on the same inherited
socket, so the requests of a single run are SPLIT across N streams
by the kernel, and which hand took which request is not reproducible:
it is the accept queue's answer on the day, and re-running the same
load will split it differently. Three consequences a bug report has to
respect:

- read `accepted=` first. Each hand's row in `lobo status` (and
  its own stanza's third head line) says how many connections THAT
  process took; the master's `workers:` block is where a reader learns
  the split before reading a line of log. A hand with `accepted=0` is
  not a hand whose log is empty by accident.
- a request lives entirely in one stream. A connection is accepted
  by one hand and served to completion by that hand (nothing hands a
  connection on), so an access line, its error lines and its
  generation events share a `worker=` stamp and one `seq` order. That
  is what keeps a per-request story readable at all, and the split
  does not take it away.
- there is NO reconstructible cross-stream order, and ws18 took the
  last one away. At ws17 there was one: hands took 10 ms accept turns
  off the wall clock, so a reader with two hands' timestamped lines
  could say which hand OUGHT to have taken a connection that arrived
  at time T. That instrument retired with the turn when wolf-lang#242
  landed (docs/WORKERS.md); the hands now accept free-for-all and the
  kernel alone decides. The loss is written down here because it
  matters: a per-hand `seq` orders one stream and nothing
  orders two, so a cross-stream claim needs a mechanism this repo does
  not have yet.

In one sentence: exploration proves ordering properties over the
events it can see and permute, and the events it can see are the
rig's model programs' channel operations, selects, spawns and joins,
which is where lobo's ordering bugs live.

## The two-command workflow

A schedule-dependent finding always arrives carrying its own
reproduction:

```console
$ .wolf-bin/lupin conform-run <case>.lu --explore=500
<case>.lu: explored 16 schedule(s) in 16 execution(s) (DPOR; ...), frontier closed
  outcomes: 3 distinct — SCHEDULE-DEPENDENT
    ...
    exit(0) ×6 stdout=... — replay: --seed=4611686018427387922
      decision stream: ev:0,0,0,0,1
$ .wolf-bin/lupin run <case>.lu --seed=4611686018427387922
```

Command one finds; command two replays, forever, on any machine at
the pinned toolchain. Hand somebody the SEED when they need a number;
hand them the DECISION STREAM (`--schedule=ev:0,0,0,0,1`, the same
run) when they need to READ the counterexample: the stream is the
schedule in diffable form, and comparing it against a passing one
says which decisions differ before you read a line of code.

## The rig surfaces

- `//! explore: N` (tests/replay/, the corpus runner): the file's
  whole schedule space explored on every gauntlet run. Green requires
  agreement AND a CLOSED frontier; an open frontier is red even when
  every explored schedule agrees, because the verdict would then be
  conditional on the budget. A dependent outcome is red with the
  explorer's replay lines printed.
- `LOBO_SEED=<seed> tools/lobo-corpus`: every lupin-lane run adds
  `--seed=$LOBO_SEED`, so the suite reruns under the seed a bug report
  names. A failure prints the replay command. (A debugging
  posture, not a gate: the FIFO-pinned directives are pinned for the
  unseeded default.)
- `tools/lobo-replay` (a gauntlet step): the end-to-end witness,
  every run. It explores the PLANTED race, requires the finding,
  captures the failing schedule as a `.loborace` artifact, replays it
  from the artifact (twice by seed, once by decision stream, all
  three byte-identical against the artifact's recorded bytes), and
  then explores the FIXED twin to a closed one-outcome frontier.

## The specimen pair (tests/replay/)

`drain_finish_race.lu` keeps the ws08 drain-finish hazard alive as a
model: generation 1 draining two held connections, and a collector
that decides "retired" by RACING the shutdown-timeout message against
the close events in one `select`. The composite "count every close,
then retire" was never atomic against the two message kinds that
decide it. Its stdout is the log excerpt a bug report would carry,
from lobo's real vocabulary builders, seq-stamped:

```
lobo: [notice] generation-draining gen=1 held=2 seq=1
lobo: [notice] connection-retired gen=1 remaining=1 seq=2
lobo: [notice] generation-retired gen=1 drained=1 aborted=1 age-ms=0 seq=3
```

Read the seq stream and the bug is visible before the code is: the
retirement at `seq=3` arrived while `remaining=1`, with a close still
outstanding. Under strict FIFO (any unseeded run, a developer's
laptop) the drain is always clean; eight of sixteen inequivalent
schedules are clean too. The machine's own schedules cluster at the
FIFO end, which is why this class "never reproduces".

`drain_finish_fixed.lu` is the REAL serve loop's shape: retirement is
a STATE CHECK (live count reaching zero; the timeout consulted
against the clock, in the loop's own bookkeeping, `retire_zero` in
`src/main.lu`), never a message race. Same tasks, same channels, same
`select`; the explorer closes a 24-schedule frontier on ONE outcome.
Its `//! explore: 64` mark keeps that true on every gauntlet run, so
the accounting stays schedule-independent under test.

## The .loborace artifact (schema 1)

Written by `tools/lobo-replay` to `target/replay/`; the shape a bug
report attaches when the finding comes from the rig:

```json
{"schema":1,
 "case":"tests/replay/drain_finish_race.lu",
 "seed":"4611686018427387922",
 "schedule":"ev:0,0,0,0,1",
 "verdict":"exit(0)",
 "stdout_sha256":"23d04d87…",
 "stdout":"lobo: [notice] generation-draining gen=1 held=2 seq=1\n…",
 "lupin":"lupin 0.1.19 (wolf-interp, reference interpreter at pin 83f83bb)"}
```

`seed` and `schedule` are BOTH carried (the number you hand somebody;
the schedule you can read and diff), the stdout pair pins the
expected bytes, and `lupin` names the interpreter identity the replay
holds under; a seed is a fact about a scheduler version, so the
artifact says which.

## What a bug report should attach (the server side)

For a live-server incident (not seed-replayable, per the boundary
above): the error-log/stderr window with its seq-stamped vocabulary
events, and a `lobo status` snapshot. The seq stream gives the
maintainer the decisive event ORDER; `events:` bounds the window's
completeness; the drain model in tests/replay/ is the template for
driving that order deterministically under the rig and exploring its
neighborhood for the counterexample the incident sampled.

## Tier 2, re-read at ws13 (what the language must provide, stated against s132)

The Tier-2 gate was filed at ws11 as wolf-lang#197 with three shapes:
(1) a runtime opt-in to the seeded scheduler for a NON-test binary,
(2) schedule capture as a value mid-run, (3) the record/replay io
boundary stated by the language. This page re-reads them against the
pin that carries s132 (regions with caps, and D68's proc-boundary
faults) because ws13 also put the first proc into lobo's request path
(the cap adoption: the regioned body work of a budgeted request runs
inside a `spawn proc`, and its breach reaches the join as
`fault(alloc-contract)`). Four things follow, each a shape, none
built:

1. A capture must be written on the JOIN side, never inside the
   failing proc. `[conc.proc.kill]`: a contained trap runs no
   further user code in the proc: no defer, no handler, no writer.
   The 5xx that Tier 2 wants to attach a schedule to is DECIDED at the
   join (the loop maps the exit reason to the response), so the
   capture writer lives in the loop, keyed on the reason class. This
   is already how lobo's `budget-exceeded site=region` event is
   emitted; a capture would ride the same seam.
2. The reason class is a stable key. `[conc.proc.exit]` is a
   closed set and `fault(kind)` draws `kind` from `[conf.trap.set]`'s
   closed vocabulary. A capture-on-5xx policy can therefore be
   spelled over reason classes (`fault(alloc-contract)`,
   `fault(*)`, `error(*)`), and the same
   spelling works for a future per-connection proc. The ask to #197:
   the mid-run capture surface should be reachable from a monitor's
   `exit(reason)` arm, so the join that already holds the reason can
   ask "the schedule so far" in the same select.
3. The record boundary now has a natural place: the proc argument
   record. s87's `[abi.native.procenv]` copies a proc's arguments at
   spawn. For lobo's body proc those are `(sock, path, head, cap,
   pipe)`: scalars and strings, no sockets read INSIDE the proc except
   the file and the write to the client. A Tier-2 recorder that
   captures proc argument records at spawn (plus the seed) has
   recorded everything the proc's schedule depended on; the io that
   crosses the membrane (the socket write) is replayed against a sink.
   That is #197's third shape made concrete: record at the proc
   boundary and replay the proc, not the process.
4. What a proc can say back is the limit on what a capture can
   carry. At this pin a proc's `normal(value)` is unreadable at the
   join and a channel cannot be a proc argument on wolfc (filed from
   ws13; the cap adoption carries its one number out through a
   loopback self-pipe). A capture token or a schedule handle produced
   INSIDE a proc could not leave it either. So shape (2)'s "capture
   as a value" must be a value the JOIN side obtains (from the
   monitor, the supervisor, or a runtime query keyed by the proc id),
   not one the proc hands back.

None of this changes lobo's honesty boundary above: a running lobo
still prints no seed and promises no replay. It changes what the ask
looks like, and the four points are posted to #197 as the ws13
re-read.
